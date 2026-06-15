# Changelog

All notable changes to this project are documented here. The format is loosely
based on [Keep a Changelog](https://keepachangelog.com/).

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
