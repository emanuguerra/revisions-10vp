"""Generators driven only by static items: reusable in any unit and any subject."""
from .base import GenContext, Generated, register

FIRST_NAMES = ["Léa", "Noah", "Lina", "Gabriel", "Emma", "Luca", "Zoé", "Nathan"]


@register("common.true_false")
def true_false(ctx: GenContext) -> Generated:
    """Items: {statement, true: bool, why}."""
    it = ctx.pick_item(ctx.params.get("kind", "vf"))
    t = bool(it["true"])
    return Generated(
        kind="choice", category=ctx.title, choices=["Vrai", "Faux"], answer=0 if t else 1,
        prompt=it["statement"],
        explain=f"<strong>{'Vrai' if t else 'Faux'}.</strong> {it['why']}",
        item_key=it["key"],
    )


@register("common.find_mistake")
def find_mistake(ctx: GenContext) -> Generated:
    """Items: {work (HTML), mistake, fix}. The other items' mistakes are the wrong choices."""
    kind = ctx.params.get("kind", "error")
    it = ctx.pick_item(kind)
    others = [o["mistake"] for o in ctx.items[kind] if o["key"] != it["key"]]
    choices = ctx.shuffle([it["mistake"], *ctx.shuffle(others)[:3]])
    who = ctx.pick(FIRST_NAMES)
    return Generated(
        kind="choice", category=ctx.title, choices=choices, answer=choices.index(it["mistake"]),
        prompt=f'Voici le calcul de {who}. Où est l\'erreur ?<span class="work">{it["work"]}</span>',
        explain=f"<strong>{it['mistake']}</strong><br>Correction : {it['fix']}",
        item_key=it["key"],
    )
