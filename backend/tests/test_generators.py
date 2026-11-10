"""Smoke-test every generator of every unit, at every level, many times."""
import math
import random
import re

import pytest

from app.algebra import check_answer, normalize, parse, show
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


def test_algebra_parser():
    assert show(parse("3(2x − 5) + x²")) == "x² + 6x − 15"
    assert show(parse("(x+3)^2")) == "x² + 6x + 9"
    assert show(parse("2x · 3y − yx")) == "5xy"
    assert show(parse("0,5x + 1,5")) == "0,5x + 1,5"
    assert normalize("2(x+1)(x−1)") == "2*(x+1)*(x-1)"
    for bad in ["__import__('os')", "x.real", "open(1)", "x^99", "9**9**9", "x2", "((x+y+a+b+n+1)^6)^6", "", "2 +"]:
        assert check_answer(bad, "x", "reduced").status == "invalid", bad
    assert check_answer("15 + 6x", "6x + 15", "reduced").status == "correct"
    assert check_answer("3(2x + 5)", "6x + 15", "reduced").status == "form"
    assert check_answer("4x + 2x + 15", "6x + 15", "reduced").status == "form"
    assert check_answer("6x + 16", "6x + 15", "reduced").status == "wrong"
    assert check_answer("−17", "-17", "value").status == "correct"
    assert check_answer("12 − 29", "-17", "value").status == "form"


def test_calcul_litteral_answers_are_right():
    """Free answers are reachable; in multiple choice the right option is equal to the expression
    (factor) and no wrong option is (translate)."""
    unit = next(u for u in UNITS if u["slug"] == "maths-calcul-litteral")
    exs = {e["key"]: e for e in unit["exercises"]}
    strip = lambda h: re.sub(r"<[^>]+>", "", h)
    for level in range(3):
        for i in range(RUNS):
            for key in ("valeur", "reduire", "developper", "double"):
                g = GENERATORS[exs[key]["generator"]](ctx_for(unit, exs[key], level, i))
                assert check_answer(g.answer_display, g.answer[0], g.form or "reduced").status == "correct"
                if key != "valeur":
                    asked = strip(g.prompt.split("<strong>")[1].split("</strong>")[0])
                    assert parse(asked) == parse(g.answer[0]), (asked, g.answer)
            g = GENERATORS["litteral.factor"](ctx_for(unit, exs["factoriser"], level, i))
            asked = strip(g.prompt.split("<strong>")[1])
            assert parse(g.choices[g.answer]) == parse(asked)
            g = GENERATORS["litteral.translate"](ctx_for(unit, exs["traduire"], level, i))
            right = parse(g.choices[g.answer])
            assert all(parse(c) != right for j, c in enumerate(g.choices) if j != g.answer), g.choices
