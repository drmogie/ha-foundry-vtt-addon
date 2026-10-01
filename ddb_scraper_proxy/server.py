#!/usr/bin/env python3
"""
ddb_scraper_proxy / server.py
-------------------------------------------------------------------------
Small HTTP proxy for D&D Beyond character JSON.

WHY THIS EXISTS: a browser (Foundry's own page) can't fetch D&D Beyond's
character API directly -- confirmed live, D&D Beyond's server never sends
the CORS header a browser requires to let another site read the response,
public character or not, logged in or not. A plain server-to-server
request has no such restriction at all (CORS is a browser-only rule), so
this tiny service does the fetch server-side and hands the JSON back to
Foundry with the header it needs.

WHY "PUBLIC CHARACTERS ONLY": this proxy never sends any login cookie or
token to D&D Beyond -- it can't, it doesn't have one, and it's not asking
for one. So it can only ever succeed for a character D&D Beyond will hand
out with no login at all, i.e. a character set to Public. A private
character request will get whatever error D&D Beyond itself returns
(typically 401/403), which this proxy passes straight through so the
caller can tell the difference between "private" and "actually broken."

Stdlib only -- no pip packages, so the Dockerfile only needs `python3`.
-------------------------------------------------------------------------
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

OPTIONS_FILE = "/data/options.json"
DEFAULT_BASE_URL = "https://character-service.dndbeyond.com/character/v5/character/"
DEFAULT_ALLOWED_ORIGIN = "*"
LISTEN_PORT = 8099
TEST_PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test.html")
REQUEST_TIMEOUT_SECONDS = 10

# Character IDs are plain numbers. Restricting to this pattern (rather than
# accepting an arbitrary path/URL from the caller) is what keeps this a
# narrow single-purpose proxy instead of an open relay that could be pointed
# at any address.
CHARACTER_ID_RE = re.compile(r"^[0-9]{1,20}$")


def log(message):
    # Unbuffered stdout (server started with `python3 -u`) so this shows up
    # in the add-on's Log tab immediately, not just on a delay/on exit.
    print(f"[ddb-public-proxy] {message}", flush=True)


def load_options():
    """Reads the add-on's config from Supervisor's options.json. Falls back
    to defaults if the file is missing (e.g. running this outside Supervisor
    for a quick local test)."""
    base_url = DEFAULT_BASE_URL
    allowed_origin = DEFAULT_ALLOWED_ORIGIN

    if os.path.isfile(OPTIONS_FILE):
        try:
            with open(OPTIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            base_url = data.get("ddb_base_url") or base_url
            allowed_origin = data.get("allowed_origin") or allowed_origin
        except (json.JSONDecodeError, OSError) as err:
            log(f"WARNING: couldn't read {OPTIONS_FILE} ({err}); using defaults")
    else:
        log(f"NOTE: {OPTIONS_FILE} not found; using built-in defaults (not running under Supervisor?)")

    if not base_url.endswith("/"):
        base_url += "/"

    return base_url, allowed_origin


BASE_URL, ALLOWED_ORIGIN = load_options()


class ProxyHandler(BaseHTTPRequestHandler):
    server_version = "ddb-public-proxy/1.0"

    # Quiets BaseHTTPRequestHandler's default per-request stderr line in
    # favor of the single, clearer log() line each handler writes itself.
    def log_message(self, fmt, *args):
        pass

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "86400")

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_raw_json(self, status, raw_bytes):
        """Passes an already-JSON response body through byte-for-byte
        (avoids re-encoding D&D Beyond's own JSON), still adding our headers."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw_bytes)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(raw_bytes)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path.split("?")[0] == "/health":
            self._send_json(200, {
                "status": "ok",
                "service": "ddb-public-proxy",
                "ddbBaseUrl": BASE_URL,
                "note": "Only works for D&D Beyond characters set to Public -- see /character/<id>. Open / for the test page."
            })
            return

        if self.path.split("?")[0] in ("/", "/test", "/test/"):
            # Simple page for trying the proxy by hand. Same origin, so no CORS needed.
            try:
                with open(TEST_PAGE, "rb") as f:
                    page = f.read()
            except OSError:
                self._send_json(404, {"error": "Test page not found."})
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(page)
            return

        match = re.match(r"^/character/([^/?]+)/?$", self.path)
        if not match:
            self._send_json(404, {"error": "Not found. Use /character/<id>."})
            return

        character_id = match.group(1)
        if not CHARACTER_ID_RE.match(character_id):
            self._send_json(400, {"error": "Character id must be a plain number."})
            return

        target_url = BASE_URL + character_id
        started = time.monotonic()
        try:
            req = urllib.request.Request(
                target_url,
                headers={"Accept": "application/json", "User-Agent": self.server_version}
            )
            # No cookies, no auth header, on purpose -- this proxy has no
            # login of its own. That's exactly what limits it to characters
            # D&D Beyond will hand out with no login at all (Public ones).
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                body = resp.read()
                elapsed_ms = round((time.monotonic() - started) * 1000)
                log(f"GET /character/{character_id} -> upstream {resp.status} in {elapsed_ms}ms")
                self._send_raw_json(resp.status, body)
        except urllib.error.HTTPError as err:
            # D&D Beyond answered, but with an error -- most likely this
            # character is private (401/403) or the id doesn't exist (404).
            # Passed straight through so the caller can tell which.
            body = err.read()
            elapsed_ms = round((time.monotonic() - started) * 1000)
            log(f"GET /character/{character_id} -> upstream error {err.code} in {elapsed_ms}ms (likely private or not found)")
            if body:
                self._send_raw_json(err.code, body)
            else:
                self._send_json(err.code, {
                    "error": f"D&D Beyond returned {err.code}.",
                    "hint": "This usually means the character is set to private, or the id is wrong."
                })
        except urllib.error.URLError as err:
            elapsed_ms = round((time.monotonic() - started) * 1000)
            log(f"GET /character/{character_id} -> network error after {elapsed_ms}ms: {err}")
            self._send_json(502, {"error": f"Couldn't reach D&D Beyond: {err.reason}"})

    def do_POST(self):
        self._send_json(404, {"error": "Not found. This proxy only supports GET /character/<id>."})


def main():
    log(f"Starting on port {LISTEN_PORT}, base URL {BASE_URL}, allowed origin {ALLOWED_ORIGIN}")
    server = ThreadingHTTPServer(("0.0.0.0", LISTEN_PORT), ProxyHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()


if __name__ == "__main__":
    sys.exit(main())
