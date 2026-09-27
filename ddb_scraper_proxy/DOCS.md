# DDB Scraper Proxy

A small HTTP proxy for D&D Beyond character data, built for Foundry VTT's
`ddb-live-importer` module (but usable by anything).

## The problem this solves

Foundry's own page can't fetch a character straight from D&D Beyond -- not
a login problem, a browser one. D&D Beyond's character API never sends the
CORS permission header a browser requires before it will let *any* other
site read the response, whether the character is public or private,
logged in or not. This was confirmed directly: even a plain, cookie-free
fetch to a character that's set to Public still gets blocked by the
browser itself.

A server-to-server request has no such restriction -- CORS is purely a
browser rule. So this add-on does the fetch server-side and hands the JSON
back with the header Foundry needs.

## Why "public characters only"

This proxy has no D&D Beyond login of its own, and never sends one. That's
what makes it safe to run wide open (it can never see anyone's private
data) -- but it also means it can only ever succeed for a character D&D
Beyond will hand out with **no login at all**, i.e. one set to Public. A
request for a private character just gets whatever error D&D Beyond
itself returns (usually 401 or 403), passed straight through, so the
caller can tell "this one's private" apart from "something's actually
broken."

## Installing

1. **Settings → Add-ons → Add-on Store**
2. **⋮** (top right) → **Repositories**
3. Add this repository's URL
4. Install **DDB Scraper Proxy**, then **Start** it (no configuration
   needed to get going -- see below for the two options if you want them)

## Configuration

```yaml
ddb_base_url: "https://character-service.dndbeyond.com/character/v5/character/"
allowed_origin: "*"
```

- **ddb_base_url** -- the address to scrape from. The character ID is
  appended straight onto the end (so it must end in `/`). You'd only
  change this if D&D Beyond changes their API address, or you want to
  point the proxy somewhere else for testing.
- **allowed_origin** -- which site is allowed to read the response from a
  browser (the CORS `Access-Control-Allow-Origin` header). `*` (default)
  allows any site -- since this only ever serves data D&D Beyond already
  hands out with no login, that's not really an exposure, just an open
  door. Set it to your Foundry URL (e.g. `https://vtt.mogie.io`) if you'd
  rather lock it down to just that.

## Using it

Once running, the add-on listens on port **8099** (remap the host port
under the add-on's own **Network** tab if you need to).

- `GET /character/<id>` -- returns that character's raw JSON, exactly as
  D&D Beyond's own API returns it, with CORS headers added. `<id>` must be
  the plain numeric character ID (the number in the character's D&D
  Beyond URL).
- `GET /health` -- a quick check that the add-on is up and what it's
  currently configured to scrape from. Returns `{"status": "ok", ...}`.

Point `ddb-live-importer` (or anything else) at
`http://<this device's address>:8099/character/<id>` to fetch a public
character with no manual copy/paste step at all.

## Troubleshooting

Check the add-on's **Log** tab first -- every request logs one line
prefixed `[ddb-public-proxy]`.

- **A request for a character you know is public still fails**: check the
  Log tab for the actual upstream status D&D Beyond returned. A 401/403
  usually means the character isn't actually set to Public (recheck its
  sharing settings on D&D Beyond's own site) -- this add-on has no way to
  authenticate around that, by design.
- **502 "Couldn't reach D&D Beyond"**: a real network problem between this
  add-on and D&D Beyond's servers (DNS, outage, firewall) -- not something
  this add-on can fix on its own.
- **CORS error in Foundry's browser console anyway**: check `allowed_origin`
  matches the exact origin Foundry is running on (scheme + host + port,
  no trailing slash) if you changed it from `*`.

## Limitations

- **Public characters only.** This is not a bug to be fixed later -- it's
  the whole reason this is safe to run without any credentials at all.
  Private characters still need `ddb-live-importer`'s console-paste flow.
- No caching -- every request hits D&D Beyond's API fresh. Fine for
  occasional use; avoid hammering it in a tight loop.
