"""Missions (a series of questions) and free training (one question at a time)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import engine
from ..db import get_db
from ..deps import current_profile
from ..models import Mission, Profile, Question
from ..schemas import (AnswerIn, AnswerOut, MissionIn, MissionNextOut, MissionStartOut, MissionState,
                       MistakeOut, QuestionOut, TrainingIn)
from .catalog import get_unit
from .profiles import best_scores

router = APIRouter(prefix="/api", tags=["play"])


def q_out(q: Question) -> QuestionOut:
    p = q.payload
    return QuestionOut(
        id=q.id, exercise=q.exercise_type.key, level=q.level, kind=p["kind"], category=p["category"],
        prompt=p["prompt"], choices=p.get("choices"), unit=p.get("unit", ""), figure=p.get("figure"),
        has_hint=p["has_hint"], hint=q.solution.get("hint") if q.hint_used else None,
        max_tries=p["max_tries"], tries=q.tries, eliminated=q.eliminated, status=q.status, position=q.position,
    )


def m_out(m: Mission) -> MissionState:
    return MissionState(id=m.id, unit=m.unit.slug, level=m.level, index=m.index, total=len(m.sequence),
                        score=m.score, streak=m.streak, good=m.good, good_first=m.good_first, status=m.status)


def own_question(db: Session, qid: str, profile: Profile) -> Question:
    q = db.get(Question, qid)
    if q is None or q.profile_id != profile.id:
        raise HTTPException(404, "Question introuvable.")
    return q


def own_mission(db: Session, mid: int, profile: Profile) -> Mission:
    m = db.get(Mission, mid)
    if m is None or m.profile_id != profile.id:
        raise HTTPException(404, "Mission introuvable.")
    return m


def fail(e: engine.EngineError):
    raise HTTPException(400, str(e)) from e


def final_out(db: Session, q: Question, status: str, message: str = "") -> AnswerOut:
    sol = q.solution
    final = q.status != "open"
    mission = db.get(Mission, q.mission_id) if q.mission_id else None
    out = AnswerOut(status=status, message=message, final=final, tries=q.tries,
                    max_tries=q.payload["max_tries"], eliminated=q.eliminated, points=q.points,
                    mission=m_out(mission) if mission else None)
    if final:
        out.explain = sol["explain"]
        out.correct_answer = sol["answer"] if q.payload["kind"] in ("choice", "side") else None
        out.answer_display = sol.get("answer_display")
        out.summary = sol.get("summary")
        out.speak = sol.get("speak")
    return out


@router.post("/questions", response_model=QuestionOut)
def training_question(body: TrainingIn, profile: Profile = Depends(current_profile), db: Session = Depends(get_db)):
    unit = get_unit(db, body.unit)
    try:
        q = engine.create_question(db, profile, engine.exercise_by_key(unit, body.exercise), body.level, category=body.category)
    except engine.EngineError as e:
        fail(e)
    db.commit()
    return q_out(q)


@router.get("/questions/{qid}", response_model=QuestionOut)
def get_question(qid: str, profile: Profile = Depends(current_profile), db: Session = Depends(get_db)):
    return q_out(own_question(db, qid, profile))


@router.post("/questions/{qid}/answer", response_model=AnswerOut)
def answer(qid: str, body: AnswerIn, profile: Profile = Depends(current_profile), db: Session = Depends(get_db)):
    q = own_question(db, qid, profile)
    try:
        out = engine.answer(db, q, body.value)
    except engine.EngineError as e:
        fail(e)
    db.commit()
    return final_out(db, q, out.status, out.message)


@router.post("/questions/{qid}/hint")
def hint(qid: str, profile: Profile = Depends(current_profile), db: Session = Depends(get_db)):
    q = own_question(db, qid, profile)
    try:
        text = engine.use_hint(q)
    except engine.EngineError as e:
        fail(e)
    db.commit()
    return {"hint": text}


@router.post("/questions/{qid}/reveal", response_model=AnswerOut)
def reveal(qid: str, profile: Profile = Depends(current_profile), db: Session = Depends(get_db)):
    q = own_question(db, qid, profile)
    try:
        engine.reveal(db, q)
    except engine.EngineError as e:
        fail(e)
    db.commit()
    return final_out(db, q, "wrong")


@router.post("/missions", response_model=MissionStartOut)
def start_mission(body: MissionIn, profile: Profile = Depends(current_profile), db: Session = Depends(get_db)):
    unit = get_unit(db, body.unit)
    levels = len(unit.config.get("levels", [])) or 1
    if not 0 <= body.level < levels:
        raise HTTPException(400, "Niveau invalide.")
    counts = unit.config.get("mission", {}).get("counts")
    if body.count and counts and body.count not in counts:
        raise HTTPException(400, "Nombre de questions invalide.")
    try:
        m, q = engine.start_mission(db, profile, unit, body.level, body.count, body.category, body.item_keys)
    except engine.EngineError as e:
        fail(e)
    db.commit()
    return MissionStartOut(mission=m_out(m), question=q_out(q))


@router.post("/missions/{mid}/next", response_model=MissionNextOut)
def next_question(mid: int, profile: Profile = Depends(current_profile), db: Session = Depends(get_db)):
    m = own_mission(db, mid, profile)
    previous = best_scores(db, profile.id, m.unit_id).get(m.level, 0)
    try:
        q = engine.next_in_mission(db, profile, m)
    except engine.EngineError as e:
        fail(e)
    db.commit()
    if q:
        return MissionNextOut(mission=m_out(m), question=q_out(q))
    qs = db.scalars(select(Question).where(Question.mission_id == m.id).order_by(Question.position)).all()
    mistakes = [MistakeOut(item_key=x.item_key, summary=x.solution.get("summary"), given=x.first_answer,
                           category=x.payload["category"])
                for x in qs if not (x.status == "correct" and x.tries == 0)]
    return MissionNextOut(mission=m_out(m), best=max(previous, m.score), previous_best=previous, mistakes=mistakes)


@router.post("/missions/{mid}/abandon", response_model=MissionState)
def abandon(mid: int, profile: Profile = Depends(current_profile), db: Session = Depends(get_db)):
    m = own_mission(db, mid, profile)
    if m.status == "active":
        m.status = "abandoned"
        db.commit()
    return m_out(m)
