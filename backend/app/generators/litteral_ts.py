"""Calcul littéral: the 8 kinds of questions of the 10VP test (TS), for the unit's practice test.

Modelled on the class test (réduire, traduire, remplacer, figures, segments, expressions
équivalentes, figure sur quadrillage, deux carrés accolés); every question has new numbers.
Answers are typed expressions checked by app.algebra (any equivalent spelling is accepted)
or oui / non. Figures are small inline SVG drawings in the prompt.
"""
from __future__ import annotations

from math import gcd

from ..algebra import Mono, parse, show
from .base import GenContext, Generated, register
from .litteral import C, X, X2, Term, nz, par, poly, seq, signed

X3: Mono = (("x", 3),)
N: Mono = (("n", 1),)
TYPE = '<span class="muted" style="display:block;font-size:.88rem;margin-top:6px">Tape x^2 pour x², x^3 pour x³, 5x/4 pour une fraction.</span>'


def expr(ctx: GenContext, prompt: str, answer: str, explain: str, hint: str, form: str = "reduced",
         display: str | None = None, variables: str = "xyabn") -> Generated:
    """Free answer compared with `answer` (any equivalent expression; `form` as in algebra.check_answer)."""
    shown = display or show(parse(answer, variables), variables)
    return Generated(kind="text", category=ctx.title, answer=[answer], check="expr", form=form,
                     answer_display=shown, prompt=prompt, hint=hint, explain=f"{explain}<br>Réponse : <strong>{shown}</strong>")


def frac(num: str, den: str) -> str:
    return (f'<span style="display:inline-flex;flex-direction:column;vertical-align:middle;text-align:center;'
            f'line-height:1.1;margin:0 2px"><span style="border-bottom:1.5px solid">{num}</span><span>{den}</span></span>')


# ------------------------------------------------------------------ SVG figures

def svg(w: int, h: int, inner: str) -> str:
    return (f'<svg viewBox="0 0 {w} {h}" width="{w}" style="display:block;max-width:100%;height:auto;margin:12px 0" '
            f'fill="none" stroke="currentColor" stroke-width="2" font-size="15" font-family="inherit" '
            f'role="img" aria-label="figure">{inner}</svg>')


def label(x: float, y: float, t: str, anchor: str = "middle") -> str:
    return f'<text x="{x}" y="{y}" fill="currentColor" stroke="none" text-anchor="{anchor}">{t}</text>'


def tick(x: float, y: float, vertical: bool = False, n: int = 1) -> str:
    """Equal-length marks: n small strokes across a segment at (x, y)."""
    out = ""
    for i in range(n):
        d = (i - (n - 1) / 2) * 5
        out += (f'<line x1="{x - 6}" y1="{y + d}" x2="{x + 6}" y2="{y + d}"/>' if vertical
                else f'<line x1="{x + d}" y1="{y - 6}" x2="{x + d}" y2="{y + 6}"/>')
    return out


# ------------------------------------------------------------------ Ex. 1 réduire

