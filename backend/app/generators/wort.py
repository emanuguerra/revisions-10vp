"""German vocabulary generators for French-speaking students.

Items, kind "wort": {key, category, de, art?, pl?, forms?, opposite?, alt?, fr, pic, group?,
                     known?, plus?, example, example_fr}.
    art     "der" | "die" | "das" for nouns ("die" + plural_only for words like die Eltern,
            singular_only for der Ärger); a word with an article is a noun
    forms   a verb's forms as in the book: "er freut sich, hat sich gefreut"; marks a verb
    opposite key of the word of opposite meaning (laut ≠ leise), one side is enough
    known   "Das kennst du schon" (grey box in the book); plus: extra vocabulary (blue box)
    alt     other accepted spellings for the written answer
    group   words with almost the same meaning share a group: never offered as wrong choices
            for each other (froh / glücklich)
    example German sentence; the gap question uses the items whose `de` appears in it
Items, kind "situation": {key, de, fr, answer, wrong: [3 words]}: "Er ist ___." in context.
Items, kind "dialog": {key, says, fr, answer, wrong: [3 replies], why}: what do you answer?
Keys are unique across the three kinds, so "Revoir mes erreurs" can find the right question.

A `de` with "?", "!", "." or "…" is a phrase: no fill-in-the-blank, no spelling question, no
picture. Wrong choices are words of the same kind (noun, verb, phrase, other) when possible.

Exercise params (unit.yaml); without them every topic is used:
    wort.picture    categories: topics whose emoji are clear; prompt: the question (HTML)
    wort.situation  categories: topics the situations are about (others ask a translation)
    wort.dialog     categories: same, for the dialogs
Items with `nopic: true` never appear in the picture question.
"""
from collections.abc import Callable

from .base import GenContext, Generated, esc, register

RETRY = "Pas tout à fait. Essaie encore !"
PICTURE_PROMPT = 'Welches Wort passt? <small class="muted">(Quel mot correspond à l\'émoji ?)</small>'
UMLAUTS = {"ä": "ae", "ö": "oe", "ü": "ue"}


def full(it) -> str:
    """The word as it is learnt: with its article for a noun."""
    return f"{it['art']} {it['de']}" if it.get("art") else it["de"]


def pos(it) -> str:
    """Kind of word: noun, verb, phrase or other (adjectives, adverbs...)."""
    if it.get("art"):
        return "noun"
    if it.get("forms"):
        return "verb"
    if any(c in it["de"] for c in "?!.…"):
        return "phrase"
    return "other"


def _opposite(ctx: GenContext, it) -> dict | None:
    words = ctx.items.get("wort", [])
    if it.get("opposite"):
        return next((x for x in words if x["key"] == it["opposite"]), None)
    return next((x for x in words if x.get("opposite") == it["key"]), None)


def _stop(text: str) -> str:
    """Full stop after a quoted answer, unless it already ends a sentence."""
    return "" if text.endswith((".", "!", "?")) else "."


def _summary(it) -> str:
    extra = f"pluriel : die {it['pl']}" if it.get("pl") else it.get("forms", "")
    extra = f" <small>({esc(extra)})</small>" if extra else ""
    return f"{it['pic']} <strong>{esc(full(it))}</strong>{extra} = {esc(it['fr'])}"


def _spellings(it) -> list[str]:
    """Accepted written answers: with or without article / "sich", and ae, oe, ue for ä, ö, ü."""
    base = [it["de"], full(it), *it.get("alt", [])]
    if it["de"].startswith("sich "):
        base.append(it["de"][5:])
    out = []
    for w in base:
        out.append(w)
        alt = w
        for u, rep in UMLAUTS.items():
            alt = alt.replace(u, rep).replace(u.upper(), rep.capitalize())
        out.append(alt)
    return list(dict.fromkeys(out))


def _forced_kind(ctx: GenContext) -> str | None:
    for kind in ("situation", "dialog"):
        if ctx.forced_item and any(it["key"] == ctx.forced_item for it in ctx.items.get(kind, [])):
            return kind
    return None


def _pick(ctx: GenContext, ok: Callable[[dict], bool]) -> dict | None:
    """Like ctx.pick_item("wort") but only among the items `ok` accepts; None if there is none."""
    items = [it for it in ctx.items.get("wort", []) if ok(it)]
    if ctx.forced_item:
        for it in items:
            if it["key"] == ctx.forced_item:
                return it
        if any(it["key"] == ctx.forced_item for it in ctx.items.get("wort", [])):
            return None                      # the forced word does not fit this exercise
    pool = [it for it in items if not ctx.category or it.get("category") == ctx.category]
    if not pool:
        return None
    fresh = [it for it in pool if it["key"] not in ctx.exclude]
    return ctx.pick(fresh or pool)


def _routed(fn):
    """A mistake to practise is a situation or a dialog: ask that one, whatever the exercise."""
    def wrapper(ctx: GenContext) -> Generated:
        kind = _forced_kind(ctx)
        if kind and kind != fn.__name__:
            return {"situation": situation, "dialog": dialog}[kind](ctx)
        return fn(ctx)
    wrapper.__name__ = fn.__name__
    return wrapper


