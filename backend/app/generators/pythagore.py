"""Pythagorean theorem generators (10VP). Level: 0 = Facile, 1 = Moyen, 2 = Expert.

Figures use the "right-triangle" type drawn by the front end (TriangleFigure):
names[2] is the right-angle vertex R, names[1] = P (end of leg a), names[0] = Q (end of leg b).
Side a = [RP], side b = [RQ], side c = [PQ] (hypotenuse).
"""
import math

from ..formatting import fr, round_to, sq
from .base import GenContext, Generated, register

NAMES = ["ABC", "DEF", "MNP", "RST", "KLM", "XYZ", "GHI"]
TRIPLES = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25), (20, 21, 29)]


def seg(p: str, q: str) -> str:
    return "".join(sorted([p, q]))


def is_int(x: float) -> bool:
    return abs(x - round(x)) < 1e-9


def scaled_triple(ctx: GenContext, level: int) -> list[float]:
    t = ctx.pick(TRIPLES if level else TRIPLES[:3])
    k = 1 if t[2] > 17 else ctx.pick([1, 2, 3, 0.5, 1.5] if level else [1, 2, 3])
    return [round_to(x * k, 2) for x in t]


def figure(ctx: GenContext, **kw) -> dict:
    return {"type": "right-triangle", "rot": ctx.rnd(0, 359), "flip": ctx.rng.random() < 0.5, **kw}


def _names(ctx: GenContext):
    base = ctx.pick(NAMES)
    return base, ctx.shuffle(base)


def _unit(ctx: GenContext) -> str:
    return "cm" if ctx.level == 0 else ctx.pick(["cm", "m", "mm"])


@register("pythagore.hyp")
def hyp(ctx: GenContext) -> Generated:
    base, v = _names(ctx)
    hy = seg(v[0], v[1])
    return Generated(
        kind="side", category=ctx.title, answer="c", choices=["a", "b", "c"], max_tries=3,
        prompt=f"Le triangle {base} est rectangle en <strong>{v[2]}</strong>. Clique sur son <strong>hypoténuse</strong>.",
        figure=figure(ctx, a=ctx.rnd(3, 9), b=ctx.rnd(3, 9), names="".join(v), click=True),
        hint="L'hypoténuse est le côté en face de l'angle droit.",
        retry_message="Ce côté est une cathète : il touche l'angle droit. Clique sur un autre côté.",
        explain=f"L'hypoténuse est le côté opposé à l'angle droit en {v[2]} : c'est <strong>[{hy}]</strong>. C'est aussi le plus long côté.",
    )


@register("pythagore.calc_hyp")
def calc_hyp(ctx: GenContext) -> Generated:
    base, v = _names(ctx)
    u = _unit(ctx)
    if ctx.level == 0:
        a, b = ctx.shuffle(scaled_triple(ctx, 0)[:2])
    elif ctx.level == 1:
        a, b = ctx.rnd(2, 15), ctx.rnd(2, 15)
    else:
        a, b = ctx.rnd(15, 90) / 10, ctx.rnd(15, 90) / 10
    c2 = round_to(sq(a) + sq(b), 4)
    c = math.sqrt(c2)
    exact = is_int(c)
    ans = round(c) if exact else round_to(c, 1)
    hy, sa, sb = seg(v[0], v[1]), seg(v[2], v[1]), seg(v[2], v[0])
    return Generated(
        kind="number", category=ctx.title, answer=ans, tol=0.001 if exact else 0.051, unit=u,
        prompt=f"Le triangle {base} est rectangle en {v[2]}. {sa} = {fr(a)} {u} et {sb} = {fr(b)} {u}. "
               f"Calcule {hy}{'' if exact else ' (arrondis au dixième)'}.",
        figure=figure(ctx, a=a, b=b, names="".join(v), lab={"a": fr(a), "b": fr(b), "c": "?"}),
        hint=f"[{hy}] est l'hypoténuse : {hy}² = {sa}² + {sb}²",
        explain=f"{hy}² = {sa}² + {sb}² = {fr(a)}² + {fr(b)}² = {fr(sq(a))} + {fr(sq(b))} = {fr(c2)}<br>"
                f"{hy} = √{fr(c2)} {'=' if exact else '≈'} <strong>{fr(ans)} {u}</strong>",
        answer_display=f"{fr(ans)} {u}",
    )


