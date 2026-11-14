"""Forces and equilibrium generators (physique 10VP). Level: 0 = Facile, 1 = Moyen, 2 = Expert.

g = 9,81 N/kg on Earth (the value is always given in the question). Force diagrams use the
"forces" figure drawn by the front end (widgets/ForceFigure.tsx): arrows on a grid of squares,
`scale` newtons per square; each force {x, y, dx, dy, label} starts at (x, y) in squares.
"""
import math

from ..formatting import fr, round_to
from .base import GenContext, Generated, register

G = {"la Terre": 9.81, "la Lune": 1.62, "Mars": 3.71, "Jupiter": 24.8}
OBJECTS = [("un sac d'école", 6), ("un vélo", 12), ("une pastèque", 4), ("un chien", 18), ("une valise", 23),
           ("un élève", 52), ("une brique", 2.5), ("un pack d'eau", 9)]


def _n(x: float) -> str:
    return fr(round_to(x, 2))


@register("forces.weight")
def weight(ctx: GenContext) -> Generated:
    """P = m · g: the weight from the mass, or the mass from the weight (on another planet at level 2)."""
    name, m = ctx.pick(OBJECTS)
    place = "la Terre" if ctx.level < 2 else ctx.pick(list(G))
    g = G[place]
    p = round_to(m * g, 2)
    if ctx.level == 0 or ctx.rng.random() < 0.5:
        return Generated(
            kind="number", category=ctx.title, unit="N", answer=p, tol=0.051,
            prompt=f"Sur {place} (g = {_n(g)} N/kg), quel est le <strong>poids</strong> de {name} de masse {_n(m)} kg ?",
            hint="Poids = masse × intensité de la pesanteur : P = m · g.",
            explain=f"P = m · g = {_n(m)} kg × {_n(g)} N/kg = <strong>{_n(p)} N</strong>. "
                    "Le poids est une force (en newtons), la masse est une quantité de matière (en kg).",
        )
    shown = round_to(p, 1)
    m2 = round_to(shown / g, 2)
    return Generated(
        kind="number", category=ctx.title, unit="kg", answer=m2, tol=0.051,
        prompt=f"Sur {place} (g = {_n(g)} N/kg), un dynamomètre indique un poids de <strong>{_n(shown)} N</strong>. "
               "Quelle est la <strong>masse</strong> de l'objet ? (arrondis au centième)",
        hint="P = m · g, donc m = P ÷ g.",
        explain=f"m = P ÷ g = {_n(shown)} ÷ {_n(g)} ≈ <strong>{_n(m2)} kg</strong>.",
    )


@register("forces.moon")
def moon(ctx: GenContext) -> Generated:
    """Mass versus weight: the same mass on two planets."""
    name, m = ctx.pick(OBJECTS)
    place = ctx.pick(["la Lune", "Mars", "Jupiter"])
    p_earth, p_there = round_to(m * 9.81, 2), round_to(m * G[place], 2)
    ask_mass = ctx.rng.random() < 0.4
    if ask_mass:
        return Generated(
            kind="number", category=ctx.title, unit="kg", answer=m, tol=0.001,
            prompt=f"Sur Terre, {name} a une masse de {_n(m)} kg. Quelle est sa <strong>masse</strong> sur {place} ?",
            explain=f"La masse ne change pas : <strong>{_n(m)} kg</strong> partout. C'est le poids qui change "
                    f"({_n(p_earth)} N sur Terre, {_n(p_there)} N sur {place}).",
        )
    return Generated(
        kind="number", category=ctx.title, unit="N", answer=p_there, tol=0.051,
        prompt=f"{name.capitalize()} a une masse de {_n(m)} kg. Quel est son <strong>poids</strong> sur {place} "
               f"(g = {_n(G[place])} N/kg) ?",
        hint="La masse reste la même ; on multiplie par le g de l'astre.",
        explain=f"P = {_n(m)} × {_n(G[place])} = <strong>{_n(p_there)} N</strong> (sur Terre : {_n(p_earth)} N). "
                "La masse ne change pas, le poids dépend de l'astre.",
    )


