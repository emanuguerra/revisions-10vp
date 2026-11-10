"""Small exact polynomial algebra for the calcul littéral exercises (no sympy).

parse("3(2x − 5) + x^2") -> Poly, a dict {monomial: Fraction}, where a monomial is a
sorted tuple of (variable, exponent), e.g. (("x", 2),) for x², () for the constant term.

Student input is rewritten to Python syntax (implicit products, ², comma decimals...)
and read with `ast`; only + − × ÷(by a number) and whole powers of the allowed letters
are evaluated, anything else is refused.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from fractions import Fraction
from .formatting import fr

Mono = tuple[tuple[str, int], ...]
Poly = dict[Mono, Fraction]

MAX_LEN = 120
MAX_POWER = 6


class ExprError(ValueError):
    pass


# ------------------------------------------------------------------ polynomials

def const(c) -> Poly:
    c = Fraction(c)
    return {(): c} if c else {}


def var(name: str) -> Poly:
    return {((name, 1),): Fraction(1)}


def add(p: Poly, q: Poly, sign: int = 1) -> Poly:
    out = dict(p)
    for m, c in q.items():
        out[m] = out.get(m, 0) + sign * c
    return {m: c for m, c in out.items() if c}


def _mono_mul(m: Mono, n: Mono) -> Mono:
    exps: dict[str, int] = dict(m)
    for v, e in n:
        exps[v] = exps.get(v, 0) + e
    return tuple(sorted(exps.items()))


def mul(p: Poly, q: Poly) -> Poly:
    if len(p) * len(q) > 2000:
        raise ExprError("expression trop grande")
    out: Poly = {}
    for m, c in p.items():
        for n, d in q.items():
            k = _mono_mul(m, n)
            out[k] = out.get(k, 0) + c * d
    return {m: c for m, c in out.items() if c}


def power(p: Poly, n: int) -> Poly:
    out = const(1)
    for _ in range(n):
        out = mul(out, p)
    return out


def evaluate(p: Poly, values: dict[str, Fraction]) -> Fraction:
    total = Fraction(0)
    for m, c in p.items():
        t = c
        for v, e in m:
            t *= Fraction(values[v]) ** e
        total += t
    return total


# ------------------------------------------------------------------ parsing

def normalize(s: str) -> str:
    """Rewrite what a student types into Python syntax: '−3x²·y' -> '-3*x**2*y'."""
    s = str(s).strip().lower()
    for a, b in (("−", "-"), ("–", "-"), ("—", "-"), ("·", "*"), ("×", "*"), ("⋅", "*"),
                 ("÷", "/"), (":", "/"), ("²", "^2"), ("³", "^3"), ("⁴", "^4"), ("[", "("), ("]", ")")):
        s = s.replace(a, b)
    s = re.sub(r"(\d),(\d)", r"\1.\2", s)
    s = re.sub(r"\s+", "", s)
    s = s.replace("**", "^")
    # implicit products: 3x, 2(x), x(…), )(, )x, )3, xy
    s = re.sub(r"(?<=[\d.)])(?=[a-z(])", "*", s)
    s = re.sub(r"(?<=[a-z])(?=[(])", "*", s)
    s = re.sub(r"(?<=\))(?=[\d.])", "*", s)
    while re.search(r"[a-z][a-z]", s):
        s = re.sub(r"([a-z])(?=[a-z])", r"\1*", s)
    return s.replace("^", "**")


def _walk(node: ast.AST, allowed: set[str]) -> Poly:
    if isinstance(node, ast.Expression):
        return _walk(node.body, allowed)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return const(Fraction(str(node.value)))
    if isinstance(node, ast.Name):
        if node.id not in allowed:
            raise ExprError(f"lettre inconnue : {node.id}")
        return var(node.id)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        p = _walk(node.operand, allowed)
        return {m: -c for m, c in p.items()} if isinstance(node.op, ast.USub) else p
    if isinstance(node, ast.BinOp):
        a = _walk(node.left, allowed)
        if isinstance(node.op, ast.Pow):
            b = _walk(node.right, allowed)
            n = b.get((), Fraction(0))
            if set(b) - {()} or n.denominator != 1 or not 0 <= n <= MAX_POWER:
                raise ExprError("puissance non entière")
            return power(a, int(n))
        b = _walk(node.right, allowed)
        if isinstance(node.op, ast.Add):
            return add(a, b)
        if isinstance(node.op, ast.Sub):
            return add(a, b, -1)
        if isinstance(node.op, ast.Mult):
            return mul(a, b)
        if isinstance(node.op, ast.Div):
            d = b.get((), Fraction(0))
            if set(b) - {()} or not d:
                raise ExprError("division par une expression")
            return {m: c / d for m, c in a.items()}
    raise ExprError("expression non reconnue")


def parse(s: str, variables: str = "xyabn") -> Poly:
    text = normalize(s)
    if not text or len(text) > MAX_LEN:
        raise ExprError("expression vide ou trop longue")
    try:
        tree = ast.parse(text, mode="eval")
    except SyntaxError as e:
        raise ExprError("expression mal écrite") from e
    return _walk(tree, set(variables))


def top_terms(s: str) -> int:
    """Number of terms at the top level: '5x + 3 − 2x' -> 3, '3(x + 1)' -> 1, '−4' -> 1."""
    node = ast.parse(normalize(s), mode="eval").body
    n = 1
    while isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
        n += 1
        node = node.left
    return n


# ------------------------------------------------------------------ display

SUP = {2: "²", 3: "³", 4: "⁴", 5: "⁵", 6: "⁶"}


def _num(c: Fraction) -> str:
    return str(c) if c.denominator not in (1, 2, 4, 5, 8, 10, 20, 25, 50, 100) else fr(float(c))


def mono_str(m: Mono) -> str:
    return "".join(v + SUP.get(e, "") if e > 1 else v for v, e in m)


def term_str(c: Fraction, m: Mono) -> str:
    """Unsigned term: (3, x²) -> '3x²', (1, x) -> 'x', (½, x) -> '0,5x'."""
    c = abs(c)
    if not m:
        return _num(c)
    return ("" if c == 1 else _num(c)) + mono_str(m)


def order(p: Poly, variables: str = "xyabn") -> list[Mono]:
    def key(m: Mono):
        deg = sum(e for _, e in m)
        return (-deg, [(variables.index(v), -e) for v, e in m])
    return sorted(p, key=key)


def show(p: Poly, variables: str = "xyabn") -> str:
    """'6x² − 2x + 5' with a real minus sign, terms by decreasing degree."""
    if not p:
        return "0"
    out = ""
    for i, m in enumerate(order(p, variables)):
        c = p[m]
        t = term_str(c, m)
        out += ("−" + t if c < 0 else t) if i == 0 else (" − " if c < 0 else " + ") + t
    return out


def pretty(s: str) -> str:
    """Make a generator's ASCII expression readable: '-3*x^2' -> '−3x²'."""
    s = s.replace("^2", "²").replace("^3", "³").replace("*", "·")
    s = re.sub(r"(?<=[\d)])·(?=[a-z(])", "", s)
    s = re.sub(r"(?<=[a-z])·(?=[a-z(])", "", s)
    s = re.sub(r"\s*([+=])\s*", r" \1 ", s)
    s = re.sub(r"(?<=[\w)²³])\s*-\s*", " − ", s)
    return s.replace("-", "−").strip()


