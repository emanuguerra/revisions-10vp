"""Calcul littéral generators (10VP). Level: 0 = Facile, 1 = Moyen, 2 = Expert.

Expressions are built as lists of terms (coefficient, monomial) so the prompt keeps the
order and repetitions the student must work on; answers are computed with app.algebra.
Free answers use kind "text" with check="expr": any equivalent expression in the
requested form is accepted (6x + 15, 15 + 6x...).
"""
from __future__ import annotations

from fractions import Fraction
from math import gcd

from ..algebra import Mono, Poly, add, mul, order, parse, show, term_str
from .base import GenContext, Generated, register

X: Mono = (("x", 1),)
X2: Mono = (("x", 2),)
Y: Mono = (("y", 1),)
XY: Mono = (("x", 1), ("y", 1))
C: Mono = ()

Term = tuple[int, Mono]
TYPE_HINT = '<span class="muted" style="display:block;font-size:.88rem;margin-top:6px">Tape x^2 pour x².</span>'


def signed(c: int, m: Mono = C) -> str:
    t = term_str(Fraction(c), m)
    return "−" + t if c < 0 else t


def seq(terms: list[Term]) -> str:
    """Terms in the given order, not reduced: [(5, x), (3, 1), (−2, x)] -> '5x + 3 − 2x'."""
    out = ""
    for i, (c, m) in enumerate(terms):
        t = term_str(Fraction(c), m)
        out += signed(c, m) if i == 0 else (" − " if c < 0 else " + ") + t
    return out


def par(c: int, m: Mono = C) -> str:
    """Signed term, in brackets when negative: −5 -> '(−5)'."""
    return f"({signed(c, m)})" if c < 0 else signed(c, m)


def poly(terms: list[Term]) -> Poly:
    p: Poly = {}
    for c, m in terms:
        p = add(p, {m: Fraction(c)} if c else {})
    return p


def mono_mul(m: Mono, n: Mono) -> Mono:
    return next(iter(mul({m: Fraction(1)}, {n: Fraction(1)})))


def nz(ctx: GenContext, a: int, b: int) -> int:
    """Random integer in [-b, -a] ∪ [a, b]."""
    return ctx.rnd(a, b) * ctx.pick([1, -1])


def expr_answer(ctx: GenContext, p: Poly, **kw) -> Generated:
    s = show(p, "xy")
    return Generated(kind="text", category=ctx.title, answer=[s], check="expr", answer_display=s,
                     prompt="", explain="", **kw)


# ------------------------------------------------------------------ valeur d'une expression

def _sub_term(c: int, m: Mono, values: dict[str, int], first: bool) -> str:
    """3x² with x = −2 -> '3·(−2)²'; keeps the sign of the coefficient in front."""
    factors = [str(abs(c))] if abs(c) != 1 or not m else []
    for v, e in m:
        x = values[v]
        f = f"({signed(x)})" if x < 0 else str(x)
        factors.append(f + ("²" if e == 2 else ""))
    body = "·".join(factors)
    if first:
        return ("−" if c < 0 else "") + body
    return (" − " if c < 0 else " + ") + body


@register("litteral.evaluate")
def evaluate_expr(ctx: GenContext) -> Generated:
    if ctx.level == 0:
        a, x = ctx.rnd(2, 9), ctx.rnd(1, 9)
        b = ctx.rnd(1, 20) * (1 if ctx.rng.random() < 0.6 else -1)
        if a * x + b < 0:
            b = -b
        terms, values = [(a, X), (b, C)], {"x": x}
    elif ctx.level == 1:
        terms = [(nz(ctx, 1, 5), X2), (nz(ctx, 1, 9), X), (nz(ctx, 1, 12), C)]
        values = {"x": ctx.pick([-5, -4, -3, -2, -1, 2, 3, 4, 5])}
    else:
        terms = ctx.shuffle([(nz(ctx, 1, 5), X2), (nz(ctx, 1, 6), XY), (nz(ctx, 1, 9), Y)])
        terms.append((nz(ctx, 1, 10), C))
        values = {"x": nz(ctx, 1, 4), "y": nz(ctx, 1, 4)}

    def val(c: int, m: Mono) -> int:
        out = c
        for v, e in m:
            out *= values[v] ** e
        return out

    parts = [val(c, m) for c, m in terms]
    result = sum(parts)
    expr = seq(terms)
    given = " et ".join(f"{v} = {signed(x)}" for v, x in values.items())
    sub = "".join(_sub_term(c, m, values, i == 0) for i, (c, m) in enumerate(terms))
    steps = f"{expr} = {sub}<br>= {seq([(p, C) for p in parts])}<br>= <strong>{signed(result)}</strong>"
    return Generated(
        kind="text", category=ctx.title, answer=[str(result)], check="expr", form="value",
        prompt=f"Calcule la valeur de <strong>{expr}</strong> pour {given}.",
        hint="Remplace chaque lettre par sa valeur, entre parenthèses si elle est négative. "
             "Calcule d'abord les puissances, puis les multiplications, puis les additions.",
        explain=steps, answer_display=signed(result),
    )


