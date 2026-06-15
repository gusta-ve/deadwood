import threading
import urllib.request

import pytest

import deadwood.levels  # noqa: F401
from deadwood import server


def test_serve_refuses_non_loopback():
    with pytest.raises(PermissionError):
        server.serve("0.0.0.0", 0, allow_unsafe=False)


def test_http_smoke(monkeypatch, tmp_path):
    """The range actually serves: the map and a level app both answer 200."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    world = server.World()
    httpd = server._Server(("127.0.0.1", 0), world)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    port = httpd.server_address[1]
    try:
        base = f"http://127.0.0.1:{port}"
        assert b"Deadwood" in urllib.request.urlopen(base + "/", timeout=5).read()
        assert b"Staff Directory" in urllib.request.urlopen(
            base + "/l/first-blood/app?id=1", timeout=5).read()
    finally:
        httpd.shutdown()