@register("litteral.ts_reduce")
def ts_reduce(ctx: GenContext) -> Generated:
    kind = ctx.pick(["like", "sumpow", "cancel", "prod", "cube", "deg3", "powmono", "letters", "priority", "fracsq"])
    hint = "Additionne seulement les termes semblables ; dans un produit, multiplie les nombres entre eux et les lettres entre elles."
    if kind == "like":
        terms: list[Term] = [(1, X), (ctx.rnd(2, 9), C), (-ctx.rnd(2, 9), X), (-ctx.rnd(2, 12), C)]
        if terms[0][0] + terms[2][0] == 0 or terms[1][0] + terms[3][0] == 0:
            return ts_reduce(ctx)
        shown, steps = seq(terms), f"({seq([terms[0], terms[2]])}) + ({seq([terms[1], terms[3]])})"
        ans = show(poly(terms))
    elif kind == "sumpow":
        e = ctx.rnd(3, 9)
        k = ctx.rnd(2, 4)
        shown = " + ".join([f"x<sup>{e}</sup>"] * k)
        steps = f"On additionne {k} fois le même terme x<sup>{e}</sup> : l'exposant ne change pas."
        ans = f"{k}x^{e}"
        hint = "x⁹ + x⁹ : deux fois x⁹. On additionne les coefficients, l'exposant reste le même."
    elif kind == "cancel":
        a = ctx.rnd(2, 9)
        shown, steps, ans = f"x + {a} − {a} − x", f"(x − x) + ({a} − {a}) = 0 + 0", "0"
    elif kind == "prod":
        a, b = ctx.rnd(2, 9), ctx.rnd(2, 9)
        shown = f"{a} · x · {b} · x"
        steps, ans = f"{a} · {b} · x · x = {a * b}x²", f"{a * b}x^2"
        hint = "Dans un produit, on peut changer l'ordre : les nombres ensemble, les lettres ensemble. x · x = x²."
    elif kind == "cube":
        k = ctx.rnd(2, 4)
        shown = "x · x · x" + " + x" * k
        steps, ans = f"x · x · x = x³ et {' + '.join(['x'] * k)} = {k}x", f"x^3 + {k}x"
        hint = "x · x · x est une puissance (x³) ; x + x est une somme (2x). On ne les additionne pas ensemble."
    elif kind == "deg3":
        X3c = [nz(ctx, 1, 4), ctx.rnd(1, 3)]
        Xc = [nz(ctx, 2, 6)]
        Xc.append(-Xc[0] if ctx.rng.random() < 0.5 else nz(ctx, 1, 6))
        X2c = [ctx.rnd(2, 7), nz(ctx, 1, 3)]
        terms = [(X3c[0], X3), (Xc[0], X), (X2c[0], X2), (nz(ctx, 2, 9), C), (X3c[1], X3), (Xc[1], X), (X2c[1], X2)]
        if any(sum(c for c, m in terms if m == mm) == 0 for mm in (X3, X2)):
            return ts_reduce(ctx)
        shown = seq(terms)
        groups = [seq([t for t in terms if t[1] == m]) for m in (X3, X2, X, C)]
        steps = " + ".join(f"({g})" if " " in g else g for g in groups)
        ans = show(poly(terms))
    elif kind == "powmono":
        k, e = ctx.pick([2, 3]), ctx.pick([1, 2])
        n = ctx.pick([2, 3, 4] if k == 2 else [2, 3])
        base = f"{k}x" + ("²" if e == 2 else "")
        shown = f"({base})<sup>{n}</sup>"
        steps = (f"{' · '.join([base] * n)} = {' · '.join([str(k)] * n)} · x<sup>{e}·{n}</sup> = {k ** n}x<sup>{e * n}</sup>")
        ans = f"{k ** n}x^{e * n}"
        hint = "La puissance s'applique au nombre ET à la lettre : (2x²)⁴ = 2x² · 2x² · 2x² · 2x²."
    elif kind == "letters":
        p, q, r, s, t = ctx.rnd(2, 5), ctx.rnd(2, 7), ctx.rnd(2, 8), ctx.rnd(2, 12), ctx.rnd(2, 4)
        if q == r:
            r += 1
        shown = f"{p}a − {q}ab + {r}ba − {s} + {t}a²"
        steps = f"ab et ba sont semblables : −{q}ab + {r}ab = {signed(r - q)}ab ; a, a² et les nombres restent seuls"
        ans = f"{t}a^2 + {r - q}ab + {p}a - {s}"
        g = expr(ctx, f"Réduis si possible : <strong>{shown}</strong>{TYPE}", ans, f"{shown}<br>{steps}", hint,
                 display=show(parse(ans, "ab"), "ab"), variables="ab")
        return g
    elif kind == "priority":
        a, b, c = ctx.rnd(2, 6), ctx.rnd(2, 5), ctx.rnd(2, 12)
        shown = f"{a} · x² · {b} − {c} · x"
        steps = f"Les multiplications d'abord : {a} · {b} · x² = {a * b}x² et {c} · x = {c}x. On ne peut pas réduire x² avec x."
        ans = f"{a * b}x^2 - {c}x"
        hint = "La soustraction sépare deux termes : calcule chaque produit, puis regarde s'ils sont semblables."
    else:  # fracsq
        while True:
            k, d = ctx.rnd(2, 7), ctx.rnd(2, 5)
            if gcd(k, d) == 1:
                break
        shown = f"({frac(f'{k}x', str(d))})²"
        steps = f"({k}x)² : ({d})² = {k * k}x² : {d * d}"
        ans = f"{k * k}x^2/{d * d}"
        hint = "Le carré s'applique au numérateur et au dénominateur, et au nombre et à la lettre : (5x)² = 25x²."
        return expr(ctx, f"Réduis si possible : <strong>{shown}</strong>{TYPE}", ans, steps, hint,
                    display=f"{k * k}x²/{d * d}")
    return expr(ctx, f"Réduis si possible : <strong>{shown}</strong>{TYPE}", ans, f"{shown}<br>= {steps}", hint)


