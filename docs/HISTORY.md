# Implementation lineage

The memory revision mechanisms existed in the private application before Evidence
Memory became a standalone public library. The public package was first released
on **1 October 2026**. A checkpoint in the private repository's canonical `main`
history, recorded on **23 September 2026**, already contains the memory publisher
and its regression tests.

## Recorded checkpoints

| Date | Record | What it establishes |
| --- | --- | --- |
| 23 September 2026 | Private canonical `main` commit `4c8c3dd576fdcaf20478d5f000bffed8d37df276` | Source-backed publication, immutable identities and availability, conflicting revision checks, corrections, retractions, and historical reads were implemented in the host application. |
| 1 October 2026 | [First public release](https://github.com/yellowagmi/evidence-memory/releases/tag/v0.1.0), source commit `51a4822cc837fd40646d5fffd9a49cbf25475a61` | The reusable mechanisms were extracted behind a generic storage interface, with standalone SQLite storage, a Python package, CLI, public tests, and contribution documentation. The private consumer was adapted to the pinned public source. |

The September date identifies a recorded checkpoint, not the original creation
date of every mechanism. The standalone API, packaging, and public integration
work belong to the October release.

## Historical source excerpts

Two small excerpts from the September checkpoint are retained verbatim:

- [Revision checks](history/2026-09-23-revision-checks.txt): rejects a backdated
  successor, identifies the current head, and requires the specified predecessor
  to match it and be available to the input.
- [Replay and competing revisions test](history/2026-09-23-replay-and-conflicts.txt):
  checks identical replay, immutable availability, and two concurrent successors
  producing one accepted head and one conflict.

These `.txt` files preserve the original source bytes, including indentation.
They are archival excerpts, not standalone historical builds. Their surrounding
host code, fixture helpers, application bindings, and private records are omitted.
No replacement historical implementation was created for this repository.

The [manifest](history/manifest.json) records the original commit and Git blob
identities, source line ranges, and SHA-256 of each published excerpt. The source
repository remains private, so readers can inspect the excerpts and verify their
published hashes but cannot independently resolve the original commits here.
Git timestamps and hashes alone do not independently establish publication dates.

## Historical validation

On **1 October 2026**, the September checkpoint's original memory regression
suite was run against an isolated snapshot of that checkpoint's source. All
**14 tests passed on Python 3.12.10**. This is a present-day check of historical
code; it is not a claim that those tests were run or passed on 23 September.
The public manifest records the bounded result. The private suite and its full
run log remain with the consuming application.

The current library's corresponding behavior is exercised by the public tests
in [test_memory.py](../tests/test_memory.py), including replay, competing revisions,
corrections and retractions, and existing-journal compatibility. The maintained
implementation is [core.py](../src/evidence_memory/core.py).

This lineage documents software development. It does not establish model learning
gains, performance at scale, or recursive self-improvement.
