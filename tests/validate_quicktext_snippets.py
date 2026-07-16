#!/usr/bin/env python3
"""Prueft die ausgelagerten Schnell-Text-Bausteine."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNIPPETS_PATH = ROOT / "data" / "schnell-text-speicher-bausteine.json"
CATEGORY_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_TOP_LEVEL = {"moduleId", "version", "description", "categories"}
REQUIRED_CATEGORY_KEYS = {"id", "name", "snippets"}
MIN_SNIPPETS_PER_CATEGORY = 3
MAX_SNIPPET_LENGTH = 360


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def load_data(errors: list[str]) -> dict:
    try:
        return json.loads(SNIPPETS_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(errors, f"Datei fehlt: {SNIPPETS_PATH.relative_to(ROOT)}")
    except json.JSONDecodeError as exc:
        fail(errors, f"JSON ungueltig: Zeile {exc.lineno}, Spalte {exc.colno}")
    return {}


def validate_category(category: object, index: int, errors: list[str], seen_snippets: set[str]) -> None:
    if not isinstance(category, dict):
        fail(errors, f"Kategorie {index}: Eintrag ist kein Objekt")
        return
    if set(category) != REQUIRED_CATEGORY_KEYS:
        fail(errors, f"Kategorie {index}: Felder stimmen nicht exakt")

    category_id = category.get("id")
    name = category.get("name")
    snippets = category.get("snippets")

    if not isinstance(category_id, str) or not CATEGORY_ID_PATTERN.fullmatch(category_id):
        fail(errors, f"Kategorie {index}: id ist keine kleine Bindestrich-ID")
    if not isinstance(name, str) or not 3 <= len(name) <= 60:
        fail(errors, f"Kategorie {index}: name hat ungueltige Laenge")
    if not isinstance(snippets, list) or len(snippets) < MIN_SNIPPETS_PER_CATEGORY:
        fail(errors, f"Kategorie {index}: zu wenige Bausteine")
        return

    for snippet_index, snippet in enumerate(snippets, start=1):
        if not isinstance(snippet, str):
            fail(errors, f"Kategorie {index}, Baustein {snippet_index}: Text ist kein String")
            continue
        normalized = " ".join(snippet.split())
        if not 20 <= len(normalized) <= MAX_SNIPPET_LENGTH:
            fail(errors, f"Kategorie {index}, Baustein {snippet_index}: Laenge ist ungueltig")
        if normalized in seen_snippets:
            fail(errors, f"Kategorie {index}, Baustein {snippet_index}: exaktes Duplikat")
        seen_snippets.add(normalized)


def validate(data: dict) -> list[str]:
    errors: list[str] = []
    if set(data) != REQUIRED_TOP_LEVEL:
        fail(errors, "Oberste Felder stimmen nicht exakt")
    if data.get("moduleId") != "schnell-text-speicher":
        fail(errors, "moduleId passt nicht zum Modul")
    if not isinstance(data.get("version"), str) or not re.fullmatch(r"\d+\.\d+\.\d+", data.get("version", "")):
        fail(errors, "version folgt nicht x.y.z")
    if not isinstance(data.get("description"), str) or len(data["description"]) < 20:
        fail(errors, "description ist zu kurz")

    categories = data.get("categories")
    if not isinstance(categories, list) or not categories:
        fail(errors, "categories braucht mindestens einen Eintrag")
        return errors

    seen_ids: set[str] = set()
    seen_snippets: set[str] = set()
    for index, category in enumerate(categories, start=1):
        category_id = category.get("id") if isinstance(category, dict) else None
        if isinstance(category_id, str):
            if category_id in seen_ids:
                fail(errors, f"Kategorie {index}: id ist doppelt")
            seen_ids.add(category_id)
        validate_category(category, index, errors, seen_snippets)
    return errors


def main() -> int:
    load_errors: list[str] = []
    data = load_data(load_errors)
    errors = load_errors or validate(data)
    if errors:
        for error in errors:
            print(f"FEHLER: {error}")
        return 1
    count = sum(len(category["snippets"]) for category in data["categories"])
    print(f"OK: {len(data['categories'])} Kategorien und {count} Textbausteine geprueft.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
