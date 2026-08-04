#!/usr/bin/env bash
set -Eeuo pipefail

PACKAGE_NAME="multimodultool2026"
STATE_ROOT="/var/lib/multimodultool2026"
ARCHIVE_ROOT="$STATE_ROOT/packages"
CURRENT_FILE="$STATE_ROOT/current.env"
PREVIOUS_FILE="$STATE_ROOT/previous.env"
ASSUME_YES=0
PURGE_SYSTEM_STATE=0
PURGE_USER_DATA=0

usage() {
    cat <<'EOF'
Verwendung:
  release-manager.sh verify <paket.deb>
  release-manager.sh install <paket.deb> --yes
  release-manager.sh upgrade <paket.deb> --yes
  release-manager.sh rollback --yes
  release-manager.sh uninstall [--purge-system-state] [--purge-current-user-data] --yes
  release-manager.sh status

Normale Deinstallation entfernt alle paketverwalteten Systemdateien und bewahrt
Nutzerdaten. --purge-current-user-data entfernt ausschließlich die XDG-Daten des
aufrufenden oder über MMT_PURGE_USER ausdrücklich angegebenen Nutzers.
EOF
}

fail() {
    printf 'ROT: %s\n' "$1" >&2
    exit "${2:-30}"
}

require_root() {
    [[ "${EUID:-$(id -u)}" -eq 0 ]] || fail "Diese Aktion benötigt root-Rechte." 31
}

confirm_mutation() {
    [[ "$ASSUME_YES" -eq 1 ]] || fail "Ändernde Aktionen benötigen ausdrücklich --yes." 32
}

atomic_env() {
    local target="$1" version="$2" build_id="$3" archive="$4"
    local temp
    temp="$(mktemp "$STATE_ROOT/.state.XXXXXX")"
    chmod 0600 "$temp"
    printf 'VERSION=%q\nBUILD_ID=%q\nARCHIVE=%q\n' "$version" "$build_id" "$archive" > "$temp"
    sync -f "$temp" 2>/dev/null || true
    mv -f -- "$temp" "$target"
    chmod 0600 "$target"
    sync -d "$STATE_ROOT" 2>/dev/null || true
}

read_env_file() {
    local path="$1"
    [[ -r "$path" && ! -L "$path" ]] || return 1
    # shellcheck disable=SC1090
    source "$path"
    [[ -n "${VERSION:-}" && -n "${BUILD_ID:-}" && -n "${ARCHIVE:-}" ]]
}

package_metadata() {
    local package="$1" temp
    [[ -f "$package" && ! -L "$package" ]] || fail "Paketdatei fehlt oder ist ein Symlink: $package" 33
    command -v dpkg-deb >/dev/null 2>&1 || fail "dpkg-deb fehlt." 34
    local name arch version
    name="$(dpkg-deb -f "$package" Package)"
    arch="$(dpkg-deb -f "$package" Architecture)"
    version="$(dpkg-deb -f "$package" Version)"
    [[ "$name" == "$PACKAGE_NAME" ]] || fail "Unerwarteter Paketname: $name" 35
    [[ "$arch" == "amd64" && "$(uname -m)" == "x86_64" ]] || fail "Paket oder System besitzt nicht die freigegebene x86-64-Architektur." 36
    temp="$(mktemp -d)"
    dpkg-deb -x "$package" "$temp"
    local info="$temp/usr/lib/multimodultool2026/BUILD_INFO.json"
    [[ -r "$info" ]] || { rm -rf "$temp"; fail "BUILD_INFO.json fehlt im Paket." 37; }
    local build_id embedded_version
    read -r build_id embedded_version < <(python3 - "$info" <<'PY'
import json, pathlib, sys
v=json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
print(v['buildId'], v['version'])
PY
)
    rm -rf "$temp"
    [[ "$embedded_version" == "$version" ]] || fail "Paketversion und Build-Metadaten widersprechen sich." 38
    [[ "$build_id" =~ ^MMTBUILD-[A-Za-z0-9._~+-]+-[a-f0-9]{16}$ ]] || fail "Build-ID besitzt ein ungültiges Format." 39
    printf '%s\t%s\n' "$version" "$build_id"
}