# ------------------------------------------------------------------ réduire

def _groups(terms: list[Term]) -> str:
    """'(5x − 2x) + (3 + 7)': like terms side by side."""
    monos = order(poly([(1, m) for _, m in terms]), "xy")
    out = ""
    for i, m in enumerate(monos):
        members = [(c, mm) for c, mm in terms if mm == m]
        if len(members) > 1:
            out += ("" if i == 0 else " + ") + f"({seq(members)})"
        else:
            c, mm = members[0]
            out += signed(c, mm) if i == 0 else (" − " if c < 0 else " + ") + term_str(Fraction(c), mm)
    return out


@register("litteral.reduce")
def reduce_expr(ctx: GenContext) -> Generated:
    products = ""
    if ctx.level == 0:
        a = ctx.rnd(2, 9)
        c = ctx.rnd(1, 9) * ctx.pick([1, 1, -1])
        if a + c == 0:
            c += 1
        terms = [(a, X), (nz(ctx, 1, 9), C), (c, X), (nz(ctx, 1, 9), C)]
        terms = [terms[0], *ctx.shuffle(terms[1:])]
        shown = seq(terms)
    elif ctx.level == 1:
        terms = [(nz(ctx, 1, 6), X2), (nz(ctx, 1, 6), X2), (nz(ctx, 1, 9), X), (nz(ctx, 1, 9), X), (nz(ctx, 1, 12), C)]
        terms = ctx.shuffle(terms)
        shown = seq(terms)
    else:
        # a product to simplify first, then like terms with two letters
        p, q = ctx.rnd(2, 5), nz(ctx, 2, 5)
        pm, qm = ctx.pick([(X, X), (X, Y), (Y, X)])
        prod_mono = mono_mul(pm, qm)
        other = [(nz(ctx, 1, 7), prod_mono), (nz(ctx, 1, 9), X), (nz(ctx, 1, 9), Y), (nz(ctx, 1, 9), X)]
        other = ctx.shuffle(other)
        terms = [(p * q, prod_mono), *other]
        prod_txt = f"{term_str(Fraction(p), pm)} · {par(q, qm)}"
        shown = prod_txt + "".join((" − " if c < 0 else " + ") + term_str(Fraction(c), m) for c, m in other)
        products = f"{prod_txt} = {signed(p * q, prod_mono)}<br>"
    result = poly(terms)
    if len(result) < 2:  # everything cancelled: start again with other numbers
        return reduce_expr(ctx)
    g = expr_answer(ctx, result, form="reduced")
    g.prompt = f"Réduis : <strong>{shown}</strong>" + (TYPE_HINT if any(m == X2 for _, m in terms) else "")
    g.hint = ("Multiplie d'abord les nombres entre eux et les lettres entre elles. " if products else "") + \
        "Additionne seulement les termes semblables : les x avec les x, les x² avec les x², les nombres avec les nombres."
    rest = f"{products}{seq(terms)}" if products else shown
    g.explain = f"{rest}<br>= {_groups(terms)}<br>= <strong>{show(result, 'xy')}</strong>"
    return g


# ------------------------------------------------------------------ développer (distributivité simple)

def _factor_txt(f: Term, inner: list[Term], first: bool) -> str:
    c, m = f
    head = "" if (abs(c) == 1 and not m) else term_str(Fraction(c), m)
    sign = ("−" if c < 0 else "") if first else (" − " if c < 0 else " + ")
    return f"{sign}{head}({seq(inner)})"


def _develop(groups: list[tuple[Term, list[Term]]]) -> tuple[str, list[Term]]:
    """'3·2x + 3·(−5)' and the products, for every factor·(inner) group."""
    line, products = [], []
    for (c, m), inner in groups:
        for ci, mi in inner:
            line.append(f"{par(c, m)}·{par(ci, mi)}")
            products.append((c * ci, mono_mul(m, mi)))
    return " + ".join(line), products


