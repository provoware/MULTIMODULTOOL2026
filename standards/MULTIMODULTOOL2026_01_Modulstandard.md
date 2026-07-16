# MULTIMODULTOOL2026 Modulstandard

Stand: 2026-07-16

## Grundsatz

Ja, Module dürfen und sollen langfristig separate Dateien sein. Die bestehende HTML-Datei bleibt aktuell lauffähig. Neue oder ausgelagerte Module müssen zuerst über ein Manifest beschrieben werden, damit Name, Typ, Version, Datenbedarf und Sicherheitsgrenzen klar sind.

## Ziel

Der Standard sorgt dafür, dass Module klein, prüfbar und austauschbar bleiben. Ein Modul soll genau eine fachliche Aufgabe erfüllen und keine versteckten Nebenwirkungen haben.

## Empfohlene Modulstruktur

```text
modules/
└── beispiel-modul/
    ├── module.manifest.json
    ├── module.html
    ├── module.css
    ├── module.js
    └── README.md
```

Für kleine Module dürfen `module.html`, `module.css` oder `module.js` entfallen, wenn sie nicht benötigt werden. Das Manifest bleibt Pflicht.

## Pflichtregeln für Module

- Jedes Modul hat ein eigenes `module.manifest.json`.
- Jedes Modul hat eine eindeutige `id` im Format `kleinbuchstaben-mit-bindestrich`.
- Jedes Modul benennt seine `version` nach SemVer, zum Beispiel `1.0.0`.
- Jedes Modul benennt seinen `type`, passend zu den erlaubten Dashboard-Typen.
- Jedes Modul beschreibt seine Aufgabe in einfacher Sprache.
- Jedes Modul speichert Daten nur in seinem eigenen Datenbereich.
- Riskante Aktionen brauchen eine sichtbare Bestätigung.
- Importierte Daten müssen geprüft werden, bevor sie gespeichert werden.
- Fehler müssen sagen: was passiert ist, warum es passiert ist und was der Nutzer tun kann.

## Größenrichtwerte

- Hilfsdateien: möglichst bis 150 Zeilen.
- Normale Moduldateien: möglichst bis 300 Zeilen.
- Kernmodule: möglichst bis 500 Zeilen.
- Funktionen: möglichst bis 40 Zeilen, ab 60 Zeilen Teilung prüfen.

## Manifest-Pflichtfelder

- `id`: eindeutige Modulkennung.
- `name`: sichtbarer Modulname.
- `version`: Modulversion.
- `type`: fachlicher Modultyp.
- `description`: kurze Erklärung für Nutzer.
- `entry`: Einstiegspunkte des Moduls.
- `permissions`: benötigte Fähigkeiten.
- `storage`: Speicherregeln.
- `validation`: Validierungsregeln.

## Erlaubte Berechtigungen

- `local-storage`: darf im lokalen Browser-Speicher lesen und schreiben.
- `file-export`: darf Dateien für den Download erzeugen.
- `file-import`: darf Nutzerdateien einlesen, wenn der Nutzer sie auswählt.
- `timer`: darf zeitbasierte Abläufe verwenden.
- `none`: keine besondere Berechtigung.

## Bewusste Grenze

Dieser Standard aktiviert noch keinen dynamischen Modul-Loader. Er definiert die sichere Grundlage dafür, Module später aus separaten Dateien zu laden.
