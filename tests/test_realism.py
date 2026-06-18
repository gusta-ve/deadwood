"""The realistic-data edge cases — the bugs a tool meets only on a real target."""

import sqlite3

from deadwood import data


def _world():
    db = sqlite3.connect(":memory:")
    data.build(db)
    return db


def test_null_cells_drop_rows_from_a_naive_dump():
    """A row with a NULL cell concatenates to NULL and group_concat skips it — a
    naive whole-table dump silently loses those rows."""
    db = _world()
    cols = [r[1] for r in db.execute("PRAGMA table_info(employees)")]
    rowexpr = " || '~c~' || ".join(cols)                     # NULL anywhere -> NULL row
    dumped = db.execute(f"SELECT group_concat({rowexpr}, '~r~') FROM employees").fetchone()[0]
    recovered = [r for r in dumped.split("~r~") if r]
    truth = db.execute("SELECT count(*) FROM employees").fetchone()[0]
    assert truth == 18
    assert db.execute("SELECT count(*) FROM employees WHERE mfa_secret IS NULL").fetchone()[0] > 0
    assert len(recovered) < truth                            # rows vanished


def test_group_concat_capped_at_1024_bytes_like_mysql():
    db = _world()
    dumped = db.execute("SELECT group_concat(detail, '~r~') FROM audit_log").fetchone()[0]
    assert db.execute("SELECT count(*) FROM audit_log").fetchone()[0] == 60
    assert len(dumped.encode("utf-8")) <= 1024              # truncates mid-table, no error


def test_concat_propagates_null_like_mysql():
    db = _world()
    assert db.execute("SELECT concat('a', NULL, 'b')").fetchone()[0] is None
    assert db.execute("SELECT concat('a', 'b')").fetchone()[0] == "ab"


def test_unicode_and_long_values_present():
    db = _world()
    cipher = db.execute("SELECT value FROM secrets WHERE label='telegraph_cipher_key'").fetchone()[0]
    assert any(ord(c) > 127 for c in cipher)                # non-ASCII -> charcode fallback
    assert db.execute("SELECT max(length(api_token)) FROM employees").fetchone()[0] > 32


def test_attached_archive_is_a_second_database():
    db = _world()
    names = [r[1] for r in db.execute("PRAGMA database_list")]
    assert "archive" in names
    assert db.execute("SELECT count(*) FROM archive.secrets").fetchone()[0] >= 1


def test_sleep_is_capped():
    db = _world()
    assert db.execute("SELECT sleep(0)").fetchone()[0] == 0
