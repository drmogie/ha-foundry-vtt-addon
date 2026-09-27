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

## 2026-09-27: fix the real slow-restart cause (version 2026.09.26.06)

- User asked to improve boot/reboot time. Grabbed the real Foundry VTT log
  from HA (via Chrome + downloading it, then reading the file directly -
  the in-app log viewer's virtualized scroll fought browser automation).
- Found the actual cost: cache-skip (from .05) was working fine ("Found
  cached Foundry 14.368 ... skipping download"), but "Extracting Node.js
  release file" to "Installation completed" took 3.5 minutes on its own.
  That is Foundry's own unzip of its already-downloaded, already-cached
  archive into /home/node/resources/app - NOT covered by our earlier fix.
- Root cause: HA Supervisor recreates the add-on's container on every
  start/stop (confirmed by "No Foundry Virtual Tabletop installation
  detected" appearing on every restart), so only bind-mounted /data
  survives; the container's own writable layer (including the unzipped
  app under /home/node/resources) does not.
- Fix: run.sh now also symlinks /home/node/resources to
  /data/resources, the same trick as the Data/Config/Logs folders, so the
  unzipped app itself survives a restart. entrypoint.sh checks
  resources/app/package.json before deciding to reinstall, so once this
  cache is warm it should skip the unzip entirely.
- Verified `rm -r resources` (entrypoint.sh's own version-mismatch cleanup)
  only removes the symlink, not the /data target, with a real shell test.
  Simulated all 4 cycles (fresh install, plain restart, version bump,
  restart after bump) in a sandbox before shipping - all behaved correctly,
  including wiping the old cached app before saving a new version so
  stale files from a previous version don't linger.
- Considered and rejected: baking Foundry into a custom multi-stage Docker
  image at build time (felddy's own "pre-installed distribution" pattern).
  Would avoid the extraction step entirely, but needs credentials or a
  timed URL at *build* time, a manual rebuild for every Foundry version,
  and a much bigger image - not worth it when this symlink fix targets the
  same measured bottleneck for much less complexity and no rebuild step.
- foundry_ip_discovery was also seen set to true on the live add-on
  (default is false in config.yaml, but an existing install keeps its
  saved option value across upgrades) - worth turning off for a small
  additional saving, but it wasn't the multi-minute cost; that was the
  extraction step above.
- Not verified beyond the sandbox simulation - no Docker here. Ask Mogie
  to update, restart twice, and check the Log tab for "Found the installed
  Foundry app already saved, skipping the unzip." on the second restart.

## 2026-09-27: added DDB Scraper Proxy as a second add-on (version 2026.09.27.03)

- Mogie asked to both push ddb-scraper-proxy to GitHub as its own repo AND
  add it into this repo (Tabletop Add-ons), so it's installable from either
  place.
- Copied ddb_scraper_proxy/ (config.yaml, build.yaml, Dockerfile, run.sh,
  server.py, translations/, DOCS.md, CHANGELOG.md) in as-is, as a sibling
  to foundry_vtt/. It keeps its own independent version (2026.09.27.01,
  tracked in its own CHANGELOG.md) -- not lockstepped with foundry_vtt's.
- Updated root README.md's Add-ons list and version badge, and root
  CHANGELOG.md with a repo-level entry for the addition.
- Standalone repo: https://github.com/drmogie/ddb-scraper-proxy (its own
  PROJECT_NOTES.md lives there).
