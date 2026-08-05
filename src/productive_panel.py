"""Guided PySide6 panel for the productive, preview-first project workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .error_events import SafeOperationError
from .productive_workflow import (
    DuplicateResult,
    InventorySnapshot,
    OperationPlan,
    OperationResult,
    RenameRule,
    analyze_project,
    execute_operation,
    find_duplicates,
    format_duplicate_summary,
    format_inventory_summary,
    format_operation_preview,
    format_project_safety,
    plan_mass_rename,
    plan_organization,
    undo_operation,
    validate_project_root,
    write_analysis_report,
)


def build_productive_panel(QtWidgets, QtCore, parent=None):
    """Build a local-only panel; construction itself performs no filesystem access."""

    class ProductiveWorkflowPanel(QtWidgets.QFrame):
        def __init__(self, parent_widget=None):
            super().__init__(parent_widget)
            self.setObjectName("productiveWorkflowPanel")
            self.project_root: Path | None = None
            self.snapshot: InventorySnapshot | None = None
            self.duplicates: DuplicateResult | None = None
            self.plan: OperationPlan | None = None
            self.last_result: OperationResult | None = None
            self._analysis_paths: list[str] = []
            self._build_ui()
            self._set_project_dependent(False)

        def _button(self, text: str, name: str, tooltip: str):
            button = QtWidgets.QPushButton(text)
            button.setObjectName(name)
            button.setMinimumHeight(42)
            button.setToolTip(tooltip)
            button.setStatusTip(tooltip)
            button.setWhatsThis(tooltip)
            button.setAccessibleDescription(tooltip)
            return button

        def _build_ui(self) -> None:
            outer = QtWidgets.QVBoxLayout(self)
            outer.setContentsMargins(14, 14, 14, 14)
            outer.setSpacing(10)

            title = QtWidgets.QLabel("Produktiver Projektworkflow")
            title.setObjectName("sectionTitle")
            title.setWordWrap(True)
            outer.addWidget(title)

            intro = QtWidgets.QLabel(
                "Projekt wählen → read-only analysieren → vollständige Vorschau prüfen → ausdrücklich bestätigen. "
                "Symlinks, Hardlinks, Mountwechsel, Zielkonflikte und stilles Überschreiben werden blockiert."
            )
            intro.setWordWrap(True)
            intro.setProperty("safetyStatus", True)
            outer.addWidget(intro)

            project_row = QtWidgets.QHBoxLayout()
            self.path_field = QtWidgets.QLineEdit()
            self.path_field.setObjectName("projectPathField")
            self.path_field.setReadOnly(True)
            self.path_field.setPlaceholderText("Noch kein Projektordner gewählt")
            self.path_field.setAccessibleName("Gewählter Projektordner")
            project_row.addWidget(self.path_field, 1)
            self.select_button = self._button(
                "Projektordner wählen …",
                "projectSelectButton",
                "Öffnet einen Ordnerdialog. Systemstämme, Home-Stamm, Symlinkpfade und fremde Eigentümer werden blockiert.",
            )
            self.select_button.clicked.connect(self.choose_project)
            project_row.addWidget(self.select_button)
            outer.addLayout(project_row)

            self.project_status = QtWidgets.QLabel(
                "Projektstatus: AUSWAHL ERFORDERLICH · keine Dateiaktion freigegeben"
            )
            self.project_status.setObjectName("projectValidationStatus")
            self.project_status.setWordWrap(True)
            self.project_status.setProperty("safetyStatus", True)
            outer.addWidget(self.project_status)

            self.tabs = QtWidgets.QTabWidget()
            self.tabs.setObjectName("productiveTabs")
            self.tabs.setDocumentMode(True)
            outer.addWidget(self.tabs, 1)

            self.analysis_tab = QtWidgets.QWidget()
            analysis_layout = QtWidgets.QVBoxLayout(self.analysis_tab)
            analysis_actions = QtWidgets.QHBoxLayout()
            self.analyze_button = self._button(
                "Bestand analysieren",
                "analyzeProjectButton",
                "Liest Typ, Größe, Datum, Namensmuster und Dateigrenzen. Es wird nichts verschoben oder umbenannt.",
            )
            self.analyze_button.clicked.connect(self.analyze)
            analysis_actions.addWidget(self.analyze_button)
            self.duplicate_button = self._button(
                "Duplikate per SHA-256 suchen",
                "findDuplicatesButton",
                "Hasht nur größenidentische reguläre Dateien streamend. Symlinks und Mehrfach-Hardlinks bleiben ausgeschlossen.",
            )
            self.duplicate_button.clicked.connect(self.find_duplicates)
            analysis_actions.addWidget(self.duplicate_button)
            self.report_button = self._button(
                "JSON- und Markdown-Bericht speichern",
                "saveAnalysisReportButton",
                "Speichert ausdrücklich einen privaten Bericht mit ausschließlich projekt-relativen Pfaden.",
            )
            self.report_button.clicked.connect(self.save_report)
            analysis_actions.addWidget(self.report_button)
            analysis_layout.addLayout(analysis_actions)
            self.analysis_summary = QtWidgets.QPlainTextEdit()
            self.analysis_summary.setObjectName("analysisSummary")
            self.analysis_summary.setReadOnly(True)
            self.analysis_summary.setMaximumHeight(150)
            self.analysis_summary.setPlaceholderText("Nach der Projektwahl kann die rein lesende Analyse gestartet werden.")
            analysis_layout.addWidget(self.analysis_summary)
            self.analysis_table = QtWidgets.QTableWidget(0, 5)
            self.analysis_table.setObjectName("analysisTable")
            self.analysis_table.setHorizontalHeaderLabels(("Typ", "Projektpfad", "Größe", "Kategorie", "Hinweise"))
            self.analysis_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
            self.analysis_table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
            self.analysis_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
            self.analysis_table.setSortingEnabled(True)
            self.analysis_table.horizontalHeader().setStretchLastSection(True)
            analysis_layout.addWidget(self.analysis_table, 1)
            self.tabs.addTab(self.analysis_tab, "Analyse & Duplikate")

            self.organize_tab = QtWidgets.QWidget()
            organize_layout = QtWidgets.QVBoxLayout(self.organize_tab)
            organize_form = QtWidgets.QFormLayout()
            self.organization_rule = QtWidgets.QComboBox()
            self.organization_rule.setObjectName("organizationRuleCombo")
            self.organization_rule.addItem("Nach Dateityp", "category")
            self.organization_rule.addItem("Nach Dateiendung", "extension")
            self.organization_rule.addItem("Nach Änderungsjahr", "year")
            self.organization_rule.setToolTip(
                "Die Regel wird ausschließlich für die Vorschau verwendet; Ziel ist der Projektordner Sortiert."
            )
            organize_form.addRow("Sortierregel:", self.organization_rule)
            destination = QtWidgets.QLineEdit("Sortiert")
            destination.setObjectName("organizationDestinationField")
            destination.setReadOnly(True)
            destination.setToolTip("Fester projektinterner Zielstamm. Vorhandene Ziele werden niemals überschrieben.")
            organize_form.addRow("Zielstamm:", destination)
            organize_layout.addLayout(organize_form)
            self.organization_preview_button = self._button(
                "Sortier-Vorschau erzeugen",
                "previewOrganizationButton",
                "Berechnet alle Vorher-/Nachher-Pfade. Bei einem einzigen Zielkonflikt wird der gesamte Plan blockiert.",
            )
            self.organization_preview_button.clicked.connect(self.preview_organization)
            organize_layout.addWidget(self.organization_preview_button)
            organize_notice = QtWidgets.QLabel(
                "Es werden ausschließlich reguläre Dateien verschoben. Der interne Steuerordner, Symlinks, "
                "Hardlinks und Dateisystemgrenzen bleiben ausgeschlossen."
            )
            organize_notice.setWordWrap(True)
            organize_notice.setProperty("safetyStatus", True)
            organize_layout.addWidget(organize_notice)
            organize_layout.addStretch(1)
            self.tabs.addTab(self.organize_tab, "Organisieren")

            self.rename_tab = QtWidgets.QWidget()
            rename_layout = QtWidgets.QVBoxLayout(self.rename_tab)
            rename_form = QtWidgets.QFormLayout()
            self.rename_scope = QtWidgets.QComboBox()
            self.rename_scope.setObjectName("renameScopeCombo")
            self.rename_scope.addItem("Nur markierte Analysedateien", "selected")
            self.rename_scope.addItem("Alle analysierten Dateien", "all")
            rename_form.addRow("Umfang:", self.rename_scope)
            self.rename_prefix = QtWidgets.QLineEdit()
            self.rename_prefix.setObjectName("renamePrefixField")
            self.rename_prefix.setPlaceholderText("optional")
            rename_form.addRow("Präfix:", self.rename_prefix)
            self.rename_suffix = QtWidgets.QLineEdit()
            self.rename_suffix.setObjectName("renameSuffixField")
            self.rename_suffix.setPlaceholderText("optional, vor Dateiendung")
            rename_form.addRow("Suffix:", self.rename_suffix)
            self.rename_search = QtWidgets.QLineEdit()
            self.rename_search.setObjectName("renameSearchField")
            self.rename_search.setPlaceholderText("optional")
            rename_form.addRow("Suchen:", self.rename_search)
            self.rename_replacement = QtWidgets.QLineEdit()
            self.rename_replacement.setObjectName("renameReplacementField")
            self.rename_replacement.setPlaceholderText("Ersatztext; darf leer sein")
            rename_form.addRow("Ersetzen:", self.rename_replacement)
            self.rename_case = QtWidgets.QComboBox()
            self.rename_case.setObjectName("renameCaseCombo")
            self.rename_case.addItem("Schreibweise beibehalten", "keep")
            self.rename_case.addItem("Kleinbuchstaben", "lower")
            self.rename_case.addItem("GROSSBUCHSTABEN", "upper")
            rename_form.addRow("Schreibweise:", self.rename_case)
            numbering_row = QtWidgets.QHBoxLayout()
            self.rename_numbering = QtWidgets.QCheckBox("fortlaufende Nummer ergänzen")
            self.rename_numbering.setObjectName("renameNumberingCheck")
            numbering_row.addWidget(self.rename_numbering)
            self.rename_start = QtWidgets.QSpinBox()
            self.rename_start.setObjectName("renameNumberStart")
            self.rename_start.setRange(0, 999_999_999)
            self.rename_start.setValue(1)
            self.rename_start.setPrefix("Start ")
            numbering_row.addWidget(self.rename_start)
            self.rename_padding = QtWidgets.QSpinBox()
            self.rename_padding.setObjectName("renameNumberPadding")
            self.rename_padding.setRange(1, 9)
            self.rename_padding.setValue(3)
            self.rename_padding.setPrefix("Stellen ")
            numbering_row.addWidget(self.rename_padding)
            numbering_widget = QtWidgets.QWidget()
            numbering_widget.setLayout(numbering_row)
            rename_form.addRow("Nummerierung:", numbering_widget)
            rename_layout.addLayout(rename_form)
            self.rename_preview_button = self._button(
                "Umbenennungs-Vorschau erzeugen",
                "previewRenameButton",
                "Berechnet jeden Zielnamen, erhält die Dateiendung und blockiert leere, zu lange, doppelte oder belegte Ziele.",
            )
            self.rename_preview_button.clicked.connect(self.preview_rename)
            rename_layout.addWidget(self.rename_preview_button)
            rename_layout.addStretch(1)
            self.tabs.addTab(self.rename_tab, "Massenumbenennen")

            self.plan_tab = QtWidgets.QWidget()
            plan_layout = QtWidgets.QVBoxLayout(self.plan_tab)
            self.plan_summary = QtWidgets.QPlainTextEdit()
            self.plan_summary.setObjectName("operationPlanSummary")
            self.plan_summary.setReadOnly(True)
            self.plan_summary.setMaximumHeight(150)
            self.plan_summary.setPlaceholderText("Noch keine produktive Vorschau erzeugt.")
            plan_layout.addWidget(self.plan_summary)
            self.preview_table = QtWidgets.QTableWidget(0, 4)
            self.preview_table.setObjectName("productivePreviewTable")
            self.preview_table.setHorizontalHeaderLabels(("Status", "Vorher", "Nachher", "Prüfung"))
            self.preview_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
            self.preview_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
            self.preview_table.horizontalHeader().setStretchLastSection(True)
            plan_layout.addWidget(self.preview_table, 1)
            plan_actions = QtWidgets.QHBoxLayout()
            self.apply_button = self._button(
                "Geprüften Plan ausführen …",
                "applyProductivePlanButton",
                "Zeigt vor der Ausführung eine letzte Zusammenfassung. Kein Ziel wird überschrieben; jeder Schritt erhält einen privaten Checkpoint.",
            )
            self.apply_button.clicked.connect(self.apply_plan)
            plan_actions.addWidget(self.apply_button)
            self.undo_button = self._button(
                "Letzte Operation rückgängig …",
                "undoProductiveOperationButton",
                "Führt nur unveränderte Zieldateien an freie Originalpfade zurück. Ein Konflikt stoppt sofort."
            )
            self.undo_button.clicked.connect(self.undo_last)
            plan_actions.addWidget(self.undo_button)
            plan_layout.addLayout(plan_actions)
            self.tabs.addTab(self.plan_tab, "Vorschau & Ausführung")

        def _set_project_dependent(self, enabled: bool) -> None:
            for widget in (
                self.analyze_button,
                self.duplicate_button,
                self.report_button,
                self.organization_preview_button,
                self.rename_preview_button,
            ):
                widget.setEnabled(enabled)
            self.apply_button.setEnabled(False)
            self.undo_button.setEnabled(False)

        def _error(self, title: str, exc: BaseException) -> None:
            cause = exc.cause if isinstance(exc, SafeOperationError) else str(exc)
            self.project_status.setText(f"ROT: {cause}")
            QtWidgets.QMessageBox.critical(self, title, cause)

        def choose_project(self) -> None:
            path = QtWidgets.QFileDialog.getExistingDirectory(
                self,
                "Sicheren Projektordner wählen",
                str(Path.home()),
                QtWidgets.QFileDialog.Option.ShowDirsOnly,
            )
            if not path:
                return
            try:
                project = validate_project_root(Path(path))
                self.project_root = project.root
                self.snapshot = None
                self.duplicates = None
                self.plan = None
                self.last_result = None
                self.path_field.setText(str(project.root))
                self.analysis_summary.setPlainText(format_project_safety(project))
                self.project_status.setText(
                    "GRÜN: Projektgrenze, Eigentümer, Rechte, Symlinkpfad und Speicher geprüft"
                )
                self._set_project_dependent(True)
            except BaseException as exc:
                self._error("Projektwahl blockiert", exc)

        def _progress(self, title: str, total: int = 0):
            dialog = QtWidgets.QProgressDialog(title, "Kontrolliert abbrechen", 0, max(total, 0), self)
            dialog.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
            dialog.setMinimumDuration(0)
            dialog.setAutoClose(False)

            def update(done: int, maximum: int, text: str) -> None:
                dialog.setMaximum(max(maximum, 1))
                dialog.setValue(done)
                dialog.setLabelText(f"{title}\n{text}")
                QtWidgets.QApplication.processEvents()

            return dialog, update

        def analyze(self) -> None:
            if self.project_root is None:
                self._error("Analyse blockiert", RuntimeError("Zuerst Projektordner wählen."))
                return
            try:
                dialog, update = self._progress("Bestand wird rein lesend analysiert")
                self.snapshot = analyze_project(
                    self.project_root,
                    progress=update,
                    should_cancel=dialog.wasCanceled,
                )
                dialog.close()
                self.duplicates = None
                self.analysis_summary.setPlainText(format_inventory_summary(self.snapshot))
                self._populate_inventory(self.snapshot.entries)
                self.project_status.setText(
                    f"GRÜN: {len(self.snapshot.files)} Dateien analysiert · keine Datei verändert"
                )
            except BaseException as exc:
                self._error("Analyse blockiert", exc)

        def _populate_inventory(self, entries) -> None:
            self.analysis_table.setSortingEnabled(False)
            self.analysis_table.setRowCount(0)
            self._analysis_paths = []
            for row, entry in enumerate(entries):
                self.analysis_table.insertRow(row)
                values = (
                    entry.entry_type,
                    entry.relative_path,
                    str(entry.size),
                    entry.category,
                    ", ".join(entry.flags),
                )
                for column, value in enumerate(values):
                    item = QtWidgets.QTableWidgetItem(value)
                    if column == 1:
                        item.setData(QtCore.Qt.ItemDataRole.UserRole, entry.relative_path)
                    self.analysis_table.setItem(row, column, item)
                self._analysis_paths.append(entry.relative_path)
            self.analysis_table.resizeColumnsToContents()
            self.analysis_table.setSortingEnabled(True)

        def _require_snapshot(self) -> InventorySnapshot:
            if self.snapshot is None:
                raise RuntimeError("Zuerst einen aktuellen Dateibestand analysieren.")
            return self.snapshot

        def find_duplicates(self) -> None:
            try:
                snapshot = self._require_snapshot()
                dialog, update = self._progress("SHA-256-Duplikatsuche")
                self.duplicates = find_duplicates(
                    snapshot,
                    progress=update,
                    should_cancel=dialog.wasCanceled,
                )
                dialog.close()
                self.analysis_summary.setPlainText(format_duplicate_summary(self.duplicates))
                rows: list[Any] = []
                for group_index, group in enumerate(self.duplicates.groups, start=1):
                    for path in group.relative_paths:
                        rows.append(
                            type(
                                "DuplicateRow",
                                (),
                                {
                                    "entry_type": f"Duplikat {group_index}",
                                    "relative_path": path,
                                    "size": group.size,
                                    "category": "SHA-256",
                                    "flags": (group.sha256,),
                                },
                            )()
                        )
                self._populate_inventory(rows)
                self.project_status.setText(
                    f"GRÜN: {len(self.duplicates.groups)} Duplikatgruppen gefunden · keine Löschung"
                )
            except BaseException as exc:
                self._error("Duplikatsuche blockiert", exc)

        def _selected_paths(self) -> list[str]:
            snapshot = self._require_snapshot()
            known = {entry.relative_path for entry in snapshot.files}
            if self.rename_scope.currentData() == "all":
                return sorted(known, key=str.casefold)
            selected: set[str] = set()
            for model_index in self.analysis_table.selectionModel().selectedRows():
                item = self.analysis_table.item(model_index.row(), 1)
                if item is None:
                    continue
                value = str(item.data(QtCore.Qt.ItemDataRole.UserRole) or item.text())
                if value in known:
                    selected.add(value)
            if not selected:
                raise RuntimeError("Mindestens eine analysierte Dateizeile markieren.")
            return sorted(selected, key=str.casefold)

        def preview_organization(self) -> None:
            try:
                plan = plan_organization(
                    self._require_snapshot(),
                    rule=str(self.organization_rule.currentData()),
                    destination_root="Sortiert",
                )
                self._show_plan(plan)
            except BaseException as exc:
                self._error("Sortier-Vorschau blockiert", exc)

        def preview_rename(self) -> None:
            try:
                rule = RenameRule(
                    prefix=self.rename_prefix.text(),
                    suffix=self.rename_suffix.text(),
                    search=self.rename_search.text(),
                    replacement=self.rename_replacement.text(),
                    case_mode=str(self.rename_case.currentData()),
                    add_number=self.rename_numbering.isChecked(),
                    number_start=self.rename_start.value(),
                    number_padding=self.rename_padding.value(),
                )
                plan = plan_mass_rename(self._require_snapshot(), self._selected_paths(), rule)
                self._show_plan(plan)
            except BaseException as exc:
                self._error("Umbenennungs-Vorschau blockiert", exc)

        def _show_plan(self, plan: OperationPlan) -> None:
            self.plan = plan
            self.plan_summary.setPlainText(format_operation_preview(plan))
            self.preview_table.setRowCount(0)
            for row, item in enumerate(plan.items):
                self.preview_table.insertRow(row)
                for column, value in enumerate(
                    (
                        "GEPRÜFT",
                        item.source_relative_path,
                        item.target_relative_path,
                        "Ziel frei · Fingerabdruck gebunden",
                    )
                ):
                    self.preview_table.setItem(row, column, QtWidgets.QTableWidgetItem(value))
            self.preview_table.resizeColumnsToContents()
            self.apply_button.setEnabled(True)
            self.undo_button.setEnabled(False)
            self.tabs.setCurrentWidget(self.plan_tab)
            self.project_status.setText(
                f"GELB: Vorschau für {len(plan.items)} Dateien · noch nichts verändert"
            )

        def apply_plan(self) -> None:
            if self.plan is None or self.project_root is None:
                self._error("Ausführung blockiert", RuntimeError("Zuerst eine produktive Vorschau erzeugen."))
                return
            summary = (
                f"Operation: {self.plan.operation}\n"
                f"Dateien: {len(self.plan.items)}\n"
                f"Planhash: {self.plan.plan_hash}\n\n"
                "Kein Ziel wird überschrieben. Den exakt angezeigten Plan jetzt ausführen?"
            )
            answer = QtWidgets.QMessageBox.question(
                self,
                "Produktive Dateiaktion bestätigen",
                summary,
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.No,
            )
            if answer != QtWidgets.QMessageBox.StandardButton.Yes:
                self.project_status.setText("GELB: Ausführung nicht bestätigt · Projekt unverändert")
                return
            try:
                dialog, update = self._progress("Geprüfter Plan wird ausgeführt", len(self.plan.items))
                self.last_result = execute_operation(
                    self.project_root,
                    self.plan,
                    progress=update,
                    should_cancel=dialog.wasCanceled,
                )
                dialog.close()
                self.project_status.setText(
                    f"GRÜN: {self.last_result.completed_count}/{self.last_result.total_count} · "
                    f"{self.last_result.state}"
                )
                self.apply_button.setEnabled(False)
                self.undo_button.setEnabled(self.last_result.changed)
                self.snapshot = None
            except BaseException as exc:
                self._error("Ausführung blockiert", exc)
                self.undo_button.setEnabled(True)

        def undo_last(self) -> None:
            operation_id = ""
            if self.last_result is not None:
                operation_id = self.last_result.operation_id
            elif self.plan is not None:
                operation_id = self.plan.operation_id
            if not operation_id or self.project_root is None:
                self._error("Rückgängig blockiert", RuntimeError("Keine produktive Operation vorhanden."))
                return
            answer = QtWidgets.QMessageBox.question(
                self,
                "Operation rückgängig",
                f"Operation {operation_id} rückwärts prüfen und vollständig zurückführen?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.No,
            )
            if answer != QtWidgets.QMessageBox.StandardButton.Yes:
                return
            try:
                self.last_result = undo_operation(self.project_root, operation_id)
                self.project_status.setText(f"GRÜN: {operation_id} vollständig rückgängig")
                self.undo_button.setEnabled(False)
                self.snapshot = None
            except BaseException as exc:
                self._error("Rückgängig blockiert", exc)

        def save_report(self) -> None:
            try:
                snapshot = self._require_snapshot()
                _json_path, markdown_path = write_analysis_report(snapshot, self.duplicates)
                self.project_status.setText(
                    f"GRÜN: Bericht gespeichert · {markdown_path.relative_to(snapshot.project.root)}"
                )
            except BaseException as exc:
                self._error("Bericht blockiert", exc)

        def show_section(self, section: str) -> None:
            mapping = {
                "analysis": self.analysis_tab,
                "duplicates": self.analysis_tab,
                "organize": self.organize_tab,
                "rename": self.rename_tab,
                "reports": self.analysis_tab,
                "plan": self.plan_tab,
            }
            self.tabs.setCurrentWidget(mapping.get(section, self.analysis_tab))

    return ProductiveWorkflowPanel(parent)
