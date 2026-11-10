"""Question lifecycle: generate, check an answer (with retries), hint, reveal, score missions.

All the rules live here so the front end never sees the answer before the end:
- number / text: up to `max_tries` attempts (expressions: an equivalent answer in the wrong
  form, e.g. not reduced, gets a message but costs no attempt)
- choice / side: each wrong option is eliminated; when only the right one is left
  (e.g. vrai/faux), the correction is shown instead of giving the answer away
- points come from the unit's `scoring` config (first try, after correction, hint cost, streak bonus)
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .algebra import check_answer
from .formatting import fr, norm_text, parse_num
from .generators import GENERATORS, GenContext
from .models import ExerciseType, Item, Mission, Profile, Question, Unit, now

DEFAULT_SCORING = {"first": 10, "retry": 5, "hint_cost": 3, "streak_bonus": 5, "streak_from": 3}
DEFAULT_RETRY = "Ce n'est pas la bonne réponse. Corrige ta réponse et vérifie à nouveau."


class EngineError(ValueError):
    """Bad request from the client (wrong state, invalid choice...)."""


def unit_items(db: Session, unit: Unit) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for it in db.scalars(select(Item).where(Item.unit_id == unit.id).order_by(Item.order)):
        out.setdefault(it.kind, []).append({"key": it.key, **it.data})
    return out


def create_question(
    db: Session, profile: Profile, ex: ExerciseType, level: int, *,
    mission: Optional[Mission] = None, category: Optional[str] = None,
    exclude: Optional[set[str]] = None, forced_item: Optional[str] = None,
    rng: Optional[random.Random] = None,
) -> Question:
    unit = ex.unit
    gen = GENERATORS.get(ex.generator)
    if gen is None:
        raise EngineError(f"unknown generator '{ex.generator}'")
    ctx = GenContext(
        level=level, rng=rng or random.Random(), title=ex.title, params=ex.params or {},
        items=unit_items(db, unit), categories=unit.config.get("categories", {}),
        category=category, exclude=exclude or set(), forced_item=forced_item,
    )
    g = gen(ctx)
    q = Question(
        profile_id=profile.id, exercise_type_id=ex.id, level=level, item_key=g.item_key,
        mission_id=mission.id if mission else None, position=mission.index if mission else None,
        payload=g.payload(), solution=g.solution(),
    )
    db.add(q)
    db.flush()
    return q


# ------------------------------------------------------------------ answers

@dataclass
class Outcome:
    status: str            # correct | retry | wrong | invalid
    message: str = ""


def _check(q: Question, value: Any) -> Outcome:
    kind, sol = q.payload["kind"], q.solution
    retry_msg = sol.get("retry_message") or DEFAULT_RETRY

    if kind == "number":
        x = parse_num(value)
        if math.isnan(x):
            return Outcome("invalid", "Écris un nombre, par exemple 8,6.")
        if abs(x - sol["answer"]) <= sol["tol"]:
            return Outcome("correct")
        q.tries += 1
        q.first_answer = q.first_answer or str(value)[:200]
        if q.tries >= q.payload["max_tries"]:
            return Outcome("wrong")
        close = abs(x - sol["answer"]) < max(1, abs(sol["answer"]) * 0.05)
        hint = ("Tu es proche : vérifie l'arrondi et ton dernier calcul." if close
                else "Vérifie ton calcul, corrige ta réponse et clique à nouveau sur Vérifier.")
        return Outcome("retry", f"{fr(x)} n'est pas juste. {hint}")

    if kind == "text":
        raw = str(value).strip()
        if not raw:
            return Outcome("invalid", "Type an answer. · Écris une réponse.")
        if sol.get("check") == "expr":
            res = check_answer(raw, sol["answer"][0], sol.get("form") or "reduced")
            if res.status in ("invalid", "form"):  # an equivalent answer in the wrong form costs no attempt
                return Outcome("invalid", res.message)
            if res.status == "correct":
                return Outcome("correct")
        elif norm_text(raw) in {norm_text(a) for a in sol["answer"]}:
            return Outcome("correct")
        q.tries += 1
        q.first_answer = q.first_answer or raw[:200]
        return Outcome("wrong") if q.tries >= q.payload["max_tries"] else Outcome("retry", retry_msg)

    if kind in ("choice", "side"):
        options = list(range(len(q.payload["choices"]))) if kind == "choice" else q.payload["choices"]
        if kind == "choice":
            try:
                value = int(value)
            except (TypeError, ValueError):
                return Outcome("invalid", "Choix invalide.")
        if value not in options or value in q.eliminated:
            return Outcome("invalid", "Choix invalide.")
        if value == sol["answer"]:
            return Outcome("correct")
        q.tries += 1
        q.eliminated = [*q.eliminated, value]
        if q.first_answer is None:
            q.first_answer = q.payload["choices"][value] if kind == "choice" else str(value)
        remaining = len(options) - len(q.eliminated)
        if remaining <= 1 or q.tries >= q.payload["max_tries"]:
            return Outcome("wrong")
        return Outcome("retry", retry_msg)

    raise EngineError(f"unknown answer kind '{kind}'")


def _scoring(unit: Unit) -> dict[str, int]:
    return {**DEFAULT_SCORING, **unit.config.get("scoring", {})}


def _finish(db: Session, q: Question, correct: bool) -> None:
    """Close the question, compute points and update the mission (if any)."""
    q.status = "correct" if correct else "wrong"
    q.answered_at = now()
    unit = q.exercise_type.unit
    s = _scoring(unit)
    mission = db.get(Mission, q.mission_id) if q.mission_id else None
    first_try = correct and q.tries == 0

    streak = (mission.streak if mission else 0) + 1 if first_try else 0
    points = 0
    if correct:
        base = s["first"] if first_try else s["retry"]
        if base > 0:
            points = max(1, base - (s["hint_cost"] if q.hint_used else 0))
        if first_try and s["streak_bonus"] and streak >= s["streak_from"]:
            points += s["streak_bonus"]
    q.points = points

    if mission:
        mission.streak = streak
        mission.score += points
        mission.good += int(correct)
        mission.good_first += int(first_try)


def answer(db: Session, q: Question, value: Any) -> Outcome:
    if q.status != "open":
        raise EngineError("question already finished")
    out = _check(q, value)
    if out.status != "invalid":
        q.answers = [*q.answers, str(value)[:200]]
    if out.status == "retry" and q.mission_id:
        mission = db.get(Mission, q.mission_id)
        mission.streak = 0
    if out.status in ("correct", "wrong"):
        _finish(db, q, out.status == "correct")
    return out


def reveal(db: Session, q: Question) -> None:
    if q.status != "open":
        raise EngineError("question already finished")
    q.tries = max(q.tries, 1)
    _finish(db, q, False)


def use_hint(q: Question) -> str:
    if q.status != "open":
        raise EngineError("question already finished")
    if not q.solution.get("hint"):
        raise EngineError("no hint for this question")
    q.hint_used = True
    return q.solution["hint"]


# ------------------------------------------------------------------ missions

def build_sequence(unit: Unit, count: Optional[int], rng: random.Random, offset: int = 0) -> list[str]:
    cfg = unit.config.get("mission", {})
    if cfg.get("mode") == "sequence":
        return list(cfg["sequence"])
    types = cfg.get("types") or [e.key for e in unit.exercise_types if e.enabled]
    counts = cfg.get("counts", [10])
    n = count or counts[0]
    seq = [types[(i + offset) % len(types)] for i in range(n)]
    rng.shuffle(seq)
    return seq


def exercise_by_key(unit: Unit, key: str) -> ExerciseType:
    for e in unit.exercise_types:
        if e.key == key and e.enabled:
            return e
    raise EngineError(f"unknown exercise '{key}' in unit '{unit.slug}'")


def mission_question(db: Session, profile: Profile, mission: Mission) -> Question:
    ex = exercise_by_key(mission.unit, mission.sequence[mission.index])
    st = mission.state or {}
    forced = st.get("items", [])
    q = create_question(
        db, profile, ex, mission.level, mission=mission, category=st.get("category"),
        exclude=set(st.get("used", [])), forced_item=forced[mission.index] if mission.index < len(forced) else None,
    )
    if q.item_key:
        mission.state = {**st, "used": [*st.get("used", []), q.item_key]}
    return q


def _close_paused(db: Session, profile: Profile, unit: Unit, mode: str) -> None:
    """One paused session per unit and mode: starting a new one abandons the old one."""
    for m in db.scalars(select(Mission).where(Mission.profile_id == profile.id, Mission.unit_id == unit.id,
                                              Mission.mode == mode, Mission.status == "active")):
        m.status = "abandoned"


def active_sessions(db: Session, profile: Profile, unit: Unit) -> list[Mission]:
    return list(db.scalars(select(Mission).where(
        Mission.profile_id == profile.id, Mission.unit_id == unit.id, Mission.status == "active",
    ).order_by(Mission.created_at.desc())))


def mission_questions(db: Session, m: Mission) -> list[Question]:
    return list(db.scalars(select(Question).where(Question.mission_id == m.id).order_by(Question.position)))


def start_training(db: Session, profile: Profile, unit: Unit, exercise: str, level: int) -> tuple[Mission, Question]:
    ex = exercise_by_key(unit, exercise)
    _close_paused(db, profile, unit, "training")
    m = Mission(profile_id=profile.id, unit_id=unit.id, level=level, mode="training", sequence=[ex.key], state={})
    db.add(m)
    db.flush()
    return m, mission_question(db, profile, m)


def start_mission(db: Session, profile: Profile, unit: Unit, level: int, count: Optional[int],
                  category: Optional[str], item_keys: Optional[list[str]]) -> tuple[Mission, Question]:
    _close_paused(db, profile, unit, "mission")
    rng = random.Random()
    if item_keys:
        seq = build_sequence(unit, len(item_keys), rng, offset=2)
        state = {"items": rng.sample(item_keys, len(item_keys))}
    else:
        if category:
            # a topic may have fewer items than the requested count: ask each item once
            available = sum(1 for items in unit_items(db, unit).values() for it in items if it.get("category") == category)
            counts = unit.config.get("mission", {}).get("counts", [10])
            count = min(count or counts[0], available) or None
        seq = build_sequence(unit, count, rng)
        state = {"category": category} if category else {}
    m = Mission(profile_id=profile.id, unit_id=unit.id, level=level, sequence=seq, state=state)
    db.add(m)
    db.flush()
    return m, mission_question(db, profile, m)


def next_in_mission(db: Session, profile: Profile, m: Mission) -> Optional[Question]:
    if m.status != "active":
        raise EngineError("mission is finished")
    current = db.scalar(select(Question).where(Question.mission_id == m.id, Question.position == m.index))
    if current and current.status == "open":
        raise EngineError("answer the current question first")
    if m.mode == "training":  # open-ended: one more question of the same exercise
        m.sequence = [*m.sequence, m.sequence[0]]
    elif m.index + 1 >= len(m.sequence):
        m.status = "done"
        m.finished_at = now()
        return None
    m.index += 1
    return mission_question(db, profile, m)