@register("forces.spring")
def spring(ctx: GenContext) -> Generated:
    """Hooke's law F = k · Δl, with units in cm and N/m."""
    k = ctx.pick([20, 25, 40, 50, 80, 100, 200, 250, 500])
    dl_cm = ctx.pick([2, 3, 4, 5, 6, 8, 10, 12, 15])
    f = round_to(k * dl_cm / 100, 2)
    ask = "F" if ctx.level == 0 else ctx.pick(["F", "k", "dl"])
    hint = "Loi de Hooke : F = k · Δl, avec Δl en mètres (1 cm = 0,01 m)."
    if ask == "F":
        return Generated(
            kind="number", category=ctx.title, unit="N", answer=f, tol=0.051, hint=hint,
            prompt=f"Un ressort de raideur <strong>k = {k} N/m</strong> s'allonge de <strong>{dl_cm} cm</strong>. "
                   "Quelle est l'intensité de la force qui l'étire ?",
            explain=f"Δl = {dl_cm} cm = {_n(dl_cm / 100)} m. F = k · Δl = {k} × {_n(dl_cm / 100)} = <strong>{_n(f)} N</strong>.",
        )
    if ask == "k":
        return Generated(
            kind="number", category=ctx.title, unit="N/m", answer=k, tol=0.51, hint=hint,
            prompt=f"Une force de <strong>{_n(f)} N</strong> allonge un ressort de <strong>{dl_cm} cm</strong>. "
                   "Quelle est la raideur k du ressort ?",
            explain=f"k = F ÷ Δl = {_n(f)} ÷ {_n(dl_cm / 100)} = <strong>{k} N/m</strong>.",
        )
    return Generated(
        kind="number", category=ctx.title, unit="cm", answer=dl_cm, tol=0.051, hint=hint,
        prompt=f"On accroche une masse à un ressort de raideur <strong>{k} N/m</strong> : la force est de "
               f"<strong>{_n(f)} N</strong>. De combien de <strong>centimètres</strong> s'allonge-t-il ?",
        explain=f"Δl = F ÷ k = {_n(f)} ÷ {k} = {_n(dl_cm / 100)} m = <strong>{dl_cm} cm</strong>.",
    )


def _arrow(x, y, dx, dy, label, color="f1"):
    return {"x": x, "y": y, "dx": dx, "dy": dy, "label": label, "color": color}


@register("forces.read")
def read(ctx: GenContext) -> Generated:
    """Read the intensity of a force drawn on a grid, with the scale."""
    scale = ctx.pick([5, 10, 20, 50] if ctx.level else [10, 20])
    dirs = [(1, 0), (0, -1), (-1, 0), (0, 1)] if ctx.level == 0 else [(1, 0), (0, -1), (-1, 0), (0, 1), (3, 4), (4, 3), (-3, 4)]
    ux, uy = ctx.pick(dirs)
    n = ctx.rnd(2, 6) if (ux, uy) in ((1, 0), (0, -1), (-1, 0), (0, 1)) else 1
    dx, dy = ux * n, uy * n
    length = math.hypot(dx, dy)
    x0 = 1 + (-dx if dx < 0 else 0)
    y0 = 1 + (-dy if dy < 0 else 0)
    fig = {"type": "forces", "w": max(8, abs(dx) + 2), "h": max(6, abs(dy) + 2), "scale": scale,
           "forces": [_arrow(x0, y0, dx, dy, "F")]}
    ans = round_to(length * scale, 2)
    return Generated(
        kind="number", category=ctx.title, unit="N", answer=ans, tol=0.51, figure=fig,
        prompt=f"Échelle : <strong>1 carré ↔ {scale} N</strong>. Quelle est l'intensité de la force F ?",
        hint="Compte la longueur de la flèche en carrés, puis multiplie par l'échelle."
             + (" Pour une flèche en biais, utilise Pythagore." if length != int(length) or (dx and dy) else ""),
        explain=(f"La flèche mesure {_n(length)} carrés"
                 + (f" (Pythagore : √({abs(dx)}² + {abs(dy)}²) = {_n(length)})" if dx and dy else "")
                 + f". Intensité = {_n(length)} × {scale} N = <strong>{_n(ans)} N</strong>."),
    )


@register("forces.resultant")
def resultant(ctx: GenContext) -> Generated:
    """Two forces on the same point: same direction, opposite, or perpendicular."""
    f1, f2 = ctx.rnd(2, 9) * 10, ctx.rnd(2, 9) * 10
    case = ctx.pick(["same", "opposite"] if ctx.level == 0 else ["same", "opposite", "perp", "perp"])
    if case == "perp":
        f1, f2 = ctx.pick([(30, 40), (60, 80), (50, 120), (90, 120), (80, 150), (20, 21)]) if ctx.level == 1 \
            else (ctx.rnd(2, 9) * 10, ctx.rnd(2, 9) * 10)
    if case == "opposite" and f1 == f2:
        f2 += 10
    s = 10
    if case == "same":
        r, how = f1 + f2, f"Même direction et même sens : R = F₁ + F₂ = {f1} + {f2} = <strong>{f1 + f2} N</strong>."
        forces = [_arrow(1, 3, f1 / s, 0, "F₁"), _arrow(1, 3.6, f2 / s, 0, "F₂", "f2")]
    elif case == "opposite":
        r = abs(f1 - f2)
        how = (f"Même direction, sens contraires : R = {max(f1, f2)} − {min(f1, f2)} = <strong>{r} N</strong>, "
               f"dans le sens de la plus grande force.")
        forces = [_arrow(10, 3, f1 / s, 0, "F₁"), _arrow(10, 3, -f2 / s, 0, "F₂", "f2")]
    else:
        r = round_to(math.hypot(f1, f2), 2)
        how = (f"Forces perpendiculaires : la résultante est la diagonale du rectangle. "
               f"R = √({f1}² + {f2}²) = <strong>{_n(r)} N</strong> (Pythagore).")
        forces = [_arrow(1, 1 + f2 / s, f1 / s, 0, "F₁"), _arrow(1, 1 + f2 / s, 0, -f2 / s, "F₂", "f2")]
    w = 20 if case != "perp" else max(10, int(f1 / s) + 3)
    h = 6 if case != "perp" else max(6, int(f2 / s) + 3)
    if case == "same":
        w = max(10, int(max(f1, f2) / s) + 3)
    return Generated(
        kind="number", category=ctx.title, unit="N", answer=r, tol=0.051 if case != "perp" or r == int(r) else 0.51,
        figure={"type": "forces", "w": w, "h": h, "scale": s, "forces": forces},
        prompt=f"Deux forces s'appliquent au même point : <strong>F₁ = {f1} N</strong> et <strong>F₂ = {f2} N</strong> "
               "(voir le schéma). Quelle est l'intensité de la <strong>résultante</strong> R ?"
               + (" (arrondis au dixième)" if case == "perp" and r != int(r) else ""),
        hint="Même sens : on additionne. Sens contraires : on soustrait. Perpendiculaires : Pythagore.",
        explain=how,
    )


