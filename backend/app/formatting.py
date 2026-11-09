"""Swiss French number formatting and parsing, shared by generators and answer checking."""
import math
import re

NNBSP = " "  # thousands separator used by fr-CH


def round_to(x: float, d: int) -> float:
    """Round half up (like JavaScript Math.round), not banker's rounding."""
    f = 10 ** d
    return math.floor(x * f + 0.5) / f


def sq(x: float) -> float:
    return round_to(x * x, 4)


def fr(x: float) -> str:
    """1440000 -> '1 440 000', 8.6 -> '8,6', 3.0 -> '3' (max 4 decimals)."""
    x = round_to(float(x), 4)
    neg = x < 0
    s = f"{abs(x):.4f}".rstrip("0").rstrip(".")
    whole, _, dec = s.partition(".")
    groups = []
    while len(whole) > 3:
        groups.insert(0, whole[-3:])
        whole = whole[:-3]
    groups.insert(0, whole)
    out = NNBSP.join(groups) + ("," + dec if dec else "")
    return ("-" if neg else "") + out


def parse_num(s: object) -> float:
    """Accepts '8,6', '8.6', '1 250', "1'250". Returns NaN when it is not a number."""
    text = re.sub(r"[\s'’]", "", str(s).strip()).replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return math.nan


def norm_text(s: str) -> str:
    return re.sub(r"[-\s]+", " ", s.strip().lower())
