"""Zentrale, datensparsame Fehler- und Ereignisschicht für MULTIMODULTOOL2026."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import stat
import sys
import threading
import traceback
from typing import Callable, Iterable, Mapping
from uuid import uuid4

EVENT_LOG_FILE_NAME = "events.jsonl"
EVENT_FILE_MODE = 0o600
MAX_EVENT_TEXT_LENGTH = 4000
MAX_TECHNICAL_DETAIL_LENGTH = 12000
_REQUIRED_USER_FIELDS = (
    "cause",
    "consequence",
    "data_state",
    "solution",
    "diagnostic_id",
    "next_step",
)
_SECRET_PATTERNS = (
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(r"(?i)(password|passwd|token|secret|api[_-]?key)\s*[:=]\s*[^\s,;]+"),
)


@dataclass(frozen=True)
class ErrorEvent:
    """Vollständiger, nutzerlesbarer und maschinenprotokollierbarer Ereignissatz."""

    timestamp_utc: str
    diagnostic_id: str
    category: str
    severity: str
    cause: str
    consequence: str
    data_state: str
    solution: str
    next_step: str
    technical_detail: str = ""
    metadata: Mapping[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return asdict(self)

    def missing_required_fields(self) -> tuple[str, ...]:
        missing: list[str] = []
        for name in _REQUIRED_USER_FIELDS:
            value = getattr(self, name, "")
            if not isinstance(value, str) or not value.strip():
                missing.append(name)
        return tuple(missing)


@dataclass(frozen=True)
class JournalWriteResult:
    success: bool
    error: str = ""


class SafeOperationError(RuntimeError):
    """Fehlervertrag für spätere Dateioperationen ohne technische UI-Abhängigkeit."""

    def __init__(
        self,
        *,
        cause: str,
        consequence: str,
        data_state: str,
        solution: str,
        next_step: str,
        category: str = "file-operation",
        technical_detail: str = "",
    ) -> None:
        super().__init__(cause)
        self.cause = cause
        self.consequence = consequence
        self.data_state = data_state
        self.solution = solution
        self.next_step = next_step
        self.category = category
        self.technical_detail = technical_detail


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _diagnostic_id(category: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", category).strip("-").upper()[:12] or "GENERAL"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"MMT-{normalized}-{timestamp}-{uuid4().hex[:8].upper()}"


def sanitize_text(
    value: object,
    *,
    home: Path | None = None,
    maximum: int = MAX_EVENT_TEXT_LENGTH,
) -> str:
    """Private Pfade, Geheimnisse und Steuerzeichen vor Ausgabe/Logging reduzieren."""

    text = str(value or "").replace("\x00", "")
    text = "".join(character if character in "\n\t" or ord(character) >= 32 else " " for character in text)
    home_path = (home or Path.home()).expanduser()
    if home_path.is_absolute():
        text = text.replace(str(home_path), "~")
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[GESCHÜTZT]", text)
    text = text.strip()
    if len(text) > maximum:
        text = text[: max(0, maximum - 24)].rstrip() + " … [gekürzt]"
    return text


def create_event(
    *,
    category: str,
    severity: str,
    cause: str,
    consequence: str,
    data_state: str,
    solution: str,
    next_step: str,
    technical_detail: str = "",
    metadata: Mapping[str, object] | None = None,
) -> ErrorEvent:
    """Ereignis mit sechs verpflichtenden Nutzerfeldern erzeugen."""

    category_clean = sanitize_text(category, maximum=80) or "general"
    event = ErrorEvent(
        timestamp_utc=_utc_timestamp(),
        diagnostic_id=_diagnostic_id(category_clean),
        category=category_clean,
        severity=(sanitize_text(severity, maximum=20) or "error").lower(),
        cause=sanitize_text(cause) or "Die Ursache konnte nicht genauer bestimmt werden.",
        consequence=sanitize_text(consequence) or "Der betroffene Vorgang wurde kontrolliert beendet.",
        data_state=sanitize_text(data_state) or "Der Datenstand ist unbekannt; keine weitere Aktion wurde gestartet.",
        solution=sanitize_text(solution) or "Die Diagnose prüfen und den Vorgang erst danach erneut starten.",
        next_step=sanitize_text(next_step) or "Diagnosekennung notieren und die Prüfung erneut ausführen.",
        technical_detail=sanitize_text(
            technical_detail,
            maximum=MAX_TECHNICAL_DETAIL_LENGTH,
        ),
        metadata={
            sanitize_text(key, maximum=80): sanitize_text(value, maximum=500)
            for key, value in (metadata or {}).items()
            if sanitize_text(key, maximum=80)
        },
    )
    if event.missing_required_fields():
        raise ValueError("Fehlerereignis enthält unvollständige Pflichtfelder.")
    return event


def event_from_exception(
    exception: BaseException,
    *,
    category: str = "unhandled-exception",
    context: str = "Eine unerwartete Ausnahme ist aufgetreten.",
    data_state: str = "Der laufende Schritt wurde beendet; bereits bestätigte Daten bleiben unverändert.",
    technical_detail: str | None = None,
) -> ErrorEvent:
    """Beliebige Ausnahme in den verbindlichen Nutzervertrag übersetzen."""

    if isinstance(exception, SafeOperationError):
        return create_event(
            category=exception.category,
            severity="error",
            cause=exception.cause,
            consequence=exception.consequence,
            data_state=exception.data_state,
            solution=exception.solution,
            next_step=exception.next_step,
            technical_detail=exception.technical_detail or repr(exception),
        )

    detail = technical_detail
    if detail is None:
        detail = "".join(
            traceback.format_exception(type(exception), exception, exception.__traceback__)
        )
    return create_event(
        category=category,
        severity="error",
        cause=f"{context} {type(exception).__name__}: {exception}",
        consequence="Der betroffene Schritt wurde kontrolliert gestoppt; weitere abhängige Aktionen wurden nicht gestartet.",
        data_state=data_state,
        solution="Die Diagnosekennung verwenden, die genannte Ursache beheben und anschließend die sichere Prüfung wiederholen.",
        next_step="Programmzustand prüfen, Diagnosekennung notieren und den Vorgang erst nach grüner Vorprüfung erneut starten.",
        technical_detail=detail,
    )


def event_from_messages(
    messages: Iterable[str],
    *,
    category: str,
    cause_prefix: str,
    consequence: str,
    data_state: str,
    solution: str,
    next_step: str,
    severity: str = "error",
) -> ErrorEvent:
    clean_messages = [sanitize_text(item) for item in messages if sanitize_text(item)]
    cause = cause_prefix
    if clean_messages:
        cause = f"{cause_prefix} {'; '.join(clean_messages)}"
    return create_event(
        category=category,
        severity=severity,
        cause=cause,
        consequence=consequence,
        data_state=data_state,
        solution=solution,
        next_step=next_step,
        metadata={"messageCount": str(len(clean_messages))},
    )


def event_from_settings_result(result: object) -> ErrorEvent:
    """Recovery- oder Blockierstatus eines SettingsLoadResult zentral abbilden."""

    errors = list(getattr(result, "errors", []) or [])
    warnings = list(getattr(result, "warnings", []) or [])
    recovered = bool(getattr(result, "recovered", False))
    source = sanitize_text(getattr(result, "source", "unbekannt"), maximum=80)
    if errors:
        return event_from_messages(
            errors,
            category="settings-blocked",
            cause_prefix="Die Einstellungen konnten nicht sicher geladen werden.",
            consequence="Die Oberfläche und alle davon abhängigen Funktionen bleiben gesperrt.",
            data_state="Aktive Einstellungen wurden nicht ungeprüft verwendet; produktive Nutzerdaten wurden nicht verändert.",
            solution="XDG-Konfigurationspfad, Dateirechte und die gemeldete JSON-/Schema-Ursache korrigieren.",
            next_step="Mit --settings-only erneut prüfen und erst bei grünem Ergebnis normal starten.",
        )
    if recovered:
        return event_from_messages(
            warnings,
            category="settings-recovery",
            cause_prefix="Die aktive Einstellungsdatei war beschädigt oder inkompatibel.",
            consequence=f"Das Tool verwendet kontrolliert die Quelle '{source}'.",
            data_state="Produktive Nutzerdaten blieben unverändert; nur die lokale Einstellungsdatei wurde isoliert oder ersetzt.",
            solution="Die wiederhergestellten Einstellungen prüfen; die isolierte Datei nur zur Diagnose aufbewahren.",
            next_step="Im Tool den Sicherheitsstatus prüfen und den normalen Workflow erst danach fortsetzen.",
            severity="warning",
        )
    return create_event(
        category="settings-status",
        severity="info",
        cause="Die versionierten Einstellungen wurden erfolgreich geprüft.",
        consequence=f"Die sichere Einstellungsquelle '{source}' ist aktiv.",
        data_state="Keine Nutzerdaten wurden verändert.",
        solution="Keine Korrektur erforderlich.",
        next_step="Mit dem freigegebenen nächsten Arbeitsschritt fortfahren.",
    )


def format_event_for_user(event: ErrorEvent) -> str:
    """Verbindliche Dialog-/Konsolendarstellung mit allen sechs Pflichtfeldern."""

    return "\n".join(
        (
            f"Ursache: {event.cause}",
            f"Folge: {event.consequence}",
            f"Datenstand: {event.data_state}",
            f"Lösung: {event.solution}",
            f"Diagnosekennung: {event.diagnostic_id}",
            f"Sicherer nächster Schritt: {event.next_step}",
        )
    )


class EventJournal:
    """Minimales privates JSONL-Ereignisjournal im validierten XDG-Logpfad."""

    def __init__(self, log_directory: Path) -> None:
        self.log_directory = log_directory.expanduser()
        self.log_file = self.log_directory / EVENT_LOG_FILE_NAME
        self._lock = threading.Lock()

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        directory = self.log_directory
        if not directory.is_absolute():
            errors.append("Ereignis-Logverzeichnis ist nicht absolut.")
            return tuple(errors)
        if directory.is_symlink():
            errors.append("Ereignis-Logverzeichnis darf kein Symlink sein.")
            return tuple(errors)
        if not directory.exists() or not directory.is_dir():
            errors.append("Ereignis-Logverzeichnis fehlt oder ist kein Verzeichnis.")
            return tuple(errors)
        try:
            directory_mode = directory.lstat().st_mode
        except OSError as exc:
            errors.append(f"Ereignis-Logverzeichnis kann nicht geprüft werden: {exc}")
        else:
            if stat.S_IMODE(directory_mode) & 0o077:
                errors.append("Ereignis-Logverzeichnis ist zu offen; erforderlich ist 0700.")
            if not os.access(directory, os.W_OK | os.X_OK):
                errors.append("Ereignis-Logverzeichnis ist nicht beschreibbar.")
        if self.log_file.is_symlink():
            errors.append("Ereignisdatei darf kein Symlink sein.")
        if self.log_file.exists():
            try:
                mode = self.log_file.lstat().st_mode
            except OSError as exc:
                errors.append(f"Ereignisdatei kann nicht geprüft werden: {exc}")
            else:
                metadata = self.log_file.lstat()
                if not stat.S_ISREG(mode):
                    errors.append("Ereignisdatei ist keine reguläre Datei.")
                elif metadata.st_nlink != 1:
                    errors.append("Ereignisdatei darf keine zusätzlichen Hardlinks besitzen.")
                elif hasattr(os, "getuid") and metadata.st_uid != os.getuid():
                    errors.append("Ereignisdatei gehört nicht dem aktuellen Linux-Nutzer.")
                elif stat.S_IMODE(mode) & 0o077:
                    errors.append("Ereignisdatei ist zu offen; erforderlich ist 0600.")
        return tuple(errors)

    def record(self, event: ErrorEvent) -> JournalWriteResult:
        with self._lock:
            errors = self.validate()
            if errors:
                return JournalWriteResult(False, "; ".join(errors))
            payload = json.dumps(event.as_dict(), ensure_ascii=False, sort_keys=True) + "\n"
            flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
            flags |= getattr(os, "O_CLOEXEC", 0)
            flags |= getattr(os, "O_NOFOLLOW", 0)
            descriptor: int | None = None
            try:
                descriptor = os.open(self.log_file, flags, EVENT_FILE_MODE)
                metadata = os.fstat(descriptor)
                if not stat.S_ISREG(metadata.st_mode):
                    raise OSError("Ereignisziel ist keine reguläre Datei.")
                if metadata.st_nlink != 1:
                    raise OSError("Ereignisziel besitzt zusätzliche Hardlinks.")
                if hasattr(os, "getuid") and metadata.st_uid != os.getuid():
                    raise OSError("Ereignisziel gehört nicht dem aktuellen Linux-Nutzer.")
                os.fchmod(descriptor, EVENT_FILE_MODE)
                remaining = memoryview(payload.encode("utf-8"))
                while remaining:
                    written = os.write(descriptor, remaining)
                    if written <= 0:
                        raise OSError("Ereignis konnte nicht vollständig geschrieben werden.")
                    remaining = remaining[written:]
                os.fsync(descriptor)
            except OSError as exc:
                return JournalWriteResult(False, sanitize_text(exc))
            finally:
                if descriptor is not None:
                    os.close(descriptor)
            return JournalWriteResult(True)


class ErrorEventCenter:
    """Einheitlicher Speicher- und Verteilpunkt für Fehler, Warnungen und Ereignisse."""

    def __init__(
        self,
        journal: EventJournal | None = None,
        *,
        maximum_memory_events: int = 100,
    ) -> None:
        self.journal = journal
        self.maximum_memory_events = max(1, maximum_memory_events)
        self._events: list[ErrorEvent] = []
        self.last_journal_error = ""
        self._lock = threading.RLock()

    @property
    def events(self) -> tuple[ErrorEvent, ...]:
        with self._lock:
            return tuple(self._events)

    @property
    def latest(self) -> ErrorEvent | None:
        with self._lock:
            return self._events[-1] if self._events else None

    def capture(self, event: ErrorEvent) -> ErrorEvent:
        with self._lock:
            self._events.append(event)
            if len(self._events) > self.maximum_memory_events:
                del self._events[: len(self._events) - self.maximum_memory_events]
            if self.journal is not None:
                result = self.journal.record(event)
                self.last_journal_error = "" if result.success else result.error
            return event

    def capture_exception(self, exception: BaseException, **kwargs: object) -> ErrorEvent:
        return self.capture(event_from_exception(exception, **kwargs))


def install_exception_hooks(
    center: ErrorEventCenter,
    *,
    on_event: Callable[[ErrorEvent], None] | None = None,
) -> tuple[Callable[..., object], object | None]:
    """sys- und Thread-Ausnahmen zentral erfassen; frühere Hooks zurückgeben."""

    previous_sys_hook = sys.excepthook
    previous_thread_hook = getattr(threading, "excepthook", None)

    def emit(event: ErrorEvent) -> None:
        center.capture(event)
        if on_event is not None:
            on_event(event)
        else:
            print(format_event_for_user(event), file=sys.stderr)

    def sys_hook(exc_type: type[BaseException], exc_value: BaseException, exc_tb: object) -> None:
        detail = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        emit(
            event_from_exception(
                exc_value,
                category="unhandled-main-thread",
                context="Eine unbehandelte Ausnahme im Hauptthread wurde abgefangen.",
                technical_detail=detail,
            )
        )

    sys.excepthook = sys_hook

    if previous_thread_hook is not None:
        def thread_hook(args: threading.ExceptHookArgs) -> None:
            detail = "".join(
                traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback)
            )
            emit(
                event_from_exception(
                    args.exc_value,
                    category="unhandled-worker-thread",
                    context=f"Eine unbehandelte Ausnahme im Thread '{getattr(args.thread, 'name', 'unbekannt')}' wurde abgefangen.",
                    technical_detail=detail,
                )
            )

        threading.excepthook = thread_hook

    return previous_sys_hook, previous_thread_hook