def _distractors(ctx: GenContext, it, ok: Callable[[dict], bool] = lambda x: True, n: int = 3) -> list[dict]:
    """Wrong options: same kind of word and topic first, never a near-synonym, never the same text."""
    items = ctx.shuffle([x for x in ctx.items["wort"] if x["key"] != it["key"] and ok(x)
                         and not (it.get("group") and x.get("group") == it["group"])])
    rank = lambda x: (pos(x) != pos(it), x["category"] != it["category"])
    out, seen = [], {it["de"].lower(), it["fr"].lower()}
    for x in sorted(items, key=rank):
        if x["de"].lower() in seen or x["fr"].lower() in seen:
            continue
        seen |= {x["de"].lower(), x["fr"].lower()}
        out.append(x)
        if len(out) == n:
            break
    return out


def _choice(ctx: GenContext, it, prompt: str, label: Callable[[dict], str], ok=lambda x: True) -> Generated:
    opts = ctx.shuffle([it, *_distractors(ctx, it, ok)])
    return Generated(
        kind="choice", category=ctx.title, prompt=prompt,
        choices=[label(o) for o in opts], answer=opts.index(it),
        max_tries=2, retry_message=RETRY,
        explain=f"La réponse est <u>{esc(label(it))}</u>{_stop(label(it))}<br><em lang=\"de\">{esc(it['example'])}</em>"
                f"<br><small class=\"muted\">{esc(it['example_fr'])}</small>",
        item_key=it["key"], summary=_summary(it), speak=full(it), answer_display=full(it),
    )


def _any(it) -> bool:
    return True


@register("wort.fr_de")
@_routed
def fr_de(ctx: GenContext) -> Generated:
    it = _pick(ctx, _any) or ctx.pick_item("wort")
    return _choice(ctx, it, f'<span class="big" aria-hidden="true">{it["pic"]}</span>'
                            f'Comment dit-on <strong>{esc(it["fr"])}</strong> en allemand ?', full)


@register("wort.de_fr")
@_routed
def de_fr(ctx: GenContext) -> Generated:
    it = _pick(ctx, _any) or ctx.pick_item("wort")
    return _choice(ctx, it, f'Que veut dire <strong lang="de">{esc(full(it))}</strong> ?', lambda o: o["fr"])


@register("wort.picture")
@_routed
def picture(ctx: GenContext) -> Generated:
    """An emoji: which word? Only the topics whose emoji are clear."""
    cats = ctx.params.get("categories")
    feeling = lambda x: (not cats or x["category"] in cats) and not x.get("nopic") and pos(x) != "phrase"
    it = _pick(ctx, feeling)
    if it is None:
        return fr_de(ctx)
    return _choice(ctx, it, f'<span class="big" aria-hidden="true">{it["pic"]}</span>'
                            + ctx.params.get("prompt", PICTURE_PROMPT), full, feeling)


def _article_tip(it) -> str:
    if it.get("singular_only"):
        return " Ce mot s'emploie seulement au singulier."
    if it.get("plural_only"):
        return " Ce mot n'existe qu'au pluriel : au pluriel, l'article est toujours <strong>die</strong>."
    for end in ("ung", "schaft", "heit", "keit", "e"):
        if it["de"].endswith(end) and it["art"] == "die":
            return f" Astuce : les noms en <strong>-{end}</strong> sont souvent féminins (die)."
    if it["de"].endswith(("chen", "lein")):
        return " Astuce : les noms en -chen et -lein sont toujours neutres (das)."
    return ""


@register("wort.artikel")
@_routed
def artikel(ctx: GenContext) -> Generated:
    it = _pick(ctx, lambda x: bool(x.get("art")))
    if it is None:
        return fr_de(ctx)
    pl = f" Pluriel : <strong>die {esc(it['pl'])}</strong>." if it.get("pl") else ""
    return Generated(
        kind="choice", category=ctx.title,
        prompt=f'<span class="big" aria-hidden="true">{it["pic"]}</span>'
               f'<strong lang="de">___ {esc(it["de"])}</strong> <small class="muted">({esc(it["fr"])})</small>'
               f'<br>der, die ou das ?',
        choices=["der", "die", "das"], answer=["der", "die", "das"].index(it["art"]),
        max_tries=1, explain=f"<strong>{esc(full(it))}</strong>.{pl}{_article_tip(it)}",
        item_key=it["key"], summary=_summary(it), speak=full(it), answer_display=full(it),
    )


def _has_gap(it) -> bool:
    return pos(it) != "phrase" and it["de"].lower() in it["example"].lower()


@register("wort.gap")
@_routed
def gap(ctx: GenContext) -> Generated:
    it = _pick(ctx, _has_gap)
    if it is None:
        return de_fr(ctx)
    i = it["example"].lower().index(it["de"].lower())
    blank = esc(it["example"][:i]) + "_____" + esc(it["example"][i + len(it["de"]):])
    same_cat = lambda x: _has_gap(x) and pos(x) == pos(it)
    return _choice(ctx, it, f'<span lang="de">{blank}</span><br><small class="muted">({esc(it["example_fr"])})</small>',
                   lambda o: o["de"], same_cat)


