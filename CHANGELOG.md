# Changelog

## 2026.09.29.06

- Foundry VTT MCP & Rest Relay 2026.09.29.12: casts skip the click-to-place spell area unless asked.

## 2026.09.29.05

- Foundry VTT MCP & Rest Relay 2026.09.29.11: the use item route takes clearArea to remove the spell area a cast leaves on the board.

## 2026.09.29.04

- Foundry VTT MCP & Rest Relay 2026.09.29.10: the compendium import route can add spells, features and gear straight onto an actor.

## 2026.09.29.03

- Adds the Foundry VTT MCP & Rest Relay add-on (`foundry_mcp_rest_relay`), moved here from the foundry-mcp repository and renamed from FGA Relay. See foundry_mcp_rest_relay/CHANGELOG.md for its own version history.

## 2026.09.29.02

- Adds a `foundry_auto_update` option (default off). Off keeps Foundry pinned to whatever version is already installed across restarts and add-on updates; the base image's Foundry build tag floats, so without this a plain add-on update could silently install a newer Foundry version. Turn it on, or set `foundry_version` explicitly, to change that.

## 2026.09.29.01

- Adds an icon and logo to the Add-on Store listing: Foundry Virtual Tabletop's own d20 mark (via homarr-labs/dashboard-icons).

## 2026.09.27.03

- Added the DDB Scraper Proxy add-on (`ddb_scraper_proxy`) to this repository -- a companion proxy for the `ddb-live-importer` Foundry module. See ddb_scraper_proxy/CHANGELOG.md for its own version history.

## 2026.09.27.02

- Fixes a real bug in .01: caching the installed Foundry app under /data/resources made Foundry refuse to start properly, because its app folder then resolved (through the symlink) to a path inside its own data path ("The data path ... must not be inside the application location ..."). This showed up as the license page reappearing even with a valid license saved. The app cache now lives under /config/resources instead, which is a separate mount, so it stays out of Foundry's data path. Also cleans up the old /data/resources folder automatically.

## 2026.09.27.01

- Fixes the .06 restart fix itself: the previous version still reinstalled Foundry every restart. The container's own filesystem resets on every start, so the check meant to migrate an old install was wiping out the good saved copy in /data before ever using it. It now only migrates when there is an actual installed app to save, so cached restarts should finally be fast.

## 2026.09.26.06

- Fixes the biggest cause of slow restarts: Home Assistant recreates this add-on's container on every start, so the installed Foundry app itself (not just the download) had to be unpacked again each time, taking several minutes. It is now saved in /data too, so a restart on the same version should be much faster.

## 2026.09.26.05

- Skips the download and login on restart when a cached copy of your Foundry version already exists. Fixes a full download and install happening every restart.

## 2026.09.26.04

- Added an Open Web UI button on the add-on page. It opens the Foundry server page.

## 2026.09.26.03

- Foundry Data, Config and Logs now live in the add-on config folder (addon_configs), so you can browse them with Samba or the File editor add-on.
- Existing files from earlier versions are moved over on first start.

## 2026.09.26.02

- Renamed the add-on repository to "Tabletop Add-ons" (store display name only).

## 2026.09.26.01

- First release.
- Wraps ghcr.io/felddy/foundryvtt:14.
- Add-on options for login, admin key, world, reverse proxy, and more.
- Watchdog on /api/status.
