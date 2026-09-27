# Changelog

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
