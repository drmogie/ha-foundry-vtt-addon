#!/bin/bash
# Home Assistant add-on start script for Foundry VTT.
# Reads add-on options from /data/options.json, turns them into the
# environment variables the felddy/foundryvtt image understands, then hands
# off to the image's own entrypoint as the unprivileged "node" user.
set -euo pipefail

OPTIONS=/data/options.json

if [ ! -f "${OPTIONS}" ]; then
  echo "[ha-foundry-vtt] ERROR: ${OPTIONS} not found. Is this running as a Home Assistant add-on?" >&2
  exit 1
fi

# Read one option. Prints nothing when it is missing, null, or empty.
# Booleans and numbers are printed as text (false stays "false").
opt() {
  jq -r --arg k "$1" \
    'if has($k) and .[$k] != null then (.[$k] | tostring) else empty end' \
    "${OPTIONS}"
}

# set_env ENV_NAME option_key  -> exports ENV_NAME only if the option has a value.
set_env() {
  local value
  value="$(opt "$2")"
  if [ -n "${value}" ]; then
    export "$1=${value}"
  fi
}

set_env FOUNDRY_USERNAME            foundry_username
set_env FOUNDRY_PASSWORD            foundry_password
set_env FOUNDRY_RELEASE_URL         foundry_release_url
set_env FOUNDRY_LICENSE_KEY         foundry_license_key
set_env FOUNDRY_ADMIN_KEY           foundry_admin_key
set_env FOUNDRY_VERSION             foundry_version
set_env FOUNDRY_WORLD               foundry_world
set_env FOUNDRY_HOSTNAME            foundry_hostname
set_env FOUNDRY_PROXY_SSL           foundry_proxy_ssl
set_env FOUNDRY_PROXY_PORT          foundry_proxy_port
set_env FOUNDRY_ROUTE_PREFIX        foundry_route_prefix
set_env FOUNDRY_LANGUAGE            foundry_language
set_env FOUNDRY_CSS_THEME           foundry_css_theme
set_env FOUNDRY_TELEMETRY           foundry_telemetry
set_env FOUNDRY_COMPRESS_WEBSOCKET  foundry_compress_websocket
set_env FOUNDRY_MINIFY_STATIC_FILES foundry_minify_static_files
set_env FOUNDRY_IP_DISCOVERY        foundry_ip_discovery
set_env CONTAINER_PRESERVE_CONFIG   container_preserve_config
set_env CONTAINER_CACHE_SIZE        container_cache_size
set_env CONTAINER_VERBOSE           container_verbose
set_env TZ                          timezone

# Basic sanity check so the user gets a clear message instead of a crash loop.
if [ -z "${FOUNDRY_RELEASE_URL:-}" ] \
   && { [ -z "${FOUNDRY_USERNAME:-}" ] || [ -z "${FOUNDRY_PASSWORD:-}" ]; }; then
  if [ ! -d /data/container_cache ] || [ -z "$(ls -A /data/container_cache 2>/dev/null)" ]; then
    echo "[ha-foundry-vtt] ERROR: No Foundry download credentials set." >&2
    echo "[ha-foundry-vtt] Fill in foundry_username and foundry_password (or foundry_release_url) on the add-on Configuration tab." >&2
    exit 1
  fi
fi

echo "[ha-foundry-vtt] Starting Foundry VTT (hostname: $(hostname))"

# The base image runs as the "node" user, so make sure it can write to /data.
chown node:node /data 2>/dev/null || true
chmod a+rwx /data 2>/dev/null || true

# Keep Foundry's important folders in the add-on config folder, so you can
# browse them from Samba or the File editor add-on.
# The base image hardcodes /data, so we link /data/<name> to /config/<name>.
CONFIG_ROOT="${CONFIG_ROOT:-/config}"
DATA_ROOT="${DATA_ROOT:-/data}"

link_dir() {
  local name="$1"
  local src="${DATA_ROOT}/${name}"
  local dst="${CONFIG_ROOT}/${name}"
  mkdir -p "${dst}"
  # Move anything from an earlier run (before this feature) into the config folder.
  if [ -d "${src}" ] && [ ! -L "${src}" ]; then
    echo "[ha-foundry-vtt] Moving existing ${name} folder to ${dst}"
    cp -a "${src}/." "${dst}/"
    rm -rf "${src}"
  fi
  ln -sfn "${dst}" "${src}"
  # Only fix ownership when needed, so big worlds do not slow every start.
  if [ "$(stat -c %U "${dst}")" != "node" ]; then
    chown -R node:node "${dst}" 2>/dev/null || true
  fi
  chmod a+rwx "${dst}" 2>/dev/null || true
}

if [ -d "${CONFIG_ROOT}" ]; then
  for name in Data Config Logs; do
    link_dir "${name}"
  done
  echo "[ha-foundry-vtt] Foundry Data, Config and Logs are in the add-on config folder."
else
  echo "[ha-foundry-vtt] WARNING: ${CONFIG_ROOT} is not mounted. Using /data only." >&2
fi

