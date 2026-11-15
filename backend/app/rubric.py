"""Grading of written answers (explanations, text analysis) with a list of expected ideas.

Each idea has keywords: the idea counts as present when one of its keywords appears in the
answer (case, accents and apostrophes do not matter; a keyword can be the start of a word,
e.g. "culpabil" matches "culpabilité"). The answer passes when enough ideas are present.
It is a helper for revising, not a teacher: the model answer is always shown at the end.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return " " + re.sub(r"[^a-z0-9]+", " ", text).strip() + " "


def words(text: str) -> int:
    return len(re.findall(r"\w+", text))


@dataclass
class Grade:
    found: list[dict]
    missing: list[dict]
    score: int
    total: int


def grade(text: str, ideas: list[dict]) -> Grade:
    t = norm(text)
    found, missing = [], []
    for idea in ideas:
        hit = any(" " + norm(k).strip() in t for k in idea["keywords"])
        (found if hit else missing).append(idea)
    return Grade(found, missing, sum(i.get("points", 1) for i in found), sum(i.get("points", 1) for i in ideas))


def feedback_html(g: Grade) -> str:
    rows = [f"✅ {i['idea']}" for i in g.found] + [f"❌ {i['idea']}" for i in g.missing]
    return f"<p><strong>Idées trouvées : {g.score} / {g.total}</strong></p><p>" + "<br>".join(rows) + "</p>"
