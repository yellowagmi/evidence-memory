# Evidence Memory

Persistent evidence memory for iterative agent improvement.

An agent's earlier conclusion is useful only if later work can inspect its
sources, recover its history, and recognize corrections. Evidence Memory is a
small Python library for retaining that chain across sessions and iterations.

The implementation was extracted from a real private stateful research system.
Its application adapter consumes the same library through a pinned, byte-identical
source snapshot. The adapter retains application authorization and its existing
journal schema. This repository contains the reusable component and its tests.

The memory implementation predates this standalone package. See the
[implementation lineage](docs/HISTORY.md) for verbatim source and test excerpts
from a September 2026 checkpoint, with commit references and file hashes.

## What it does

- Retains JSON evidence with stable content identities and availability times.
- Publishes source-backed interpretations, including contrary evidence and limitations.
- Preserves corrections and retractions through compare-and-swap revision history.
- Reads versions and their status as of a specified cutoff.
- Isolates records by namespace and stream, and supports paginated discovery.
- Works standalone with SQLite or inside an existing application's transaction.

The library has no runtime dependencies beyond Python's standard library.
Python 3.11 or later is required.

## Install

Install the initial tagged release from GitHub:

```sh
python -m pip install "git+https://github.com/yellowagmi/evidence-memory.git@v0.1.0"
```

This release is not published to PyPI.

## Use the library

```python
from evidence_memory import Memory, Scope, SQLiteStore

scope = Scope("my-project", "investigation-1")
store = SQLiteStore("memory.sqlite3")
memory = Memory(store, scope)

source = store.register(
    scope,
    {"observation": "Restoration failed after the context transition"},
    available_at="2026-01-01T10:00:00Z",
)
version = memory.publish(
    kind="workflow_memory",
    key="restoration-check",
    content={"next_step": "Inspect the retained response before retrying"},
    supporting_refs=[source],
    contrary_refs=[],
    applicability="Investigations of interrupted work",
    limitations="An interpretation requiring further verification",
    provenance={"cutoff": "2026-01-01T10:00:00Z", "task_id": "investigation-1"},
    available_at="2026-01-01T10:01:00Z",
)

record = memory.read(version, "2026-01-01T10:02:00Z")
original = memory.evidence(source, "2026-01-01T10:02:00Z")
```

To correct a version, publish with the same `kind` and `key`, pass its ID as
`supersedes`, and provide the new content and input cutoff. To retract it, also
pass `status="retracted"`. Old versions remain readable. Replaying an identical
publication returns the same ID; conflicting successors cannot both become heads.

## Command line

`evidence-memory` uses the same API. Supply a database, namespace, and stream,
then choose `register`, `publish`, `read`, `evidence`, or `list`:

```sh
evidence-memory --database memory.sqlite3 --namespace my-project --stream investigation-1 --help
```

`register` accepts an evidence JSON file and `--available-at`. `publish` accepts
a JSON file with the fields shown in `memory.publish` above. Reads and lists
require `--cutoff`; `list` accepts `--after` for the returned cursor.

## Relationship to recursive self-improvement

This is one infrastructure slice for RSI research: keeping previous attempts,
evidence, and revised interpretations available to subsequent work. It does not
modify an agent, select improvements, train a model, or establish improved
capability. Whether retained memory helps an improvement loop is a separate
evaluation question. See the [research direction](docs/ROADMAP.md).

## Boundaries

Availability times and provenance come from the host application. A hash identifies
the registered JSON body, not the truth of a statement or the original external
source bytes. Scope filtering is not an authentication system. Source prose remains
data; the library executes no model-authored commands.

The initial release targets local SQLite use. Distributed operation, semantic
search, automatic summarization, and measured learning gains are outside its
current scope. See [design and integration](docs/DESIGN.md).

## Develop and contribute

```sh
python -m pip install .
python -m unittest discover -s tests -v
```

Tests use self-contained fixtures and exercise chronology, revisions, concurrent
conflicts, transaction rollback, restart, journal adapters, and the command line.
They require neither model credentials nor private application data.

Contributions are welcome. Start with the [contribution guide](CONTRIBUTING.md)
and the [bounded roadmap](docs/ROADMAP.md).

MIT licensed. Built by [@yellowagmi](https://github.com/yellowagmi).
