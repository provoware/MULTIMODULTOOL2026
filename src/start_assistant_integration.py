"""Bind the P1-001 start assistant to the existing productive workflow panel."""
from __future__ import annotations

from types import MethodType

from .productive_integration import install_productive_ui
from .productive_workflow import plan_organization
from .start_assistant import (
    MODE_PRODUCTIVE,
    StartSelection,
    revalidate_start_selection,
    run_start_assistant,
)


def install_guided_productive_ui(QtWidgets, window):
    """Install the productive panel and gate it behind the validated start assistant."""

    panel = install_productive_ui(QtWidgets, window)
    if getattr(panel, "startAssistantInstalled", False):
        return panel

    panel.startAssistantInstalled = True
    panel.start_selection = None
    panel.target_root = None
    panel.target_relative = ""
    panel.safety_mode = ""

    original_analyze = panel.analyze
    original_show_plan = panel.show_plan
    original_execute = panel.execute
    original_undo = panel.undo_last
    original_report = panel.report

    def _disconnect_and_connect(button, slot) -> None:
        if button is None:
            return
        try:
            button.clicked.disconnect()
        except (RuntimeError, TypeError):
            pass
        button.clicked.connect(slot)

    def _button(name: str):
        return window.findChild(QtWidgets.QPushButton, name)

    def _require_selection(self) -> StartSelection:
        if self.start_selection is None:
            raise RuntimeError("Zuerst den geführten Startassistenten vollständig abschließen.")
        current = revalidate_start_selection(self.start_selection)
        self.start_selection = current
        self.target_root = current.target_root
        self.target_relative = current.target_relative
        self.safety_mode = current.safety_mode.key
        return current

    def _set_mode_gates(self) -> None:
        selection = self.start_selection
        enabled = selection is not None
        self.analyze_b.setEnabled(enabled)
        self.dup_b.setEnabled(enabled)
        self.org_b.setEnabled(enabled)
        self.ren_b.setEnabled(enabled)
        self.report_b.setEnabled(bool(selection and selection.allows_report))
        self.apply.setEnabled(False)
        self.undo.setEnabled(False)
        for name in ("analyzeProjectAction", "showPlanAction"):
            button = _button(name)
            if button is not None:
                button.setEnabled(enabled)
        report_action = _button("saveReportAction")
        if report_action is not None:
            report_action.setEnabled(bool(selection and selection.allows_report))
        execute_action = _button("executePlanAction")
        if execute_action is not None:
            execute_action.setEnabled(False)
        undo_action = _button("undoPlanAction")
        if undo_action is not None:
            undo_action.setEnabled(False)

    def apply_start_selection(self, selection: StartSelection) -> None:
        selection = revalidate_start_selection(selection)
        self.start_selection = selection
        self.root = selection.project.root
        self.target_root = selection.target_root
        self.target_relative = selection.target_relative
        self.safety_mode = selection.safety_mode.key
        self.snapshot = None
        self.duplicates = None
        self.plan = None
        self.result = None
        self.path.setText(f"{selection.project.root}  →  {selection.target_root}")
        self.summary.setPlainText(selection.summary)
        self.status.setText(
            f"GRÜN: Startfreigabe übernommen · {selection.safety_mode.label} · "
            f"Ziel {selection.target_relative}"
        )
        _set_mode_gates(self)
        window.startAssistantSelection = selection

    def guided_choose(self) -> None:
        current = self.start_selection
        dialog_selection = run_start_assistant(
            QtWidgets,
            self,
            initial_project=current.project.root if current else self.root,
            initial_target=current.target_root if current else self.target_root,
            initial_mode=current.safety_mode.key if current else MODE_PRODUCTIVE,
        )
        if dialog_selection is None:
            self.status.setText("GELB: Startassistent abgebrochen · bisherige Freigabe unverändert")
            return
        apply_start_selection(self, dialog_selection)

    def guided_analyze(self) -> None:
        try:
            _require_selection(self)
        except BaseException as exc:
            return self.error("Analyse blockiert", exc)
        original_analyze()

    def guided_show_plan(self, plan) -> None:
        try:
            selection = _require_selection(self)
        except BaseException as exc:
            return self.error("Vorschau blockiert", exc)
        original_show_plan(plan)
        write_allowed = selection.allows_write
        self.apply.setEnabled(write_allowed)
        execute_action = _button("executePlanAction")
        if execute_action is not None:
            execute_action.setEnabled(write_allowed)
        if write_allowed:
            self.status.setText(
                f"GELB: Vorschau für {len(plan.items)} Dateien · zweite Bestätigung erforderlich"
            )
        else:
            self.status.setText(
                f"GRÜN: Vorschau für {len(plan.items)} Dateien · "
                f"Modus {selection.safety_mode.label} sperrt die Ausführung"
            )

    def guided_preview_org(self) -> None:
        try:
            selection = _require_selection(self)
            plan = plan_organization(
                self.require_snapshot(),
                rule=str(self.org_rule.currentData()),
                destination_root=selection.target_relative,
            )
            guided_show_plan(self, plan)
        except BaseException as exc:
            self.error("Sortier-Vorschau blockiert", exc)

    def guided_execute(self) -> None:
        try:
            selection = _require_selection(self)
            if not selection.allows_write:
                raise RuntimeError(
                    f"Der Sicherheitsmodus {selection.safety_mode.label} erlaubt keine Dateiänderung."
                )
            if self.plan is None:
                raise RuntimeError("Zuerst eine vollständige Vorschau erzeugen.")
            if self.plan.operation == "organize":
                prefix = selection.target_relative.rstrip("/") + "/"
                if any(
                    item.target_relative_path != selection.target_relative
                    and not item.target_relative_path.startswith(prefix)
                    for item in self.plan.items
                ):
                    raise RuntimeError(
                        "Der Organisationsplan liegt nicht vollständig im bestätigten Zielordner."
                    )
        except BaseException as exc:
            return self.error("Ausführung blockiert", exc)
        original_execute()
        execute_action = _button("executePlanAction")
        undo_action = _button("undoPlanAction")
        if execute_action is not None:
            execute_action.setEnabled(False)
        if undo_action is not None:
            undo_action.setEnabled(bool(self.result and self.result.changed))

    def guided_undo(self) -> None:
        try:
            selection = _require_selection(self)
            if not selection.allows_write:
                raise RuntimeError(
                    f"Der Sicherheitsmodus {selection.safety_mode.label} erlaubt kein produktives Rückgängig."
                )
        except BaseException as exc:
            return self.error("Rückgängig blockiert", exc)
        original_undo()
        undo_action = _button("undoPlanAction")
        if undo_action is not None:
            undo_action.setEnabled(False)

    def guided_report(self) -> None:
        try:
            selection = _require_selection(self)
            if not selection.allows_report:
                raise RuntimeError(
                    f"Der Sicherheitsmodus {selection.safety_mode.label} erlaubt keinen Berichtsschreibzugriff."
                )
        except BaseException as exc:
            return self.error("Bericht blockiert", exc)
        original_report()

    panel.require_start_selection = MethodType(_require_selection, panel)
    panel.apply_start_selection = MethodType(apply_start_selection, panel)
    panel.choose_project = MethodType(guided_choose, panel)
    panel.analyze = MethodType(guided_analyze, panel)
    panel.show_plan = MethodType(guided_show_plan, panel)
    panel.preview_org = MethodType(guided_preview_org, panel)
    panel.execute = MethodType(guided_execute, panel)
    panel.undo_last = MethodType(guided_undo, panel)
    panel.report = MethodType(guided_report, panel)

    connection_map = (
        ("projectSelectButton", panel.choose_project),
        ("chooseProjectAction", panel.choose_project),
        ("analyzeProjectButton", panel.analyze),
        ("analyzeProjectAction", panel.analyze),
        ("previewOrganizationButton", panel.preview_org),
        ("applyProductivePlanButton", panel.execute),
        ("executePlanAction", panel.execute),
        ("undoProductiveOperationButton", panel.undo_last),
        ("undoPlanAction", panel.undo_last),
        ("saveAnalysisReportButton", panel.report),
        ("saveReportAction", panel.report),
    )
    for name, slot in connection_map:
        _disconnect_and_connect(_button(name), slot)

    for button in (_button("projectSelectButton"), _button("chooseProjectAction")):
        if button is not None:
            button.setText(
                "Startassistent öffnen …"
                if button.objectName() == "projectSelectButton"
                else "1\nStartassistent"
            )
            button.setToolTip(
                "Wählt Projektordner, getrennten Zielordner und Sicherheitsmodus; "
                "übernimmt erst nach vollständiger Vorvalidierung und Zusammenfassungsbestätigung."
            )
            button.setStatusTip(button.toolTip())
            button.setWhatsThis(button.toolTip())
            button.setAccessibleDescription(button.toolTip())

    _set_mode_gates(panel)
    panel.status.setText(
        "Projektstatus: Startassistent erforderlich · ohne bestätigte Zusammenfassung keine Freigabe"
    )
    panel.path.setPlaceholderText("Startassistent noch nicht abgeschlossen")
    window.startAssistantIntegrationInstalled = True
    return panel
