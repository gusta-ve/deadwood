from deadwood import progress


def test_progress_roundtrip(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert progress.solved() == set()
    progress.mark("first-blood")
    progress.mark("whispers")
    assert progress.solved() == {"first-blood", "whispers"}
    progress.mark("first-blood")                    # idempotent
    assert progress.solved() == {"first-blood", "whispers"}
    progress.reset()
    assert progress.solved() == set()
