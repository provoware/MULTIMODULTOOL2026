"""Install the productive preview-first workflow into the existing nine-zone GUI."""
from __future__ import annotations

from pathlib import Path

from .productive_workflow import (
    RenameRule, analyze_project, execute_operation, find_duplicates,
    format_duplicate_summary, format_inventory_summary, format_operation_preview,
    format_project_safety, plan_mass_rename, plan_organization, undo_operation,
    validate_project_root, write_analysis_report,
)


def install_productive_ui(QtWidgets, window):
    """Attach productive controls once; construction performs no filesystem access."""
    if getattr(window, "productiveWorkflowPanel", None) is not None:
        return window.productiveWorkflowPanel
    from PySide6 import QtCore

    class Panel(QtWidgets.QFrame):
        def __init__(self):
            super().__init__()
            self.setObjectName("productiveWorkflowPanel")
            self.root = None
            self.snapshot = None
            self.duplicates = None
            self.plan = None
            self.result = None
            self._build()
            self._state(False)

        def button(self, text, name, tip):
            button = QtWidgets.QPushButton(text)
            button.setObjectName(name)
            button.setMinimumHeight(42)
            button.setToolTip(tip)
            button.setStatusTip(tip)
            button.setWhatsThis(tip)
            button.setAccessibleDescription(tip)
            return button

        def _build(self):
            outer = QtWidgets.QVBoxLayout(self)
            title = QtWidgets.QLabel("Produktiver Projektworkflow")
            title.setObjectName("sectionTitle")
            outer.addWidget(title)
            info = QtWidgets.QLabel("Projekt wählen → read-only analysieren → vollständige Vorschau prüfen → ausdrücklich bestätigen. Kein stilles Überschreiben.")
            info.setWordWrap(True)
            info.setProperty("safetyStatus", True)
            outer.addWidget(info)
            row = QtWidgets.QHBoxLayout()
            self.path = QtWidgets.QLineEdit()
            self.path.setObjectName("projectPathField")
            self.path.setReadOnly(True)
            self.path.setPlaceholderText("Noch kein Projektordner gewählt")
            row.addWidget(self.path, 1)
            self.choose = self.button("Projektordner wählen …", "projectSelectButton", "Prüft Eigentümer, Rechte, Symlinks, Mountgrenzen und freien Speicher.")
            self.choose.clicked.connect(self.choose_project)
            row.addWidget(self.choose)
            outer.addLayout(row)
            self.status = QtWidgets.QLabel("Projektstatus: Auswahl erforderlich")
            self.status.setObjectName("projectValidationStatus")
            self.status.setWordWrap(True)
            self.status.setProperty("safetyStatus", True)
            outer.addWidget(self.status)
            self.tabs = QtWidgets.QTabWidget()
            self.tabs.setObjectName("productiveTabs")
            outer.addWidget(self.tabs, 1)

            analysis = QtWidgets.QWidget()
            analysis_layout = QtWidgets.QVBoxLayout(analysis)
            analysis_actions = QtWidgets.QHBoxLayout()
            self.analyze_b = self.button("Bestand analysieren", "analyzeProjectButton", "Liest Bestand und Namenshinweise; verändert keine Datei.")
            self.analyze_b.clicked.connect(self.analyze)
            analysis_actions.addWidget(self.analyze_b)
            self.dup_b = self.button("Duplikate per SHA-256", "findDuplicatesButton", "Hasht nur reguläre größenidentische Dateien; keine Löschung.")
            self.dup_b.clicked.connect(self.find_dups)
            analysis_actions.addWidget(self.dup_b)
            self.report_b = self.button("JSON/Markdown-Bericht", "saveAnalysisReportButton", "Speichert private Berichte mit projekt-relativen Pfaden.")
            self.report_b.clicked.connect(self.report)
            analysis_actions.addWidget(self.report_b)
            analysis_layout.addLayout(analysis_actions)
            self.summary = QtWidgets.QPlainTextEdit()
            self.summary.setObjectName("analysisSummary")
            self.summary.setReadOnly(True)
            self.summary.setMaximumHeight(140)
            analysis_layout.addWidget(self.summary)
            self.table = QtWidgets.QTableWidget(0, 5)
            self.table.setObjectName("analysisTable")
            self.table.setHorizontalHeaderLabels(("Typ", "Projektpfad", "Größe", "Kategorie", "Hinweise"))
            self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
            self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
            self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
            self.table.horizontalHeader().setStretchLastSection(True)
            analysis_layout.addWidget(self.table, 1)
            self.tabs.addTab(analysis, "Analyse & Duplikate")
            self.analysis_tab = analysis

            organize = QtWidgets.QWidget()
            organize_layout = QtWidgets.QVBoxLayout(organize)
            form = QtWidgets.QFormLayout()
            self.org_rule = QtWidgets.QComboBox()
            self.org_rule.setObjectName("organizationRuleCombo")
            self.org_rule.addItem("Nach Dateityp", "category")
            self.org_rule.addItem("Nach Dateiendung", "extension")
            self.org_rule.addItem("Nach Änderungsjahr", "year")
            form.addRow("Sortierregel:", self.org_rule)
            organize_layout.addLayout(form)
            self.org_b = self.button("Sortier-Vorschau erzeugen", "previewOrganizationButton", "Erzeugt Vorher/Nachher-Pfade unter Sortiert; jeder Konflikt blockiert den Plan.")
            self.org_b.clicked.connect(self.preview_org)
            organize_layout.addWidget(self.org_b)
            organize_layout.addStretch(1)
            self.tabs.addTab(organize, "Organisieren")
            self.org_tab = organize

            rename = QtWidgets.QWidget()
            rename_layout = QtWidgets.QVBoxLayout(rename)
            rename_form = QtWidgets.QFormLayout()
            self.scope = QtWidgets.QComboBox()
            self.scope.setObjectName("renameScopeCombo")
            self.scope.addItem("Nur markierte Dateien", "selected")
            self.scope.addItem("Alle analysierten Dateien", "all")
            rename_form.addRow("Umfang:", self.scope)
            self.prefix = QtWidgets.QLineEdit()
            self.prefix.setObjectName("renamePrefixField")
            rename_form.addRow("Präfix:", self.prefix)
            self.suffix = QtWidgets.QLineEdit()
            self.suffix.setObjectName("renameSuffixField")
            rename_form.addRow("Suffix:", self.suffix)
            self.search = QtWidgets.QLineEdit()
            self.search.setObjectName("renameSearchField")
            rename_form.addRow("Suchen:", self.search)
            self.replacement = QtWidgets.QLineEdit()
            self.replacement.setObjectName("renameReplacementField")
            rename_form.addRow("Ersetzen:", self.replacement)
            self.case = QtWidgets.QComboBox()
            self.case.setObjectName("renameCaseCombo")
            self.case.addItem("Beibehalten", "keep")
            self.case.addItem("klein", "lower")
            self.case.addItem("GROSS", "upper")
            rename_form.addRow("Schreibweise:", self.case)
            self.number = QtWidgets.QCheckBox("Nummer ergänzen")
            self.number.setObjectName("renameNumberingCheck")
            self.start = QtWidgets.QSpinBox()
            self.start.setObjectName("renameNumberStart")
            self.start.setRange(0, 999999999)
            self.start.setValue(1)
            self.padding = QtWidgets.QSpinBox()
            self.padding.setObjectName("renameNumberPadding")
            self.padding.setRange(1, 9)
            self.padding.setValue(3)
            numbering = QtWidgets.QWidget()
            numbering_layout = QtWidgets.QHBoxLayout(numbering)
            numbering_layout.setContentsMargins(0, 0, 0, 0)
            numbering_layout.addWidget(self.number)
            numbering_layout.addWidget(self.start)
            numbering_layout.addWidget(self.padding)
            rename_form.addRow("Nummerierung:", numbering)
            rename_layout.addLayout(rename_form)
            self.ren_b = self.button("Umbenennungs-Vorschau erzeugen", "previewRenameButton", "Blockiert leere, doppelte, zu lange oder bereits belegte Zielnamen.")
            self.ren_b.clicked.connect(self.preview_rename)
            rename_layout.addWidget(self.ren_b)
            rename_layout.addStretch(1)
            self.tabs.addTab(rename, "Massenumbenennen")
            self.ren_tab = rename

            plan = QtWidgets.QWidget()
            plan_layout = QtWidgets.QVBoxLayout(plan)
            self.plan_text = QtWidgets.QPlainTextEdit()
            self.plan_text.setObjectName("operationPlanSummary")
            self.plan_text.setReadOnly(True)
            self.plan_text.setMaximumHeight(135)
            plan_layout.addWidget(self.plan_text)
            self.preview = QtWidgets.QTableWidget(0, 4)
            self.preview.setObjectName("productivePreviewTable")
            self.preview.setHorizontalHeaderLabels(("Status", "Vorher", "Nachher", "Prüfung"))
            self.preview.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
            self.preview.horizontalHeader().setStretchLastSection(True)
            plan_layout.addWidget(self.preview, 1)
            plan_actions = QtWidgets.QHBoxLayout()
            self.apply = self.button("Geprüften Plan ausführen …", "applyProductivePlanButton", "Benötigt zweite Bestätigung; jeder Schritt erhält privaten Checkpoint.")
            self.apply.clicked.connect(self.execute)
            plan_actions.addWidget(self.apply)
            self.undo = self.button("Letzte Operation rückgängig …", "undoProductiveOperationButton", "Führt nur unveränderte Zieldateien an freie Originalpfade zurück.")
            self.undo.clicked.connect(self.undo_last)
            plan_actions.addWidget(self.undo)
            plan_layout.addLayout(plan_actions)
            self.tabs.addTab(plan, "Vorschau & Ausführung")
            self.plan_tab = plan

        def _state(self, enabled):
            for widget in (self.analyze_b, self.dup_b, self.report_b, self.org_b, self.ren_b):
                widget.setEnabled(enabled)
            self.apply.setEnabled(False)
            self.undo.setEnabled(False)

        def error(self, title, exc):
            cause = getattr(exc, "cause", str(exc))
            QtWidgets.QMessageBox.critical(self, title, cause)
            self.status.setText(f"ROT: {cause}")

        def choose_project(self):
            path = QtWidgets.QFileDialog.getExistingDirectory(self, "Sicheren Projektordner wählen", str(Path.home()), QtWidgets.QFileDialog.Option.ShowDirsOnly)
            if not path:
                return
            try:
                project = validate_project_root(Path(path))
                self.root = project.root
                self.snapshot = self.duplicates = self.plan = self.result = None
                self.path.setText(str(project.root))
                self.summary.setPlainText(format_project_safety(project))
                self.status.setText("GRÜN: Projektgrenze geprüft · Analyse freigegeben")
                self._state(True)
            except BaseException as exc:
                self.error("Projektwahl blockiert", exc)

        def progress(self, title, total=0):
            dialog = QtWidgets.QProgressDialog(title, "Kontrolliert abbrechen", 0, max(total, 0), self)
            dialog.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
            dialog.setMinimumDuration(0)

            def update(done, maximum, text):
                dialog.setMaximum(max(maximum, 1))
                dialog.setValue(done)
                dialog.setLabelText(f"{title}\n{text}")
                QtWidgets.QApplication.processEvents()

            return dialog, update

        def analyze(self):
            if not self.root:
                return self.error("Analyse blockiert", RuntimeError("Zuerst Projektordner wählen."))
            try:
                dialog, update = self.progress("Bestand wird rein lesend analysiert")
                self.snapshot = analyze_project(self.root, progress=update, should_cancel=dialog.wasCanceled)
                dialog.close()
                self.duplicates = None
                self.summary.setPlainText(format_inventory_summary(self.snapshot))
                self.populate(self.snapshot.entries)
                self.status.setText(f"GRÜN: {len(self.snapshot.files)} Dateien analysiert")
            except BaseException as exc:
                self.error("Analyse blockiert", exc)

        def populate(self, entries):
            self.table.setRowCount(0)
            for row, entry in enumerate(entries):
                self.table.insertRow(row)
                for column, value in enumerate((entry.entry_type, entry.relative_path, str(entry.size), entry.category, ", ".join(entry.flags))):
                    item = QtWidgets.QTableWidgetItem(value)
                    self.table.setItem(row, column, item)
                    if column == 1:
                        item.setData(QtCore.Qt.ItemDataRole.UserRole, entry.relative_path)
            self.table.resizeColumnsToContents()

        def require_snapshot(self):
            if self.snapshot is None:
                raise RuntimeError("Zuerst aktuellen Bestand analysieren.")
            return self.snapshot

        def find_dups(self):
            try:
                snapshot = self.require_snapshot()
                dialog, update = self.progress("SHA-256-Duplikatsuche")
                self.duplicates = find_duplicates(snapshot, progress=update, should_cancel=dialog.wasCanceled)
                dialog.close()
                self.summary.setPlainText(format_duplicate_summary(self.duplicates))
                rows = []
                for index, group in enumerate(self.duplicates.groups, 1):
                    for path in group.relative_paths:
                        rows.append(type("Row", (), {"entry_type": f"Duplikat {index}", "relative_path": path, "size": group.size, "category": "SHA-256", "flags": (group.sha256,)})())
                self.populate(rows)
                self.status.setText(f"GRÜN: {len(self.duplicates.groups)} Gruppen · keine Löschung")
            except BaseException as exc:
                self.error("Duplikatsuche blockiert", exc)

        def selected(self):
            snapshot = self.require_snapshot()
            known = {entry.relative_path for entry in snapshot.files}
            if self.scope.currentData() == "all":
                return sorted(known, key=str.casefold)
            values = set()
            for index in self.table.selectionModel().selectedRows():
                item = self.table.item(index.row(), 1)
                if item:
                    value = str(item.data(QtCore.Qt.ItemDataRole.UserRole) or item.text())
                    if value in known:
                        values.add(value)
            if not values:
                raise RuntimeError("Mindestens eine analysierte Dateizeile markieren.")
            return sorted(values, key=str.casefold)

        def preview_org(self):
            try:
                self.show_plan(plan_organization(self.require_snapshot(), rule=str(self.org_rule.currentData())))
            except BaseException as exc:
                self.error("Sortier-Vorschau blockiert", exc)

        def preview_rename(self):
            try:
                rule = RenameRule(self.prefix.text(), self.suffix.text(), self.search.text(), self.replacement.text(), str(self.case.currentData()), self.number.isChecked(), self.start.value(), self.padding.value())
                self.show_plan(plan_mass_rename(self.require_snapshot(), self.selected(), rule))
            except BaseException as exc:
                self.error("Umbenennungs-Vorschau blockiert", exc)

        def show_plan(self, plan):
            self.plan = plan
            self.plan_text.setPlainText(format_operation_preview(plan))
            self.preview.setRowCount(0)
            for row, item in enumerate(plan.items):
                self.preview.insertRow(row)
                for column, value in enumerate(("GEPRÜFT", item.source_relative_path, item.target_relative_path, "Ziel frei · Fingerabdruck gebunden")):
                    self.preview.setItem(row, column, QtWidgets.QTableWidgetItem(value))
            self.apply.setEnabled(True)
            self.undo.setEnabled(False)
            self.tabs.setCurrentWidget(self.plan_tab)
            self.status.setText(f"GELB: Vorschau für {len(plan.items)} Dateien · noch nichts verändert")

        def execute(self):
            if not self.plan or not self.root:
                return self.error("Ausführung blockiert", RuntimeError("Zuerst Vorschau erzeugen."))
            text = f"{len(self.plan.items)} Dateien · Planhash {self.plan.plan_hash}\nKein Ziel wird überschrieben. Exakten Plan ausführen?"
            answer = QtWidgets.QMessageBox.question(self, "Produktive Dateiaktion bestätigen", text, QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No, QtWidgets.QMessageBox.StandardButton.No)
            if answer != QtWidgets.QMessageBox.StandardButton.Yes:
                return
            try:
                dialog, update = self.progress("Geprüfter Plan wird ausgeführt", len(self.plan.items))
                self.result = execute_operation(self.root, self.plan, progress=update, should_cancel=dialog.wasCanceled)
                dialog.close()
                self.status.setText(f"GRÜN: {self.result.completed_count}/{self.result.total_count} · {self.result.state}")
                self.apply.setEnabled(False)
                self.undo.setEnabled(self.result.changed)
                self.snapshot = None
            except BaseException as exc:
                self.error("Ausführung blockiert", exc)
                self.undo.setEnabled(True)

        def undo_last(self):
            operation_id = self.result.operation_id if self.result else self.plan.operation_id if self.plan else ""
            if not operation_id or not self.root:
                return self.error("Rückgängig blockiert", RuntimeError("Keine Operation vorhanden."))
            answer = QtWidgets.QMessageBox.question(self, "Operation rückgängig", f"Operation {operation_id} rückwärts prüfen und zurückführen?", QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No, QtWidgets.QMessageBox.StandardButton.No)
            if answer != QtWidgets.QMessageBox.StandardButton.Yes:
                return
            try:
                self.result = undo_operation(self.root, operation_id)
                self.status.setText(f"GRÜN: {operation_id} rückgängig")
                self.undo.setEnabled(False)
                self.snapshot = None
            except BaseException as exc:
                self.error("Rückgängig blockiert", exc)

        def report(self):
            try:
                snapshot = self.require_snapshot()
                _, markdown = write_analysis_report(snapshot, self.duplicates)
                self.status.setText(f"GRÜN: Bericht gespeichert · {markdown.relative_to(snapshot.project.root)}")
            except BaseException as exc:
                self.error("Bericht blockiert", exc)

        def show_section(self, section):
            self.tabs.setCurrentWidget({"analysis": self.analysis_tab, "duplicates": self.analysis_tab, "organize": self.org_tab, "rename": self.ren_tab, "reports": self.analysis_tab, "plan": self.plan_tab}.get(section, self.analysis_tab))

    panel = Panel()
    scroll = window.findChild(QtWidgets.QScrollArea, "workspaceScroll")
    workspace = scroll.widget() if scroll else None
    if workspace and workspace.layout():
        workspace.layout().insertWidget(1, panel, 2)

    navigation = window.findChildren(QtWidgets.QPushButton, "lockedNavigation")
    navigation_definitions = (("⌕  Analysieren", "analysisNavigation", "analysis"), ("▣  Duplikate", "duplicatesNavigation", "duplicates"), ("↕  Organisieren", "organizeNavigation", "organize"), ("✎  Umbenennen", "renameNavigation", "rename"), ("▤  Berichte", "reportsNavigation", "reports"))
    for button, (text, name, section) in zip(navigation, navigation_definitions):
        button.setText(text)
        button.setObjectName(name)
        button.setEnabled(True)
        button.setToolTip(f"Öffnet {text[3:]} im produktiven Vorschau-Workflow.")
        button.clicked.connect(lambda checked=False, selected=section: panel.show_section(selected))

    actions = window.findChildren(QtWidgets.QPushButton, "lockedPrimaryAction")
    action_definitions = (("1\nProjekt wählen", "chooseProjectAction", panel.choose_project), ("2\nAnalysieren", "analyzeProjectAction", panel.analyze), ("3\nVorschau", "showPlanAction", lambda: panel.show_section("plan")), ("4\nBestätigt ausführen", "executePlanAction", panel.execute), ("5\nRückgängig", "undoPlanAction", panel.undo_last), ("6\nBericht", "saveReportAction", panel.report))
    for button, (text, name, slot) in zip(actions, action_definitions):
        button.setText(text)
        button.setObjectName(name)
        button.setEnabled(True)
        button.setToolTip("Produktiver Schritt mit Vorvalidierung, klarer Bestätigung und Nachprüfung.")
        button.clicked.connect(slot)

    window.productiveWorkflowPanel = panel
    return panel
