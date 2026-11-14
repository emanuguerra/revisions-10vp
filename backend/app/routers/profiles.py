from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import current_profile
from ..models import ExerciseType, FocusSession, Mission, Profile, Question, Unit
from ..rewards import rewards
from ..schemas import FocusIn, ProfileIn, ProfileOut, RewardsOut, UnitProgress

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.post("", response_model=ProfileOut)
def create_profile(body: ProfileIn, db: Session = Depends(get_db)):
    p = Profile(nickname=body.nickname.strip(), class_code=body.class_code.strip().upper())
    db.add(p)
    db.commit()
    return p


@router.get("/me", response_model=ProfileOut)
def me(profile: Profile = Depends(current_profile)):
    return profile


def best_scores(db: Session, profile_id: int, unit_id: int) -> dict[int, int]:
    rows = db.execute(
        select(Mission.level, func.max(Mission.score))
        .where(Mission.profile_id == profile_id, Mission.unit_id == unit_id, Mission.status == "done")
        .group_by(Mission.level)
    ).all()
    return {level: score for level, score in rows}


@router.get("/me/progress", response_model=list[UnitProgress])
def progress(unit: Optional[str] = None, profile: Profile = Depends(current_profile), db: Session = Depends(get_db)):
    units = db.scalars(select(Unit).where(Unit.enabled.is_(True)).order_by(Unit.order)).all()
    out = []
    for u in units:
        if unit and u.slug != unit:
            continue
        base = (select(Question).join(ExerciseType)
                .where(Question.profile_id == profile.id, ExerciseType.unit_id == u.id, Question.status != "open"))
        qs = db.scalars(base).all()
        missions_done = db.scalar(select(func.count(Mission.id)).where(
            Mission.profile_id == profile.id, Mission.unit_id == u.id, Mission.status == "done")) or 0
        out.append(UnitProgress(
            unit=u.slug, title=u.title, answered=len(qs),
            correct=sum(q.status == "correct" for q in qs),
            correct_first=sum(q.status == "correct" and q.tries == 0 for q in qs),
            best=best_scores(db, profile.id, u.id), missions_done=missions_done,
            last_activity=max((q.answered_at for q in qs if q.answered_at), default=None),
        ))
    return out


@router.get("/me/rewards", response_model=RewardsOut)
def my_rewards(profile: Profile = Depends(current_profile), db: Session = Depends(get_db)):
    return rewards(db, profile)


@router.post("/me/focus", response_model=RewardsOut)
def focus_done(body: FocusIn, profile: Profile = Depends(current_profile), db: Session = Depends(get_db)):
    """A focus session was completed: it counts for the XP and the badges."""
    db.add(FocusSession(profile_id=profile.id, minutes=body.minutes))
    db.commit()
    return rewards(db, profile)
