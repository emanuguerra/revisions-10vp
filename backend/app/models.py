"""Database schema.

Catalogue (loaded from content/ by `python -m app.seed`):
    Subject -> Unit -> Lesson (theory blocks)
                    -> ExerciseType (points to a generator in app/generators)
                    -> Item (static content: vocabulary, true/false statements, ...)

Student activity:
    Profile -> Mission (a series of questions) -> Question (one generated question, its answers and points)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def now() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return uuid.uuid4().hex


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    color: Mapped[str] = mapped_column(String(20), default="#2f5bea")
    order: Mapped[int] = mapped_column(Integer, default=0)
    planned: Mapped[list[str]] = mapped_column(JSON, default=list)

    units: Mapped[list[Unit]] = relationship(back_populates="subject", order_by="Unit.order")


class Unit(Base):
    __tablename__ = "units"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    title: Mapped[str] = mapped_column(String(200))
    subtitle: Mapped[str] = mapped_column(Text, default="")
    order: Mapped[int] = mapped_column(Integer, default=0)
    ui_lang: Mapped[str] = mapped_column(String(8), default="fr")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    # levels, categories, mission, scoring, training... (see content/units/*/unit.yaml)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    subject: Mapped[Subject] = relationship(back_populates="units")
    lessons: Mapped[list[Lesson]] = relationship(back_populates="unit", order_by="Lesson.order", cascade="all, delete-orphan")
    exercise_types: Mapped[list[ExerciseType]] = relationship(back_populates="unit", order_by="ExerciseType.order")


class Lesson(Base):
    __tablename__ = "lessons"
    __table_args__ = (UniqueConstraint("unit_id", "slug"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"))
    slug: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(200))
    order: Mapped[int] = mapped_column(Integer, default=0)
    # [{"type": "html"|"markdown"|"widget", ...}]
    blocks: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)

    unit: Mapped[Unit] = relationship(back_populates="lessons")


class ExerciseType(Base):
    __tablename__ = "exercise_types"
    __table_args__ = (UniqueConstraint("unit_id", "key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"))
    key: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(200))
    generator: Mapped[str] = mapped_column(String(100))
    order: Mapped[int] = mapped_column(Integer, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    params: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    unit: Mapped[Unit] = relationship(back_populates="exercise_types")


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (UniqueConstraint("unit_id", "kind", "key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"))
    kind: Mapped[str] = mapped_column(String(32))
    key: Mapped[str] = mapped_column(String(100))
    order: Mapped[int] = mapped_column(Integer, default=0)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, default=new_id)
    nickname: Mapped[str] = mapped_column(String(60))
    class_code: Mapped[str] = mapped_column(String(30), default="", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"), index=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"))
    level: Mapped[int] = mapped_column(Integer, default=0)
    # "mission": fixed series with a result · "training": one exercise type, open-ended
    mode: Mapped[str] = mapped_column(String(16), default="mission", server_default="mission")
    # exercise keys, one per question
    sequence: Mapped[list[str]] = mapped_column(JSON, default=list)
    # {"category": ..., "items": [forced item keys], "used": [item keys already asked]}
    state: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    index: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[int] = mapped_column(Integer, default=0)
    streak: Mapped[int] = mapped_column(Integer, default=0)
    good: Mapped[int] = mapped_column(Integer, default=0)
    good_first: Mapped[int] = mapped_column(Integer, default=0)
    # active (also when paused: the student can resume it later) | done | abandoned
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    unit: Mapped[Unit] = relationship()


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"), index=True)
    exercise_type_id: Mapped[int] = mapped_column(ForeignKey("exercise_types.id"))
    mission_id: Mapped[Optional[int]] = mapped_column(ForeignKey("missions.id"), nullable=True, index=True)
    position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=0)
    item_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # sent to the student: prompt, choices, figure, ...
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    # never sent before the end: answer, tolerance, explanation, hint
    solution: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    tries: Mapped[int] = mapped_column(Integer, default=0)
    eliminated: Mapped[list[Any]] = mapped_column(JSON, default=list)
    first_answer: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    answers: Mapped[list[Any]] = mapped_column(JSON, default=list, server_default="[]")  # every checked answer
    hint_used: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(16), default="open")  # open | correct | wrong
    points: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    answered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    exercise_type: Mapped[ExerciseType] = relationship()


class FocusSession(Base):
    """A completed focus session (15 or 20 minutes of work before a break)."""
    __tablename__ = "focus_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"), index=True)
    minutes: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
