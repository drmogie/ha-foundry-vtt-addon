# Changelog

## 2026.09.30.02

- The test page is now the home page (/). /test still works. The JSON health check moved to /health only, so anything that checked / for the JSON should use /health.

## 2026.09.30.01

- New test page at /test. Find a character ID from a link to your D&D Beyond campaigns, paste it, get the data, open the proxy link, copy the data, or clear it.
- The /health answer now mentions the test page.

## 2026.09.28.01

- Documentation: added guidance on exposing the proxy externally --
  recommend a dedicated subdomain proxy host instead of a path-based
  "Custom Location" under an existing domain, after confirming the latter
  can silently fail to route in Nginx Proxy Manager.


## 2026.09.27.01

- Initial release. Proxies `GET /character/<id>` to D&D Beyond's character
  API server-side and returns the JSON with CORS headers added, so a
  browser page (Foundry VTT) can read it directly -- something D&D
  Beyond's own server never allows on its own, confirmed even for a public
  character with no login cookie sent at all.
- Public characters only, by design: this add-on never sends a D&D Beyond
  login of any kind, so it can only ever succeed where D&D Beyond hands
  out data with none. A private character's request gets D&D Beyond's own
  error passed straight through.
- Configurable `ddb_base_url` (the address to scrape from) and
  `allowed_origin` (CORS allow-list, defaults to `*`).
