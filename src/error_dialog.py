"""Qt-Dialog für den verbindlichen Fehlervertrag ohne PySide6-Import zur Modulzeit."""

from __future__ import annotations

from .error_events import ErrorEvent, format_event_for_user


FIELD_DEFINITIONS = (
    ("Ursache", "cause", "errorCause"),
    ("Folge", "consequence", "errorConsequence"),
    ("Datenstand", "data_state", "errorDataState"),
    ("Lösung", "solution", "errorSolution"),
    ("Diagnosekennung", "diagnostic_id", "errorDiagnosticId"),
    ("Sicherer nächster Schritt", "next_step", "errorNextStep"),
)


def build_error_dialog(QtWidgets, event: ErrorEvent, parent=None):
    """Modalen, vollständig beschrifteten Fehlerdialog erzeugen."""

    dialog = QtWidgets.QDialog(parent)
    dialog.setObjectName("globalErrorDialog")
    dialog.setWindowTitle("MULTIMODULTOOL2026 – Sicherer Fehlerbericht")
    dialog.setModal(True)
    dialog.setMinimumWidth(680)

    layout = QtWidgets.QVBoxLayout(dialog)
    layout.setContentsMargins(18, 18, 18, 18)
    layout.setSpacing(12)

    title = QtWidgets.QLabel("Der Vorgang wurde kontrolliert gestoppt")
    title.setObjectName("errorDialogTitle")
    title.setWordWrap(True)
    layout.addWidget(title)

    summary = QtWidgets.QLabel(
        "Es wurden keine weiteren abhängigen Aktionen gestartet. Prüfe die folgenden Angaben, bevor du fortfährst."
    )
    summary.setObjectName("errorDialogSummary")
    summary.setWordWrap(True)
    layout.addWidget(summary)

    for caption, attribute, object_name in FIELD_DEFINITIONS:
        frame = QtWidgets.QFrame()
        frame.setObjectName("errorField")
        field_layout = QtWidgets.QVBoxLayout(frame)
        field_layout.setContentsMargins(12, 9, 12, 9)
        field_layout.setSpacing(3)
        label = QtWidgets.QLabel(caption)
        label.setObjectName("errorFieldCaption")
        value = QtWidgets.QLabel(str(getattr(event, attribute)))
        value.setObjectName(object_name)
        value.setWordWrap(True)
        field_layout.addWidget(label)
        field_layout.addWidget(value)
        layout.addWidget(frame)

    buttons = QtWidgets.QHBoxLayout()
    copy_button = QtWidgets.QPushButton("Diagnose kopieren")
    copy_button.setObjectName("copyErrorReport")
    close_button = QtWidgets.QPushButton("Schließen")
    close_button.setObjectName("closeErrorDialog")
    close_button.setDefault(True)

    def copy_report() -> None:
        application = QtWidgets.QApplication.instance()
        if application is not None:
            application.clipboard().setText(format_event_for_user(event))

    copy_button.clicked.connect(copy_report)
    close_button.clicked.connect(dialog.accept)
    buttons.addWidget(copy_button)
    buttons.addStretch(1)
    buttons.addWidget(close_button)
    layout.addLayout(buttons)
    return dialog


def show_error_dialog(QtWidgets, event: ErrorEvent, parent=None) -> int:
    dialog = build_error_dialog(QtWidgets, event, parent)
    return dialog.exec()
