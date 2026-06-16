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
import sys
from pathlib import Path

# Read once per process: the secret stays stable for the run even if the data dir
# is unwritable, and we never re-warn or re-mint on every flag() call.
_secret_cache: bytes | None = None


def state_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return Path(base) / "deadwood"


def _secret() -> bytes:
    global _secret_cache
    if _secret_cache is not None:
        return _secret_cache
    p = state_dir() / "secret"
    try:
        s = p.read_bytes()
    except OSError:
        s = b""
    if not s:                                   # missing, empty, or unreadable — mint a fresh one
        s = secrets.token_bytes(32)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(s)
        except OSError as exc:                   # can't persist → flags differ run-to-run; say so
            print(f"deadwood: warning — can't persist the flag secret ({exc}); "
                  "flags won't be stable across runs.", file=sys.stderr)
    _secret_cache = s
    return s


def flag(slug: str) -> str:
    digest = hmac.new(_secret(), slug.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
    return f"DEADWOOD{{{slug.replace('-', '_')}_{digest}}}"


def check(slug: str, value: str) -> bool:
    return secrets.compare_digest((value or "").strip(), flag(slug))
