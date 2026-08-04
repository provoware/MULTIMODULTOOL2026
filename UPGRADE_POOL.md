# UPGRADE_POOL

Optionale Linux-Erweiterungen nach stabilem Kern:

| Idee | Nutzen | Risiko | Einordnung |
|---|---|---:|---|
| Prozessbasierte `SIGKILL`-/Neustartmatrix für Intent-Zustände | realistischere Crashabnahme | niedrig | geeignete Ergänzung vor P0-008-Abschluss |
| Read-only Paginierung für mehr als 1.000 Transaktionen | große Projekte übersichtlicher | niedrig | nach Journalrotation |
| Hashgesicherte Journalarchive mit fortlaufender Kettenwurzel | lange Historien | mittel | zusammen mit P3-003 entwickeln |
| Nutzerbestätigtes Verwerfen einer Redo-Kette mit Vorschau | neuer Verlaufzweig | mittel | erst nach eigenem unveränderlichen Branch-Ereignisvertrag |
| Signierter read-only Journal- und Manifestexport | bessere Supportdiagnose | mittel | erst mit Datenschutzvorschau und sicherem Dateidialog |
| Geführte alternative Restore-Auswahl bei fehlendem Elternordner | höhere Wiederherstellbarkeit | mittel | kein automatisches Neuanlegen |
| Linux-Mountinfo-Prüfung für eingebettete Mounts in Verzeichnisbäumen | schützt komplexe Ordneraktionen | mittel | vor produktiver Ordnerfreigabe |
| Vorschau für spätere Papierkorbleerung mit Aufbewahrungsfrist | kontrollierter Speicherabbau | hoch | erst nach Wiederanlauf, Versionierung und starker Bestätigung |
| ACL-/Gruppenprojektmodus | gemeinsame Projekte | hoch | getrennt entwickeln; Eigentümerprüfung nicht still lockern |
| KDE-DBus-Aktivierung zusätzlich zum Unix-Socket | bessere Desktopintegration | mittel | nach physischer X11/Wayland-Abnahme |
| systemd-user Socket-Aktivierung | robuster Lebenszyklus | hoch | nicht vor installierbarem Releasekandidaten |

Pflichtaufgaben zu Abbruch/Wiederanlauf, Loggingrotation und Release-Gate bleiben ausschließlich in `TODO.md`.
