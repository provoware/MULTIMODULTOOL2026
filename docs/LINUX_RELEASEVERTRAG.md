# Linux-Releasevertrag – MULTIMODULTOOL2026

## Ziel

Der Releasekandidat wird als installierbares Debian-Paket für Kubuntu 22.04 und Kubuntu 24.04 auf x86-64 bereitgestellt. Installation, erster Start, Upgrade, Rollback, normale Entfernung und ausdrücklich bestätigte vollständige Entfernung müssen automatisiert und ohne versteckte Cloud-Abhängigkeit geprüft werden.

Ein Artefakt gilt erst dann als **releasefertig**, wenn beide Kubuntu-Lebenszyklen erfolgreich abgeschlossen wurden. Erst danach erzeugt der Finalisierungsschritt Dateien mit dem Namenszusatz `_save_`.

## Paketformat und Systempfade

```text
/usr/bin/multimodultool2026
/usr/sbin/multimodultool2026-release-manager
/usr/lib/multimodultool2026/
├── app/
├── wheelhouse/
├── BUILD_INFO.json
├── SOURCE_MANIFEST.json
├── FILE_MANIFEST.sha256
└── requirements.lock
/usr/share/applications/multimodultool2026.desktop
```

- Paketname: `multimodultool2026`
- Architektur: `amd64`
- Zielsysteme: Kubuntu 22.04 und Kubuntu 24.04
- Python: mindestens 3.10
- GUI-Runtime: lokal gebündelte, SHA-256-geprüfte PySide6-Wheels
- Netzwerkzugriff beim ersten Start: nicht erforderlich

## Build-ID

Jeder Build besitzt eine eindeutige Kennung:

```text
MMTBUILD-<VERSION>-<16 HEX AUS SHA-256>
```

Die Build-ID entsteht aus Paketversion, sortierter Runtime-Dateiliste sowie SHA-256 aller Runtime-Dateien und gebündelten Wheels. `BUILD_INFO.json` enthält Version, Architektur, Build-ID, Source-Manifest-Hash, reproduzierbaren Zeitstempel, Python-Mindestversion und PySide6-Version.

## Reproduzierbare Dateiliste

Nur Pfade aus `release/package-files.txt` werden übernommen. Verzeichnisse werden sortiert rekursiv expandiert. Symlinks, fehlende Einträge, Pfadüberschreitungen und Duplikate blockieren den Build.

Das Paket enthält:

- `SOURCE_MANIFEST.json` für die Buildquellen,
- `FILE_MANIFEST.sha256` für installierte Dateien,
- `WHEELHOUSE.sha256` für die Offline-Runtime.

Zwei Builds mit identischen Eingaben und gleichem `SOURCE_DATE_EPOCH` müssen byteidentische `.deb`- und `.tar.gz`-Artefakte erzeugen.

## Abhängigkeitsprüfung

Vor Installation werden Linux und x86-64, Paketname, Architektur, Paket-SHA-256, Build-ID, Paketversion, `dpkg-deb`, `apt-get`, Python 3.10+ und die deklarierten Qt-/KDE-Abhängigkeiten geprüft. Nach Installation validiert `postinst` die vollständige installierte Dateiliste und Python-Mindestversion.

## Offline-Erststart

Der Starter legt pro Build-ID eine private Nutzer-Runtime an:

```text
$XDG_DATA_HOME/multimodultool2026/runtime/venv-<BUILD-ID>/
```

Ablauf:

1. installierte Dateien per SHA-256 prüfen,
2. private Runtime-Sperre erwerben,
3. temporäre Python-venv anlegen,
4. PySide6 ausschließlich aus dem lokalen Wheelhouse installieren,
5. Importtest durchführen,
6. Build-ID-Marker schreiben,
7. Runtime atomar aktivieren,
8. Anwendung mit installiertem Quellbaum starten.

Unterschiedliche Build-IDs verwenden getrennte Runtime-Slots. Dadurch kann ein Rollback ohne Überschreiben der vorherigen Runtime erfolgen. Ein beschädigter Slot wird unter Sperre isoliert und vollständig neu aufgebaut.

## Installation und Upgrade

`release-manager.sh` akzeptiert Änderungen nur mit `--yes`.

- Paket und dateinamengebundenes Sidecar werden vorab geprüft.
- Das Paket wird privat unter `/var/lib/multimodultool2026/packages/` archiviert.
- Aktueller und vorheriger Stand werden atomar in privaten Statusdateien dokumentiert.
- `apt-get install` löst nur deklarierte Systemabhängigkeiten auf.
- Nach Installation muss `multimodultool2026 --verify-installation` grün sein.

## Rollback

