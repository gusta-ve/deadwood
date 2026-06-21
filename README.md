# deadwood

A self-hosted **web-security range** that doubles as a tutorial — graded levels
from the first trivial injection to the deliberately near-impossible. It's the
practice town for the dead man's hand: scout each room with
[**wraith**](https://github.com/gusta-ve/wraith), take it with
[**hickok**](https://github.com/gusta-ve/hickok), capture the flag, then read the
vulnerable source and the fix.

Dependency-free (stdlib + SQLite). Runs on **127.0.0.1 only**.

[![PyPI](https://img.shields.io/pypi/v/deadwood-sec?color=ffb946&label=pypi)](https://pypi.org/project/deadwood-sec/)
[![CI](https://github.com/gusta-ve/deadwood/actions/workflows/ci.yml/badge.svg)](https://github.com/gusta-ve/deadwood/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/gusta-ve/deadwood?color=ffb946)](https://github.com/gusta-ve/deadwood/releases)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![MIT](https://img.shields.io/badge/license-MIT-green)

> ⚠️ **deadwood is intentionally vulnerable, by design.** It refuses to bind
> anything but loopback unless you force it. Never expose it to a network, a VM
> bridge, or the internet. Attack only this app, on your own machine.

- [Install](#install)
- [Run it](#run-it)
- [Take your first flag](#take-your-first-flag)
- [How a level works](#how-a-level-works)
- [The levels](#the-levels)
- [Pairing with wraith & hickok](#pairing-with-wraith--hickok)
- [Tests](#tests)

## Install

```bash
pipx install deadwood-sec      # gives you the `deadwood` command
```

Or from a clone: `pip install -e .` — or run it with no install:
`PYTHONPATH=src python3 -m deadwood`.

## Run it

```bash
deadwood serve                 # http://127.0.0.1:8666  (the town map)
deadwood levels                # list the rooms and your progress
deadwood learn first-blood     # a level's briefing: objective, hints, source, the fix
deadwood flag first-blood 'DEADWOOD{...}'   # submit a captured flag
```

Open the map in a browser, pick a room, and point your tools at the app URL it
gives you (e.g. `http://127.0.0.1:8666/l/first-blood/app?id=1`).

## Take your first flag

Room 1 is a staff directory that drops your `id` straight into the SQL. The query
returns three columns, so a `UNION SELECT` of three values reads any table you
like — here, the hidden `secrets`:

```console
$ deadwood serve &
$ curl 'http://127.0.0.1:8666/l/first-blood/app?id=0 UNION SELECT 1,label,value FROM secrets'
...
DEADWOOD{first_blood_825bb8670d30d32c}

$ deadwood flag first-blood 'DEADWOOD{first_blood_825bb8670d30d32c}'
  ✓ First Blood — taken. that's the hand.
```

That's the whole loop: find the flaw, read the flag, submit it. Flags are unique
to your install, so the one above won't match yours — capture your own. Stuck?
`deadwood learn first-blood` walks you in, one hint at a time.

## How a level works

Every room is the same shape, easy to the hard:

- a **realistic app** (the fictional *Deadwood Telegraph & Trust Co.* — employees,
  customers, accounts, telegrams) with one real flaw;
- a **flag** to capture (`DEADWOOD{...}`, unique to your install);
- **progressive hints** — reveal them one at a time, only if you want them;
- the **vulnerable source** and **how to fix it**, once you ask (spoilers).

Play blind for the CTF, or lean on the hints and `learn` for the tutorial. Your
captures are tracked locally.

## The levels

Fifteen rooms, Tutorial → Endgame. Each maps to a technique you can practise by
hand or drive with hickok/wraith:

| # | Room | Tier | Vector |
|---|------|------|--------|
| 1 | First Blood | Tutorial | SQL injection — UNION (in-band) |
| 2 | Whispers | Easy | SQL injection — boolean-blind |
| 3 | The Ledger | Easy | SQL injection — error-based (extractvalue, 32-char windows) |
| 4 | The Strongbox | Medium | SQL injection — UNION (double-quote context) |
| 5 | The Telegraph | Medium | SQL injection — time-based blind |
| 6 | The Bouncer | Medium | SQL injection — authentication bypass |
| 7 | Back Door | Medium | OS command injection → shell |
| 8 | The Watchman | Hard | SQL injection — time-based (parenthesised `func('…')` context) |
| 9 | Sleight of Hand | Hard | UNION behind a quote/catalog filter |
| 10 | The Gauntlet | Hard | UNION behind a keyword WAF (case/comment evasion) |
| 11 | The Cipher | Hard | Server-side template injection → RCE |
| 12 | The Annex | Brutal | SQL injection — cross-database (ATTACH) |
| 13 | Dead Man's Hand | Brutal | Blind injection behind a WAF denylist |
| 14 | The Vault | Impossible | Second-order (stored) SQL injection |
| 15 | The Whole Hand | Endgame | Full chain — recon → SQLi → session pivot → BAC → the vault |

The world behind the rooms is deliberately the edge-case data a real dump hits, not
a toy table: **NULL** cells that drop rows from a naive dump, a `group_concat`
**capped at 1024 bytes** like MySQL, values **longer than 32 chars**, **unicode**,
and a second **ATTACHed database**. That's where a tool's real bugs show up.

## Pairing with wraith & hickok

deadwood is the range the tools grew up on. Scout the whole town, then take it:

```bash
deadwood serve &                                                  # the town
wraith 127.0.0.1:8666 --sessions examples/deadwood_sessions.json  # recon the whole surface
hickok sql -u 'http://127.0.0.1:8666/l/first-blood/app?id=1' -p id --dump secrets
```

**The Whole Hand** (room 15) is the live company app, end to end: recon it with
wraith — it lights the IDOR, the broken access control, the XSS, the open redirect,
the reflective CORS, the missing headers and the injectable directory — then dump the
sessions table with hickok, ride a live **admin** token to the vault. SQLi → a real
credential → broken access control → the house's deepest secret. A genuine
discovery, on the one target that's yours.

When a tool can't take a room, that's a bug to fix in the tool; when a room is
too easy, that's a room to harden. They sharpen each other.

## Tests

```bash
pip install -e ".[dev]" && pytest
```

The suite checks the engine (flags, registry, per-level isolation, the seeded
world) and that each level's flaw behaves as taught. See
[CONTRIBUTING.md](CONTRIBUTING.md) to add a room and [SECURITY.md](SECURITY.md)
for the responsible-use policy.

## License

MIT.

---

*Deadwood, 1876 — where the dead man's hand was dealt.*
