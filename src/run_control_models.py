"""Pure serialized run-state types shared by validation and execution."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

RUN_SCHEMA_VERSION = 1
MAXIMUM_RUN_ITEMS = 1000
RUN_OPERATION = "project-trash-batch"
_RUN_ID_PATTERN = re.compile(r"^MMTRUN-[0-9]{8}T[0-9]{6}-[A-F0-9]{12}$")
_ALLOWED_RUN_STATES = {"prepared", "running", "cancelled", "completed", "blocked"}


@dataclass(frozen=True)
class RunPaths:
    project_root: Path
    control_directory: Path
    runs_directory: Path
    run_directory: Path
    plan_file: Path
    checkpoint_file: Path
    lock_file: Path
    cancel_file: Path


@dataclass(frozen=True)
class RunItem:
    index: int
    source_relative_path: str

    def as_dict(self) -> dict[str, object]:
        return {"index": self.index, "sourceRelativePath": self.source_relative_path}


@dataclass(frozen=True)
class RunPlan:
    schema_version: int
    run_id: str
    operation: str
    created_utc: str
    items: tuple[RunItem, ...]
    plan_hash: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": self.schema_version,
            "runId": self.run_id,
            "operation": self.operation,
            "createdUtc": self.created_utc,
            "items": [item.as_dict() for item in self.items],
            "planHash": self.plan_hash,
        }


@dataclass(frozen=True)
class CurrentStep:
    index: int
    attempt: int
    action_id: str
    transaction_id: str
    source_relative_path: str

    def as_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "attempt": self.attempt,
            "actionId": self.action_id,
            "transactionId": self.transaction_id,
            "sourceRelativePath": self.source_relative_path,
        }


@dataclass(frozen=True)
class RunCheckpoint:
    schema_version: int
    run_id: str
    plan_hash: str
    state: str
    next_index: int
    completed_indices: tuple[int, ...]
    attempt_counts: tuple[int, ...]
    current_step: CurrentStep | None
    generation: int
    created_utc: str
    updated_utc: str
    cancel_requested: bool
    message: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": self.schema_version,
            "runId": self.run_id,
            "planHash": self.plan_hash,
            "state": self.state,
            "nextIndex": self.next_index,
            "completedIndices": list(self.completed_indices),
            "attemptCounts": list(self.attempt_counts),
            "currentStep": self.current_step.as_dict() if self.current_step else None,
            "generation": self.generation,
            "createdUtc": self.created_utc,
            "updatedUtc": self.updated_utc,
            "cancelRequested": self.cancel_requested,
            "message": self.message,
        }


@dataclass(frozen=True)
class RunSnapshot:
    plan: RunPlan
    checkpoint: RunCheckpoint
    paths: RunPaths


@dataclass(frozen=True)
class RunResult:
    run_id: str
    state: str
    completed_count: int
    total_count: int
    changed: bool
    recovered: bool = False
    message: str = ""
