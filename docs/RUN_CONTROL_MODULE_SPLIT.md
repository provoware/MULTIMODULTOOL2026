# Abgesicherte Modultrennung der Laufsteuerung (Ausführung unverändert)

Ergänzung zum [Refactoring-Plan](RUN_CONTROL_REFACTOR_PLAN.md). Diese Iteration ist ein **reiner Strukturumbau**.

- `src/run_control_models.py`: bisherige unveränderliche Datenklassen, Lauf-ID-Muster, Zustands-/Schema-Konstanten.
- `src/run_control_validation.py`: Prüfung von Laufplänen, Checkpoints und relativen Pfaden sowie kanonischer Hash und kontrollierte Fehlermeldungen.
- `src/run_control.py`: bleibt der bisherige Einstieg mit **denselben importierbaren Klassen und Funktionen** und enthält weiter Dateischutz, Abbruchsignale, Journal-/Papierkorb-Operationen und Wiederanlauf.

**Nicht verändert:** Dateiformate, JSON-Schlüssel, Schema 1, Passwort-/Dateischutz, 0700-/0600-Rechte, Protokollierung, `flock`, SIGKILL-Wiederaufnahme und alle produktiven Ausführungsfunktionen. Die Klassen liegen intern in einem anderen Python-Modul; ob Drittanbieter deren exakte `__module__`-Eigenschaft oder alte Pickle-Daten voraussetzen, ist nicht gesondert belegt. Eine solche Migration wird hier **nicht** zugesagt.

**Pflichttests vor Übernahme:** neuer `test_run_control_module_split.py` (API-Identität, JSON-Schlüssel und Negativdaten), Sicherheitsbaseline `test_run_control_refactor_contract.py`, gesamter Repository-Vertrag inklusive SIGKILL-Matrix und Linux Release Candidate. Praktischer Kubuntu-Desktop-Test bleibt für die spätere Release-Abnahme getrennt.

**PR-Abhängigkeit:** Zuerst das Sicherheitsbaseline-PR #107 zusammenführen; danach diesen gestapelten PR gegen den aktuellen Hauptzweig erneut prüfen.