# Home Assistant recreates this container on every start/stop, which throws
# away the installed Foundry application (it only keeps /data and /config).
# That means the base image has to unzip the ~3.5-minute Foundry install
# from scratch on every restart, even though it already skips the download.
# Fix: keep the installed app itself around too, so it survives restarts.
#
# IMPORTANT: this cache must live under CONFIG_ROOT (/config, the separate
# addon_config mount), never under DATA_ROOT (/data). Foundry refuses to
# start if its own application folder resolves (through symlinks) to a path
# inside its data path ("The data path ... must not be inside the
# application location ..."). /home/node/resources is a symlink, and its
# real target counts for that check - putting it under /data trips it, even
# though /data is where Foundry's Data/Config/Logs folders themselves
# correctly live (those are meant to be inside the data path).
# One-time cleanup: an earlier version of this add-on (2026.09.27.01)
# mistakenly cached the app under /data/resources, which is what caused the
# Foundry data-path error above. Remove it if present.
if [ -e "${DATA_ROOT}/resources" ]; then
  echo "[ha-foundry-vtt] Removing old app cache at ${DATA_ROOT}/resources (moved to ${CONFIG_ROOT})."
  rm -rf "${DATA_ROOT}/resources"
fi

if [ -d "${CONFIG_ROOT}" ]; then
  APP_CACHE="${CONFIG_ROOT}/resources"
  mkdir -p "${APP_CACHE}"

  # Every container start, /home/node/resources shows up as a fresh, empty,
  # non-symlink folder (it is part of the container's own throwaway
  # filesystem) - NOT just the one time this feature was added. So only
  # treat it as something to migrate into the cache when it actually
  # contains an installed app; otherwise this would wipe out a good cache
  # with an empty folder on every single restart.
  if [ -e /home/node/resources ] && [ ! -L /home/node/resources ] \
     && [ -f /home/node/resources/app/package.json ]; then
    echo "[ha-foundry-vtt] Saving the installed Foundry app to ${APP_CACHE} for next restart."
    rm -rf "${APP_CACHE}"
    mkdir -p "${APP_CACHE}"
    cp -a /home/node/resources/. "${APP_CACHE}/"
  fi
  rm -rf /home/node/resources
  ln -sfn "${APP_CACHE}" /home/node/resources
  if [ "$(stat -c %U "${APP_CACHE}")" != "node" ]; then
    chown -R node:node "${APP_CACHE}" 2>/dev/null || true
  fi
  if [ -f "${APP_CACHE}/app/package.json" ]; then
    echo "[ha-foundry-vtt] Found the installed Foundry app already saved, skipping the unzip."
  fi
else
  echo "[ha-foundry-vtt] WARNING: ${CONFIG_ROOT} is not mounted. Restarts will reinstall Foundry." >&2
fi

CACHE_DIR="${CONTAINER_CACHE:-/data/container_cache}"

# Foundry updates: the felddy/foundryvtt base image tag this add-on builds
# from floats (new Foundry builds land under the same tag), so an add-on
# update/rebuild can silently pull in a newer Foundry version even though
# foundry_version was left empty. By default (foundry_auto_update: false),
# stay on whatever version is already installed instead. Turn
# foundry_auto_update on, or set foundry_version explicitly, to change that.
FOUNDRY_AUTO_UPDATE="$(opt foundry_auto_update)"
if [ "${FOUNDRY_AUTO_UPDATE:-false}" != "true" ] && [ -z "${FOUNDRY_VERSION:-}" ]; then
  INSTALLED_VERSION=""
  if [ -f "${APP_CACHE:-}/app/package.json" ]; then
    INSTALLED_VERSION="$(jq -r '.version // empty' "${APP_CACHE}/app/package.json" 2>/dev/null || true)"
  fi
  if [ -z "${INSTALLED_VERSION}" ] && [ -d "${CACHE_DIR}" ]; then
    INSTALLED_VERSION="$(ls "${CACHE_DIR}"/foundryvtt-*.zip 2>/dev/null \
      | sed -E 's#.*/foundryvtt-(.+)\.zip#\1#' | sort -V | tail -n1)"
  fi
  if [ -n "${INSTALLED_VERSION}" ]; then
    export FOUNDRY_VERSION="${INSTALLED_VERSION}"
    echo "[ha-foundry-vtt] Auto-update is off, staying on the installed Foundry ${FOUNDRY_VERSION}."
  else
    echo "[ha-foundry-vtt] Auto-update is off, but no installed version was found yet - installing the version this add-on bundles."
  fi
fi

# If we already have a cached copy of this Foundry version, skip login
# entirely so we don't redownload it on every restart. The base image tries,
# in order: foundry_release_url, then username/password, then the cache -
# so as long as credentials are set, it ignores a cache that's already there.
if [ -n "${FOUNDRY_VERSION:-}" ] && [ -f "${CACHE_DIR}/foundryvtt-${FOUNDRY_VERSION}.zip" ]; then
  echo "[ha-foundry-vtt] Found cached Foundry ${FOUNDRY_VERSION} in ${CACHE_DIR}, skipping download."
  unset FOUNDRY_USERNAME FOUNDRY_PASSWORD FOUNDRY_RELEASE_URL
fi

cd /home/node

if command -v setpriv >/dev/null 2>&1; then
  exec setpriv --reuid=node --regid=node --init-groups ./entrypoint.sh "$@"
else
  echo "[ha-foundry-vtt] WARNING: setpriv not found, running as root." >&2
  exec ./entrypoint.sh "$@"
fi
