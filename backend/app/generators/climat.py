"""Climate generators (géographie 10VP): reading climate diagrams and the albedo.

Stations are items of kind "station" in the unit:
    {key, name, country, lat, alt, climate (key of CLIMATES), temp: [12 °C], prec: [12 mm]}
The diagram is drawn by the front end (figure type "climograph", widgets/Climograph.tsx).
"""
from ..formatting import fr, round_to
from .base import GenContext, Generated, esc, register

MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
          "septembre", "octobre", "novembre", "décembre"]

CLIMATES = {
    "oceanique": ("Tempéré océanique", "hivers doux, étés frais, pluies toute l'année : faible amplitude thermique."),
    "continental": ("Tempéré continental", "hivers froids sous 0 °C, étés chauds, pluies surtout en été : forte amplitude."),
    "mediterraneen": ("Méditerranéen", "étés chauds et secs, hivers doux, pluies en automne et en hiver."),
    "equatorial": ("Équatorial (tropical humide)", "chaud toute l'année (environ 26 °C), très pluvieux chaque mois, amplitude très faible."),
    "tropical-sec": ("Tropical à saison sèche", "chaud toute l'année, une longue saison sèche et une saison des pluies (mousson)."),
    "desertique": ("Désertique (aride)", "presque pas de pluie de toute l'année, chaud."),
    "polaire": ("Polaire", "très froid, températures au-dessus de 0 °C seulement 2 ou 3 mois, peu de précipitations."),
    "montagnard": ("Montagnard", "froid à cause de l'altitude, beaucoup de précipitations (souvent sous forme de neige)."),
    # Shown in the summaries, never asked in "Quel climat ?"
    "transition": ("Tempéré de transition", "entre océanique et continental, comme sur le Plateau suisse."),
    "subtropical": ("Subtropical humide", "étés chauds et humides, hivers doux."),
}
STUDIED = ["oceanique", "continental", "mediterraneen", "equatorial", "tropical-sec", "desertique", "polaire", "montagnard"]

SURFACES = [  # (name, albedo)
    ("de la neige fraîche", 0.85), ("de la glace de mer (banquise)", 0.6), ("un océan", 0.06),
    ("une forêt", 0.15), ("un désert de sable", 0.35), ("une prairie", 0.25), ("une route goudronnée", 0.05),
    ("un glacier", 0.5),
]


def figure(st, **kw) -> dict:
    return {"type": "climograph", "name": f"{st['name']} ({st['country']})", "lat": st["lat"], "alt": st["alt"],
            "temp": st["temp"], "prec": st["prec"], **kw}


def amplitude(st) -> float:
    return round_to(max(st["temp"]) - min(st["temp"]), 1)


def _station(ctx: GenContext, ok=lambda s: True):
    items = [s for s in ctx.items["station"] if ok(s)]
    for s in items:
        if s["key"] == ctx.forced_item:
            return s
    return ctx.pick([s for s in items if s["key"] not in ctx.exclude] or items)


def _summary(st) -> str:
    t, p = st["temp"], st["prec"]
    return (f"📊 {esc(st['name'])} : {CLIMATES[st['climate']][0].lower()}, amplitude {fr(amplitude(st))} °C, "
            f"{sum(p)} mm par an, de {fr(min(t))} à {fr(max(t))} °C")


def _months(ctx: GenContext, right: int) -> tuple[list[str], int]:
    others = ctx.shuffle([m for m in range(12) if abs(m - right) not in (0, 1, 11)])[:3]
    opts = sorted([right, *others])
    return [MONTHS[m] for m in opts], opts.index(right)


