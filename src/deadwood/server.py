"""The range server: builds the world once, routes requests to the core pages and
to each level's vulnerable app. Binds to loopback only unless explicitly forced."""

from __future__ import annotations

import sqlite3
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from deadwood import data, ui, web
from deadwood.level import Request, Response, all_levels, by_slug

_LOOPBACK = {"127.0.0.1", "localhost", "::1", ""}


class World:
    """One in-memory company database **per level**, so taking one room never leaks
    another's secrets. Each db has the full company world plus that level's own
    seed, and its own lock — a request holds only its room's lock, so a slow
    injection in one room (a capped sleep, a long ping) never freezes the rest."""

    def __init__(self):
        self.dbs: dict[str, sqlite3.Connection] = {}
        self.locks: dict[str, threading.Lock] = {}
        self.build()

    def build(self) -> None:
        for lv in all_levels():
            db = sqlite3.connect(":memory:", check_same_thread=False)
            data.build(db)
            lv.seed(db)
            self.dbs[lv.slug] = db
            self.locks[lv.slug] = threading.Lock()

    def db_for(self, slug: str) -> sqlite3.Connection:
        return self.dbs[slug]

    def lock_for(self, slug: str) -> threading.Lock:
        return self.locks[slug]


def _read_request(h: BaseHTTPRequestHandler) -> Request:
    length = int(h.headers.get("Content-Length") or 0)
    body = h.rfile.read(length) if length else b""
    return Request(h.command, h.path, h.headers, body, h.client_address)


def _not_found() -> Response:
    return Response(ui.shell("not found", '<h1>no such room</h1>'
                             '<p class="dim"><a href="/">← town map</a></p>'), status=404)


class _Handler(BaseHTTPRequestHandler):
    server_version = "Deadwood/range"

    def log_message(self, *a):
        pass

    def _route(self, req: Request) -> Response:
        parts = [p for p in req.route.split("/") if p]
        if not parts:
            return web.town_map()
        if parts[0] == "l" and len(parts) >= 2:
            lv = by_slug(parts[1])
            if lv is None:
                return _not_found()
            if len(parts) == 2:
                return web.briefing(lv, req)
            if parts[2] == "app":
                req.subpath = "/" + "/".join(parts[3:])
                world = self.server.world
                with world.lock_for(lv.slug):
                    return lv.handle(req, world.db_for(lv.slug))
            if parts[2] == "flag" and req.method == "POST":
                return web.submit_flag(lv, req)
        return _not_found()

    def _dispatch(self):
        req = _read_request(self)
        try:
            resp = self._route(req)
        except Exception as exc:                  # a level blowing up shouldn't kill the range
            resp = Response(f"server error: {exc}", status=500,
                            content_type="text/plain; charset=utf-8")
        self.send_response(resp.status)
        self.send_header("Content-Type", resp.content_type)
        self.send_header("Content-Length", str(len(resp.body)))
        for k, v in resp.headers.items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(resp.body)

    do_GET = _dispatch
    do_POST = _dispatch
    do_HEAD = _dispatch


class _Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, addr, world):
        self.world = world
        super().__init__(addr, _Handler)

    def handle_error(self, request, client_address):
        # A scanner — or a browser — hanging up mid-response is routine traffic
        # for a range, not a fault. Swallow the connection-reset noise instead of
        # spilling a socketserver traceback; anything else is a real bug, so let
        # the default handler report it.
        exc = sys.exc_info()[1]
        if isinstance(exc, (BrokenPipeError, ConnectionResetError, ConnectionAbortedError)):
            return
        super().handle_error(request, client_address)


def serve(host: str = "127.0.0.1", port: int = 8666, allow_unsafe: bool = False) -> None:
    if host not in _LOOPBACK and not allow_unsafe:
        raise PermissionError(
            f"refusing to bind {host} — this app is intentionally vulnerable. "
            "Keep it on localhost, or pass --unsafe if you really mean it.")
    world = World()
    httpd = _Server((host, port), world)
    httpd.serve_forever()
