# Foundry VTT add-on

## First start

1. Open the Configuration tab.
2. Enter `foundry_username` and `foundry_password`.
   Or use `foundry_release_url` instead (a timed link from your
   foundryvtt.com profile).
3. Set `foundry_admin_key`. This is the admin password for the setup screen.
4. Save, then Start the add-on.
5. Wait a few minutes. The first start downloads Foundry.
6. Open `http://<your-ha-ip>:30000`.

Watch the Log tab. It shows download and license messages.

## Options

### Login (pick one way)

- `foundry_username` and `foundry_password`: your foundryvtt.com login.
- `foundry_release_url`: a timed download link. Runs once, then the download is cached.
- `foundry_license_key`: optional. Only needed if you have several licenses.

### Server

- `foundry_admin_key`: admin password. If empty, no admin password is set.
- `foundry_version`: leave empty for the newest version the image supports.
  Set it to pin a version, like `14.367`.
- `foundry_world`: folder name of a world to start automatically.
- `foundry_language`: default language. Default `en.core`.
- `foundry_css_theme`: `dark`, `fantasy`, or `scifi`.
- `foundry_telemetry`: send anonymous usage data to Foundry.
- `foundry_compress_websocket`: less network use. Recommended on.
- `foundry_minify_static_files`: faster page loads. Recommended on.
- `foundry_ip_discovery`: lets Foundry check its public IP at startup.
  Off makes startup faster.

### Reverse proxy (Nginx Proxy Manager, Cloudflare Tunnel)

- `foundry_hostname`: your public name, like `foundry.example.com`.
- `foundry_proxy_ssl`: turn on if your proxy uses HTTPS.
- `foundry_proxy_port`: the public port, usually `443`.
- `foundry_route_prefix`: only if you serve Foundry from a sub path.

In Nginx Proxy Manager:

- Forward to your HA host, port 30000.
- Turn on Websockets Support. Foundry needs it.

### Container

- `container_preserve_config`: on means changes made in Foundry's own
  setup screen are kept across restarts. Off means the add-on options
  rewrite the config every start.
- `container_cache_size`: how many downloaded Foundry versions to keep.
- `container_verbose`: more log detail.
- `timezone`: for example `America/Los_Angeles`.

## Data and backups

- Everything lives in the add-on's data folder.
- Home Assistant backups include it, so large worlds make large backups.
- You can exclude this add-on from a backup if your world is big.

## License note

Foundry ties your license to the container hostname. Home Assistant gives
this add-on a fixed hostname, so restarts are fine. Do not run the same
license on two servers at once.

## Troubleshooting

- "No Foundry download credentials set": fill in the login options.
- Stuck at download: check the Log tab and your login.
- Cannot connect through the proxy: check Websockets Support, and set
  `foundry_hostname`, `foundry_proxy_ssl`, and `foundry_proxy_port`.
- Not tested on every setup yet. Please report problems on GitHub.
