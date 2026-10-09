"""Strict run-plan and checkpoint validation without side effects."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from .error_events import SafeOperationError
from .run_control_models import (
    CurrentStep,
    RunCheckpoint,
    RunItem,
    RunPlan,
    RUN_SCHEMA_VERSION,
    RUN_OPERATION,
    MAXIMUM_RUN_ITEMS,
    _ALLOWED_RUN_STATES,
    _RUN_ID_PATTERN,
)


def _fail(
    cause: str,
    *,
    consequence: str = "Der lange Lauf wurde kontrolliert angehalten oder blockiert.",
    data_state: str = "Projektdateien, Papierkorbmanifeste, Aktionsjournal und Laufcheckpoint blieben nachvollziehbar.",
    solution: str = "Laufplan, Checkpoint, Journal, Manifest und Dateizustand gemeinsam prüfen.",
    next_step: str = "Diagnosekennung sichern und den Lauf erst nach grüner Zustandsprüfung fortsetzen.",
    technical_detail: str = "",
) -> SafeOperationError:
    return SafeOperationError(
        category="run-control",
        cause=cause,
        consequence=consequence,
        data_state=data_state,
        solution=solution,
        next_step=next_step,
        technical_detail=technical_detail,
    )


def _safe_relative(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _fail("Laufplan enthält keinen gültigen relativen Projektpfad.")
    path = Path(value)
    if path.is_absolute() or path == Path(".") or ".." in path.parts:
        raise _fail("Laufplanpfad überschreitet die Projektgrenze.")
    return path.as_posix()


def _canonical_hash(value: dict[str, object], *, excluded: str) -> str:
    payload = dict(value)
    payload.pop(excluded, None)
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _parse_plan(value: object) -> RunPlan:
    keys = {"schemaVersion", "runId", "operation", "createdUtc", "items", "planHash"}
    if not isinstance(value, dict) or set(value) != keys:
        raise _fail("Laufplan besitzt einen unbekannten Aufbau.")
    if value["schemaVersion"] != RUN_SCHEMA_VERSION:
        raise _fail("Laufplan verwendet eine unbekannte Schemaversion.")
    run_id = value["runId"]
    if not isinstance(run_id, str) or not _RUN_ID_PATTERN.fullmatch(run_id):
        raise _fail("Laufplan enthält keine gültige Lauf-ID.")
    if value["operation"] != RUN_OPERATION:
        raise _fail("Laufplan enthält eine nicht freigegebene Operation.")
    if not isinstance(value["createdUtc"], str) or not value["createdUtc"]:
        raise _fail("Laufplan enthält keinen Erstellungszeitpunkt.")
    raw_items = value["items"]
    if not isinstance(raw_items, list) or not 1 <= len(raw_items) <= MAXIMUM_RUN_ITEMS:
        raise _fail("Laufplan enthält keine zulässige Anzahl von Arbeitsschritten.")
    items: list[RunItem] = []
    seen: set[str] = set()
    for expected, raw in enumerate(raw_items):
        if not isinstance(raw, dict) or set(raw) != {"index", "sourceRelativePath"}:
            raise _fail("Laufplan enthält einen unbekannten Arbeitsschritt.")
        if raw["index"] != expected:
            raise _fail("Laufplanindizes müssen lückenlos bei null beginnen.")
        relative = _safe_relative(raw["sourceRelativePath"])
        if relative in seen:
            raise _fail("Laufplan enthält denselben Projektpfad mehrfach.")
        seen.add(relative)
        items.append(RunItem(expected, relative))
    plan_hash = value["planHash"]
    if not isinstance(plan_hash, str) or not re.fullmatch(r"[a-f0-9]{64}", plan_hash):
        raise _fail("Laufplan enthält keinen gültigen Planhash.")
    if _canonical_hash(value, excluded="planHash") != plan_hash:
        raise _fail("Laufplan wurde nach seiner Erstellung verändert.")
    return RunPlan(
        RUN_SCHEMA_VERSION,
        run_id,
        RUN_OPERATION,
        value["createdUtc"],
        tuple(items),
        plan_hash,
    )


def _parse_current_step(value: object, plan: RunPlan) -> CurrentStep | None:
    if value is None:
        return None
    keys = {"index", "attempt", "actionId", "transactionId", "sourceRelativePath"}
    if not isinstance(value, dict) or set(value) != keys:
        raise _fail("Checkpoint enthält einen unbekannten aktuellen Arbeitsschritt.")
    index = value["index"]
    attempt = value["attempt"]
    if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(plan.items):
        raise _fail("Checkpoint enthält einen ungültigen Schrittindex.")
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 1:
        raise _fail("Checkpoint enthält keinen gültigen Versuchszähler.")
    action_id = value["actionId"]
    transaction_id = value["transactionId"]
    if not isinstance(action_id, str) or not re.fullmatch(
        r"MMTACTION-[0-9]{8}T[0-9]{6}-[A-F0-9]{12}", action_id
    ):
        raise _fail("Checkpoint enthält keine gültige Aktions-ID.")
    if not isinstance(transaction_id, str) or not re.fullmatch(
        r"MMTTRASH-[0-9]{8}T[0-9]{6}-[A-F0-9]{12}", transaction_id
    ):
        raise _fail("Checkpoint enthält keine gültige Transaktions-ID.")
    relative = _safe_relative(value["sourceRelativePath"])
    if relative != plan.items[index].source_relative_path:
        raise _fail("Checkpoint und Laufplan verweisen auf unterschiedliche Projektpfade.")
    return CurrentStep(index, attempt, action_id, transaction_id, relative)


def _parse_checkpoint(value: object, plan: RunPlan) -> RunCheckpoint:
    keys = {
        "schemaVersion", "runId", "planHash", "state", "nextIndex",
        "completedIndices", "attemptCounts", "currentStep", "generation",
        "createdUtc", "updatedUtc", "cancelRequested", "message",
    }
    if not isinstance(value, dict) or set(value) != keys:
        raise _fail("Laufcheckpoint besitzt einen unbekannten Aufbau.")
    if value["schemaVersion"] != RUN_SCHEMA_VERSION:
        raise _fail("Laufcheckpoint verwendet eine unbekannte Schemaversion.")
    if value["runId"] != plan.run_id or value["planHash"] != plan.plan_hash:
        raise _fail("Laufcheckpoint gehört nicht zum unveränderten Laufplan.")
    state = value["state"]
    if not isinstance(state, str) or state not in _ALLOWED_RUN_STATES:
        raise _fail("Laufcheckpoint enthält einen unbekannten Zustand.")
    next_index = value["nextIndex"]
    if not isinstance(next_index, int) or isinstance(next_index, bool) or not 0 <= next_index <= len(plan.items):
        raise _fail("Laufcheckpoint enthält keinen gültigen nächsten Schritt.")
    completed = value["completedIndices"]
    if not isinstance(completed, list) or any(
        not isinstance(item, int) or isinstance(item, bool) for item in completed
    ):
        raise _fail("Laufcheckpoint enthält ungültige Abschlussindizes.")
    expected_completed = list(range(next_index))
    if completed != expected_completed:
        raise _fail("Laufcheckpoint besitzt keine lückenlose abgeschlossene Schrittfolge.")
    attempts = value["attemptCounts"]
    if (
        not isinstance(attempts, list)
        or len(attempts) != len(plan.items)
        or any(not isinstance(item, int) or isinstance(item, bool) or item < 0 for item in attempts)
    ):
        raise _fail("Laufcheckpoint enthält ungültige Versuchszähler.")
    current = _parse_current_step(value["currentStep"], plan)
    if current is not None:
        if current.index != next_index or attempts[current.index] != current.attempt:
            raise _fail("Aktueller Schritt und Versuchszähler des Checkpoints widersprechen sich.")
    generation = value["generation"]
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 1:
        raise _fail("Laufcheckpoint enthält keine gültige Generation.")
    for field in ("createdUtc", "updatedUtc", "message"):
        if not isinstance(value[field], str):
            raise _fail("Laufcheckpoint enthält ungültige Textfelder.")
    if not isinstance(value["cancelRequested"], bool):
        raise _fail("Laufcheckpoint enthält kein gültiges Abbruchkennzeichen.")
    if state == "completed" and next_index != len(plan.items):
        raise _fail("Abgeschlossener Lauf enthält noch offene Schritte.")
    return RunCheckpoint(
        RUN_SCHEMA_VERSION,
        plan.run_id,
        plan.plan_hash,
        state,
        next_index,
        tuple(completed),
        tuple(attempts),
        current,
        generation,
        value["createdUtc"],
        value["updatedUtc"],
        value["cancelRequested"],
        value["message"],
    )
