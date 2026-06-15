from deadwood import flags


def test_flag_format_is_stable_and_per_slug(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    f = flags.flag("first-blood")
    assert f.startswith("DEADWOOD{") and f.endswith("}")
    assert "first_blood" in f                       # slug, dashes → underscores
    assert flags.flag("first-blood") == f           # stable across calls
    assert flags.flag("whispers") != f              # unique per level


def test_check_grades_the_flag(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    f = flags.flag("whispers")
    assert flags.check("whispers", f)
    assert flags.check("whispers", f"  {f}  ")      # tolerant of whitespace
    assert not flags.check("whispers", "DEADWOOD{nope}")
    assert not flags.check("whispers", flags.flag("first-blood"))   # wrong level
