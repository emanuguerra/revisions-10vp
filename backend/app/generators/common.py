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


@register("common.mcq")
def mcq(ctx: GenContext) -> Generated:
    """Multiple-choice questions written in the content (params kind, default "qcm").

    Items: {question (HTML), answer, wrong: [...], why, doc?, category?}
    or, to sort statements into fixed groups: {question, choices: [...], answer, why}
    (the choices then stay in their order, e.g. ["Météo", "Climat"]).
    `doc` is a short document shown above the question (HTML).
    """
    it = ctx.pick_item(ctx.params.get("kind", "qcm"))
    choices = list(it["choices"]) if it.get("choices") else ctx.shuffle([it["answer"], *it["wrong"]])
    doc = f'<div class="doc">{it["doc"]}</div>' if it.get("doc") else ""
    return Generated(
        kind="choice", category=ctx.title, choices=choices, answer=choices.index(it["answer"]),
        prompt=doc + it["question"], max_tries=1 if len(choices) <= 3 else 2,
        retry_message="Pas tout à fait. Relis la question et essaie encore.",
        # The explanation is in the summary, so it is shown after a right answer too
        explain="", item_key=it["key"],
        summary=f"{it['question']} → <strong>{it['answer']}</strong><br>{it['why']}",
    )


@register("common.order")
def order(ctx: GenContext) -> Generated:
    """Chronology: which of four events comes first (or last)?

    Items (params kind, default "event"): {key, text, order (position in the story), part?}.
    """
    kind = ctx.params.get("kind", "event")
    events = ctx.items[kind]
    first = ctx.rng.random() < 0.6
    it = ctx.pick_item(kind)
    others = [e for e in events if e["order"] != it["order"]]
    # the asked event must be the first (or last) of the four shown
    pool = [e for e in others if (e["order"] > it["order"]) == first]
    if len(pool) < 3:
        first = not first
        pool = [e for e in others if (e["order"] > it["order"]) == first]
    shown = ctx.shuffle([it, *ctx.shuffle(pool)[:3]])
    ordered = sorted(shown, key=lambda e: e["order"])
    return Generated(
        kind="choice", category=ctx.title, choices=[e["text"] for e in shown], answer=shown.index(it),
        prompt=f"Parmi ces événements, lequel se passe <strong>{'en premier' if first else 'en dernier'}</strong> ?",
        explain="", item_key=it["key"],
        summary="Dans l'ordre :<br>" + "<br>".join(f"{i + 1}. {e['text']}" + (f" ({e['part']})" if e.get("part") else "")
                                         for i, e in enumerate(ordered)),
    )
