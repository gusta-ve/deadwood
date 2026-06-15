# Contributing

deadwood is dependency-free — standard library and SQLite only, Python 3.10+.

## Setup

```bash
pip install -e ".[dev]"
pytest
```

## Adding a level

Each level is a module under `src/deadwood/levels/` that subclasses `Level` and
self-registers with `@register`:

- set the metadata: `num`, `slug`, `title`, `tier`, `category`, `brief`,
  `objective`, `hints` (progressive), `remediation`, `source` (the vulnerable
  snippet shown on request);
- seed your secret/flag in `seed(db)` if the level needs one;
- serve the vulnerable app in `handle(req, db)`.

Then add it to `levels/__init__.py` and give it a test in `tests/`. Keep every
level **isolated** — exploiting one must never leak another's flag (each level
gets its own database).

## House rules

- Standard library only.
- Run `pytest` before opening a PR; CI runs it on Python 3.10–3.12.
- Only run the range, and the attacks it teaches, against your own loopback host.