# ------------------------------------------------------------------ Ex. 2 traduire en expression

PHRASES = [
    # (phrase, what the letter stands for, answer, why)
    ("un multiple de {k} qui suit un multiple de {k}", "n = un nombre entier", "{k}n + {k}",
     "Un multiple de {k} s'écrit {k}n ; le suivant est {k} plus loin : {k}n + {k}."),
    ("le carré d'un nombre pair", "n = un nombre entier", "(2n)^2",
     "Un nombre pair s'écrit 2n ; son carré : (2n)² = 4n²."),
    ("la différence entre un multiple de {k} et {m}", "n = un nombre entier", "{k}n - {m}",
     "Un multiple de {k} : {k}n ; on lui enlève {m} : {k}n − {m}."),
    ("la somme de {c} nombres entiers consécutifs", "n = le plus petit des nombres", "{sumc}",
     "{terms} = {sumc_show}."),
    ("un nombre impair", "n = un nombre entier", "2n + 1",
     "Un nombre pair s'écrit 2n ; le nombre impair qui suit : 2n + 1."),
    ("la somme de deux nombres pairs consécutifs", "n = un nombre entier", "4n + 2",
     "2n + (2n + 2) = 4n + 2."),
    ("le produit de deux nombres entiers consécutifs", "n = le plus petit des nombres", "n(n + 1)",
     "n · (n + 1) = n² + n."),
    ("le triple du nombre qui suit n", "n = un nombre entier", "3(n + 1)",
     "Le nombre qui suit n : n + 1 ; son triple : 3(n + 1) = 3n + 3."),
    ("le périmètre d'un losange", "x = le côté du losange", "4x",
     "Un losange a 4 côtés égaux : x + x + x + x = 4x (et pas x⁴ !)."),
    ("le périmètre d'un triangle équilatéral", "x = le côté du triangle", "3x",
     "3 côtés égaux : x + x + x = 3x."),
    ("l'aire d'un carré", "x = le côté du carré", "x^2", "côté · côté = x · x = x²."),
    ("le périmètre d'un rectangle dont la longueur vaut {k} de plus que la largeur", "x = la largeur",
     "4x + {kk}", "2 · (x + x + {k}) = 4x + {kk}."),
]


@register("litteral.ts_translate")
def ts_translate(ctx: GenContext) -> Generated:
    phrase, letter, ans, why = ctx.pick(PHRASES)
    k, m, c = ctx.rnd(3, 9), ctx.rnd(2, 12), ctx.rnd(3, 5)
    names = ["n"] + [f"(n + {i})" for i in range(1, c)]
    sumc = f"{c}n + {c * (c - 1) // 2}"
    sub = {"k": k, "m": m, "c": c, "kk": 2 * k, "sumc": sumc, "sumc_show": sumc, "terms": " + ".join(names)}
    phrase, ans, why = phrase.format(**sub), ans.format(**sub), why.format(**sub)
    var = "x" if letter.startswith("x") else "n"
    return expr(ctx, f"Écris l'expression littérale de : <strong>« {phrase} »</strong><br>"
                     f"<span class=\"muted\">avec {letter}</span>{TYPE}",
                ans, why, "Remplace chaque mot par une opération : « le double » = 2·…, « suit » = + 1, « le carré » = (…)².",
                form="any", display=show(parse(ans, var), var), variables=var)


