"""Vocabulary quiz generators.

Items (kind "vocab"): {key, category, en, alt?, fr, pic, definition, example}.
The example sentence must contain the word `en` (used by the gap-fill question).
"""
import re

from .base import GenContext, Generated, esc, register

RETRY = "Not quite. Try again! · Essaie encore."


def _summary(it) -> str:
    alt = f" · also: {', '.join(esc(a) for a in it['alt'])}" if it.get("alt") else ""
    return f"{it['pic']} <strong>{esc(it['en'])}</strong> = {esc(it['fr'])}{alt}"


def _choice(ctx: GenContext, it, prompt: str) -> Generated:
    """4 options; distractors from the same topic first, so the choice is harder."""
    items = ctx.items["vocab"]
    same = ctx.shuffle([x for x in items if x["key"] != it["key"] and x["category"] == it["category"]])
    other = ctx.shuffle([x for x in items if x["category"] != it["category"]])
    opts = ctx.shuffle([it, *(same + other)[:3]])
    return Generated(
        kind="choice", category=ctx.title, prompt=prompt,
        choices=[o["en"] for o in opts], answer=opts.index(it),
        max_tries=2, retry_message=RETRY,
        explain=f"The answer is <u>{esc(it['en'])}</u>.",
        item_key=it["key"], summary=_summary(it), speak=it["en"], answer_display=it["en"],
    )


@register("vocab.definition")
def definition(ctx: GenContext) -> Generated:
    it = ctx.pick_item("vocab")
    first = it["definition"].split(". ")[0].rstrip(".")
    return _choice(ctx, it, esc(first) + ".")


@register("vocab.translate")
def translate(ctx: GenContext) -> Generated:
    it = ctx.pick_item("vocab")
    return _choice(ctx, it, f"How do you say <strong>{esc(it['fr'])}</strong> in English?")


@register("vocab.picture")
def picture(ctx: GenContext) -> Generated:
    it = ctx.pick_item("vocab")
    cat = ctx.categories.get(it["category"], "")
    return _choice(ctx, it, f'<span class="big" aria-hidden="true">{it["pic"]}</span>Which job is this? '
                            f'<small class="muted">({esc(cat)})</small>')


@register("vocab.gap")
def gap(ctx: GenContext) -> Generated:
    it = ctx.pick_item("vocab")
    blank = re.sub(re.escape(it["en"]), "_____", it["example"], count=1, flags=re.I)
    return _choice(ctx, it, esc(blank))


@register("vocab.spell")
def spell(ctx: GenContext) -> Generated:
    it = ctx.pick_item("vocab")
    return Generated(
        kind="text", category=ctx.title,
        prompt=f'<span class="big" aria-hidden="true">{it["pic"]}</span>Write the English word for <strong>{esc(it["fr"])}</strong>.',
        answer=[it["en"], *it.get("alt", [])], max_tries=3, retry_message=RETRY,
        explain=f"The answer is <u>{esc(it['en'])}</u>.",
        item_key=it["key"], summary=_summary(it), speak=it["en"], answer_display=it["en"],
    )
