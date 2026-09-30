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

## 2026-09-28: ddb_scraper_proxy docs update (version 2026.09.28.01, this add-on only)

- Same fix/finding as the standalone ddb-scraper-proxy repo's own
  PROJECT_NOTES.md entry for today: exposing the add-on via a path-based
  Nginx Proxy Manager "Custom Location" under an existing domain doesn't
  work reliably; a dedicated subdomain proxy host does. DOCS.md,
  CHANGELOG.md, and config.yaml updated in ddb_scraper_proxy/ to match the
  standalone repo's copy (still not auto-synced -- copied by hand).
- foundry_vtt/ untouched -- this was ddb_scraper_proxy-only.
- New wrinkle: this is the first time a single add-on inside this
  multi-add-on repo got its own release independent of the others. Tagged
  the GitHub Release as `ddb_scraper_proxy-2026.09.28.01` (prefixed with
  the add-on name) rather than the repo's usual plain `YYYY.MM.DD.##`, to
  disambiguate it from a root-level/whole-repo release like `2026.09.27.03`.
  This is a new precedent, not yet confirmed with Mogie -- worth checking
  he's fine with prefixed tags for single-add-on releases in a
  multi-add-on repo going forward, versus some other scheme.

## 2026-09-28: ddb_scraper_proxy is now the only copy (standalone repo removed)

- Mogie removed the standalone `drmogie/ddb-scraper-proxy` GitHub repo --
  this add-on's copy here is now the only maintained one, no more
  by-hand syncing between two repos.

## 2026-09-29: foundry_vtt gets an icon and logo (2026.09.29.01)

- Mogie asked for "the d20 icon of vtt" on the add-on's Store listing.
  Foundry VTT itself has no public asset repo, so pulled its official
  d20-and-anvil mark from `homarr-labs/dashboard-icons` on GitHub
  (`raw.githubusercontent.com/homarr-labs/dashboard-icons/main/png/foundry-vtt.png`,
  448x512, clean transparent background) rather than felddy/foundryvtt-docker's
  own `assets/logo.png`, which turned out to be a fan-made mashup (the
  same d20 combined with the Docker whale + an anvil), not Foundry's
  actual brand mark.
- Resized with Pillow into `icon.png` (128x128, padded to square first)
  and `logo.png` (250x100 landscape, fit-and-centered) -- both transparent
  background, matching the icon/logo convention set on `network-services`.
- Credited the source in foundry_vtt/README.md.
- Used the add-on's own plain `YYYY.MM.DD.##` tag (`2026.09.29.01`), not
  the `ddb_scraper_proxy-` style prefix -- foundry_vtt's own release
  history has always used plain tags (2026.09.26.01 through .06,
  2026.09.27.01-.03), the prefix convention was only introduced for
  ddb_scraper_proxy to disambiguate it from those.

## 2026-09-29: foundry_auto_update option (2026.09.29.02)

- Mogie asked for a way to stop Foundry from auto-updating on restart.
  Root cause: our Dockerfile builds from `ghcr.io/felddy/foundryvtt:14`,
  a floating major-version tag -- felddy publishes new Foundry builds
  under the same tag over time. `foundry_version` defaults to empty, so
  the version actually installed is whatever the base image happens to
  bundle at build time. Every time the add-on's own image gets
  rebuilt/re-pulled (an add-on update), that bundled default can shift,
  and `run.sh`'s cache-skip logic is keyed on an exact string match
  against `FOUNDRY_VERSION`, so a shifted default forces a fresh
  download+install of the new version -- an implicit, easy-to-miss
  auto-update.
- Added `foundry_auto_update` (bool, default `false`) rather than
  changing what an empty `foundry_version` means, so an explicit
  `foundry_version` still always wins and existing installs that already
  pin a version see no behavior change.
- When off and no explicit `foundry_version` is set, `run.sh` now detects
  the currently-installed version and pins `FOUNDRY_VERSION` to it before
  the existing cache-skip check runs: first from the persisted app
  cache's `${APP_CACHE}/app/package.json` (`.version` field via `jq`,
  most reliable since it's the actual installed app), falling back to
  the newest `foundryvtt-*.zip` under the container cache dir (sorted
  with `sort -V`) if the app cache isn't populated yet. If neither
  exists (first-ever install), there's nothing to pin to, so it installs
  whatever version the image bundles and logs that plainly.
- Default is `false` (auto-update off) rather than `true`/matching prior
  implicit behavior, since "off" is what Mogie asked for and is
  non-breaking either way: on an existing install it just pins to
  whatever is already running, it never forces a downgrade or a
  surprise reinstall.
- Documented in `foundry_vtt/DOCS.md` under Server options and in the
  "Restarts are fast" troubleshooting section.

## 2026-09-29: relay moved in

- Foundry VTT MCP & Rest Relay (`foundry_mcp_rest_relay`) moved here from drmogie/foundry-mcp. Was called FGA Relay.
- Reason: keep the tabletop add-ons together in one store repository.
- New repository means a new add-on ID in Home Assistant (8126043a_foundry_mcp_rest_relay). Data does not carry over: set the login again, new connect key, new API tokens.
- Image is built by .github/workflows/build-foundry-mcp-rest-relay.yml and pushed to ghcr.io. Packages must be set to Public once.
- The Foundry module (fga-relay-connect) and the MCP server stay in foundry-mcp.

## 2026-09-29: relay serves many Foundry servers (2026.09.29.14)

- Each Foundry server is a connection with its own name and connect key, kept in /data/connections.json. Added by app/connections.py. Limit 20.
- First start after the update: the old connect_key.txt key becomes the connection Main, so the module keeps working.
- The socket checks the offered key against every connection and tags the client with its connection id and name. Client lists show them.
- Hub.pick and close_all take an optional connection id. A new key or a removal only closes that connection's sockets.
- Web page: one collapsible status line, one card per connection (name, address, key, test, new key, remove). A new card opens by itself. Cards update in place every 3 seconds so open cards stay open.
- The old /api/connect routes stay and act on the first connection.
- API tokens are not tied to a connection. A token limited to a world already picks the client in that world.
- Tests: 8 new in tests/test_relay.py (72 total).
