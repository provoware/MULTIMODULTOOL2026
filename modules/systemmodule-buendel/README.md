# Systemmodule-Bündel

Dieses Bündel beschreibt die vorhandenen Systemmodule als gemeinsame Übergangsgruppe. Es lädt noch keinen eigenen Code, weil die Anwendung aktuell bewusst als stabile Single-File-HTML-App läuft.

## Enthaltene Systembereiche

- Muttermodul: zentrale Hinweise, lokaler Updatecheck und Schnellzugriff.
- Registry: Übersicht über registrierte, aktive und platzierte Module.
- Debugging: lokale Fehler- und Diagnoseereignisse.
- Einstellungen: Verhalten, Darstellung, Autosave und Sicherung.
- Modul-Werkstatt: Erstellen und Bearbeiten eigener Module.

## Zweck

Das Bündel macht sichtbar, welche Teile später gemeinsam in echte Moduldateien ausgelagert werden können. Es ist damit eine kleine, sichere Vorstufe für den geplanten manifestbasierten Modul-Loader.

## Grenze

Die Datei `module.manifest.json` ist heute eine Beschreibung. Die eigentliche Laufzeitlogik bleibt in `dashboard-studio-ultimate-pro-v3.1.0.html`.
