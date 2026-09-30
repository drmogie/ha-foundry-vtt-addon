"""The list of Foundry servers that may connect. Each one has a name and its own connect key."""

from __future__ import annotations

import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .settings import Settings, load_connect_key

MAX_CONNECTIONS = 20
MAX_NAME = 40


class ConnectionError_(Exception):
    """A problem worded so a person can act on it."""


@dataclass
class Connection:
    id: str
    name: str
    key: str
    created_at: float = field(default_factory=time.time)

    def dump(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "key": self.key, "createdAt": self.created_at}


def _new_key() -> str:
    return "fga_" + secrets.token_urlsafe(24)


class ConnectionStore:
    def __init__(self, settings: Settings) -> None:
        self.path = settings.data_dir / "connections.json"
        self.items: list[Connection] = []
        self._load(settings)

    def _load(self, settings: Settings) -> None:
        if self.path.exists():
            try:
                rows = json.loads(self.path.read_text())
                self.items = [Connection(r["id"], r["name"], r["key"], r.get("createdAt", time.time())) for r in rows]
                return
            except (ValueError, KeyError, TypeError):
                pass
        # First run with this feature: the one old key becomes the first connection, so Foundry keeps working.
        self.items = [Connection(secrets.token_hex(4), "Main", load_connect_key(settings))]
        self._save()

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps([c.dump() for c in self.items], indent=2) + "\n")
        try:
            tmp.chmod(0o600)
        except OSError:
            pass
        os.replace(tmp, self.path)

    def get(self, conn_id: str) -> Connection | None:
        return next((c for c in self.items if c.id == conn_id), None)

    def first(self) -> Connection | None:
        return self.items[0] if self.items else None

    def match_key(self, offered: str) -> Connection | None:
        """Find the connection that owns this key. Checks every one so timing tells nothing."""
        found = None
        for conn in self.items:
            if hmac.compare_digest(offered.encode(), conn.key.encode()):
                found = conn
        return found

    def _clean_name(self, name: str) -> str:
        name = " ".join((name or "").split())
        if not name:
            raise ConnectionError_("Give the connection a name.")
        if len(name) > MAX_NAME:
            raise ConnectionError_(f"Keep the name under {MAX_NAME} letters.")
        return name

    def add(self, name: str) -> Connection:
        if len(self.items) >= MAX_CONNECTIONS:
            raise ConnectionError_(f"That is the limit of {MAX_CONNECTIONS} connections.")
        name = self._clean_name(name)
        if any(c.name.lower() == name.lower() for c in self.items):
            raise ConnectionError_("A connection with that name already exists.")
        conn = Connection(secrets.token_hex(4), name, _new_key())
        self.items.append(conn)
        self._save()
        return conn

    def rename(self, conn_id: str, name: str) -> Connection:
        conn = self.get(conn_id)
        if conn is None:
            raise ConnectionError_("That connection is already gone.")
        name = self._clean_name(name)
        if any(c.id != conn_id and c.name.lower() == name.lower() for c in self.items):
            raise ConnectionError_("A connection with that name already exists.")
        conn.name = name
        self._save()
        return conn

    def regenerate(self, conn_id: str) -> Connection:
        conn = self.get(conn_id)
        if conn is None:
            raise ConnectionError_("That connection is already gone.")
        conn.key = _new_key()
        self._save()
        return conn

    def remove(self, conn_id: str) -> Connection:
        conn = self.get(conn_id)
        if conn is None:
            raise ConnectionError_("That connection is already gone.")
        self.items.remove(conn)
        self._save()
        return conn