@register("pythagore.calc_leg")
def calc_leg(ctx: GenContext) -> Generated:
    base, v = _names(ctx)
    u = _unit(ctx)
    if ctx.level == 0:
        t = scaled_triple(ctx, 0)
        a, c = ctx.pick(t[:2]), t[2]
    elif ctx.level == 1:
        c = ctx.rnd(8, 20)
        a = ctx.rnd(3, c - 2)
    else:
        c = ctx.rnd(50, 150) / 10
        a = ctx.rnd(15, round(c * 10) - 8) / 10
    b2 = round_to(sq(c) - sq(a), 4)
    b = math.sqrt(b2)
    exact = is_int(b)
    ans = round(b) if exact else round_to(b, 1)
    hy, sa, sb = seg(v[0], v[1]), seg(v[2], v[1]), seg(v[2], v[0])
    return Generated(
        kind="number", category=ctx.title, answer=ans, tol=0.001 if exact else 0.051, unit=u,
        prompt=f"Le triangle {base} est rectangle en {v[2]}. {hy} = {fr(c)} {u} et {sa} = {fr(a)} {u}. "
               f"Calcule {sb}{'' if exact else ' (arrondis au dixième)'}.",
        figure=figure(ctx, a=a, b=b, names="".join(v), lab={"a": fr(a), "b": "?", "c": fr(c)}),
        hint=f"On cherche une cathète : {sb}² = {hy}² − {sa}²",
        explain=f"{sb}² = {hy}² − {sa}² = {fr(c)}² − {fr(a)}² = {fr(sq(c))} − {fr(sq(a))} = {fr(b2)}<br>"
                f"{sb} = √{fr(b2)} {'=' if exact else '≈'} <strong>{fr(ans)} {u}</strong>",
        answer_display=f"{fr(ans)} {u}",
    )


@register("pythagore.reciprocal")
def reciprocal(ctx: GenContext) -> Generated:
    base = ctx.pick(NAMES)
    s = scaled_triple(ctx, 1 if ctx.level else 0)
    if ctx.rng.random() < 0.5:
        i = ctx.rnd(0, 2)
        s[i] = round_to(s[i] + ctx.pick([-1, 1]) * (1 if s[i] >= 4 else 0.5), 2)
    segs, lens = ctx.shuffle([(0, 1), (1, 2), (0, 2)]), ctx.shuffle(s)
    items = [{"name": base[p] + base[q], "len": lens[i], "opp": base[3 - p - q]} for i, (p, q) in enumerate(segs)]
    longest = max(items, key=lambda x: x["len"])
    others = [x for x in items if x is not longest]
    c2 = sq(longest["len"])
    ab = round_to(sq(others[0]["len"]) + sq(others[1]["len"]), 4)
    right = abs(c2 - ab) < 1e-6
    expert = ctx.level == 2
    if expert:
        choices = ["Rectangle", "Acutangle (3 angles aigus)", "Obtusangle (1 angle obtus)"]
        answer = 0 if right else (1 if c2 < ab else 2)
    else:
        choices = ["Oui, il est rectangle", "Non, il n'est pas rectangle"]
        answer = 0 if right else 1
    sides = ", ".join(f"{x['name']} = {fr(x['len'])} cm" for x in items)
    explain = (
        f"Plus long côté : [{longest['name']}] = {fr(longest['len'])} cm<br>{longest['name']}² = {fr(c2)}<br>"
        f"{others[0]['name']}² + {others[1]['name']}² = {fr(sq(others[0]['len']))} + {fr(sq(others[1]['len']))} = {fr(ab)}<br>"
    )
    if right:
        explain += f"Égalité : d'après la réciproque, le triangle est <strong>rectangle en {longest['opp']}</strong>."
    else:
        explain += f"{fr(c2)} {'<' if c2 < ab else '>'} {fr(ab)} : pas d'égalité, le triangle <strong>n'est pas rectangle</strong>"
        if expert:
            explain += ". Il est acutangle." if c2 < ab else f". Il est obtusangle (angle obtus en {longest['opp']})."
        else:
            explain += "."
    return Generated(
        kind="choice", category=ctx.title, choices=choices, answer=answer,
        prompt=f"Le triangle {base} a pour côtés {sides}. {'Quelle est sa nature ?' if expert else 'Est-il rectangle ?'}",
        hint="Compare le carré du plus long côté avec la somme des carrés des deux autres.",
        explain=explain,
    )


