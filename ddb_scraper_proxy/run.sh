#!/usr/bin/env bash
# D&D Beyond Public Character Proxy - Home Assistant add-on
#
# All the actual logic (reading options.json, serving requests) lives in
# server.py, which is plain Python 3 standard library, no pip packages.
# This script just starts it. -u keeps stdout unbuffered so log lines show
# up in the add-on's Log tab immediately instead of only on exit.
set -e
exec python3 -u /server.py
