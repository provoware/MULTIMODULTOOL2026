#!/usr/bin/env bash
set -Eeuo pipefail

[[ $# -eq 2 ]] || { echo "usage: $0 <22.04|24.04> <artifact-dir>" >&2; exit 2; }
SERIES="$1"
ARTIFACT_DIR="$(cd "$2" && pwd)"
[[ "$SERIES" == "22.04" || "$SERIES" == "24.04" ]] || { echo "unsupported series" >&2; exit 3; }

BASELINE="$ARTIFACT_DIR/multimodultool2026_0.8.0~rc1_amd64.deb"
CANDIDATE="$ARTIFACT_DIR/multimodultool2026_0.9.0~rc1_amd64.deb"
MANAGER="$ARTIFACT_DIR/release-manager.sh"
for path in "$BASELINE" "$BASELINE.sha256" "$CANDIDATE" "$CANDIDATE.sha256" "$MANAGER"; do
    [[ -r "$path" ]] || { echo "missing artifact: $path" >&2; exit 4; }
done

REPORT_DIR="$ARTIFACT_DIR/lifecycle-reports"
mkdir -p "$REPORT_DIR"
REPORT="$REPORT_DIR/kubuntu-$SERIES.json"

DOCKER_SCRIPT='set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends ca-certificates software-properties-common passwd util-linux
add-apt-repository -y universe
apt-get update
printf "sddm shared/default-x-display-manager select sddm\n" | debconf-set-selections || true
apt-get install -y --no-install-recommends kubuntu-desktop plasma-desktop

dpkg-query -W -f="${Status}\n" kubuntu-desktop | grep -q "install ok installed"
dpkg-query -W -f="${Status}\n" plasma-desktop | grep -q "install ok installed"

useradd -m -u 1000 -s /bin/bash mmt
mkdir -p /run/user/1000
chown 1000:1000 /run/user/1000
chmod 0700 /run/user/1000
chmod 0755 /artifacts/release-manager.sh

run_as_mmt() {
  runuser -u mmt -- env \
    HOME=/home/mmt \
    XDG_CONFIG_HOME=/home/mmt/.config \
    XDG_DATA_HOME=/home/mmt/.local/share \
    XDG_CACHE_HOME=/home/mmt/.cache \
    XDG_STATE_HOME=/home/mmt/.local/state \
    XDG_RUNTIME_DIR=/run/user/1000 \
    QT_QPA_PLATFORM=offscreen \
    "$@"
}

build_version() {
  /usr/bin/multimodultool2026 --build-info | python3 -c "import json,sys; print(json.load(sys.stdin)[\"version\"])"
}

/artifacts/release-manager.sh verify /artifacts/multimodultool2026_0.8.0~rc1_amd64.deb
/artifacts/release-manager.sh verify /artifacts/multimodultool2026_0.9.0~rc1_amd64.deb

/artifacts/release-manager.sh install /artifacts/multimodultool2026_0.8.0~rc1_amd64.deb --yes
[[ "$(build_version)" == "0.8.0~rc1" ]]
run_as_mmt /usr/bin/multimodultool2026 --validate-only
BASELINE_BUILD="$(run_as_mmt /usr/bin/multimodultool2026 --build-info | python3 -c "import json,sys; print(json.load(sys.stdin)[\"buildId\"])" )"
[[ -d "/home/mmt/.local/share/multimodultool2026/runtime/venv-${BASELINE_BUILD//[^A-Za-z0-9._-]/_}" ]]

/artifacts/release-manager.sh upgrade /artifacts/multimodultool2026_0.9.0~rc1_amd64.deb --yes
[[ "$(build_version)" == "0.9.0~rc1" ]]
run_as_mmt /usr/bin/multimodultool2026 --validate-only
CANDIDATE_BUILD="$(run_as_mmt /usr/bin/multimodultool2026 --build-info | python3 -c "import json,sys; print(json.load(sys.stdin)[\"buildId\"])" )"
[[ "$BASELINE_BUILD" != "$CANDIDATE_BUILD" ]]

/artifacts/release-manager.sh rollback --yes
[[ "$(build_version)" == "0.8.0~rc1" ]]
run_as_mmt /usr/bin/multimodultool2026 --validate-only

/artifacts/release-manager.sh upgrade /artifacts/multimodultool2026_0.9.0~rc1_amd64.deb --yes
[[ "$(build_version)" == "0.9.0~rc1" ]]
run_as_mmt /usr/bin/multimodultool2026 --validate-only

mkdir -p /home/mmt/.config/multimodultool2026
printf preserved > /home/mmt/.config/multimodultool2026/preserve.test
chown -R mmt:mmt /home/mmt/.config
/artifacts/release-manager.sh uninstall --yes
[[ -f /home/mmt/.config/multimodultool2026/preserve.test ]]
[[ ! -e /usr/bin/multimodultool2026 ]]
[[ ! -e /usr/lib/multimodultool2026 ]]
[[ ! -e /usr/share/applications/multimodultool2026.desktop ]]

/artifacts/release-manager.sh install /artifacts/multimodultool2026_0.9.0~rc1_amd64.deb --yes
run_as_mmt /usr/bin/multimodultool2026 --validate-only
MMT_PURGE_USER=mmt /artifacts/release-manager.sh uninstall --purge-system-state --purge-current-user-data --yes
[[ ! -e /usr/bin/multimodultool2026 ]]
[[ ! -e /usr/lib/multimodultool2026 ]]
[[ ! -e /usr/share/applications/multimodultool2026.desktop ]]
[[ ! -e /var/lib/multimodultool2026 ]]
[[ ! -e /home/mmt/.config/multimodultool2026 ]]
[[ ! -e /home/mmt/.local/share/multimodultool2026 ]]
[[ ! -e /home/mmt/.cache/multimodultool2026 ]]
[[ ! -e /home/mmt/.local/state/multimodultool2026 ]]

python3 - <<PY > /artifacts/lifecycle-reports/kubuntu-'"$SERIES"'.json
import json
print(json.dumps({
  "schemaVersion": 1,
  "series": "'"$SERIES"'",
  "kubuntuDesktop": True,
  "plasmaDesktop": True,
  "architecture": "amd64",
  "install": "passed",
  "firstStart": "passed",
  "upgrade": "passed",
  "rollback": "passed",
  "removePreservesUserData": "passed",
  "purgeRemovesSelectedUserData": "passed",
}, sort_keys=True, indent=2))
PY
'

docker run --rm --platform linux/amd64 \
    -v "$ARTIFACT_DIR:/artifacts" \
    "ubuntu:$SERIES" \
    bash -lc "$DOCKER_SCRIPT"

[[ -s "$REPORT" ]] || { echo "lifecycle report missing: $REPORT" >&2; exit 5; }
cat "$REPORT"