def _distribute_generated(ctx: GenContext, groups: list[tuple[Term, list[Term]]], shown: str, hint: str) -> Generated:
    line, products = _develop(groups)
    result = poly(products)
    g = expr_answer(ctx, result, form="reduced")
    g.prompt = f"Développe et réduis : <strong>{shown}</strong>" + (TYPE_HINT if any(m == X2 for _, m in products) else "")
    g.hint = hint
    steps = [shown, line, seq(products)]
    final = show(result, "xy")
    if steps[-1] == final:
        steps.pop()
    g.explain = "<br>= ".join(steps) + f"<br>= <strong>{final}</strong>"
    return g


@register("litteral.distribute")
def distribute(ctx: GenContext) -> Generated:
    hint = "Multiplie le facteur devant la parenthèse par chaque terme de la parenthèse : k(a + b) = k·a + k·b."
    if ctx.level == 0:
        f = (ctx.rnd(2, 9), C)
        inner = [(ctx.rnd(1, 9), X), (nz(ctx, 1, 9), C)]
    elif ctx.level == 1:
        kind = ctx.pick(["neg", "x", "kx", "minus"])
        inner = [(ctx.rnd(1, 9), X), (nz(ctx, 1, 9), C)]
        f = {"neg": (-ctx.rnd(2, 9), C), "x": (1, X), "kx": (nz(ctx, 2, 6), X), "minus": (-1, C)}[kind]
        if kind == "minus":
            hint = "Un signe − devant une parenthèse change le signe de chaque terme : −(a − b) = −a + b."
        elif kind == "neg":
            hint += " Attention aux signes : (−)·(−) = (+)."
    else:
        g1 = ((ctx.rnd(2, 6), C), [(ctx.rnd(1, 6), X), (nz(ctx, 1, 9), C)])
        g2 = ((nz(ctx, 2, 6), ctx.pick([C, X])), [(ctx.rnd(1, 6), X), (nz(ctx, 1, 9), C)])
        groups = ctx.shuffle([g1, g2])
        shown = _factor_txt(*groups[0], True) + _factor_txt(*groups[1], False)
        return _distribute_generated(ctx, groups, shown, hint + " Développe chaque partie, puis réduis.")
    return _distribute_generated(ctx, [(f, inner)], _factor_txt(f, inner, True), hint)


# ------------------------------------------------------------------ double distributivité et identités

def _binom(t1: Term, t2: Term) -> str:
    return f"({seq([t1, t2])})"


@register("litteral.double_distribute")
def double_distribute(ctx: GenContext) -> Generated:
    hint = "Multiplie chaque terme de la 1re parenthèse par chaque terme de la 2e : (a + b)(c + d) = ac + ad + bc + bd."
    note = ""
    if ctx.level == 0:
        p, q = [(1, X), (ctx.rnd(1, 9), C)], [(1, X), (ctx.rnd(1, 9), C)]
        shown = _binom(*p) + _binom(*q)
    elif ctx.level == 1:
        p, q = [(ctx.rnd(1, 5), X), (nz(ctx, 1, 9), C)], [(ctx.rnd(1, 5), X), (nz(ctx, 1, 9), C)]
        shown = _binom(*p) + _binom(*q)
    else:
        a, b = ctx.rnd(1, 4), ctx.rnd(1, 9)
        kind = ctx.pick(["plus", "minus", "diff"])
        if kind == "diff":
            p, q = [(a, X), (-b, C)], [(a, X), (b, C)]
            shown = _binom(*p) + _binom(*q)
            note = "Identité remarquable : (a − b)(a + b) = a² − b²."
        else:
            s = 1 if kind == "plus" else -1
            p = q = [(a, X), (s * b, C)]
            shown = _binom(*p) + "²"
            note = f"Identité remarquable : (a {'+' if s > 0 else '−'} b)² = a² {'+' if s > 0 else '−'} 2ab + b²."
        hint = "Utilise une identité remarquable, ou écris le carré comme un produit : (a + b)² = (a + b)(a + b)."
    line = " + ".join(f"{par(c1, m1)}·{par(c2, m2)}" for c1, m1 in p for c2, m2 in q)
    products = [(c1 * c2, mono_mul(m1, m2)) for c1, m1 in p for c2, m2 in q]
    result = poly(products)
    g = expr_answer(ctx, result, form="reduced")
    g.prompt = f"Développe et réduis : <strong>{shown}</strong>{TYPE_HINT}"
    g.hint = hint
    steps = [shown] + ([_binom(*p) + _binom(*q)] if shown.endswith("²") else []) + [line, seq(products)]
    g.explain = "<br>= ".join(steps) + f"<br>= <strong>{show(result)}</strong>" + (f"<br>{note}" if note else "")
    return g


