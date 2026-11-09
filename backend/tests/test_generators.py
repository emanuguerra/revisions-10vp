"""Smoke-test every generator of every unit, at every level, many times."""
import math
import random
import re

import pytest

from app.formatting import fr, parse_num, round_to
from app.generators import GENERATORS, GenContext
from app.seed import read_content

SUBJECTS, UNITS = read_content()
CASES = [(u, e) for u in UNITS for e in u["exercises"]]
RUNS = 200


def ctx_for(unit, ex, level, seed):
    return GenContext(level=level, rng=random.Random(seed), title=ex["title"], params=ex.get("params", {}),
                      items=unit["items"], categories=unit.get("categories", {}))


@pytest.mark.parametrize("unit,ex", CASES, ids=[f"{u['slug']}:{e['key']}" for u, e in CASES])
def test_generator_output_is_well_formed(unit, ex):
    levels = len(unit.get("levels", [])) or 1
    for level in range(levels):
        for i in range(RUNS):
            g = GENERATORS[ex["generator"]](ctx_for(unit, ex, level, i))
            text = g.prompt + g.explain + str(g.figure or "") + str(g.choices or "")
            assert not re.search(r"NaN|None|inf\b|undefined", text), (ex["key"], level, g.prompt)
            if g.kind == "number":
                assert math.isfinite(g.answer) and g.answer > 0
                assert g.tol > 0
            elif g.kind == "choice":
                assert 0 <= g.answer < len(g.choices)
                assert len(set(g.choices)) == len(g.choices), g.choices
            elif g.kind == "side":
                assert g.answer in g.choices
            elif g.kind == "text":
                assert g.answer and all(isinstance(a, str) for a in g.answer)
            else:
                pytest.fail(f"unknown kind {g.kind}")


def test_pythagoras_answers_are_mathematically_right():
    unit = next(u for u in UNITS if u["slug"] == "maths-pythagore")
    exs = {e["key"]: e for e in unit["exercises"]}
    for level in range(3):
        for i in range(RUNS):
            g = GENERATORS["pythagore.calc_hyp"](ctx_for(unit, exs["calcHyp"], level, i))
            f = g.figure
            assert abs(math.hypot(f["a"], f["b"]) - g.answer) <= g.tol
            g = GENERATORS["pythagore.calc_leg"](ctx_for(unit, exs["calcLeg"], level, i))
            f = g.figure
            c = parse_num(f["lab"]["c"])
            assert abs(math.sqrt(c * c - f["a"] ** 2) - g.answer) <= g.tol


def test_formatting():
    assert fr(1440000) == "1 440 000"
    assert fr(8.6) == "8,6"
    assert fr(3.0) == "3"
    assert fr(0.2025) == "0,2025"
    assert parse_num("8,6") == 8.6
    assert parse_num("1 250") == 1250
    assert parse_num("1'250") == 1250
    assert math.isnan(parse_num("abc"))
    assert round_to(2.5, 0) == 3  # half up, like the original JavaScript