Rollback verwendet ausschließlich das zuvor geprüfte lokale Paketarchiv. Ein fehlendes, verändertes oder nicht verifizierbares Archiv blockiert den Rollback. Der Manager prüft Paket und SHA-256 erneut, erlaubt den notwendigen Downgrade ausdrücklich, validiert Build-ID und Dateimanifest und tauscht Statusdateien atomar.

## Deinstallation

### Normale Entfernung

- entfernt alle paketverwalteten Systemdateien,
- bewahrt XDG-Nutzerdaten und lokale Runtime-Slots,
- bewahrt das lokale Rollbackarchiv.

### Vollständige bestätigte Entfernung

```bash
sudo ./release-manager.sh uninstall \
  --purge-system-state \
  --purge-current-user-data \
  --yes
```

Zusätzlich entfernt werden `/var/lib/multimodultool2026`, ausschließlich die bekannten XDG-Verzeichnisse des ausdrücklich bestimmten Nicht-root-Nutzers und dessen privater Runtime-Pfad. Symlinks, fremde Home-Pfade und unklare Nutzerzuordnung blockieren den Nutzerdaten-Purge.

## Kubuntu-Matrix

Die CI erzeugt zwei frische Container auf Basis von Ubuntu 22.04 und 24.04 und installiert darin `kubuntu-desktop` sowie `plasma-desktop`. Anschließend werden geprüft:

1. Paketstatus des Kubuntu-/Plasma-Userlands,
2. Bindung der SHA-256-Sidecars an den exakten Dateinamen,
3. Baseline-Installation und erster Offline-Start,
4. private Runtime-Rechte `0700`,
5. Wiederherstellung eines absichtlich beschädigten Runtime-Slots,
6. Upgrade auf den Kandidaten,
7. Rollback auf die Baseline,
8. erneutes Upgrade,
9. normale Entfernung mit erhaltenem Nutzerdaten-Sentinel,
10. Neuinstallation und bestätigter vollständiger Purge.

Die Matrix ist eine containerisierte Kubuntu-Userland-Abnahme. Eine gebootete KDE-VM mit echtem SDDM, X11 und Wayland bleibt Bestandteil der späteren physischen Releaseabnahme.

## Unverdeckte Fehler- und Evidenzsicherung

Jeder Kubuntu-Job schreibt seine letzte Phase in eine eigene Phasendatei und den inneren ursprünglichen Exit-Code in eine separate Datei. Der Workflow erfasst zusätzlich den äußeren Exit-Code des Docker-/Shell-Aufrufs und das vollständige Rohprotokoll.

Die Evidenz wird mit `if: always()` bei Erfolg, Fehler, Timeout oder Abbruch hochgeladen. Der Lebenszyklusschritt beendet sich anschließend weiterhin mit dem ursprünglichen Fehlercode. Das Hochladen darf einen roten Lauf weder grün färben noch dessen Exit-Code ersetzen.

## `_save_`-Finalisierung

Quelldateien, Python-Module, Startskripte und Paketpfade behalten ihre kanonischen Namen. Eine pauschale Umbenennung des Quellbaums ist verboten, weil sie Imports und Manifestbindungen beschädigen würde.

Nach vollständig grüner Matrix verarbeitet `tools/finalize_release_artifacts.py` ausschließlich die geprüften Kandidatenartefakte. Er erzeugt atomar:

```text
multimodultool2026_<version>_amd64_save_.deb
multimodultool2026_<version>_amd64_save_.deb.sha256
multimodultool2026-<version>-amd64_save_.tar.gz
release-manager_save_.sh
CANDIDATE_BUILD_RESULT_save_.json
RELEASE_STATUS_save_.json
```

Vor dem Austausch des Ausgabeordners werden geprüft:

- keine Symlinkkomponente in Quelle, Richtlinie oder Ziel,
- Paket- und Bundlehash stimmen mit `CANDIDATE_BUILD_RESULT.json` überein,
- Sidecar enthält exakt Hash und ursprünglichen Paketdateinamen,
- jede finale Datei enthält `_save_`,
- Dateirechte sind `0644`, nur der Release-Manager ist `0755`,
- Baseline-, Log- und Diagnoseartefakte werden nicht übernommen,
- vorhandene generierte Reste werden erst nach vollständiger Validierung atomar ersetzt.

Verbindliche Klassifikation: `release/release-status.json`.

## Signaturgrenze

P0-009 verwendet SHA-256-Sidecars und reproduzierbare Artefakte. Eine kryptografische Release-Signatur und Vertrauenskette ist bewusst noch nicht freigegeben und folgt mit `P3-009`. `_save_` bedeutet deshalb: technisch geprüft und durch die Kubuntu-Matrix freigegeben, nicht kryptografisch signiert.