@register("pythagore.triplet")
def triplet(ctx: GenContext) -> Generated:
    L = ctx.level
    if ctx.rng.random() < 0.5:
        t = TRIPLES[ctx.rnd(0, 3 if L else 2)]
        k = 1 if t[2] > 17 else ctx.rnd(1, 4 if L else 3)
        s = [x * k for x in t]
        miss = 2 if L == 0 else ctx.rnd(0, 2)
        shown = " ; ".join("<strong>?</strong>" if i == miss else str(x) for i, x in enumerate(s))
        if miss == 2:
            explain = f"? ² = {s[0]}² + {s[1]}² = {s[0] ** 2} + {s[1] ** 2} = {s[2] ** 2}, donc ? = <strong>{s[2]}</strong>"
        else:
            other = s[1 - miss]
            explain = f"? ² = {s[2]}² − {other}² = {s[2] ** 2} − {other ** 2} = {s[miss] ** 2}, donc ? = <strong>{s[miss]}</strong>"
        return Generated(
            kind="number", category=ctx.title, answer=s[miss], tol=0.001,
            prompt=f'Complète le triplet pythagoricien ({shown}). <span class="muted">Le dernier nombre est le plus grand.</span>',
            hint="c² = a² + b²" if miss == 2 else "Il manque un petit nombre : a² = c² − b²",
            explain=explain, answer_display=str(s[miss]),
        )

    t = TRIPLES[ctx.rnd(0, 3)]
    k = 1 if t[2] > 17 else ctx.rnd(1, 3)
    good = [x * k for x in t]

    def is_p(x):
        return x[0] ** 2 + x[1] ** 2 == x[2] ** 2

    fakes: list[list[int]] = []
    while len(fakes) < 3:
        f = [x * ctx.rnd(1, 2) for x in TRIPLES[ctx.rnd(0, 3)]]
        f[ctx.rnd(0, 2)] += ctx.pick([-1, 1, 2])
        f.sort()
        if not is_p(f) and f[0] > 0 and f != good and f not in fakes:
            fakes.append(f)
    opts = ctx.shuffle([good, *fakes])
    return Generated(
        kind="choice", category=ctx.title, choices=[f"({' ; '.join(map(str, x))})" for x in opts], answer=opts.index(good),
        prompt="Lequel de ces triplets est pythagoricien ?",
        hint="Teste a² + b² = c² pour chacun, c étant le plus grand nombre.",
        explain=f"{good[0]}² + {good[1]}² = {good[0] ** 2} + {good[1] ** 2} = {good[2] ** 2} = {good[2]}², "
                f"donc <strong>({' ; '.join(map(str, good))})</strong> est pythagoricien.",
    )


# ---------------------------------------------------------------- word problems
# Each problem returns (emoji, prompt, answer, decimals, unit, explain, hint or None).

def _kite(ctx):
    d, h, L = ctx.pick([(30, 40, 50), (24, 32, 40), (36, 48, 60), (15, 20, 25)])
    return ("🪁", f"Le fil de ton cerf-volant est bien tendu et mesure {L} m. Tu te trouves à {d} m du point situé juste sous le cerf-volant. À quelle hauteur vole-t-il ?",
            h, 0, "m", f"Le fil est l'hypoténuse.<br>h² = {L}² − {d}² = {L * L} − {d * d} = {h * h}<br>h = √{h * h} = <strong>{h} m</strong>", None)


def _park(ctx):
    w, l, d = ctx.pick([(60, 80, 100), (90, 120, 150), (50, 120, 130), (30, 40, 50)])
    return ("🌳", f"Un parc rectangulaire mesure {l} m sur {w} m. Pour aller d'un coin au coin opposé, combien de mètres économises-tu en traversant en diagonale plutôt qu'en longeant deux côtés ?",
            l + w - d, 0, "m",
            f"Diagonale : d² = {l}² + {w}² = {fr(l * l)} + {fr(w * w)} = {fr(d * d)}, donc d = {d} m.<br>Le long des côtés : {l} + {w} = {l + w} m.<br>Économie : {l + w} − {d} = <strong>{l + w - d} m</strong>",
            "Calcule d'abord la diagonale, puis compare avec le chemin le long des côtés.")


