# Changelog

All notable changes to this project are documented here. The format is loosely
based on [Keep a Changelog](https://keepachangelog.com/).

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
