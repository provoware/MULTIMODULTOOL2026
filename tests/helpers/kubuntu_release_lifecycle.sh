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
PHASE_FILE="$REPORT_DIR/kubuntu-$SERIES.phase"
INNER_EXIT_FILE="$REPORT_DIR/kubuntu-$SERIES.inner-exit-code"
printf '%s\n' 'prepare-container' > "$PHASE_FILE"
printf '[mmt-release-diagnostic] requested-series=%s container-image=ubuntu:%s artifact-dir=%s phase=prepare-container\n' \
    "$SERIES" "$SERIES" "$ARTIFACT_DIR"

DOCKER_SCRIPT='set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive
PHASE_FILE=/artifacts/lifecycle-reports/kubuntu-'"$SERIES"'.phase
INNER_EXIT_FILE=/artifacts/lifecycle-reports/kubuntu-'"$SERIES"'.inner-exit-code
phase() {
  printf "%s\n" "$1" > "$PHASE_FILE"
  printf "[mmt-release-diagnostic] requested-series='"$SERIES"' actual-version-id=%s bash=%s phase=%s\n" \
    "$(. /etc/os-release && printf "%s" "$VERSION_ID")" "$BASH_VERSION" "$1"
}
on_exit() {
  code=$?
  current_phase="$(cat "$PHASE_FILE" 2>/dev/null || printf unknown)"
  printf "%s\n" "$code" > "$INNER_EXIT_FILE"
  printf "[mmt-release-diagnostic] requested-series='"$SERIES"' phase=%s original-exit-code=%s\n" \
    "$current_phase" "$code"
  exit "$code"
}
trap on_exit EXIT

phase prepare-kubuntu-packages
printf "#!/bin/sh\nexit 101\n" > /usr/sbin/policy-rc.d
chmod 0755 /usr/sbin/policy-rc.d
apt-get update
apt-get install -y --no-install-recommends ca-certificates software-properties-common passwd util-linux
add-apt-repository -y universe
apt-get update
printf "sddm shared/default-x-display-manager select sddm\n" | debconf-set-selections || true
apt-get install -y --no-install-recommends kubuntu-desktop plasma-desktop

phase validate-package-state
dpkg-query -W -f="\${Status}\n" kubuntu-desktop | grep -q "install ok installed"
dpkg-query -W -f="\${Status}\n" plasma-desktop | grep -q "install ok installed"

phase prepare-test-user
useradd -m -s /bin/bash mmt
MMT_UID="$(id -u mmt)"
MMT_GID="$(id -g mmt)"
MMT_RUNTIME_DIR="/run/user/$MMT_UID"
mkdir -p "$MMT_RUNTIME_DIR"
chown "$MMT_UID:$MMT_GID" "$MMT_RUNTIME_DIR"
chmod 0700 "$MMT_RUNTIME_DIR"
[[ "$(stat -c %u:%g:%a "$MMT_RUNTIME_DIR")" == "$MMT_UID:$MMT_GID:700" ]]
chmod 0755 /artifacts/release-manager.sh

run_as_mmt() {
  runuser -u mmt -- env \
    HOME=/home/mmt \
    XDG_CONFIG_HOME=/home/mmt/.config \
    XDG_DATA_HOME=/home/mmt/.local/share \
    XDG_CACHE_HOME=/home/mmt/.cache \
    XDG_STATE_HOME=/home/mmt/.local/state \
    XDG_RUNTIME_DIR="$MMT_RUNTIME_DIR" \
    QT_QPA_PLATFORM=offscreen \
    "$@"
}

build_version() {
  /usr/bin/multimodultool2026 --build-info | python3 -c "import json,sys; print(json.load(sys.stdin)[\"version\"])"
}

phase verify-release-artifacts
/artifacts/release-manager.sh verify /artifacts/multimodultool2026_0.8.0~rc1_amd64.deb
/artifacts/release-manager.sh verify /artifacts/multimodultool2026_0.9.0~rc1_amd64.deb

phase reject-misbound-checksum
cp /artifacts/multimodultool2026_0.8.0~rc1_amd64.deb /artifacts/checksum-binding.deb
cp /artifacts/multimodultool2026_0.8.0~rc1_amd64.deb.sha256 /artifacts/checksum-binding.deb.sha256
if /artifacts/release-manager.sh verify /artifacts/checksum-binding.deb; then
  echo "checksum sidecar accepted a different package filename" >&2
  exit 61
fi
rm -f /artifacts/checksum-binding.deb /artifacts/checksum-binding.deb.sha256