# ------------------------------------------------------------------ factoriser (mise en évidence)

def _fac(c: int, m: Mono, inner: list[Term]) -> str:
    head = "" if (c == 1 and not m) else ("−" if c == -1 and not m else term_str(Fraction(c), m) if c > 0 else signed(c, m))
    return f"{head}({seq(inner)})"


@register("litteral.factor")
def factor(ctx: GenContext) -> Generated:
    if ctx.level < 2:
        # Facile: k(ax + b) · Moyen: kx(ax + b)
        k = ctx.rnd(2, 9) if ctx.level == 0 else ctx.rnd(2, 6)
        fm = C if ctx.level == 0 else X
        while True:
            a, b = ctx.rnd(1, 7), ctx.rnd(1, 9)
            if gcd(a, b) == 1:
                break
        b *= ctx.pick([1, 1, -1])
        inner = [(a, X), (b, C)]
        terms = [(k * a, mono_mul(fm, X)), (k * b, fm)]
        target = poly(terms)
        right = _fac(k, fm, inner)
        cands = [
            _fac(k, fm, [(a, X), (-b, C)]),                         # sign error
            _fac(k, fm, [(k * a, X), (b, C)]),                      # one term not divided
            _fac(k + 1, fm, inner),
        ]
        divs = [d for d in range(2, k) if k % d == 0]
        if divs:                                                    # common factor not the greatest
            d = ctx.pick(divs)
            cands.append(_fac(d, fm, [(k // d * a, X), (k // d * b, C)]))
        if fm:
            cands.append(_fac(k, C, [(a, X2), (b, X)]))             # x left inside
            cands.append(_fac(1, X, [(k * a, X), (k * b, C)]))      # k left inside
        kf = term_str(Fraction(k), fm)
        explain = (f"Le plus grand facteur commun de {term_str(Fraction(k * a), terms[0][1])} et "
                   f"{term_str(Fraction(abs(k * b)), fm)} est <strong>{kf}</strong>.<br>"
                   f"{seq(terms)} = {kf}·{par(a, X)} + {kf}·{par(b)} = <strong>{right}</strong>")
        hint = "Cherche le plus grand nombre (et la lettre) qui divise tous les termes, puis mets-le devant la parenthèse."
    else:
        a, b = ctx.rnd(1, 3), ctx.rnd(1, 9)
        kind = ctx.pick(["diff", "plus", "minus"])
        ax = term_str(Fraction(a), X)
        if kind == "diff":
            terms, right = [(a * a, X2), (-b * b, C)], f"({ax} − {b})({ax} + {b})"
            rule = "a² − b² = (a − b)(a + b)"
        elif kind == "plus":
            terms, right = [(a * a, X2), (2 * a * b, X), (b * b, C)], f"({ax} + {b})²"
            rule = "a² + 2ab + b² = (a + b)²"
        else:
            terms, right = [(a * a, X2), (-2 * a * b, X), (b * b, C)], f"({ax} − {b})²"
            rule = "a² − 2ab + b² = (a − b)²"
        target = poly(terms)
        cands = [f"({ax} − {b})({ax} + {b})", f"({ax} + {b})²", f"({ax} − {b})²",
                 f"({ax} − {b * b})({ax} + {b * b})", f"({ax} + {b * b})²", f"{ax}({ax} − {b})"]
        explain = f"Identité remarquable : {rule}, avec a = {ax} et b = {b}.<br>{seq(terms)} = <strong>{right}</strong>"
        hint = "Reconnais une identité remarquable : a² − b², a² + 2ab + b² ou a² − 2ab + b²."
    wrong = []
    for cand in cands:
        if cand == right or cand in wrong:
            continue
        if ctx.level == 2 and parse(cand) == target:
            continue
        wrong.append(cand)
    choices = ctx.shuffle([right, *ctx.shuffle(wrong)[:3]])
    return Generated(
        kind="choice", category=ctx.title, choices=choices, answer=choices.index(right),
        prompt=f"Factorise complètement : <strong>{seq(terms)}</strong>",
        hint=hint, explain=explain,
        retry_message="Ce n'est pas la bonne réponse. Développe ta proposition pour vérifier, et choisis-en une autre.",
    )


# ------------------------------------------------------------------ traduire en expression

TRANSLATE = [
    # (phrase, correct, wrong answers, why) — n is a random number from 2 to 9
    [
        ("le double de x augmenté de {n}", "2x + {n}", ["2(x + {n})", "x² + {n}", "2 + x + {n}"],
         "« le double de x » = 2x, puis on ajoute {n}."),
        ("le triple de x diminué de {n}", "3x − {n}", ["3(x − {n})", "x³ − {n}", "{n} − 3x"],
         "« le triple de x » = 3x, puis on enlève {n}."),
        ("le carré de x augmenté de {n}", "x² + {n}", ["2x + {n}", "(x + {n})²", "x² + {n}²"],
         "« le carré de x » = x², puis on ajoute {n}."),
        ("{n} de moins que x", "x − {n}", ["{n} − x", "{n}x", "x + {n}"],
         "On part de x et on enlève {n}."),
        ("le produit de {n} et de x", "{n}x", ["{n} + x", "x − {n}", "x : {n}"],
         "Un produit est le résultat d'une multiplication : {n}·x = {n}x."),
    ],
    [
        ("le double de la somme de x et de {n}", "2(x + {n})", ["2x + {n}", "x + 2·{n}", "(x + {n})²"],
         "D'abord la somme x + {n}, puis on la double : 2(x + {n})."),
        ("le carré de la somme de x et de {n}", "(x + {n})²", ["x² + {n}²", "x² + {n}", "2(x + {n})"],
         "D'abord la somme x + {n}, puis on l'élève au carré : (x + {n})²."),
        ("la différence entre le triple de x et {n}", "3x − {n}", ["3(x − {n})", "{n} − 3x", "x − 3·{n}"],
         "Le triple de x moins {n} : 3x − {n}."),
        ("le produit de x par la somme de x et de {n}", "x(x + {n})", ["x·x + {n}", "x + x + {n}", "2x + {n}"],
         "La somme x + {n}, multipliée par x : x(x + {n})."),
        ("la somme de x et de son carré", "x + x²", ["2x", "(2x)²", "x + 2x"],
         "x plus x² : x + x²."),
    ],
    [
        ("Un rectangle mesure x + {n} de long et x de large. Son <strong>périmètre</strong> est…",
         "4x + {2n}", ["2x + {n}", "x² + {n}x", "4x + {n}"],
         "Périmètre = 2·(longueur + largeur) = 2(x + {n} + x) = 4x + {2n}."),
        ("Un rectangle mesure x + {n} de long et x de large. Son <strong>aire</strong> est…",
         "x² + {n}x", ["2x + {n}", "4x + {2n}", "x² + {n}"],
         "Aire = longueur·largeur = x(x + {n}) = x² + {n}x."),
        ("Un carré a un côté de x + {n}. Son <strong>périmètre</strong> est…",
         "4x + {4n}", ["4x + {n}", "x² + {nn}", "x + {4n}"],
         "Périmètre = 4·côté = 4(x + {n}) = 4x + {4n}."),
        ("Un carré a un côté de x + {n}. Son <strong>aire</strong> est…",
         "x² + {2n}x + {nn}", ["x² + {nn}", "4x + {4n}", "x² + {n}x + {nn}"],
         "Aire = côté² = (x + {n})² = x² + {2n}x + {nn}."),
        ("Léa a x ans. Son frère a {n} ans de moins qu'elle et sa mère a le triple de son âge. "
         "La <strong>somme</strong> de leurs trois âges est…",
         "5x − {n}", ["4x − {n}", "5x + {n}", "3x − {n}"],
         "x + (x − {n}) + 3x = 5x − {n}."),
    ],
]


@register("litteral.translate")
def translate(ctx: GenContext) -> Generated:
    phrase, right, wrongs, why = ctx.pick(TRANSLATE[min(ctx.level, 2)])
    n = ctx.rnd(2, 9)
    sub = {"n": n, "2n": 2 * n, "4n": 4 * n, "nn": n * n}

    def f(s: str) -> str:
        return s.format(**sub)

    right = f(right)
    choices = ctx.shuffle([right, *(f(w) for w in wrongs)])
    question = f(phrase) if ctx.level == 2 else f"Quelle expression correspond à : <strong>« {f(phrase)} »</strong> ?"
    return Generated(
        kind="choice", category=ctx.title, choices=choices, answer=choices.index(right), prompt=question,
        hint="Repère l'opération principale : « le double de la somme » = on calcule la somme d'abord, avec des parenthèses.",
        explain=f"<strong>{right}</strong><br>{f(why)}",
    )

