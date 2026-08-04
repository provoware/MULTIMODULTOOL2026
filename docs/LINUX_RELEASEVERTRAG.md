# Linux-Releasevertrag – MULTIMODULTOOL2026

## Ziel

Der Releasekandidat wird als installierbares Debian-Paket für Kubuntu 22.04 und Kubuntu 24.04 auf x86-64 bereitgestellt. Installation, erster Start, Upgrade, Rollback, normale Entfernung und ausdrücklich bestätigte vollständige Entfernung müssen automatisiert und ohne versteckte Cloud-Abhängigkeit geprüft werden.

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

Die Build-ID entsteht aus:

- Paketversion,
- sortierter, expliziter Runtime-Dateiliste,
- SHA-256 jeder Runtime-Datei,
- SHA-256 aller gebündelten Wheels.

`BUILD_INFO.json` enthält Version, Architektur, Build-ID, Source-Manifest-Hash, reproduzierbaren Zeitstempel, Python-Mindestversion und PySide6-Version.

## Reproduzierbare Dateiliste

Nur Pfade aus `release/package-files.txt` werden übernommen. Verzeichnisse werden sortiert rekursiv expandiert. Symlinks, fehlende Einträge, Pfadüberschreitungen und Duplikate blockieren den Build.

Das Paket enthält:

- `SOURCE_MANIFEST.json` für die Buildquellen,
- `FILE_MANIFEST.sha256` für installierte Dateien,
- `WHEELHOUSE.sha256` für die Offline-Runtime.

Zwei Builds mit identischen Eingaben und gleichem `SOURCE_DATE_EPOCH` müssen byteidentische `.deb`- und `.tar.gz`-Artefakte erzeugen.

## Abhängigkeitsprüfung

Vor Installation werden geprüft:

- Linux und x86-64,
- Paketname und Architektur,
- Paket-SHA-256,
- Build-ID und Paketversion,
- `dpkg-deb`, `apt-get`, Python 3.10+,
- Debian-Abhängigkeiten für Python, venv, Qt und KDE-Offscreen-Start.

Nach Installation validiert `postinst` die vollständige installierte Dateiliste und Python-Mindestversion.

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

Unterschiedliche Build-IDs verwenden getrennte Runtime-Slots. Dadurch kann ein Rollback ohne Überschreiben der vorherigen Runtime erfolgen.

## Installation und Upgrade

`release-manager.sh` akzeptiert Änderungen nur mit `--yes`.

- Paket und Sidecar werden vorab geprüft.
- Das Paket wird privat unter `/var/lib/multimodultool2026/packages/` archiviert.
- Aktueller und vorheriger Stand werden atomar in privaten Statusdateien dokumentiert.
- `apt-get install` löst nur deklarierte Systemabhängigkeiten auf.
- Nach Installation muss `multimodultool2026 --verify-installation` grün sein.

## Rollback

Rollback verwendet ausschließlich das zuvor geprüfte lokale Paketarchiv. Der Manager:

1. prüft archiviertes Paket und SHA-256 erneut,
2. installiert mit explizit erlaubtem Downgrade,
3. prüft Paketdateien und Build-ID,
4. tauscht aktuellen und vorherigen Status atomar.

Ein fehlendes, verändertes oder nicht verifizierbares Archiv blockiert den Rollback.

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

Zusätzlich entfernt werden:

- `/var/lib/multimodultool2026`,
- ausschließlich die bekannten XDG-Verzeichnisse des ausdrücklich bestimmten Nicht-root-Nutzers,
- der private Runtime-Pfad dieses Nutzers.

Symlinks, fremde Home-Pfade und unklare Nutzerzuordnung blockieren den Nutzerdaten-Purge.

## Kubuntu-Matrix

Die CI erzeugt zwei frische Container auf Basis von Ubuntu 22.04 und 24.04 und installiert darin `kubuntu-desktop-minimal` sowie `plasma-desktop`. Anschließend werden geprüft:

1. Baseline installieren,
2. erster Offline-Start,
3. Upgrade auf Releasekandidat,
4. erster Start des neuen Builds,
5. Rollback auf Baseline,
6. erneuter Start,
7. erneutes Upgrade,
8. normale Entfernung mit Erhalt eines Nutzerdaten-Sentinels,
9. Neuinstallation,
10. vollständiger Purge von Systemzustand und ausdrücklich ausgewählten Nutzerdaten.

Die Matrix ist eine containerisierte Kubuntu-Userland-Abnahme. Eine gebootete KDE-VM mit echtem SDDM, X11 und Wayland bleibt Bestandteil der späteren physischen Releaseabnahme.

## Signaturgrenze

P0-009 verwendet SHA-256-Sidecars und reproduzierbare Artefakte. Eine kryptografische Release-Signatur und Vertrauenskette ist bewusst noch nicht freigegeben und folgt mit `P3-009`.
