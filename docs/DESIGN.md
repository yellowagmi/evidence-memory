# Design and integration

## Extraction boundary

The original application separated retained evidence, historical interpretations,
and authoritative current state. This library extracts source identity, revision
publication, and time-aware reads from its memory implementation. Application
task ownership, review identities, worker leases, outcome/accounting adapters,
and operational actions remain in the consuming application's adapter.

The original consumer uses the released source files directly through a pinned
snapshot. It configures its existing table layout and artifact metadata, leaving
its stored IDs and JSON representation unchanged. Compatibility checks remain
in that private consumer; the public tests verify the reusable behavior without
requiring its journal or source data.

## Data model

A `Scope(namespace, stream)` identifies a logical partition. Source records carry
an ID, record class, registered JSON body, and availability time. Memory versions
add a key, authored content, supporting and contrary references, applicability,
limitations, provenance, status, and an optional superseded version.

The ID hashes a canonical representation of record class and body. Publication
time is stored separately and cannot change on replay. References identify exact
registered bodies; hashes do not establish source accuracy. `provenance.cutoff`
specifies what was available to the originating input. Timestamps require a
timezone and comparisons preserve microsecond precision.

## Publication transaction

Publication obtains a SQLite write transaction before reading sources and heads.
It verifies source availability, preserves source-body hashes, checks that the
named predecessor is the current head, and inserts one new version. A competing
successor conflicts rather than silently replacing another revision.

Corrections and retractions append versions. Reads of earlier cutoffs exclude
later corrections. Reading an old version at a later cutoff exposes its
supersession status without changing its stored body. The host determines which
interpretations to use; a retrieved record never becomes authoritative state.

## Existing journals

`SQLiteRecords` wraps a host connection factory and a `RecordLayout`. Optional
`SourceLayout` entries expose additional retained sources. Layouts name columns
and tables, not arbitrary SQL. The connection factory must yield `sqlite3.Row`
records, commit on success, roll back on failure, and close connections.

`Memory.publish_in_transaction` lets a host validate its own task ownership or
lease and publish within the same transaction. The host can provide
`resolved_sources` and `source_records` for references it has already resolved
in the correct scope and at the declared cutoff. These are trusted adapter hooks,
not an untrusted client API. They must not be exposed directly to a model or
remote caller that can invent provenance or bypass source checks.

Adapters may configure `artifact_schema`, `index_schema`, and `scope_label` to
preserve an existing wire format. The standalone defaults use library-owned
tables and `evidence_memory.*` schema identifiers. No existing application schema
is migrated by constructing `SQLiteRecords`.

## Limits and tradeoffs

SQLite provides a compact local persistence boundary and serializes competing
writes. This release makes no distributed throughput or universal exactly-once
claim. Discovery cursors are insertion positions; use a fixed cutoff when paging.
They do not pin membership against sources inserted later with older availability
times. The host must seal availability inputs when it needs a reproducible snapshot.

Views and some revision checks inspect scoped history. Performance improvements
should preserve time and revision semantics and be supported by measurements.
The library does not defend against a host that directly rewrites its database.
Namespace filtering does not replace authentication, filesystem permissions,
or a service's access controls.

Preserving a conclusion makes it inspectable. It does not show that the conclusion
is correct, that a model used it, or that a subsequent result improved because of it.
