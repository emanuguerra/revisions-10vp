from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Item, Subject, Unit
from ..schemas import ExerciseOut, ItemOut, LessonOut, SubjectOut, UnitOut

router = APIRouter(prefix="/api", tags=["catalogue"])


def get_unit(db: Session, slug: str) -> Unit:
    unit = db.scalar(select(Unit).where(Unit.slug == slug, Unit.enabled.is_(True)))
    if unit is None:
        raise HTTPException(404, f"Unité « {slug} » introuvable.")
    return unit


@router.get("/subjects", response_model=list[SubjectOut])
def subjects(db: Session = Depends(get_db)):
    rows = db.scalars(select(Subject).order_by(Subject.order)).all()
    return [
        SubjectOut(slug=s.slug, title=s.title, color=s.color, planned=s.planned or [],
                   units=[u for u in s.units if u.enabled])
        for s in rows
    ]


@router.get("/units/{slug}", response_model=UnitOut)
def unit(slug: str, db: Session = Depends(get_db)):
    u = get_unit(db, slug)
    return UnitOut(
        slug=u.slug, title=u.title, subtitle=u.subtitle, ui_lang=u.ui_lang, subject=u.subject.slug,
        config=u.config, lessons=[LessonOut.model_validate(lesson) for lesson in u.lessons],
        exercises=[ExerciseOut.model_validate(e) for e in u.exercise_types if e.enabled],
    )


@router.get("/units/{slug}/items", response_model=list[ItemOut])
def items(slug: str, kind: Optional[str] = None, db: Session = Depends(get_db)):
    u = get_unit(db, slug)
    stmt = select(Item).where(Item.unit_id == u.id).order_by(Item.order)
    if kind:
        stmt = stmt.where(Item.kind == kind)
    return [ItemOut(key=i.key, kind=i.kind, data=i.data) for i in db.scalars(stmt)]
