# Project notes: ha-foundry-vtt-addon

## 2026-09-26: initial build (version 2026.09.26.01)

Decisions (asked via AskUserQuestion):
- Purpose: run the Foundry VTT server as a HA add-on.
- Source: wrap the felddy/foundryvtt image (tag :14, major version).
- Repo name: ha-foundry-vtt-addon (user chose the ha- prefix; add-ons are
  unprefixed by default, so this was an explicit choice).

Design:
- repository.yaml at root, one add-on folder foundry_vtt/.
- Dockerfile: FROM ghcr.io/felddy/foundryvtt:14, USER root, custom ENTRYPOINT
  run.sh, original CMD kept.
- run.sh: reads /data/options.json with jq, exports FOUNDRY_* / CONTAINER_*
  env vars, chowns /data to node, drops to node with setpriv, then execs the
  image's ./entrypoint.sh.
- Foundry data shares /data with HA's options.json. Foundry uses /data/Config,
  /data/Data, /data/Logs, so there is no file clash. Included in HA backups.
- Watchdog: /api/status. Port 30000/tcp.
- No hacs.json: HACS does not install Supervisor add-ons.

Verified here: YAML parses, run.sh passes bash -n, option reading logic tested
with jq for false/null/empty values.

NOT verified: no Docker daemon in the cloud container, so the image build and
a real start were not tested. Test on ha-pi4 first (supports amd64/aarch64
only via the base image). Ask before installing on ha-blue.

Open risks to check on first real run:
- setpriv present in the base image (Debian slim should have it).
- felddy entrypoint may expect to be run as node; we drop to node before it.
- Add-on hostname stability for the Foundry license.

## 2026-09-26: rename store name (version 2026.09.26.02)

- User did not want "DrMogie" in the add-on repository name.
- repository.yaml name is now "Tabletop Add-ons" (chosen from FGA, Tabletop,
  Critical Hit, Dungeon Master options).
- GitHub repo name stays ha-foundry-vtt-addon. Maintainer field still drmogie.

## 2026-09-26: data in add-on config folder (version 2026.09.26.03)

- User wanted to reach Foundry files from HA (Samba, File editor).
- felddy scripts hardcode /data (DATA_DIR in entrypoint.sh, CONFIG_DIR in
  launcher.sh), so --dataPath cannot be moved.
- Fix: config.yaml maps addon_config (mounted at /config). run.sh symlinks
  /data/Data, /data/Config and /data/Logs to /config/<name>. Existing real
  folders are copied over first.
- container_cache stays in /data (large Foundry zips, no need to browse).
- Not verified on a real server. Symlinked data dir is the main thing to watch.

## 2026-09-26: Open Web UI button (version 2026.09.26.04)

- Added `webui: http://[HOST]:[PORT:30000]` to config.yaml so the add-on page
  shows an Open Web UI button that opens Foundry.
- No ingress: Foundry needs its own port and websockets, so the button opens
  the direct port 30000 address on the HA host.

## 2026-09-27: skip redownload on restart (version 2026.09.26.05)

- User's foundry_username/password were set, which the base image checks
  before its own container_cache (order: release_url, username/password,
  cache) - so it redownloaded and reinstalled Foundry on every restart even
  though a cached copy already existed.
- Fix: run.sh now checks for a cached foundryvtt-<version>.zip in
  CONTAINER_CACHE before starting; if found, it unsets
  FOUNDRY_USERNAME/PASSWORD/RELEASE_URL so the base image falls through to
  its own cache path instead of logging in again.
- Tested the unset logic standalone; not tested against the real image
  (no Docker here). Watch the Log tab for "Found cached Foundry" on the
  second start.
