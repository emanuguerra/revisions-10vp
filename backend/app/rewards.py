"""Game rewards computed from what the student did: experience points (XP), levels and badges.

Nothing is stored apart from the focus sessions: the rewards are recomputed from the answered
questions and the missions, so changing the rules below applies to past work too.

XP: 10 per answer right the first time, 5 per answer right after a correction, 20 per mission
finished, 30 per focus session. Level n starts at 50 * n * (n + 1) XP (100, 300, 600, ...).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import ExerciseType, FocusSession, Mission, Profile, Question, Unit

LEVEL_TITLES = ["Débutant·e", "Apprenti·e", "Explorateur·rice", "Aventurier·ère", "Expert·e",
                "Champion·ne", "Maître·sse", "Légende"]


@dataclass
class Badge:
    id: str
    icon: str
    title: str
    description: str
    stat: str            # key in the stats
    goal: int


BADGES = [
    Badge("first-step", "🐣", "Premiers pas", "Répondre à ta première question.", "answered", 1),
    Badge("answers-50", "✏️", "Bien lancé·e", "Répondre à 50 questions.", "answered", 50),
    Badge("answers-200", "📚", "Grand·e travailleur·euse", "Répondre à 200 questions.", "answered", 200),
    Badge("answers-500", "🏛️", "Infatigable", "Répondre à 500 questions.", "answered", 500),
    Badge("first-try-25", "🎯", "Dans le mille", "25 réponses justes du premier coup.", "first_try", 25),
    Badge("first-try-100", "🏹", "Tireur·euse d'élite", "100 réponses justes du premier coup.", "first_try", 100),
    Badge("first-try-300", "🥇", "Sans faute", "300 réponses justes du premier coup.", "first_try", 300),
    Badge("streak-5", "🔥", "En feu", "5 réponses justes de suite, du premier coup.", "best_streak", 5),
    Badge("streak-10", "☄️", "Inarrêtable", "10 réponses justes de suite, du premier coup.", "best_streak", 10),
    Badge("streak-20", "🌟", "Superstar", "20 réponses justes de suite, du premier coup.", "best_streak", 20),
    Badge("mission-1", "🚀", "Décollage", "Terminer ta première mission.", "missions", 1),
    Badge("missions-10", "🛰️", "Pilote confirmé·e", "Terminer 10 missions.", "missions", 10),
    Badge("perfect", "💎", "Mission parfaite", "Une mission sans aucune erreur.", "perfect", 1),
    Badge("perfect-5", "👑", "Perfectionniste", "5 missions parfaites.", "perfect", 5),
    Badge("days-3", "📅", "Régulier·ère", "Travailler 3 jours de suite.", "best_days", 3),
    Badge("days-7", "🗓️", "Une semaine entière", "Travailler 7 jours de suite.", "best_days", 7),
    Badge("focus-1", "⏱️", "Concentré·e", "Terminer une session de concentration.", "focus", 1),
    Badge("focus-10", "🧘", "Maître de la concentration", "Terminer 10 sessions de concentration.", "focus", 10),
    Badge("explorer", "🧭", "Explorateur·rice", "Travailler dans 3 chapitres différents.", "units", 3),
    Badge("all-rounder", "🌍", "Touche-à-tout", "Travailler dans 3 matières différentes.", "subjects", 3),
]


def level_for(xp: int) -> tuple[int, int, int]:
    """(level starting at 0, XP where it starts, XP where the next one starts)."""
    n = 0
    while 50 * (n + 1) * (n + 2) <= xp:
        n += 1
    return n, 50 * n * (n + 1), 50 * (n + 1) * (n + 2)


def _longest_run(days: set[date]) -> int:
    best = run = 0
    prev = None
    for d in sorted(days):
        run = run + 1 if prev and d - prev == timedelta(days=1) else 1
        best, prev = max(best, run), d
    return best


def _current_run(days: set[date], today: date) -> int:
    d, run = today, 0
    if d not in days:
        d -= timedelta(days=1)            # today not worked yet: the run is still alive
    while d in days:
        run, d = run + 1, d - timedelta(days=1)
    return run


def stats(db: Session, profile: Profile) -> dict[str, int]:
    rows = db.execute(
        select(Question.status, Question.tries, Question.answered_at, Unit.id, Unit.subject_id)
        .join(ExerciseType, Question.exercise_type_id == ExerciseType.id)
        .join(Unit, ExerciseType.unit_id == Unit.id)
        .where(Question.profile_id == profile.id, Question.status != "open")
        .order_by(Question.answered_at)
    ).all()
    run = best_streak = 0
    for status, tries, *_ in rows:
        run = run + 1 if status == "correct" and tries == 0 else 0
        best_streak = max(best_streak, run)
    missions = db.scalars(select(Mission).where(
        Mission.profile_id == profile.id, Mission.mode == "mission", Mission.status == "done")).all()
    focus = db.scalars(select(FocusSession).where(FocusSession.profile_id == profile.id)).all()
    days = {r.answered_at.date() for r in rows if r.answered_at} | {f.created_at.date() for f in focus}
    today = datetime.now(timezone.utc).date()
    return {
        "answered": len(rows),
        "first_try": sum(r.status == "correct" and r.tries == 0 for r in rows),
        "corrected": sum(r.status == "correct" and r.tries > 0 for r in rows),
        "best_streak": best_streak,
        "missions": len(missions),
        "perfect": sum(m.good_first >= len(m.sequence) > 0 for m in missions),
        "focus": len(focus),
        "focus_minutes": sum(f.minutes for f in focus),
        "best_days": _longest_run(days),
        "days": _current_run(days, today),
        "units": len({r[3] for r in rows}),
        "subjects": len({r[4] for r in rows}),
    }


def rewards(db: Session, profile: Profile) -> dict:
    s = stats(db, profile)
    xp = 10 * s["first_try"] + 5 * s["corrected"] + 20 * s["missions"] + 30 * s["focus"]
    level, start, nxt = level_for(xp)
    return {
        "xp": xp, "level": level + 1, "level_title": LEVEL_TITLES[min(level, len(LEVEL_TITLES) - 1)],
        "level_start": start, "next_level": nxt, "stats": s,
        "badges": [{"id": b.id, "icon": b.icon, "title": b.title, "description": b.description,
                    "goal": b.goal, "value": min(s[b.stat], b.goal), "earned": s[b.stat] >= b.goal}
                   for b in BADGES],
    }