phase install-baseline
/artifacts/release-manager.sh install /artifacts/multimodultool2026_0.8.0~rc1_amd64.deb --yes
[[ "$(build_version)" == "0.8.0~rc1" ]]
run_as_mmt /usr/bin/multimodultool2026 --validate-only
BASELINE_BUILD="$(run_as_mmt /usr/bin/multimodultool2026 --build-info | python3 -c "import json,sys; print(json.load(sys.stdin)[\"buildId\"])" )"
SAFE_BASELINE_BUILD="${BASELINE_BUILD//[^A-Za-z0-9._-]/_}"
RUNTIME_ROOT="/home/mmt/.local/share/multimodultool2026/runtime"
VENV_DIR="$RUNTIME_ROOT/venv-$SAFE_BASELINE_BUILD"
[[ -d "$VENV_DIR" ]]
[[ "$(stat -c %a /home/mmt/.local/share/multimodultool2026)" == "700" ]]
[[ "$(stat -c %a "$RUNTIME_ROOT")" == "700" ]]

phase recover-damaged-runtime
rm -f "$VENV_DIR/bin/python"
run_as_mmt /usr/bin/multimodultool2026 --validate-only
[[ -x "$VENV_DIR/bin/python" ]]
[[ "$(find "$RUNTIME_ROOT" -maxdepth 1 -name ".venv-*.tmp" -o -name ".venv-*.invalid" | wc -l)" -eq 0 ]]

phase upgrade-candidate
/artifacts/release-manager.sh upgrade /artifacts/multimodultool2026_0.9.0~rc1_amd64.deb --yes
[[ "$(build_version)" == "0.9.0~rc1" ]]
run_as_mmt /usr/bin/multimodultool2026 --validate-only
CANDIDATE_BUILD="$(run_as_mmt /usr/bin/multimodultool2026 --build-info | python3 -c "import json,sys; print(json.load(sys.stdin)[\"buildId\"])" )"
[[ "$BASELINE_BUILD" != "$CANDIDATE_BUILD" ]]

phase rollback-baseline
/artifacts/release-manager.sh rollback --yes
[[ "$(build_version)" == "0.8.0~rc1" ]]
run_as_mmt /usr/bin/multimodultool2026 --validate-only

phase reupgrade-candidate
/artifacts/release-manager.sh upgrade /artifacts/multimodultool2026_0.9.0~rc1_amd64.deb --yes
[[ "$(build_version)" == "0.9.0~rc1" ]]
run_as_mmt /usr/bin/multimodultool2026 --validate-only

phase uninstall-preserve-user-data
mkdir -p /home/mmt/.config/multimodultool2026
printf preserved > /home/mmt/.config/multimodultool2026/preserve.test
chown -R mmt:mmt /home/mmt/.config
/artifacts/release-manager.sh uninstall --yes
[[ -f /home/mmt/.config/multimodultool2026/preserve.test ]]
[[ ! -e /usr/bin/multimodultool2026 ]]
[[ ! -e /usr/lib/multimodultool2026 ]]
[[ ! -e /usr/share/applications/multimodultool2026.desktop ]]

phase purge-selected-user-data
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
[[ ! -e "$MMT_RUNTIME_DIR/multimodultool2026" ]]

phase write-report
export MMT_REPORT_UID="$MMT_UID"
python3 - <<PY > /artifacts/lifecycle-reports/kubuntu-'"$SERIES"'.json
import json
import os
print(json.dumps({
  "schemaVersion": 1,
  "series": "'"$SERIES"'",
  "kubuntuDesktop": True,
  "plasmaDesktop": True,
  "architecture": "amd64",
  "testUserUid": int(os.environ["MMT_REPORT_UID"]),
  "install": "passed",
  "firstStart": "passed",
  "privateRuntime0700": "passed",
  "damagedRuntimeRecovery": "passed",
  "checksumBinding": "passed",
  "upgrade": "passed",
  "rollback": "passed",
  "removePreservesUserData": "passed",
  "purgeRemovesSelectedUserData": "passed",
  "lastPhase": "completed"
}, sort_keys=True, indent=2))
PY
phase completed
'

docker run --rm --platform linux/amd64 \
    -v "$ARTIFACT_DIR:/artifacts" \
    "ubuntu:$SERIES" \
    bash -lc "$DOCKER_SCRIPT"

[[ -s "$REPORT" ]] || { echo "lifecycle report missing: $REPORT" >&2; exit 5; }
cat "$REPORT"
