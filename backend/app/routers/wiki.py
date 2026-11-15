"""Knowledge base pages (content/knowledge): tree, one page, search."""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import knowledge

router = APIRouter(prefix="/api/wiki", tags=["wiki"])


class PageBrief(BaseModel):
    path: str
    subject: str
    theme: str
    title: str
    summary: str


class ThemeOut(BaseModel):
    subject: str
    slug: str
    title: str
    pages: list[PageBrief]


class PageOut(PageBrief):
    theme_title: str
    body: str
    keywords: list[str]
    objectives: list[str]
    units: list[str]
    lessons: list[str]
    sources: list[str]
    related: list[PageBrief]


class SearchHit(PageBrief):
    score: int


def brief(p: knowledge.Page) -> PageBrief:
    return PageBrief(path=p.path, subject=p.subject, theme=p.theme, title=p.title, summary=p.summary)


@router.get("", response_model=list[ThemeOut])
def tree(unit: Optional[str] = None):
    """All themes and their pages; with `unit`, only the pages linked to that unit of the app."""
    out = []
    for t in knowledge.themes():
        pages = [p for p in t.pages if unit is None or unit in p.get("units")]
        if pages:
            out.append(ThemeOut(subject=t.subject, slug=t.slug, title=t.title, pages=[brief(p) for p in pages]))
    return out


@router.get("/search", response_model=list[SearchHit])
def search(q: str, subject: Optional[str] = None, limit: int = 10):
    return [SearchHit(**brief(p).model_dump(), score=s)
            for p, s in knowledge.search(q, limit=min(max(limit, 1), 30), subject=subject)]


@router.get("/page/{path:path}", response_model=PageOut)
def page(path: str):
    all_pages = knowledge.pages()
    p = all_pages.get(path)
    if p is None:
        raise HTTPException(404, f"Fiche « {path} » introuvable.")
    theme = next(t for t in knowledge.themes() if t.subject == p.subject and t.slug == p.theme)
    return PageOut(**brief(p).model_dump(), theme_title=theme.title, body=p.body,
                   keywords=[str(k) for k in p.get("keywords")], objectives=[str(o) for o in p.get("objectives")],
                   units=p.get("units"), lessons=p.get("lessons"), sources=[str(s) for s in p.get("sources")],
                   related=[brief(all_pages[r]) for r in p.get("related") if r in all_pages])