# ------------------------------------------------------------------ Ex. 3 remplacer et calculer

@register("litteral.ts_substitute")
def ts_substitute(ctx: GenContext) -> Generated:
    kind = ctx.pick(["minus", "third", "neg", "square", "priority", "bracket"])
    hint = ("Remplace x par sa valeur entre parenthèses. Priorités : puissances, puis multiplications et divisions, "
            "puis additions et soustractions.")
    if kind == "minus":
        a, x = ctx.rnd(10, 30), ctx.rnd(2, 9)
        shown, steps, r = f"{a} − x", f"{a} − {x} = {a - x}", a - x
    elif kind == "third":
        d = ctx.pick([2, 3, 4, 5])
        x, b = -d * ctx.rnd(1, 5), ctx.rnd(1, 9)
        shown = f"{frac('x', str(d))} + {b}"
        steps = f"{frac(par(x), str(d))} + {b} = {signed(x // d)} + {b} = {x // d + b}"
        r = x // d + b
        hint = "La division ne porte que sur x : divise d'abord, puis ajoute. " + hint
    elif kind == "neg":
        k, x = ctx.rnd(2, 9), -ctx.rnd(2, 9)
        shown, steps, r = f"−{k}x", f"−{k} · {par(x)} = {-k * x}", -k * x
        hint = "Le signe « − » fois un nombre négatif donne un résultat positif."
    elif kind == "square":
        k, x = ctx.rnd(2, 4), -ctx.rnd(2, 5)
        shown = f"{k}x² + x"
        steps = f"{k} · {par(x)}² + {par(x)} = {k} · {x * x} + {par(x)} = {k * x * x} {'−' if x < 0 else '+'} {abs(x)} = {k * x * x + x}"
        r = k * x * x + x
        hint = "(−3)² = (−3)·(−3) = +9 : le carré d'un nombre négatif est positif. " + hint
    elif kind == "priority":
        d = ctx.pick([2, 3, 4])
        x = d * ctx.rnd(2, 5)
        shown = f"x² − x : {d}"
        steps = f"{x}² − {x} : {d} = {x * x} − {x // d} = {x * x - x // d}"
        r = x * x - x // d
        hint = "La division passe avant la soustraction : x² − x : 4 n'est pas (x² − x) : 4."
    else:
        a, k, x = ctx.rnd(1, 6), ctx.rnd(2, 5), -ctx.rnd(1, 9)
        shown = f"{k}(x + {a})"
        steps = f"{k} · ({x} + {a}) = {k} · {par(x + a)} = {k * (x + a)}"
        r = k * (x + a)
    return expr(ctx, f"Remplace x par <strong>{par(x)}</strong> et calcule : <strong>{shown}</strong>",
                str(r), steps, hint, form="value", display=signed(r))


# ------------------------------------------------------------------ Ex. 4 périmètre et aire de figures

def _triangle(k: int, h: int) -> str:
    """Right triangle: vertical leg x, horizontal leg made of k segments of length x, hypotenuse h."""
    W, H = 60 * k, 60
    ox, oy = 40, 20
    inner = (f'<polygon points="{ox},{oy} {ox},{oy + H} {ox + W},{oy + H}"/>'
             f'<polyline points="{ox},{oy + H - 12} {ox + 12},{oy + H - 12} {ox + 12},{oy + H}" stroke-width="1.5"/>'
             + tick(ox, oy + H / 2, vertical=True) + label(ox - 14, oy + H / 2 + 5, "x")
             + "".join(f'<line x1="{ox + 60 * i}" y1="{oy + H - 5}" x2="{ox + 60 * i}" y2="{oy + H + 5}" stroke-width="1.5"/>'
                       + tick(ox + 60 * i + 30, oy + H) for i in range(1, k))
             + tick(ox + 30, oy + H)
             + label(ox + W / 2 + 14, oy + H / 2 - 6, str(h)))
    return svg(W + 80, H + 40, inner)


