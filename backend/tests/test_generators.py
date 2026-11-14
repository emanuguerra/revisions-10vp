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


def test_german_vocabulary_questions():
    from app.formatting import norm_text
    from app.generators.wort import full, pos

    unit = next(u for u in UNITS if u["slug"] == "allemand-gefuehle")
    words = {it["key"]: it for it in unit["items"]["wort"]}
    ex = {e["key"]: e for e in unit["exercises"]}

    # Category filter: verbs-only pool has no noun for the article exercise in "sollen"? It has
    # die Ruhe; use a topic without nouns instead: a forced verb asks a translation
    c = ctx_for(unit, ex["artikel"], 0, 1)
    c.forced_item = "lachen"
    g = GENERATORS["wort.artikel"](c)
    assert g.item_key == "lachen" and g.choices != ["der", "die", "das"]

    # A situation mistake is practised as a situation, whatever exercise comes up
    c = ctx_for(unit, ex["artikel"], 0, 1)
    c.forced_item = "sit-katze"
    assert GENERATORS["wort.artikel"](c).item_key == "sit-katze"

    # Opposites: both directions, the answer is the other word of the pair
    for i in range(100):
        g = GENERATORS["wort.opposite"](ctx_for(unit, ex["gegenteil"], 0, i))
        a, b = words[g.item_key], g.choices[g.answer]
        assert b in {full(words[a["opposite"]])} if a.get("opposite") else \
            any(w.get("opposite") == a["key"] and full(w) == b for w in words.values())
        assert len(set(g.choices)) == 4

    # Phrases never get a spelling or a fill-in-the-blank question
    for i in range(200):
        for key, gen in (("schreiben", "wort.spell"), ("luecke", "wort.gap")):
            g = GENERATORS[gen](ctx_for(unit, ex[key], 0, i))
            if g.kind == "text" or "_____" in g.prompt:
                assert pos(words[g.item_key]) != "phrase"

    # Spellings: with or without article / sich, umlaut as ae/oe/ue, ß and ss
    c = ctx_for(unit, ex["schreiben"], 0, 1)
    for key, typed in [("muede", "muede"), ("streit", "der Streit"), ("suess", "süß"),
                       ("sich-freuen", "freuen"), ("enttaeuscht", "enttäuscht")]:
        c.forced_item = key
        g = GENERATORS["wort.spell"](c)
        assert norm_text(typed) in {norm_text(a) for a in g.answer}, (key, g.answer)


@pytest.mark.parametrize("slug", ["allemand-gefuehle", "allemand-kleidung"])
def test_german_units_questions_fit_their_words(slug):
    unit = next(u for u in UNITS if u["slug"] == slug)
    words = {it["key"]: it for it in unit["items"]["wort"]}
    ex = {e["key"]: e for e in unit["exercises"]}
    pic_cats = ex["bild"].get("params", {}).get("categories", ["gefuehle"])
    for i in range(300):
        art = GENERATORS["wort.artikel"](ctx_for(unit, ex["artikel"], 0, i))
        assert words[art.item_key].get("art") == art.choices[art.answer]
        gap = GENERATORS["wort.gap"](ctx_for(unit, ex["luecke"], 0, i))
        assert "_____" in gap.prompt and words[gap.item_key]["de"] == gap.choices[gap.answer]
        pic = GENERATORS["wort.picture"](ctx_for(unit, ex["bild"], 0, i))
        w = words[pic.item_key]
        assert w["category"] in pic_cats and not w.get("nopic")
        # no two options show the same emoji's word group
        groups = [x.get("group") for x in words.values() if x["key"] != w["key"] and x.get("group")]
        assert w.get("group") is None or all(
            next(x for x in words.values() if (x["de"] if not x.get("art") else f"{x['art']} {x['de']}") == c).get("group") != w["group"]
            for j, c in enumerate(pic.choices) if j != pic.answer), pic.choices


def test_climate_generators():
    from app.generators.climat import STUDIED, amplitude

    unit = next(u for u in UNITS if u["slug"] == "geo-climat")
    ex = {e["key"]: e for e in unit["exercises"]}
    stations = {s["key"]: s for s in unit["items"]["station"]}
    assert amplitude(stations["moscou"]) == 25.9
    for i in range(300):
        g = GENERATORS["climat.read_diagram"](ctx_for(unit, ex["diagramme"], 0, i))
        st = stations[g.item_key]
        assert g.figure["type"] == "climograph" and len(g.figure["temp"]) == 12
        if g.kind == "number":
            assert g.answer == amplitude(st)
        elif "hémisphère" in g.prompt:
            assert g.answer == (0 if st["lat"] > 0 else 1)
        c = GENERATORS["climat.classify"](ctx_for(unit, ex["type"], 0, i))
        assert stations[c.item_key]["climate"] in STUDIED and c.figure.get("hide_name")
        a = GENERATORS["climat.albedo"](ctx_for(unit, ex["albedo"], 0, i))
        assert 0 < a.answer < 1000
    # sorting questions keep their fixed choices
    tri = {it["key"]: it for it in unit["items"]["tri"]}
    for i in range(50):
        g = GENERATORS["common.mcq"](ctx_for(unit, ex["tri"], 0, i))
        assert g.choices == tri[g.item_key]["choices"] and g.choices[g.answer] == tri[g.item_key]["answer"]


def test_forces_and_chronology():
    unit = next(u for u in UNITS if u["slug"] == "phys-forces")
    ex = {e["key"]: e for e in unit["exercises"]}
    c = ctx_for(unit, ex["resultante"], 1, 0)
    for i in range(200):
        g = GENERATORS["forces.read"](ctx_for(unit, ex["lire"], 2, i))
        f = g.figure["forces"][0]
        assert abs(g.answer - math.hypot(f["dx"], f["dy"]) * g.figure["scale"]) < 0.01
        g = GENERATORS["forces.spring"](ctx_for(unit, ex["ressort"], 1, i))
        assert g.answer > 0
    # chronology: the right answer is really the first (or last) of the four events shown
    play = next(u for u in UNITS if u["slug"] == "fr-vieille-dame")
    events = {e["text"]: e["order"] for e in play["items"]["event"]}
    ex2 = {e["key"]: e for e in play["exercises"]}
    for i in range(200):
        g = GENERATORS["common.order"](ctx_for(play, ex2["ordre"], 0, i))
        orders = [events[t] for t in g.choices]
        pick = orders[g.answer]
        assert pick == (min(orders) if "premier" in g.prompt else max(orders)) and len(set(orders)) == 4
