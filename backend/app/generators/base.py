"""Generator contract.

A generator is a function `(ctx: GenContext) -> Generated`, registered under a key
such as "pythagore.calc_hyp". Exercise types in content/units/*/unit.yaml refer to that key.

Answer kinds:
    number  answer: float, tol: allowed difference, unit: shown next to the input
    choice  answer: index in `choices`
    side    answer: "a" | "b" | "c" (side of the right-triangle figure the student clicks)
    text    answer: list of accepted spellings
            with check="expr": answer[0] is an expression compared by algebra.check_answer,
            `form` says what is expected ("reduced" or "value")
"""
from __future__ import annotations

import html
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Optional

esc = html.escape


@dataclass
class GenContext:
    level: int
    rng: random.Random
    title: str                                   # exercise title, shown above the prompt
    params: dict[str, Any] = field(default_factory=dict)
    items: dict[str, list[dict[str, Any]]] = field(default_factory=dict)  # unit items by kind
    categories: dict[str, str] = field(default_factory=dict)
    category: Optional[str] = None               # filter chosen by the student
    exclude: set[str] = field(default_factory=set)  # item keys already used in this mission
    forced_item: Optional[str] = None            # e.g. "Practise my mistakes"

    def shuffle(self, seq):
        seq = list(seq)
        self.rng.shuffle(seq)
        return seq

    def pick(self, seq):
        return self.rng.choice(list(seq))

    def rnd(self, a: int, b: int) -> int:
        return self.rng.randint(a, b)

    def pick_item(self, kind: str) -> dict[str, Any]:
        """Pick a static item, honouring the forced item, the category filter and the exclusions."""
        items = self.items.get(kind, [])
        if not items:
            raise LookupError(f"no items of kind '{kind}' in this unit")
        if self.forced_item:
            for it in items:
                if it["key"] == self.forced_item:
                    return it
        pool = [it for it in items if not self.category or it.get("category") == self.category]
        fresh = [it for it in pool if it["key"] not in self.exclude]
        return self.pick(fresh or pool or items)


@dataclass
class Generated:
    kind: str
    prompt: str                       # trusted HTML
    explain: str                      # trusted HTML, shown after the last attempt
    answer: Any
    category: str = ""
    choices: Optional[list[str]] = None
    tol: float = 0.0
    unit: str = ""
    hint: Optional[str] = None
    figure: Optional[dict[str, Any]] = None
    max_tries: int = 3
    retry_message: Optional[str] = None
    item_key: Optional[str] = None
    summary: Optional[str] = None     # short recap line, e.g. "🩺 nurse = infirmier"
    speak: Optional[str] = None       # word the browser pronounces after the answer
    answer_display: Optional[str] = None
    check: Optional[str] = None       # "expr": compare algebraic expressions, not spellings
    form: Optional[str] = None

    def payload(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "category": self.category,
            "prompt": self.prompt,
            "choices": self.choices,
            "unit": self.unit,
            "figure": self.figure,
            "has_hint": bool(self.hint),
            "max_tries": self.max_tries,
        }

    def solution(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "tol": self.tol,
            "hint": self.hint,
            "explain": self.explain,
            "retry_message": self.retry_message,
            "summary": self.summary,
            "speak": self.speak,
            "answer_display": self.answer_display,
            "check": self.check,
            "form": self.form,
        }


Generator = Callable[[GenContext], Generated]
GENERATORS: dict[str, Generator] = {}


def register(key: str):
    def deco(fn: Generator) -> Generator:
        if key in GENERATORS:
            raise ValueError(f"generator '{key}' registered twice")
        GENERATORS[key] = fn
        return fn
    return deco