verify_package() {
    local package="$1" sidecar="${1}.sha256"
    [[ -r "$sidecar" && ! -L "$sidecar" ]] || fail "SHA-256-Sidecar fehlt oder ist unsicher: $sidecar" 40
    (cd "$(dirname "$package")" && sha256sum --quiet -c "$(basename "$sidecar")") \
        || fail "Paket-SHA-256 ist ungültig." 41
    local metadata
    metadata="$(package_metadata "$package")"
    printf 'GRÜN: Paket geprüft: %s\n' "$metadata"
}

prepare_state() {
    mkdir -p "$ARCHIVE_ROOT"
    chmod 0700 "$STATE_ROOT" "$ARCHIVE_ROOT"
    [[ ! -L "$STATE_ROOT" && ! -L "$ARCHIVE_ROOT" ]] || fail "Releasezustand darf kein Symlink sein." 42
}

archive_package() {
    local package="$1" version="$2" build_id="$3"
    local safe_version="${version//[^A-Za-z0-9._~+-]/_}"
    local target="$ARCHIVE_ROOT/${safe_version}__${build_id}.deb"
    install -m 0600 "$package" "$target"
    (cd "$ARCHIVE_ROOT" && sha256sum "$(basename "$target")" > "$(basename "$target").sha256")
    chmod 0600 "$target.sha256"
    sync -f "$target" 2>/dev/null || true
    sync -f "$target.sha256" 2>/dev/null || true
    printf '%s\n' "$target"
}

install_package() {
    local mode="$1" package="$2"
    require_root
    confirm_mutation
    verify_package "$package"
    command -v apt-get >/dev/null 2>&1 || fail "apt-get fehlt." 43
    command -v python3 >/dev/null 2>&1 || fail "Python 3 fehlt." 44
    python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)' \
        || fail "Python 3.10 oder neuer wird benötigt." 45
    prepare_state
    local metadata version build_id archive old_version old_build old_archive
    metadata="$(package_metadata "$package")"
    version="${metadata%%$'\t'*}"
    build_id="${metadata#*$'\t'}"
    archive="$(archive_package "$package" "$version" "$build_id")"
    if read_env_file "$CURRENT_FILE"; then
        old_version="$VERSION"; old_build="$BUILD_ID"; old_archive="$ARCHIVE"
    else
        old_version=""; old_build=""; old_archive=""
    fi
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "$package"
    /usr/bin/multimodultool2026 --verify-installation >/dev/null
    if [[ -n "$old_archive" && "$old_build" != "$build_id" ]]; then
        atomic_env "$PREVIOUS_FILE" "$old_version" "$old_build" "$old_archive"
    fi
    atomic_env "$CURRENT_FILE" "$version" "$build_id" "$archive"
    printf 'GRÜN: %s abgeschlossen: Version %s, Build-ID %s\n' "$mode" "$version" "$build_id"
}

rollback_package() {
    require_root
    confirm_mutation
    prepare_state
    read_env_file "$PREVIOUS_FILE" || fail "Kein geprüfter vorheriger Paketstand für Rollback vorhanden." 46
    local rollback_version="$VERSION" rollback_build="$BUILD_ID" rollback_archive="$ARCHIVE"
    [[ -r "$rollback_archive" ]] || fail "Archiviertes Rollback-Paket fehlt." 47
    local current_version="" current_build="" current_archive=""
    if read_env_file "$CURRENT_FILE"; then
        current_version="$VERSION"; current_build="$BUILD_ID"; current_archive="$ARCHIVE"
    fi
    verify_package "$rollback_archive"
    DEBIAN_FRONTEND=noninteractive apt-get install -y --allow-downgrades --no-install-recommends "$rollback_archive"
    /usr/bin/multimodultool2026 --verify-installation >/dev/null
    atomic_env "$CURRENT_FILE" "$rollback_version" "$rollback_build" "$rollback_archive"
    if [[ -n "$current_archive" ]]; then
        atomic_env "$PREVIOUS_FILE" "$current_version" "$current_build" "$current_archive"
    else
        rm -f "$PREVIOUS_FILE"
    fi
    printf 'GRÜN: Rollback abgeschlossen: Version %s, Build-ID %s\n' "$rollback_version" "$rollback_build"
}