@register("forces.balance")
def balance(ctx: GenContext) -> Generated:
    """Equilibrium: the force that balances one or two given forces (intensity, or angle at level 2)."""
    if ctx.level == 0:
        name, m = ctx.pick(OBJECTS[:5])
        p = round_to(m * 9.81, 2)
        what = ctx.pick(["un fil", "une table", "un ressort"])
        force = {"un fil": "la tension du fil", "une table": "la force de soutien de la table", "un ressort": "la force du ressort"}[what]
        return Generated(
            kind="number", category=ctx.title, unit="N", answer=p, tol=0.051,
            prompt=f"{name.capitalize()} de {_n(m)} kg est immobile, tenu par {what} (g = 9,81 N/kg). "
                   f"Quelle est l'intensité de <strong>{force}</strong> ?",
            hint="À l'équilibre, les deux forces ont la même direction, la même intensité et des sens contraires.",
            explain=f"Le poids vaut P = {_n(m)} × 9,81 = {_n(p)} N, vers le bas. À l'équilibre, {force} le compense : "
                    f"<strong>{_n(p)} N</strong>, vers le haut.",
        )
    f1, f2 = ctx.pick([(30, 40), (60, 80), (50, 120), (90, 120), (40, 30), (120, 160), (70, 70), (100, 60)])
    r = round_to(math.hypot(f1, f2), 2)
    s = 10 if max(f1, f2) <= 90 else 20
    fig = {"type": "forces", "w": int(f1 / s) + 4, "h": int(f2 / s) + 4, "scale": s,
           "forces": [_arrow(2, 2 + f2 / s, f1 / s, 0, "F₁"), _arrow(2, 2 + f2 / s, 0, -f2 / s, "F₂", "f2")]}
    if ctx.level == 2 and ctx.rng.random() < 0.5:
        angle = round_to(math.degrees(math.atan2(f2, f1)), 1)
        return Generated(
            kind="number", category=ctx.title, unit="°", answer=angle, tol=0.51, figure=fig,
            prompt=f"Un anneau est tiré par <strong>F₁ = {f1} N</strong> (vers la droite) et <strong>F₂ = {f2} N</strong> "
                   "(vers le haut). Quel angle la <strong>résultante</strong> fait-elle avec F₁ ? (au dixième de degré)",
            hint="Dans le triangle rectangle : tan(α) = côté opposé ÷ côté adjacent = F₂ ÷ F₁.",
            explain=f"tan(α) = {f2} ÷ {f1} = {_n(f2 / f1)}, donc α = arctan({_n(f2 / f1)}) ≈ <strong>{fr(angle)}°</strong>. "
                    "La force qui équilibre l'anneau a la même direction, mais le sens contraire.",
        )
    return Generated(
        kind="number", category=ctx.title, unit="N", answer=r, tol=0.051 if r == int(r) else 0.51, figure=fig,
        prompt=f"Un anneau est tiré par <strong>F₁ = {f1} N</strong> et <strong>F₂ = {f2} N</strong>, perpendiculaires. "
               "Quelle force F₃ faut-il exercer pour qu'il reste <strong>en équilibre</strong> ? Donne son intensité"
               + (" (au dixième)." if r != int(r) else "."),
        hint="F₃ doit compenser la résultante de F₁ et F₂ : même intensité, sens contraire.",
        explain=f"Résultante : R = √({f1}² + {f2}²) = {_n(r)} N. F₃ a la même intensité, <strong>{_n(r)} N</strong>, "
                "la même direction que R et le sens contraire : la somme des trois forces est nulle.",
    )
