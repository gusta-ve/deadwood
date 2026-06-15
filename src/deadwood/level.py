"""The level contract and registry.

A level is one room in the range: metadata (tier, objective), the *vulnerable app*
itself (``handle``), and the teaching material (hints, the vulnerable source, the
fix). The core renders the chrome — info page, hint reveal, flag form — from this
metadata; the level only has to serve its app and seed its secret.
"""

from __future__ import annotations

import sqlite3
from urllib.parse import parse_qs, urlsplit

from deadwood import flags

# Difficulty tiers, easiest first (used for ordering and the town map).
TIERS = ["Tutorial", "Easy", "Medium", "Hard", "Brutal", "Impossible"]


class Request:
    def __init__(self, method, path, headers, body, client):
        self.method = method
        self.path = path
        u = urlsplit(path)
        self.route = u.path
        self.subpath = ""          # set by the router: path under the level's /app mount
        self.query = {k: v[0] for k, v in parse_qs(u.query, keep_blank_values=True).items()}
        self.raw_query = u.query
        self.headers = headers
        self.body = body or b""
        self.client = client       # (ip, port)


class Response:
    def __init__(self, body, status=200, content_type="text/html; charset=utf-8", headers=None):
        self.body = body.encode("utf-8") if isinstance(body, str) else body
        self.status = status
        self.content_type = content_type
        self.headers = headers or {}


class Level:
    """Subclass and set the metadata; override ``handle`` (the vulnerable app) and,
    if the level hides its own secret, ``seed``."""

    num: int = 0
    slug: str = ""
    title: str = ""
    tier: str = "Tutorial"
    category: str = ""
    brief: str = ""            # one line for the town map
    objective: str = ""        # what to capture
    hints: list[str] = []      # progressive — revealed one at a time
    remediation: str = ""      # how a real app should fix it
    source: str = ""           # the vulnerable code, shown once the player asks

    def flag(self) -> str:
        return flags.flag(self.slug)

    def seed(self, db: sqlite3.Connection) -> None:
        """Insert this level's secret/flag into the world. Default: nothing."""

    def handle(self, req: Request, db: sqlite3.Connection) -> Response:
        """Serve the vulnerable app, mounted at /l/<slug>/app. Override me."""
        return Response("not implemented", status=404)


_REGISTRY: list[Level] = []


def register(cls):
    """Class decorator: instantiate and add a level to the registry."""
    _REGISTRY.append(cls())
    return cls


def all_levels() -> list[Level]:
    return sorted(_REGISTRY, key=lambda lv: lv.num)


def by_slug(slug: str) -> Level | None:
    return next((lv for lv in _REGISTRY if lv.slug == slug), None)
