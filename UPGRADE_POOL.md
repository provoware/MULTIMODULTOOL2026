# UPGRADE_POOL

Optionale Linux-Erweiterungen nach stabilem Kern:

| Idee | Nutzen | Risiko | Einordnung |
|---|---|---:|---|
| Read-only Transaktionsübersicht mit Filter nach ID, Zustand und Datum | schnellere Wiederherstellung | niedrig | nach P0-007 |
| Reconcile-Assistent für vollständigen Payload mit `prepared`-Manifest | bessere Crashdiagnose | mittel | erst nach Wiederanlaufvertrag P0-008 |
| Geführte alternative Restore-Auswahl bei fehlendem Elternordner | höhere Wiederherstellbarkeit | mittel | kein automatisches Neuanlegen |
| Linux-Mountinfo-Prüfung für eingebettete Mounts in Verzeichnisbäumen | schützt komplexe Ordneraktionen | mittel | vor produktiver Ordnerfreigabe |
| Vorschau für spätere Papierkorbleerung mit Aufbewahrungsfrist | kontrollierter Speicherabbau | hoch | erst nach Undo, Versionierung und starker Bestätigung |
| ACL-/Gruppenprojektmodus | gemeinsame Projekte | hoch | getrennt entwickeln; Eigentümerprüfung nicht still lockern |
| KDE-DBus-Aktivierung zusätzlich zum Unix-Socket | bessere Desktopintegration | mittel | nach physischer X11/Wayland-Abnahme |
| systemd-user Socket-Aktivierung | robuster Lebenszyklus | hoch | nicht vor installierbarem Releasekandidaten |
| Diagnose-Paginierung bei rotierten Journalen | bessere Langzeitsuche | niedrig | zusammen mit `P3-003` |

Pflichtaufgaben zu Undo/Redo, Wiederanlauf, Loggingrotation und Release-Gate bleiben ausschließlich in `TODO.md`.