@register("climat.read_diagram")
def read_diagram(ctx: GenContext) -> Generated:
    """One question about the diagram of a station: warmest / driest month, amplitude, hemisphere, rainfall."""
    st = _station(ctx)
    t, p = st["temp"], st["prec"]
    kinds = ["hot", "amp", "hemi", "wet", "dry", "cold"]
    if sum(p) < 60:
        kinds.remove("dry")                      # desert: every month is dry
    kind = ctx.pick(kinds)
    fig = figure(st)
    base = dict(category=ctx.title, figure=fig, item_key=st["key"], summary=_summary(st))
    if kind == "amp":
        a = amplitude(st)
        return Generated(
            kind="number", prompt=f"Lis le diagramme de <strong>{esc(st['name'])}</strong>. "
                                  "Quelle est l'<strong>amplitude thermique annuelle</strong> ?",
            answer=a, tol=1.51, unit="°C",
            hint="Amplitude = température du mois le plus chaud − température du mois le plus froid.",
            explain=f"Mois le plus chaud : {fr(max(t))} °C, mois le plus froid : {fr(min(t))} °C. "
                    f"Amplitude = {fr(max(t))} − ({fr(min(t))}) = <strong>{fr(a)} °C</strong>. "
                    "Une lecture à 1 ou 1,5 °C près est acceptée.", **base)
    if kind == "hemi":
        north = st["lat"] > 0
        hot = MONTHS[t.index(max(t))]
        return Generated(
            kind="choice", prompt=f"D'après le diagramme, <strong>{esc(st['name'])}</strong> est-elle dans l'hémisphère nord ou sud ?",
            choices=["Hémisphère nord", "Hémisphère sud"], answer=0 if north else 1, max_tries=1,
            explain=f"Le mois le plus chaud est {hot}. "
                    + ("L'été est en juin–août : c'est l'hémisphère <strong>nord</strong>." if north else
                       "L'été est en décembre–février : c'est l'hémisphère <strong>sud</strong>.")
                    + (" Près de l'équateur, il faut regarder aussi la saison des pluies." if abs(st["lat"]) < 10 else ""),
            **base)
    if kind in ("hot", "cold", "wet", "dry"):
        vals, label = (t, "la température") if kind in ("hot", "cold") else (p, "les précipitations")
        right = vals.index(max(vals) if kind in ("hot", "wet") else min(vals))
        words = {"hot": "le plus chaud", "cold": "le plus froid", "wet": "le plus pluvieux", "dry": "le plus sec"}[kind]
        choices, ans = _months(ctx, right)
        unit = "°C" if kind in ("hot", "cold") else "mm"
        return Generated(
            kind="choice", prompt=f"Sur le diagramme de <strong>{esc(st['name'])}</strong>, quel est le mois <strong>{words}</strong> ?",
            choices=choices, answer=ans,
            hint=f"Regarde {'la courbe rouge' if unit == '°C' else 'les barres bleues'}.",
            explain=f"<strong>{MONTHS[right].capitalize()}</strong> : {fr(vals[right])} {unit}. "
                    f"Pour {label}, on lit {'la courbe' if unit == '°C' else 'les barres'}.", **base)
    raise AssertionError(kind)


@register("climat.classify")
def classify(ctx: GenContext) -> Generated:
    """Which type of climate does this diagram show?"""
    st = _station(ctx, lambda s: s["climate"] in STUDIED)
    right = st["climate"]
    others = ctx.shuffle([k for k in STUDIED if k != right])[:3]
    keys = ctx.shuffle([right, *others])
    name, why = CLIMATES[right]
    alt = f", altitude {st['alt']} m" if st["alt"] >= 1000 else ""
    return Generated(
        kind="choice", category=ctx.title, figure=figure(st, hide_name=True),
        prompt=f"Quel type de climat montre ce diagramme ? <small class=\"muted\">(latitude {fr(abs(st['lat']))}° "
               f"{'N' if st['lat'] > 0 else 'S'}{alt})</small>",
        choices=[CLIMATES[k][0] for k in keys], answer=keys.index(right),
        hint="Regarde la température toute l'année, l'amplitude et la répartition des pluies.",
        explain=f"C'est <strong>{esc(st['name'])}</strong> ({esc(st['country'])}) : climat <strong>{name.lower()}</strong>, {why}",
        item_key=st["key"], summary=_summary(st),
    )


@register("climat.albedo")
def albedo(ctx: GenContext) -> Generated:
    """Energy reflected or absorbed by a surface, from its albedo."""
    name, a = ctx.pick(SURFACES)
    energy = ctx.pick([100, 200, 340, 400, 500, 1000])
    absorbed = ctx.rng.random() < 0.5
    ans = round_to(energy * ((1 - a) if absorbed else a), 1)
    what = "absorbe" if absorbed else "réfléchit"
    return Generated(
        kind="number", category=ctx.title, unit="W/m²", answer=ans, tol=0.051,
        prompt=f"Le Soleil envoie <strong>{energy} W/m²</strong> sur {name}, dont l'albédo est <strong>{fr(a)}</strong>. "
               f"Combien d'énergie cette surface <strong>{what}</strong>-t-elle ?",
        hint="L'albédo est la part de l'énergie réfléchie (de 0 à 1). Le reste est absorbé.",
        explain=f"Réfléchie = {energy} × {fr(a)} = {fr(round_to(energy * a, 1))} W/m². "
                f"Absorbée = {energy} − {fr(round_to(energy * a, 1))} = {fr(round_to(energy * (1 - a), 1))} W/m². "
                f"La réponse est <strong>{fr(ans)} W/m²</strong>."
                + (" Une surface claire réfléchit beaucoup ; une surface sombre absorbe et se réchauffe." if a in (0.85, 0.06) else ""),
    )