def _ladder_easy(ctx):
    d, h, L = ctx.pick([(3, 4, 5), (1.5, 2, 2.5), (1.2, 1.6, 2)])
    return ("🪜", f"Une échelle de {fr(L)} m est appuyée contre un mur. Son pied est à {fr(d)} m du mur. À quelle hauteur arrive le haut de l'échelle ?",
            h, 2, "m", f"L'échelle est l'hypoténuse.<br>h² = {fr(L)}² − {fr(d)}² = {fr(sq(L))} − {fr(sq(d))} = {fr(sq(h))}<br>h = √{fr(sq(h))} = <strong>{fr(h)} m</strong>", None)


def _ladder(ctx):
    L, d = ctx.pick([3, 3.5, 4, 4.5]), ctx.pick([0.8, 1, 1.2])
    h2 = round_to(L * L - d * d, 4)
    h = math.sqrt(h2)
    return ("🪜", f"Une échelle de {fr(L)} m est appuyée contre un mur. Son pied est à {fr(d)} m du mur. À quelle hauteur arrive le haut de l'échelle ? (en m, arrondis au cm)",
            h, 2, "m", f"L'échelle est l'hypoténuse.<br>h² = {fr(L)}² − {fr(d)}² = {fr(sq(L))} − {fr(sq(d))} = {fr(h2)}<br>h = √{fr(h2)} ≈ <strong>{fr(round_to(h, 2))} m</strong>", None)


def _football(ctx):
    l, w = ctx.pick([(105, 68), (100, 64), (90, 45)])
    d2 = l * l + w * w
    d = math.sqrt(d2)
    return ("⚽", f"Un terrain de football mesure {l} m sur {w} m. Quelle est la longueur de sa diagonale ? (arrondis au dixième)",
            d, 1, "m", f"d² = {l}² + {w}² = {fr(l * l)} + {fr(w * w)} = {fr(d2)}<br>d = √{fr(d2)} ≈ <strong>{fr(round_to(d, 1))} m</strong>", None)


def _skilift(ctx):
    hd, v = ctx.pick([(800, 300), (1200, 350), (950, 420)])
    L2 = hd * hd + v * v
    L = math.sqrt(L2)
    return ("🚡", f"Un téléski monte de {v} m (dénivelé) sur une distance horizontale de {hd} m. Quelle est la longueur du câble, supposé bien droit ? (arrondis au mètre)",
            L, 0, "m", f"L² = {fr(hd)}² + {v}² = {fr(hd * hd)} + {fr(v * v)} = {fr(L2)}<br>L = √{fr(L2)} ≈ <strong>{fr(round_to(L, 0))} m</strong>", None)


def _square(ctx):
    s = ctx.rnd(3, 15)
    d2 = 2 * s * s
    d = math.sqrt(d2)
    return ("⬛", f"Calcule la longueur de la diagonale d'un carré de {s} cm de côté. (arrondis au dixième)",
            d, 1, "cm", f"d² = {s}² + {s}² = {s * s} + {s * s} = {d2}<br>d = √{d2} ≈ <strong>{fr(round_to(d, 1))} cm</strong>",
            "La diagonale coupe le carré en deux triangles rectangles.")


def _tv(ctx):
    w, h = ctx.pick([(89, 50), (110, 62), (122, 69), (144, 81)])
    d2 = w * w + h * h
    d = math.sqrt(d2)
    return ("📺", f"L'écran d'une télévision mesure {w} cm de large et {h} cm de haut. Quelle est la longueur de sa diagonale ? (arrondis au cm)",
            d, 0, "cm", f"d² = {w}² + {h}² = {fr(w * w)} + {fr(h * h)} = {fr(d2)}<br>d = √{fr(d2)} ≈ <strong>{fr(round_to(d, 0))} cm</strong>, soit environ {fr(round_to(d / 2.54, 0))} pouces (1 pouce = 2,54 cm).", None)


