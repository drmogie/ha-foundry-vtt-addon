# Changelog

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