purge_user_data() {
    local user="${MMT_PURGE_USER:-${SUDO_USER:-}}"
    [[ -n "$user" && "$user" != "root" ]] || fail "Für den Nutzerdaten-Purge muss MMT_PURGE_USER oder SUDO_USER auf einen Nicht-root-Nutzer zeigen." 48
    local entry home uid
    entry="$(getent passwd "$user")" || fail "Nutzer für Purge nicht gefunden: $user" 49
    IFS=: read -r _ _ uid _ _ home _ <<<"$entry"
    [[ -d "$home" && "$home" == /home/* ]] || fail "Unsicheres Nutzer-Home für Purge: $home" 50
    local paths=(
        "$home/.config/multimodultool2026"
        "$home/.local/share/multimodultool2026"
        "$home/.cache/multimodultool2026"
        "$home/.local/state/multimodultool2026"
        "/run/user/$uid/multimodultool2026"
    )
    local path
    for path in "${paths[@]}"; do
        [[ ! -L "$path" ]] || fail "Purge-Ziel ist ein Symlink und wurde blockiert: $path" 51
        [[ "$path" == "$home"/* || "$path" == "/run/user/$uid/multimodultool2026" ]] \
            || fail "Purge-Ziel verlässt die erlaubte Grenze: $path" 52
        rm -rf --one-file-system -- "$path"
    done
}

uninstall_package() {
    require_root
    confirm_mutation
    if [[ "$PURGE_SYSTEM_STATE" -eq 1 ]]; then
        DEBIAN_FRONTEND=noninteractive apt-get purge -y "$PACKAGE_NAME" || true
    else
        DEBIAN_FRONTEND=noninteractive apt-get remove -y "$PACKAGE_NAME" || true
    fi
    dpkg-query -W -f='${Status}' "$PACKAGE_NAME" 2>/dev/null | grep -q 'install ok installed' \
        && fail "Paket ist nach Entfernung noch installiert." 53
    [[ ! -e /usr/bin/multimodultool2026 ]] || fail "Starter blieb nach Entfernung zurück." 54
    [[ ! -e /usr/lib/multimodultool2026 ]] || fail "Runtime blieb nach Entfernung zurück." 55
    [[ ! -e /usr/share/applications/multimodultool2026.desktop ]] || fail "Desktopdatei blieb nach Entfernung zurück." 56
    [[ "$PURGE_USER_DATA" -eq 0 ]] || purge_user_data
    if [[ "$PURGE_SYSTEM_STATE" -eq 1 && -e "$STATE_ROOT" ]]; then
        [[ ! -L "$STATE_ROOT" ]] || fail "Systemzustand ist ein Symlink und wurde nicht gelöscht." 57
        rm -rf --one-file-system -- "$STATE_ROOT"
    fi
    printf 'GRÜN: Paketverwaltete Systemdateien vollständig entfernt.\n'
}

status() {
    if dpkg-query -W -f='${Status}\t${Version}\n' "$PACKAGE_NAME" 2>/dev/null; then :; else printf 'nicht installiert\n'; fi
    [[ -x /usr/bin/multimodultool2026 ]] && /usr/bin/multimodultool2026 --build-info || true
}

[[ $# -ge 1 ]] || { usage; exit 2; }
COMMAND="$1"; shift
POSITIONAL=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --yes) ASSUME_YES=1 ;;
        --purge-system-state) PURGE_SYSTEM_STATE=1 ;;
        --purge-current-user-data) PURGE_USER_DATA=1 ;;
        --help|-h) usage; exit 0 ;;
        *) POSITIONAL+=("$1") ;;
    esac
    shift
done

case "$COMMAND" in
    verify) [[ ${#POSITIONAL[@]} -eq 1 ]] || fail "verify benötigt genau eine Paketdatei."; verify_package "${POSITIONAL[0]}" ;;
    install|upgrade) [[ ${#POSITIONAL[@]} -eq 1 ]] || fail "$COMMAND benötigt genau eine Paketdatei."; install_package "$COMMAND" "${POSITIONAL[0]}" ;;
    rollback) [[ ${#POSITIONAL[@]} -eq 0 ]] || fail "rollback akzeptiert keine Paketdatei."; rollback_package ;;
    uninstall) [[ ${#POSITIONAL[@]} -eq 0 ]] || fail "uninstall akzeptiert keine Paketdatei."; uninstall_package ;;
    status) status ;;
    *) usage; fail "Unbekannter Befehl: $COMMAND" 2 ;;
esac