def _parallelogram(b: int, s: int, h: int) -> str:
    ox, oy, W, H, sh = 30, 25, 180, 70, 60
    inner = (f'<polygon points="{ox},{oy + H} {ox + W},{oy + H} {ox + W + sh},{oy} {ox + sh},{oy}"/>'
             f'<line x1="{ox + W + sh}" y1="{oy}" x2="{ox + W + sh}" y2="{oy + H}" stroke-dasharray="4 4" stroke-width="1.5"/>'
             f'<line x1="{ox + W}" y1="{oy + H}" x2="{ox + W + sh}" y2="{oy + H}" stroke-dasharray="4 4" stroke-width="1.5"/>'
             f'<polyline points="{ox + W + sh - 10},{oy + H} {ox + W + sh - 10},{oy + H - 10} {ox + W + sh},{oy + H - 10}" stroke-width="1.5"/>'
             + label(ox + W / 2, oy + H + 20, f"{b}x") + label(ox + sh / 2 - 12, oy + H / 2, str(s))
             + label(ox + W + sh + 14, oy + H / 2 + 5, str(h))
             + label(ox - 8, oy + H + 6, "B") + label(ox + W, oy + H + 20, "C") + label(ox + sh, oy - 8, "A")
             + label(ox + W + sh + 8, oy - 8, "D"))
    return svg(W + sh + 70, H + 55, inner)


@register("litteral.ts_figures")
def ts_figures(ctx: GenContext) -> Generated:
    what = ctx.pick(["périmètre", "aire"])
    hint = "Écris d'abord la formule (périmètre = somme des côtés, aire du triangle rectangle = côté · côté : 2), puis réduis."
    if ctx.rng.random() < 0.5:
        k, h = ctx.pick([2, 3, 4]), ctx.rnd(4, 12)
        fig = _triangle(k, h) + '<p class="muted" style="font-size:.88rem;margin:4px 0">Les segments marqués d\'un même trait ont la même longueur (x).</p>'
        if what == "périmètre":
            ans, steps = f"{k + 1}x + {h}", f"x + {k}x + {h}"
        else:
            ans, steps = f"{k}x^2/2", f"x · {k}x : 2 = {k}x² : 2"
        name = "de ce triangle rectangle"
    else:
        b, s, h = ctx.rnd(2, 9), ctx.rnd(3, 9), ctx.rnd(2, 8)
        if h >= s:
            h = s - 1
        fig = _parallelogram(b, s, h) + '<p class="muted" style="font-size:.88rem;margin:4px 0">AB ∥ CD et AD ∥ BC (parallélogramme), hauteur en pointillé.</p>'
        if what == "périmètre":
            ans, steps = f"{2 * b}x + {2 * s}", f"{b}x + {s} + {b}x + {s} = 2 · {b}x + 2 · {s}"
        else:
            ans, steps = f"{b * h}x", f"base · hauteur = {b}x · {h}"
            hint = "Aire du parallélogramme = base · hauteur (la hauteur, pas le côté oblique)."
        name = "du parallélogramme ABCD"
    return expr(ctx, f"Écris le plus simplement possible le <strong>{what}</strong> {name}.{fig}{TYPE}",
                ans, steps, hint)


# ------------------------------------------------------------------ Ex. 5 segments