# ------------------------------------------------------------------ answer checking

@dataclass
class ExprCheck:
    status: str                 # correct | wrong | form (equal but not in the requested form) | invalid
    message: str = ""


def check_answer(value: object, expected: str, form: str, variables: str = "xyabn") -> ExprCheck:
    """Compare a student expression to the expected one.

    form: "reduced" (developed and reduced, no brackets) or "value" (a single number).
    An equivalent answer in the wrong form does not cost an attempt.
    """
    raw = str(value).strip()
    if not raw:
        return ExprCheck("invalid", "Écris une réponse.")
    try:
        got = parse(raw, variables)
        terms = top_terms(raw)
    except (ExprError, RecursionError, ValueError):
        hint = " Tape x^2 pour x²." if re.search(r"[a-z]\d", raw.lower()) else ""
        return ExprCheck("invalid", "Je ne comprends pas cette expression, par exemple 3x + 5 ou x^2 − 4." + hint)
    want = parse(expected, variables)
    if got != want:
        return ExprCheck("wrong")
    if form == "value":
        if terms > 1 or "(" in normalize(raw) or "/" in normalize(raw):
            return ExprCheck("form", "C'est juste, mais calcule jusqu'au bout : la réponse est un seul nombre.")
    elif form == "reduced":
        if "(" in normalize(raw):
            return ExprCheck("form", "C'est égal, mais il reste des parenthèses : développe complètement.")
        if terms > max(1, len(want)):
            return ExprCheck("form", "C'est égal, mais pas encore réduit : regroupe les termes semblables.")
    return ExprCheck("correct")
