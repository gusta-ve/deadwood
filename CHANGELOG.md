# Changelog

All notable changes to this project are documented here. The format is loosely
based on [Keep a Changelog](https://keepachangelog.com/).

## [0.5.3]

Follow-up to the 0.5.2 housekeeping — fixes two things that pass left behind.

### Fixed
- **The README's first-flag demo now actually runs.** The `curl` line carried
  literal spaces in the URL, which curl rejects (`HTTP 000`); it uses
  `-G --data-urlencode` now — copy-paste-able, and the SQL stays readable.
- **Every level's docstring number matches its place in the range.** The 0.4–0.5
  renumbering had left thirteen of them stale (`l05_the_telegraph.py` opened
  "Level 3 —") or blank ("Level — …"); each now reads "Level N —" with the same
  N the registry sorts by.

## [0.5.2]

Housekeeping — no behaviour change.

### Changed
- **Level files are renamed to match their actual order.** After the 0.4–0.5
  renumbering, the on-disk prefixes had drifted (`l03_the_telegraph.py` was
  room 5, six newer rooms had no number at all). Every level module is now
  `lNN_<slug>.py` in play order, so the directory reads top-to-bottom like the
  range itself.
- The README gains a **Take your first flag** walkthrough — the full
  find → read → submit loop on room 1 — and its level table and tiers track the
  current fifteen rooms (Tutorial → Endgame).
- `.ruff_cache/` is git-ignored.

## [0.5.1]

### Fixed
- Two company-wide secrets (`smtp_relay`, `backup_passphrase`) were seeded both in the
  shared world and again inside a level's own `seed`, so they appeared twice when that
  room's `secrets` table was dumped. The levels keep only their own flag now.

## [0.5.0]

The range becomes a target you can take whole. On top of the leveled rooms, deadwood
now serves the **live company app** with the full recon surface, and a capstone heist
that chains the rooms into one real conquest.

### Added
- **The Whole Hand** (room 15, the **Endgame**) — the live Deadwood Trust web app in
  one crawlable target: a real login and sessions, broken access control (`/admin`
  checks login, not role), IDOR (`/orders/<id>`), reflected XSS, an open redirect,
  reflective CORS, an insecure tracking cookie, missing security headers, and a
  UNION-injectable staff directory. The heist: SQLi the directory → dump the live
  **sessions** table → ride an **admin** token to the vault → the flag. SQLi → a real
  credential → broken access control → the prize, on the one target that's yours.
- **A wider recon surface**, server-wide: a virtual host that serves an internal
  site, exposed files (`/.git/config`, `/backup.sql`, `/.env`), and a **soft-404**
  (200 on missing paths) so a content scanner has to calibrate its noise.
- `examples/deadwood_sessions.json` — drop-in sessions for wraith's access-control
  phase (`wraith 127.0.0.1:8666 --sessions examples/deadwood_sessions.json`).

### Changed
- A new `Endgame` tier for the capstone (fifteen rooms now, Tutorial → Endgame).

## [0.4.0]

The range grew up. Nine focused rooms became fourteen, and the world behind them is
now the edge-case-rich data a *real* dump hits — so a tool walked over deadwood meets
the bugs a small lab hides (NULL coalescing, group_concat truncation, error-window
chunking, context detection, cross-database reach).

### Added
- **An edge-case world.** The company database now carries NULL cells in dumpable
  tables, values longer than 32 chars, tables over 1024 bytes, unicode / accented
  data, live staff sessions and API keys, and a second **ATTACHed database**
  (`archive`) — a cross-database surface.
- **`group_concat` modelled on MySQL** (skip NULLs, cap the result at 1024 bytes),
  and a MySQL-style NULL-propagating `concat`. A whole-table dump on this SQLite
  range now hits the same two bugs a real one does: a row with a NULL cell silently
  vanishes, and a table past the cap truncates mid-dump with no error.
- **Five new rooms**, each a distinct technique / injection context:
  - **The Ledger** — error-based: a verbose MySQL error is the read channel, with the
    real ~32-char `extractvalue` truncation, so a long value must be read in windows
    and reassembled.
  - **The Strongbox** — UNION in a double-quote string context.
  - **The Watchman** — time-based blind in a parenthesised `func('…')` context (the
    `')` breakout).
  - **The Gauntlet** — UNION behind a keyword WAF: case-folding / inline-comment
    evasion, quote-free literals.
  - **The Annex** — cross-database: the flag lives in the ATTACHed `archive`.

### Changed
- The rooms are renumbered into one escalating run, Tutorial → Impossible (fourteen).

## [0.3.4]

### Added
- **`make lint` (and a CI lint step) now run ruff** over `src` and `tests`,
  restricted to the pyflakes F-rules — unused imports, f-strings with no
  placeholders, undefined names. Security and style rule sets stay off by design:
  the rooms are intentionally vulnerable and those rules would be all false
  positives. This is the check that catches the kind of dead f-string tidied up
  in 0.3.3.

## [0.3.3]

### Fixed
- **Back Door no longer leaks The Cipher's flag.** The Cipher seeds its flag into
  the process environment (`DEADWOOD_CIPHER`); Back Door ran its shell with the
  whole environment, so `host=…; env` in a Medium room handed you a Hard room's
  flag with no SSTI at all. Back Door now scrubs every *other* room's `DEADWOOD_*`
  from the shell environment, keeping only its own — per-room isolation holds.
- **The per-install flag secret is read once and fails loud.** A missing or empty
  secret file is regenerated correctly, and if it can't be persisted deadwood now
  warns instead of silently minting a fresh, ungradable flag on every call.

### Changed
- **Per-room database locks.** Each level's in-memory database gets its own lock
  rather than sharing one global lock, so a long-running injection in one room (a
  capped `sleep`, a slow diagnostics ping) no longer freezes the whole range.
- A missing banner asset degrades to a plain wordmark instead of taking down the
  entire CLI at import time.

## [0.3.2]

### Fixed
- **No more `BrokenPipeError` tracebacks when a client hangs up.** A scanner
  (wraith) or a browser dropping a connection mid-response is routine traffic for
  a range, but the stdlib server was spilling a `socketserver` traceback to the
  console each time. The server now swallows connection-reset/broken-pipe errors
  quietly and keeps serving; any other error still surfaces.

## [0.3.1]

### Changed
- New banner: a **dead tree** — the wood the town is named for — drawn in a
  density ramp and lit by a vertical gold→amber gradient (bright twigs, ember
  trunk), the companion to wraith's wraith and hickok's gunslinger. Honours
  `NO_COLOR` and falls back to clean monochrome off a terminal; `DEADWOOD_COLOR=1`
  forces colour. The version and tagline moved onto a single identity line.

## [0.3.0]

### Added
- The final two rooms: **Dead Man's Hand** (Brutal — boolean-blind injection
  behind a WAF that strips quotes, blocks the catalog and blocks UNION with a
  third-state page) and **The Vault** (Impossible — second-order / stored SQL
  injection: input stored safely, then used unescaped on another query). The
  range is now nine rooms, Tutorial → Impossible.

### Changed
- The web UI got a pass: a progress bar on the town map, tier-coloured difficulty
  badges (Tutorial → Impossible), and tidier level rows.

## [0.2.0]

### Added
- Three new rooms: **The Bouncer** (Medium — SQLi authentication bypass),
  **Sleight of Hand** (Hard — UNION behind a quote-stripping / catalog-blocking
  filter, the kind that exercises a quote-free engine), and **The Cipher**
  (Hard — server-side template injection → RCE).
- Repo parity with the tools: `SECURITY.md`, `CONTRIBUTING.md`, a `Makefile`,
  CI/Release badges and a Tests section in the README.

## [0.1.0]

### Added
- The range: a dependency-free, leveled web-security target that runs on
  localhost only, with a town-map UI, per-level briefings, **progressive hints**,
  a **view-the-vulnerable-source / how-to-fix** reveal, per-install flags
  (`DEADWOOD{...}`) and a local scoreboard.
- A realistic seeded world — the fictional *Deadwood Telegraph & Trust Co.*
  (employees, customers, accounts, transactions, telegrams).
- CLI: `serve`, `levels`, `learn <slug>`, `flag <slug> <value>`, `reset`.
- **Level 1 — First Blood**: in-band UNION SQL injection in the staff directory.
