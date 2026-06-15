"""Which rooms you've taken — a tiny local scoreboard (JSON under the data dir)."""

from __future__ import annotations

import json

from deadwood import flags


def _path():
    return flags.state_dir() / "progress.json"


def solved() -> set[str]:
    try:
        return set(json.loads(_path().read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return set()


def mark(slug: str) -> None:
    s = solved()
    s.add(slug)
    try:
        flags.state_dir().mkdir(parents=True, exist_ok=True)
        _path().write_text(json.dumps(sorted(s)), encoding="utf-8")
    except OSError:
        pass


def reset() -> None:
    try:
        _path().unlink()
    except OSError:
        pass
