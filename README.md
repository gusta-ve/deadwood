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

Tutorial → impossible. Each maps to a technique you can practise by hand or drive
with hickok/wraith:

| # | Room | Tier | Vector |
|---|------|------|--------|
| 1 | First Blood | Tutorial | SQL injection — UNION (in-band) |
| 2 | Whispers | Easy | SQL injection — boolean-blind |
| 3 | The Telegraph | Medium | SQL injection — time-based blind |
| 4 | Back Door | Medium | OS command injection → shell |
| 5 | The Bouncer | Medium | SQL injection — authentication bypass |
| 6 | Sleight of Hand | Hard | UNION behind a quote/catalog filter |
| 7 | The Cipher | Hard | Server-side template injection → RCE |

*(the Brutal and Impossible rooms — a WAF'd blind injection and the Vault —
land next.)*

## Pairing with wraith & hickok

deadwood is the range the tools grew up on. A typical run:

```bash
deadwood serve &                                   # the town
hickok sql -u 'http://127.0.0.1:8666/l/first-blood/app?id=1' -p id --dump secrets
```

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