def _roof(ctx):
    w, h = ctx.pick([8, 10, 12]), ctx.pick([2.5, 3, 3.5, 4])
    x2 = round_to((w / 2) ** 2 + h * h, 4)
    x = math.sqrt(x2)
    return ("🏠", f"Le toit d'un chalet est symétrique. Sa largeur est de {w} m et son sommet se trouve {fr(h)} m au-dessus des murs. Quelle est la longueur d'un pan du toit ? (en m, arrondis au cm)",
            x, 2, "m", f"Demi-largeur : {w} : 2 = {fr(w / 2)} m.<br>x² = {fr(w / 2)}² + {fr(h)}² = {fr((w / 2) ** 2)} + {fr(sq(h))} = {fr(x2)}<br>x = √{fr(x2)} ≈ <strong>{fr(round_to(x, 2))} m</strong>",
            "La hauteur du toit coupe la largeur en deux moitiés égales.")


def _equilateral(ctx):
    s = ctx.rnd(4, 12)
    h2 = round_to(s * s - (s / 2) ** 2, 4)
    h = math.sqrt(h2)
    return ("🔺", f"Calcule la hauteur d'un triangle équilatéral de {s} cm de côté. (arrondis au dixième)",
            h, 1, "cm", f"Triangle rectangle d'hypoténuse {s} cm et de cathète {fr(s / 2)} cm.<br>h² = {s}² − {fr(s / 2)}² = {s * s} − {fr((s / 2) ** 2)} = {fr(h2)}<br>h = √{fr(h2)} ≈ <strong>{fr(round_to(h, 1))} cm</strong>",
            "La hauteur coupe le côté opposé en son milieu : elle forme un triangle rectangle.")


def _phone(ctx):
    w, h = ctx.pick([(7.1, 15.3), (6.8, 14.7), (7.6, 16.3)])
    d2 = round_to(w * w + h * h, 4)
    d = math.sqrt(d2)
    p = d / 2.54
    return ("📱", f"L'écran d'un smartphone mesure {fr(w)} cm sur {fr(h)} cm. La taille d'un écran se donne en pouces (1 pouce = 2,54 cm). Quelle est la taille de cet écran en pouces ? (arrondis au dixième)",
            p, 1, "pouces", f"d² = {fr(w)}² + {fr(h)}² = {fr(sq(w))} + {fr(sq(h))} = {fr(d2)}<br>d = √{fr(d2)} ≈ {fr(round_to(d, 2))} cm<br>{fr(round_to(d, 2))} : 2,54 ≈ <strong>{fr(round_to(p, 1))} pouces</strong>",
            "Calcule d'abord la diagonale en cm, puis divise par 2,54.")


def _ramp(ctx):
    h, l = ctx.pick([(0.3, 3.6), (0.45, 5.4), (0.6, 7.2)])
    x2 = round_to(h * h + l * l, 4)
    x = math.sqrt(x2)
    return ("♿", f"Une rampe d'accès pour fauteuil roulant monte de {fr(h)} m sur une distance horizontale de {fr(l)} m. Quelle est la longueur de la rampe ? (en m, arrondis au cm)",
            x, 2, "m", f"x² = {fr(l)}² + {fr(h)}² = {fr(sq(l))} + {fr(sq(h))} = {fr(x2)}<br>x = √{fr(x2)} ≈ <strong>{fr(round_to(x, 2))} m</strong>", None)


# (minimum level, problem)
PROBLEMS = [
    (0, _kite), (0, _park), (0, _ladder_easy),
    (1, _ladder), (1, _football), (1, _skilift), (1, _square), (1, _tv),
    (2, _roof), (2, _equilateral), (2, _phone), (2, _ramp),
]


@register("pythagore.problem")
def problem(ctx: GenContext) -> Generated:
    fn = ctx.pick([f for lv, f in PROBLEMS if lv <= ctx.level])
    emoji, prompt, ans, dec, unit, explain, hint = fn(ctx)
    ans = round_to(ans, dec)
    return Generated(
        kind="number", category=ctx.title, answer=ans, tol=0.51 * 10 ** -dec, unit=unit,
        prompt=f'<span class="emo" aria-hidden="true">{emoji}</span>{prompt}',
        hint=hint or "Fais un croquis : repère l'angle droit, puis l'hypoténuse.",
        explain=explain, answer_display=f"{fr(ans)} {unit}",
    )