@register("wort.spell")
@_routed
def spell(ctx: GenContext) -> Generated:
    it = _pick(ctx, lambda x: pos(x) != "phrase")
    if it is None:
        return fr_de(ctx)
    noun = " <small class=\"muted\">(avec ou sans article)</small>" if it.get("art") else ""
    return Generated(
        kind="text", category=ctx.title,
        prompt=f'<span class="big" aria-hidden="true">{it["pic"]}</span>'
               f'Écris en allemand : <strong>{esc(it["fr"])}</strong>{noun}',
        answer=_spellings(it), max_tries=3, retry_message=RETRY + " Attention à l'orthographe (ä, ö, ü).",
        explain=f"La réponse est <u>{esc(full(it))}</u>{_stop(full(it))}"
                + (" En allemand, les noms prennent toujours une majuscule." if it.get("art") else ""),
        item_key=it["key"], summary=_summary(it), speak=full(it), answer_display=full(it),
    )


@register("wort.opposite")
@_routed
def opposite(ctx: GenContext) -> Generated:
    """laut ≠ ? : the word of opposite meaning, among other words of the same kind."""
    it = _pick(ctx, lambda x: _opposite(ctx, x) is not None)
    if it is None:
        return de_fr(ctx)
    opp = _opposite(ctx, it)
    others = [x for x in _distractors(ctx, opp, lambda x: x["key"] != it["key"] and pos(x) == pos(it), 3)]
    opts = ctx.shuffle([opp, *others])
    return Generated(
        kind="choice", category=ctx.title,
        prompt=f'<span class="big" aria-hidden="true">{it["pic"]} ≠ ?</span>'
               f'Quel est le contraire de <strong lang="de">{esc(full(it))}</strong> '
               f'<small class="muted">({esc(it["fr"])})</small> ?',
        choices=[full(o) for o in opts], answer=opts.index(opp), max_tries=2, retry_message=RETRY,
        explain=f"<strong lang=\"de\">{esc(full(it))} ≠ {esc(full(opp))}</strong>"
                f"<br><small class=\"muted\">{esc(it['fr'])} ≠ {esc(opp['fr'])}</small>",
        item_key=it["key"], summary=f"{_summary(it)} ≠ <strong>{esc(full(opp))}</strong>",
        speak=f"{full(it)}, {full(opp)}", answer_display=full(opp),
    )


def _pick_kind(ctx: GenContext, kind: str) -> dict:
    items = ctx.items[kind]
    for it in items:
        if it["key"] == ctx.forced_item:
            return it
    return ctx.pick([it for it in items if it["key"] not in ctx.exclude] or items)


@register("wort.situation")
@_routed
def situation(ctx: GenContext) -> Generated:
    cats = ctx.params.get("categories")
    if ctx.category and cats and ctx.category not in cats and _forced_kind(ctx) != "situation":
        return fr_de(ctx)
    it = _pick_kind(ctx, "situation")
    choices = ctx.shuffle([it["answer"], *it["wrong"]])
    return Generated(
        kind="choice", category=ctx.title,
        prompt=f'<span lang="de">{esc(it["de"]).replace("___", "_____")}</span>',
        choices=choices, answer=choices.index(it["answer"]), max_tries=2, retry_message=RETRY,
        explain=f"<strong lang=\"de\">{esc(it['de'].replace('___', it['answer']))}</strong>"
                f"<br><small class=\"muted\">{esc(it['fr'])}</small>",
        item_key=it["key"], speak=it["de"].replace("___", it["answer"]), answer_display=it["answer"],
        summary=f"<span lang=\"de\">{esc(it['de']).replace('___', '<strong>' + esc(it['answer']) + '</strong>')}</span>"
                f" <small>({esc(it['fr'])})</small>",
    )


@register("wort.dialog")
@_routed
def dialog(ctx: GenContext) -> Generated:
    cats = ctx.params.get("categories")
    if ctx.category and cats and ctx.category not in cats and _forced_kind(ctx) != "dialog":
        return de_fr(ctx)
    it = _pick_kind(ctx, "dialog")
    choices = ctx.shuffle([it["answer"], *it["wrong"]])
    return Generated(
        kind="choice", category=ctx.title,
        prompt=f'💬 <strong lang="de">„{esc(it["says"])}“</strong><br>'
               f'<small class="muted">({esc(it["fr"])})</small><br>Que réponds-tu ?',
        choices=choices, answer=choices.index(it["answer"]), max_tries=2, retry_message=RETRY,
        explain=f"<strong lang=\"de\">{esc(it['answer'])}</strong><br>{esc(it['why'])}",
        item_key=it["key"], speak=it["answer"], answer_display=it["answer"],
        summary=f"💬 <span lang=\"de\">„{esc(it['says'])}“ → <strong>{esc(it['answer'])}</strong></span>",
    )
