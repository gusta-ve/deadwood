"""Per-install flags.

Each level's flag is `DEADWOOD{<slug>_<digest>}`, where the digest is an HMAC of
the slug under a secret generated once on this machine. So flags are stable (the
CLI can grade them) but unique to your install — you can't google the answer.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from pathlib import Path


def state_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return Path(base) / "deadwood"


def _secret() -> bytes:
    p = state_dir() / "secret"
    try:
        return p.read_bytes()
    except OSError:
        p.parent.mkdir(parents=True, exist_ok=True)
        s = secrets.token_bytes(32)
        try:
            p.write_bytes(s)
        except OSError:
            pass
        return s


def flag(slug: str) -> str:
    digest = hmac.new(_secret(), slug.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
    return f"DEADWOOD{{{slug.replace('-', '_')}_{digest}}}"


def check(slug: str, value: str) -> bool:
    return secrets.compare_digest((value or "").strip(), flag(slug))
