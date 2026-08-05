# UPGRADE_POOL

Dieser Pool enthält ausschließlich **optionale** Verbesserungen nach dem stabilen Kern. Verbindliche Aufgaben, Releaseblocker und bereits nummerierte Arbeitspakete stehen nur in [`TODO.md`](TODO.md) und werden hier nicht wiederholt.

| Optionale Idee | Nutzen | Risiko | Frühester sinnvoller Zeitpunkt |
|---|---|---:|---|
| Read-only Laufübersicht mit Zustand, Fortschritt und letzter Checkpointgeneration | schnelle Diagnose mehrerer Läufe | niedrig | nach geführter Projektauswahl |
| Segmentierte Laufpläne oberhalb von 1.000 Schritten | sehr große Bestände | mittel | nach Last- und Speicherprofilen |
| Reconcile-Assistent für widersprüchliche Laufzustände | verständlichere Crashdiagnose | hoch | zunächst ausschließlich Vorschau |
| Geführte Archivierung alter abgeschlossener Laufpläne | übersichtlicher Projektbereich | mittel | nach eigenem Aufbewahrungsvertrag |
| ACL-/Gruppenprojektmodus | gemeinsame Linux-Projekte | hoch | getrennt von der Eigentümerprüfung entwickeln |
| KDE-DBus-Aktivierung zusätzlich zum Unix-Socket | bessere Desktopintegration | mittel | nach physischer X11-/Wayland-Abnahme |
| Read-only Release-Statusdialog mit Build-ID, Paketversion und Runtime-Slot | schneller lokaler Support | niedrig | nach signiertem Release-Gate |
| Vorschau für nicht mehr benötigte Runtime-Slots | kontrollierte Speicherbereinigung | mittel | erst nach Migrations- und Rollbackvertrag |
| Diagnose-Paginierung über rotierte Journale | bessere Langzeitsuche | niedrig | nach implementierter Journalrotation |

## Nicht in diesem Pool

Die folgenden Punkte sind Pflichtaufgaben und bleiben deshalb ausschließlich in `TODO.md`:

- Mountprüfung vor produktiver Ordnerfreigabe
- Journalrotation und Migration
- Testabdeckung und statische Qualitätsgrenzen
- signierte Release-Manifeste und Vertrauenskette
- physische Kubuntu-/KDE-/X11-/Wayland-Abnahme
- portable Ausgabe, Medienvorschau und Plugin-Sandbox
