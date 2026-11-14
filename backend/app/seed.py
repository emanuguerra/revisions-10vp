"""Load content/ into the database. Safe to run again after every content change.

    uv run python -m app.seed            # load / update
    uv run python -m app.seed --check    # validate content only, no database write

Layout:
    content/subjects.yaml
    content/units/<slug>/unit.yaml       unit metadata, lessons, exercises, mission, scoring
    content/units/<slug>/*.yaml          item files: {kind: <kind>, items: [{key: ..., ...}]}
    content/units/<slug>/*.html|*.md     lesson blocks referenced with `file:`

Rows are matched by slug/key, so student history (missions, questions) is kept.
Exercise types or items removed from the content are disabled or deleted.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import CONTENT_DIR
from .generators import GENERATORS
from .models import ExerciseType, Item, Lesson, Subject, Unit

UNIT_CONFIG_KEYS = ("speech_lang", "break_videos", "levels", "categories", "mission", "scoring", "training", "exercises_title", "subtitle_fr")


class ContentError(Exception):
    pass


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def read_unit(folder: Path) -> dict[str, Any]:
    """Read unit.yaml, inline block files and collect item files."""
    unit = load_yaml(folder / "unit.yaml")
    for lesson in unit.get("lessons", []):
        for block in lesson.get("blocks", []):
            if "file" in block:
                block["content"] = (folder / block.pop("file")).read_text(encoding="utf-8")
    unit["items"] = {}
    for path in sorted(folder.glob("*.yaml")):
        if path.name == "unit.yaml":
            continue
        data = load_yaml(path)
        unit["items"].setdefault(data["kind"], []).extend(data["items"])
    return unit


def validate(subjects: list[dict], units: list[dict]) -> list[str]:
    errors = []
    subject_slugs = {s["slug"] for s in subjects}
    for u in units:
        where = f"unit '{u.get('slug')}'"
        if u.get("subject") not in subject_slugs:
            errors.append(f"{where}: unknown subject '{u.get('subject')}'")
        keys = [e["key"] for e in u.get("exercises", [])]
        for e in u.get("exercises", []):
            if e["generator"] not in GENERATORS:
                errors.append(f"{where}: exercise '{e['key']}' uses unknown generator '{e['generator']}'")
        mission = u.get("mission", {})
        for k in mission.get("sequence", []) + mission.get("types", []):
            if k not in keys:
                errors.append(f"{where}: mission refers to unknown exercise '{k}'")
        all_keys: set = set()
        for kind, items in u["items"].items():
            seen = set()
            for it in items:
                if it.get("key") in all_keys and kind in ("wort", "situation", "dialog"):
                    errors.append(f"{where}: key '{it['key']}' is used by two kinds of items")
                all_keys.add(it.get("key"))
                if "key" not in it:
                    errors.append(f"{where}: an item of kind '{kind}' has no key")
                elif it["key"] in seen:
                    errors.append(f"{where}: duplicate {kind} key '{it['key']}'")
                seen.add(it.get("key"))
                if kind == "vocab" and it["en"].lower() not in it["example"].lower():
                    errors.append(f"{where}: example sentence of '{it['en']}' must contain the word")
                if kind == "vocab" and it.get("category") not in u.get("categories", {}):
                    errors.append(f"{where}: '{it['en']}' has unknown category '{it.get('category')}'")
                if kind == "wort" and it.get("category") not in u.get("categories", {}):
                    errors.append(f"{where}: '{it.get('de')}' has unknown category '{it.get('category')}'")
                if kind == "wort" and it.get("art") not in (None, "der", "die", "das"):
                    errors.append(f"{where}: '{it.get('de')}' has a wrong article '{it['art']}'")
                if kind == "wort" and it.get("opposite") and it["opposite"] not in {x["key"] for x in items}:
                    errors.append(f"{where}: '{it.get('de')}' has an unknown opposite '{it['opposite']}'")
                if kind == "station" and (len(it.get("temp", [])) != 12 or len(it.get("prec", [])) != 12):
                    errors.append(f"{where}: station '{it.get('key')}' needs 12 temperatures and 12 precipitations")
                if kind in ("qcm", "doc", "tri") and it.get("answer") not in (it.get("choices") or [it.get("answer")]):
                    errors.append(f"{where}: {kind} '{it.get('key')}': the answer is not one of the choices")
                if kind in ("situation", "dialog") and it.get("answer") in it.get("wrong", []):
                    errors.append(f"{where}: {kind} '{it.get('key')}' lists its answer as wrong")
    return errors


def read_content(content_dir: Path = CONTENT_DIR) -> tuple[list[dict], list[dict]]:
    subjects = load_yaml(content_dir / "subjects.yaml")["subjects"]
    units = [read_unit(f) for f in sorted((content_dir / "units").iterdir()) if (f / "unit.yaml").exists()]
    errors = validate(subjects, units)
    if errors:
        raise ContentError("\n".join(errors))
    return subjects, units


def upsert(db: Session, model, where: dict, values: dict):
    row = db.scalar(select(model).filter_by(**where))
    if row is None:
        row = model(**where)
        db.add(row)
    for k, v in values.items():
        setattr(row, k, v)
    return row


def seed(db: Session, content_dir: Path = CONTENT_DIR) -> dict[str, int]:
    subjects, units = read_content(content_dir)
    by_slug = {}
    for s in subjects:
        by_slug[s["slug"]] = upsert(db, Subject, {"slug": s["slug"]}, {
            "title": s["title"], "color": s.get("color", "#2f5bea"), "order": s.get("order", 0),
            "planned": s.get("planned", []),
        })
    db.flush()

    seen_units = set()
    counts = {"units": 0, "lessons": 0, "exercises": 0, "items": 0}
    for u in units:
        seen_units.add(u["slug"])
        unit = upsert(db, Unit, {"slug": u["slug"]}, {
            "subject_id": by_slug[u["subject"]].id, "title": u["title"], "subtitle": u.get("subtitle", ""),
            "order": u.get("order", 0), "ui_lang": u.get("ui_lang", "fr"), "enabled": u.get("enabled", True),
            "config": {k: u[k] for k in UNIT_CONFIG_KEYS if k in u},
        })
        db.flush()
        counts["units"] += 1

        lesson_slugs = set()
        for i, lesson in enumerate(u.get("lessons", [])):
            lesson_slugs.add(lesson["slug"])
            upsert(db, Lesson, {"unit_id": unit.id, "slug": lesson["slug"]},
                   {"title": lesson["title"], "order": i, "blocks": lesson.get("blocks", [])})
            counts["lessons"] += 1
        for old in db.scalars(select(Lesson).where(Lesson.unit_id == unit.id)):
            if old.slug not in lesson_slugs:
                db.delete(old)

        ex_keys = set()
        for i, e in enumerate(u.get("exercises", [])):
            ex_keys.add(e["key"])
            upsert(db, ExerciseType, {"unit_id": unit.id, "key": e["key"]}, {
                "title": e["title"], "generator": e["generator"], "order": i,
                "params": e.get("params", {}), "enabled": e.get("enabled", True),
            })
            counts["exercises"] += 1
        # keep removed exercise types (student history points to them) but hide them
        for old in db.scalars(select(ExerciseType).where(ExerciseType.unit_id == unit.id)):
            if old.key not in ex_keys:
                old.enabled = False

        item_ids = set()
        for kind, items in u["items"].items():
            for i, it in enumerate(items):
                item_ids.add((kind, it["key"]))
                upsert(db, Item, {"unit_id": unit.id, "kind": kind, "key": it["key"]},
                       {"order": i, "data": {k: v for k, v in it.items() if k != "key"}})
                counts["items"] += 1
        for old in db.scalars(select(Item).where(Item.unit_id == unit.id)):
            if (old.kind, old.key) not in item_ids:
                db.delete(old)

    for old in db.scalars(select(Unit)):
        if old.slug not in seen_units:
            old.enabled = False
    db.commit()
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="validate content without writing to the database")
    args = parser.parse_args()
    try:
        if args.check:
            subjects, units = read_content()
            print(f"Content OK: {len(subjects)} subjects, {len(units)} units")
            return
        from .db import SessionLocal
        with SessionLocal() as db:
            counts = seed(db)
        print("Seeded:", ", ".join(f"{v} {k}" for k, v in counts.items()))
    except ContentError as e:
        print("Content errors:\n" + str(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
