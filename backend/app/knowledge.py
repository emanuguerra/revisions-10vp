"""Knowledge base: one Markdown file per notion, in content/knowledge/<subject>/<theme>/<slug>.md.

Each file starts with a YAML header (between two `---` lines):

    title: L'effet de serre                 (required)
    summary: one sentence                   (required, shown in lists and search results)
    keywords: [effet de serre, infrarouge]  (help the search)
    objectives: ["Géo TS obj. 5"]           (objectives of the school programme)
    units: [geo-climat]                     (units of the app that train this notion)
    lessons: [geo-climat/effet-de-serre]    (lessons of the app on this notion)
    sources: ["…"]                          (where the content comes from)
    related: [geographie/climat/albedo]     (other pages)

A theme folder may hold `_theme.yaml` ({title, order}). The pages are written in our own words:
they are the reference used to write lessons and exercises, and later to answer questions in a chat.
The files are read once and kept in memory (a few hundred pages at most); search is a simple
word count, accents and case ignored, a search word can be the start of a word.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

from .config import CONTENT_DIR
from .rubric import norm

KNOWLEDGE_DIR = CONTENT_DIR / "knowledge"
REQUIRED = ("title", "summary")
LIST_FIELDS = ("keywords", "objectives", "units", "lessons", "sources", "related")


@dataclass
class Page:
    path: str            # "geographie/climat/effet-de-serre"
    subject: str
    theme: str
    slug: str
    title: str
    summary: str
    body: str
    order: int = 100
    meta: dict = field(default_factory=dict)

    def get(self, key: str) -> list:
        return list(self.meta.get(key) or [])


@dataclass
class Theme:
    subject: str
    slug: str
    title: str
    order: int
    pages: list[Page]


class KnowledgeError(ValueError):
    pass


def parse(text: str, where: str) -> tuple[dict, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        raise KnowledgeError(f"{where}: missing YAML header between two '---' lines")
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        raise KnowledgeError(f"{where}: bad YAML header: {e}") from e
    if not isinstance(meta, dict):
        raise KnowledgeError(f"{where}: the header must be a mapping")
    return meta, m.group(2).strip()


def load(root: Path = KNOWLEDGE_DIR) -> tuple[list[Theme], list[str]]:
    """All themes with their pages, and the list of problems found (empty when all is fine)."""
    errors: list[str] = []
    themes: list[Theme] = []
    if not root.is_dir():
        return themes, errors
    for theme_dir in sorted(p for p in root.glob("*/*") if p.is_dir()):
        subject, theme = theme_dir.parent.name, theme_dir.name
        info = {}
        if (theme_dir / "_theme.yaml").exists():
            info = yaml.safe_load((theme_dir / "_theme.yaml").read_text(encoding="utf-8")) or {}
        pages = []
        for f in sorted(theme_dir.glob("*.md")):
            where = f"knowledge/{subject}/{theme}/{f.name}"
            try:
                meta, body = parse(f.read_text(encoding="utf-8"), where)
            except KnowledgeError as e:
                errors.append(str(e))
                continue
            missing = [k for k in REQUIRED if not meta.get(k)]
            if missing:
                errors.append(f"{where}: missing {', '.join(missing)}")
                continue
            for k in LIST_FIELDS:
                if meta.get(k) is not None and not isinstance(meta[k], list):
                    errors.append(f"{where}: '{k}' must be a list")
                    meta[k] = []
            pages.append(Page(path=f"{subject}/{theme}/{f.stem}", subject=subject, theme=theme, slug=f.stem,
                              title=str(meta["title"]), summary=str(meta["summary"]), body=body,
                              order=int(meta.get("order", 100)), meta=meta))
        pages.sort(key=lambda p: (p.order, p.title))
        themes.append(Theme(subject, theme, str(info.get("title", theme.replace("-", " ").capitalize())),
                            int(info.get("order", 100)), pages))
    themes.sort(key=lambda t: (t.subject, t.order, t.title))
    known = {p.path for t in themes for p in t.pages}
    for t in themes:
        for p in t.pages:
            for r in p.get("related"):
                if r not in known:
                    errors.append(f"knowledge/{p.path}.md: related page '{r}' does not exist")
            for link in re.findall(r"\]\(wiki:([^)#\s]+)", p.body):
                if link not in known:
                    errors.append(f"knowledge/{p.path}.md: link to unknown page 'wiki:{link}'")
    return themes, errors


@lru_cache(maxsize=1)
def themes() -> list[Theme]:
    return load()[0]


def pages() -> dict[str, Page]:
    return {p.path: p for t in themes() for p in t.pages}


def _plain(md: str) -> str:
    md = re.sub(r"<[^>]+>", " ", md)                  # html tags (widgets, tables)
    return re.sub(r"[#*_`>|\[\]()-]", " ", md)


def search(query: str, limit: int = 10, subject: str | None = None) -> list[tuple[Page, int]]:
    """Pages ranked by how well they match the query (title > keywords > summary > text)."""
    words = [w for w in norm(query).split() if len(w) > 1]
    if not words:
        return []
    results = []
    for p in pages().values():
        if subject and p.subject != subject:
            continue
        title, keys = norm(p.title), norm(" ".join(map(str, p.get("keywords"))))
        summary, body = norm(p.summary), norm(_plain(p.body))
        score = 0
        for w in words:
            needle = " " + w
            score += 6 * (needle in title) + 4 * (needle in keys) + 2 * (needle in summary) + min(body.count(needle), 5)
        if score:
            results.append((p, score))
    results.sort(key=lambda r: (-r[1], r[0].title))
    return results[:limit]
