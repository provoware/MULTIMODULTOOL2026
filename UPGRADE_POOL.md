# UPGRADE_POOL

Optionale Linux-Erweiterungen nach stabilem Kern:

| Idee | Nutzen | Risiko | Einordnung |
|---|---|---:|---|
| KDE-DBus-Aktivierung zusätzlich zum Unix-Socket | bessere Desktopintegration | mittel | erst nach physischer X11/Wayland-Abnahme |
| systemd-user Socket-Aktivierung | robuster Lebenszyklus | hoch | nicht vor installierbarem Releasekandidaten |
| Diagnose-Paginierung bei rotierten Journalen | bessere Langzeitsuche | niedrig | zusammen mit `P3-003` |
| nutzerbestätigter Diagnoseexport | Supportfähigkeit | mittel | erst mit Datenschutzvorschau und sicherem Dateidialog |
| Desktop-Benachrichtigung bei Zweitstart | sichtbare Rückmeldung | niedrig | nach KDE-Abnahme |

Pflichtaufgaben zu Papierkorb, Undo, Wiederanlauf, Loggingrotation und Release-Gate bleiben in `TODO.md`.