def _line(points: list[tuple[float, str]], n_ticks: int, span: tuple[float, float], arrow: str = "") -> str:
    x0, x1 = 30, 30 + 40 * n_ticks
    inner = f'<line x1="{x0}" y1="40" x2="{x1}" y2="40"/>'
    a, b = span
    for i in range(n_ticks + 1):
        x = x0 + 40 * i
        big = any(abs(p - i) < 1e-9 for p, _ in points)
        inner += f'<line x1="{x}" y1="{32 if big else 35}" x2="{x}" y2="{48 if big else 45}" stroke-width="{2 if big else 1.5}"/>'
        if a <= i < b:
            inner += tick(x + 20, 40)
    for p, name in points:
        inner += label(x0 + 40 * p, 24, name)
    if arrow:
        inner += (f'<line x1="{x0}" y1="68" x2="{x1}" y2="68" stroke-width="1.5"/>'
                  f'<polyline points="{x0 + 8},63 {x0},68 {x0 + 8},73" stroke-width="1.5"/>'
                  f'<polyline points="{x1 - 8},63 {x1},68 {x1 - 8},73" stroke-width="1.5"/>'
                  + label((x0 + x1) / 2, 88, arrow))
    return svg(x1 + 30, 96 if arrow else 60, inner)


@register("litteral.ts_segments")
def ts_segments(ctx: GenContext) -> Generated:
    kind = ctx.pick(["parts", "rest", "minus"])
    hint = "Les traits égaux partagent le segment en parties de même longueur. Compte combien de parties forment AC."
    if kind == "parts":
        n = ctx.rnd(5, 9)
        m = ctx.rnd(1, n - 1)
        fig = _line([(0, "A"), (m, "C"), (n, "B")], n, (0, n))
        g = gcd(m, n)
        ans, disp = f"{m}x/{n}", (f"{m // g}x/{n // g}" if m // g != 1 else f"x/{n // g}")
        steps = f"AB = x est partagé en {n} parties égales ; AC en compte {m} : AC = {m} · x : {n}"
    elif kind == "rest":
        k = ctx.rnd(3, 6)
        L = ctx.pick([f"{ctx.rnd(20, 60)},5", str(ctx.rnd(20, 60))])
        fig = _line([(0, "B"), (k, "A"), (k + 4, "C")], k + 4, (0, k), arrow=L)
        ans = f"{L.replace(',', '.')} - x"
        disp = f"{L} − x"
        steps = f"BC = {L} et BA = x, donc AC = BC − BA = {L} − x"
        hint = "La flèche donne la longueur totale BC. Enlève la partie BA = x."
    else:
        d = ctx.rnd(2, 15)
        fig = _line([(0, "A"), (5, "C"), (7, "B")], 7, (0, 0), arrow="")
        fig += f'<p class="muted" style="font-size:.88rem;margin:4px 0">AB = x et CB = {d}</p>'
        ans, disp = f"x - {d}", f"x − {d}"
        steps = f"AC = AB − CB = x − {d}"
        hint = "AC est la partie de AB qui reste quand on enlève CB."
    return expr(ctx, f"Sachant que AB = x, écris l'expression littérale <strong>réduite</strong> de AC.{fig}{TYPE}",
                ans, steps, hint, form="any", display=disp)


# ------------------------------------------------------------------ Ex. 6 expressions équivalentes ?

def _pairs(ctx: GenContext) -> list[tuple[str, str, str]]:
    a, b, c, k, m = ctx.rnd(10, 30), ctx.rnd(2, 8), ctx.pick([2, 4]), ctx.rnd(2, 9), ctx.rnd(2, 9)
    while (a - b) % c:
        a += 1
    q = (a - b) // c
    p1 = ctx.rnd(2, 12)
    good, bad = q + p1, q + p1 + ctx.pick([-2 * c, c, 3])
    return [
        ("x · x · x", "x³", "x · x · x : trois facteurs x, donc x³."),
        ("x · x · x", "3x", "x · x · x = x³ ; 3x = x + x + x."),
        ("x + x", "x²", "x + x = 2x ; x² = x · x."),
        ("x + x", "2x", "x + x : deux fois x, donc 2x."),
        ("(−x)²", "−x²", "(−x)² = (−x)·(−x) = x², alors que −x² = −(x·x)."),
        ("(−x)²", "x²", "(−x)·(−x) = x² : moins fois moins donne plus."),
        (f"({a}x − {b}x) : {c}", f"−{p1}x + {good}x", f"({a}x − {b}x) : {c} = {a - b}x : {c} = {q}x et −{p1}x + {good}x = {q}x."),
        (f"({a}x − {b}x) : {c}", f"−{p1}x + {bad}x", f"({a}x − {b}x) : {c} = {q}x, mais −{p1}x + {bad}x = {bad - p1}x."),
        (f"{k}(x + {m})", f"{k}x + {m}", f"{k}(x + {m}) = {k}x + {k * m} : le {k} multiplie les deux termes."),
        (f"{k}(x + {m})", f"{k}x + {k * m}", f"{k}(x + {m}) = {k}·x + {k}·{m} = {k}x + {k * m}."),
        (f"(x + {m})²", f"x² + {m * m}", f"(x + {m})² = x² + {2 * m}x + {m * m} : il manque le double produit {2 * m}x."),
        (f"(x + {m})²", f"x² + {2 * m}x + {m * m}", f"(x + {m})(x + {m}) = x² + {m}x + {m}x + {m * m} = x² + {2 * m}x + {m * m}."),
        (f"{k}x · {m}x", f"{k * m}x²", f"{k}·{m}·x·x = {k * m}x²."),
        (f"{k}x · {m}x", f"{k * m}x", f"{k}x · {m}x = {k * m}x² (x · x = x²)."),
    ]


@register("litteral.ts_equivalent")
def ts_equivalent(ctx: GenContext) -> Generated:
    e1, e2, why = ctx.pick(_pairs(ctx))
    same = parse(e1) == parse(e2)
    choices = ["oui, elles sont équivalentes", "non, elles ne sont pas équivalentes"]
    return Generated(
        kind="choice", category=ctx.title, choices=choices, answer=0 if same else 1,
        prompt=f"Ces deux expressions sont-elles équivalentes (égales pour toutes les valeurs de x) ?<br>"
               f"<strong>{e1}</strong> &nbsp; et &nbsp; <strong>{e2}</strong>",
        hint="Réduis les deux expressions, ou essaie une valeur (x = 2, x = −1) dans les deux.",
        explain=f"<strong>{'Oui' if same else 'Non'}.</strong> {why}<br>"
                f"Au test, il faut justifier : écris le calcul qui le montre, pas seulement oui ou non.",
    )


# ------------------------------------------------------------------ Ex. 7 figure sur quadrillage (a et b)

def _grid(p: int, q: int, cut: bool) -> str:
    """p columns of width b, q rows of height a; with `cut`, the top-right cell is missing."""
    cw, ch, ox, oy = 34, 50, 30, 20
    W, H = p * cw, q * ch
    if cut:
        pts = [(ox, oy), (ox + W - cw, oy), (ox + W - cw, oy + ch), (ox + W, oy + ch), (ox + W, oy + H), (ox, oy + H)]
    else:
        pts = [(ox, oy), (ox + W, oy), (ox + W, oy + H), (ox, oy + H)]
    inner = ""
    for i in range(1, p):
        inner += f'<line x1="{ox + i * cw}" y1="{oy + (ch if cut and i == p - 1 else 0)}" x2="{ox + i * cw}" y2="{oy + H}" stroke-width="1" stroke-dasharray="3 3"/>'
    for j in range(1, q):
        inner += f'<line x1="{ox}" y1="{oy + j * ch}" x2="{ox + W}" y2="{oy + j * ch}" stroke-width="1" stroke-dasharray="3 3"/>'
    inner += '<polygon points="' + " ".join(f"{x},{y}" for x, y in pts) + '"/>'
    inner += label(ox + cw / 2, oy + H + 18, "b") + label(ox - 12, oy + H - ch / 2 + 5, "a")
    return svg(W + 60, H + 30, inner)


@register("litteral.ts_grid")
def ts_grid(ctx: GenContext) -> Generated:
    p, q = ctx.rnd(2, 4), ctx.rnd(2, 3)
    cut = ctx.rng.random() < 0.5
    cells = p * q - cut
    fig = _grid(p, q, cut) + ('<p class="muted" style="font-size:.88rem;margin:4px 0">Chaque case mesure b de large et a de haut. '
                              'Attention : tu ne sais pas si a = 2b.</p>')
    per, area = f"{2 * q}a + {2 * p}b", f"{cells}ab"
    per_steps = (f"côtés verticaux : {q}a + {q}a ; côtés horizontaux : {p}b + {p}b"
                 + (" (l'encoche ne change pas le périmètre : les côtés déplacés gardent la même longueur)" if cut else ""))
    area_steps = f"{cells} cases de b · a = {cells}ab"
    ask = ctx.pick(["per", "area", "per_val", "area_val"])
    if ask in ("per", "area"):
        what = "périmètre" if ask == "per" else "aire"
        ans, steps = (per, per_steps) if ask == "per" else (area, area_steps)
        return expr(ctx, f"Écris le <strong>{what}</strong> de cette figure en fonction de a et b.{fig}{TYPE}",
                    ans, steps, "Compte les côtés de longueur a et ceux de longueur b, ou le nombre de cases.",
                    display=show(parse(ans, "ab"), "ab"), variables="ab")
    a, b = ctx.rnd(2, 5), ctx.rnd(2, 5)
    if ask == "per_val":
        r = 2 * q * a + 2 * p * b
        steps = f"Périmètre = {per} = {2 * q} · {a} + {2 * p} · {b} = {2 * q * a} + {2 * p * b} = {r} cm"
        what, unit = "périmètre", "cm"
    else:
        r = cells * a * b
        steps = f"Aire = {area} = {cells} · {a} · {b} = {r} cm²"
        what, unit = "aire", "cm²"
    return expr(ctx, f"Si a = {a} cm et b = {b} cm, calcule le <strong>{what}</strong> de cette figure (en {unit}).{fig}",
                str(r), steps, "Écris d'abord l'expression en a et b, puis remplace a et b par leurs valeurs.",
                form="value", display=f"{r} {unit}")


# ------------------------------------------------------------------ Ex. 8 deux carrés accolés

def _squares(k: int) -> str:
    ox, oy, S, s = 40, 15, 120, 70
    inner = (f'<polyline points="{ox},{oy} {ox + S},{oy} {ox + S},{oy + S - s} {ox + S + s},{oy + S - s} '
             f'{ox + S + s},{oy + S} {ox},{oy + S} {ox},{oy}"/>'
             f'<line x1="{ox + S}" y1="{oy + S - s}" x2="{ox + S}" y2="{oy + S}" stroke-dasharray="4 4" stroke-width="1.5"/>'
             + label(ox - 14, oy + S / 2 + 5, "x"))
    return svg(S + s + 80, S + 30, inner) + (f'<p class="muted" style="font-size:.88rem;margin:4px 0">Deux carrés accolés : le petit a un côté '
                                               f'de {k} unités de moins que le grand (côté x).</p>')


@register("litteral.ts_squares")
def ts_squares(ctx: GenContext) -> Generated:
    k = ctx.rnd(2, 6)
    fig = _squares(k)
    if ctx.rng.random() < 0.5:
        ans = f"6x - {2 * k}"
        steps = (f"Côtés du contour : x (gauche) + x (haut) + {k} (marche) + (x − {k}) (haut du petit) + (x − {k}) (droite) "
                 f"+ x + (x − {k}) (bas) = 6x − {3 * k} + {k}")
        what, hint = "périmètre", f"Le côté du petit carré est x − {k}. Fais le tour de la figure et note chaque côté (n'oublie pas la marche de {k})."
    else:
        ans = f"2x^2 - {2 * k}x + {k * k}"
        steps = f"x² + (x − {k})² = x² + x² − {2 * k}x + {k * k}"
        what, hint = "aire", f"Aire = aire du grand carré + aire du petit : x² + (x − {k})², puis développe (x − {k})²."
    return expr(ctx, f"Exprime le plus simplement possible le <strong>{what}</strong> de cette figure.{fig}{TYPE}",
                ans, steps, hint)
