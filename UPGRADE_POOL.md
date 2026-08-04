# UPGRADE_POOL

Optionale Linux-Erweiterungen nach stabilem Kern:

| Idee | Nutzen | Risiko | Einordnung |
|---|---|---:|---|
| Read-only Laufübersicht mit Zustand, Fortschritt und letzter Checkpointgeneration | schnelle Diagnose mehrerer Läufe | niedrig | nach geführter Projektauswahl |
| Segmentierte Laufpläne oberhalb von 1.000 Schritten | sehr große Bestände | mittel | erst nach Last- und Speicherprofilen |
| VM-Stromausfallmatrix mit erzwungenem Neustart | stärkere Persistenzabnahme | hoch | nach installierbarem Releasekandidaten |
| Reconcile-Assistent für widersprüchliche Laufzustände | bessere Crashdiagnose | hoch | zunächst nur Vorschau; keine Auto-Reparatur |
| Geführter Abschluss oder Archivierung alter Laufpläne | übersichtlicher Projektbereich | mittel | Aufbewahrungsvertrag erforderlich |
| Linux-Mountinfo-Prüfung für eingebettete Mounts | schützt komplexe Ordneraktionen | mittel | vor produktiver Ordnerfreigabe |
| ACL-/Gruppenprojektmodus | gemeinsame Projekte | hoch | getrennt entwickeln; Eigentümerprüfung nicht still lockern |
| KDE-DBus-Aktivierung zusätzlich zum Unix-Socket | bessere Desktopintegration | mittel | nach physischer X11/Wayland-Abnahme |
| Diagnose-Paginierung bei rotierten Journalen | bessere Langzeitsuche | niedrig | zusammen mit `P3-003` |

Pflichtaufgaben zu Release, Projektworkflow, Loggingrotation, Migration und Qualitätsgrenzen bleiben ausschließlich in `TODO.md`.

## Release-Erweiterungen nach P0-009

- signierte Release-Manifeste und Schlüsselrotation zusammen mit `P3-009`
- echte Kubuntu-VM-Matrix mit SDDM, KDE Plasma, X11 und Wayland
- delta-basierte Updates erst nach signierter Build-ID- und Dateimanifestprüfung
- optionaler read-only Release-Statusdialog mit Build-ID, Paketversion und Runtime-Slot
- langfristige Bereinigung nicht mehr benötigter Nutzer-Runtime-Slots nur nach Vorschau
