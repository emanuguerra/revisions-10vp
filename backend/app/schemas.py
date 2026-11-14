from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------- catalogue

class UnitBrief(ORM):
    slug: str
    title: str
    subtitle: str
    ui_lang: str
    enabled: bool


class SubjectOut(ORM):
    slug: str
    title: str
    color: str
    planned: list[str]
    units: list[UnitBrief]


class LessonOut(ORM):
    slug: str
    title: str
    blocks: list[dict[str, Any]]


class ExerciseOut(ORM):
    key: str
    title: str


class UnitOut(ORM):
    slug: str
    title: str
    subtitle: str
    ui_lang: str
    subject: str
    config: dict[str, Any]
    lessons: list[LessonOut]
    exercises: list[ExerciseOut]


class ItemOut(BaseModel):
    key: str
    kind: str
    data: dict[str, Any]


# ---------------------------------------------------------------- profiles

class ProfileIn(BaseModel):
    nickname: str = Field(min_length=1, max_length=60)
    class_code: str = Field(default="", max_length=30)


class ProfileOut(ORM):
    nickname: str
    class_code: str
    token: str
    created_at: datetime


class UnitProgress(BaseModel):
    unit: str
    title: str
    answered: int
    correct_first: int
    correct: int
    best: dict[int, int]          # level -> best mission score
    missions_done: int
    last_activity: Optional[datetime]


# ---------------------------------------------------------------- questions & missions

class MissionState(ORM):
    id: int
    unit: str
    level: int
    index: int
    total: int
    score: int
    streak: int
    good: int
    good_first: int
    status: str
    mode: str = "mission"         # mission | training
    exercise: Optional[str] = None  # training: exercise title
    answered: int = 0             # finished questions


class AnswerOut(BaseModel):
    status: str                    # correct | retry | wrong | invalid
    message: str
    final: bool
    tries: int
    max_tries: int
    eliminated: list[Any]
    points: int = 0
    # filled when final
    explain: Optional[str] = None
    correct_answer: Any = None     # index (choice), side key, or display string
    answer_display: Optional[str] = None
    summary: Optional[str] = None
    speak: Optional[str] = None
    mission: Optional[MissionState] = None


class QuestionOut(BaseModel):
    id: str
    exercise: str
    level: int
    kind: str
    category: str
    prompt: str
    choices: Optional[list[str]]
    unit: str
    figure: Optional[dict[str, Any]]
    has_hint: bool
    hint: Optional[str]
    max_tries: int
    tries: int
    eliminated: list[Any]
    status: str
    position: Optional[int]
    answers: list[Any] = []                 # the student's checked answers, in order
    result: Optional["AnswerOut"] = None    # filled once the question is finished (review, resume)


class AnswerIn(BaseModel):
    value: Union[int, float, str]


class TrainingIn(BaseModel):
    unit: str
    exercise: str
    level: int = 0
    category: Optional[str] = None


class MissionIn(BaseModel):
    unit: str
    level: int = 0
    count: Optional[int] = None
    category: Optional[str] = None
    item_keys: Optional[list[str]] = None   # "Practise my mistakes"


class MistakeOut(BaseModel):
    item_key: Optional[str]
    summary: Optional[str]
    given: Optional[str]
    category: str


class MissionStartOut(BaseModel):
    mission: MissionState
    question: QuestionOut


class MissionFullOut(BaseModel):
    """A session with all its questions so far (resume, go back to a finished question)."""
    mission: MissionState
    questions: list[QuestionOut]


class MissionNextOut(BaseModel):
    mission: MissionState
    question: Optional[QuestionOut] = None
    best: Optional[int] = None
    previous_best: Optional[int] = None
    mistakes: list[MistakeOut] = []


class BadgeOut(BaseModel):
    id: str
    icon: str
    title: str
    description: str
    goal: int
    value: int
    earned: bool


class RewardsOut(BaseModel):
    xp: int
    level: int                    # starts at 1
    level_title: str
    level_start: int              # XP where this level starts
    next_level: int               # XP where the next level starts
    stats: dict[str, int]
    badges: list[BadgeOut]


class FocusIn(BaseModel):
    minutes: int = Field(ge=5, le=60)
