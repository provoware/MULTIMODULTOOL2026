# MULTIMODULTOOL2026

Lokales Dashboard-Werkzeug als Single-File-HTML-App.

## Start

Die Anwendung wird direkt im Browser geöffnet:

```text
dashboard-studio-ultimate-pro-v3.1.0.html
```

Es ist kein Build-Schritt und keine Installation nötig.

## Modulstrategie

Ja, Module können künftig separate Dateien sein. Die laufende Version bleibt zuerst als stabile Single-File-HTML-App bestehen. Neue oder ausgelagerte Module sollen nach dem Modulstandard beschrieben werden:

- Standard: `standards/MULTIMODULTOOL2026_01_Modulstandard.md`
- Manifest-Schema: `manifests/MULTIMODULTOOL2026_01_ModuleManifest.schema.json`
- App-Manifest: `manifests/MULTIMODULTOOL2026_02_AppManifest.json`
- Beispielmanifest: `manifests/MULTIMODULTOOL2026_03_ExampleModule.manifest.json`

## Warum zuerst Standards?

Ein direkter Umbau der großen HTML-Datei in viele Dateien kann funktionierende Bereiche beschädigen. Die Standards legen deshalb zuerst fest, wie Module sicher benannt, beschrieben, geprüft und später geladen werden.

## Nächster sinnvoller Schritt

Als nächste Iteration kann ein kleiner Modul-Loader geplant werden. Er sollte Manifeste lesen, Pflichtfelder prüfen und nur gültige Module in die Oberfläche aufnehmen.
