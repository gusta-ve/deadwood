import sqlite3

import deadwood.levels  # noqa: F401
from deadwood import data
from deadwood.level import by_slug


def _db_for(lv):
    db = sqlite3.connect(":memory:")
    data.build(db)
    lv.seed(db)
    return db


def test_company_world_is_populated():
    db = sqlite3.connect(":memory:")
    data.build(db)
    assert db.execute("SELECT count(*) FROM employees").fetchone()[0] > 5
    assert db.execute("SELECT count(*) FROM customers").fetchone()[0] > 5
    assert db.execute("SELECT count(*) FROM accounts").fetchone()[0] > 5
    assert db.execute("SELECT count(*) FROM transactions").fetchone()[0] > 5


def test_sleep_function_is_available():
    db = sqlite3.connect(":memory:")
    data.build(db)
    assert db.execute("SELECT sleep(0)").fetchone()[0] == 0      # registered for time-based


def test_levels_are_isolated(monkeypatch, tmp_path):
    """Taking one room must not expose another's flag — each level has its own db."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    fb, wh = by_slug("first-blood"), by_slug("whispers")
    fb_secrets = "".join(r[0] for r in _db_for(fb).execute("SELECT value FROM secrets"))
    wh_secrets = "".join(r[0] for r in _db_for(wh).execute("SELECT value FROM secrets"))
    assert fb.flag() in fb_secrets and fb.flag() not in wh_secrets
    assert wh.flag() in wh_secrets and wh.flag() not in fb_secrets
