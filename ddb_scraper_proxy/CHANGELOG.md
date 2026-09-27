# Changelog

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
