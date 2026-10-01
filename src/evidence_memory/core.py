"""Source-backed revisions extracted from an existing application memory layer."""
from copy import deepcopy
import json

from ._json import MemoryError, at, content_sha256, nonempty

KINDS_MEMORY = ("research_dossier", "workflow_memory")


class Memory:
    """An isolated namespace/stream view; interpretations never become facts.

    Provenance and evidence availability are supplied by a trusted host. This
    library does not authenticate users or determine whether a source is true.
    """
    def __init__(self, store, scope, *, artifact_schema="evidence_memory.artifact.v1",
                 index_schema="evidence_memory.index.v1", scope_label="namespace_stream"):
        self.store, self.scope = store, scope
        self.artifact_schema, self.index_schema, self.scope_label = artifact_schema, index_schema, scope_label

    def publish(self, **values):
        with self.store.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            return self.publish_in_transaction(connection, **values)

    def publish_in_transaction(self, connection, *, kind, key, content,
                               supporting_refs, contrary_refs, applicability, limitations,
                               provenance, available_at, supersedes=None, status="proposed",
                               source_cutoff=None, resolved_sources=None, source_records=None):
        """Join a host transaction, retaining compare-and-swap revision lineage.

        resolved_sources/source_records are adapter hooks for host-resolved
        external references. The host must resolve them in the same scope and
        at source_cutoff; standalone publication resolves registered sources.
        """
        if not connection.in_transaction:
            raise MemoryError("memory:publication_requires_transaction")
        if kind not in KINDS_MEMORY or status not in ("proposed", "retracted"):
            raise MemoryError("memory:kind_or_status")
        for name, value in dict(key=key, applicability=applicability, limitations=limitations).items():
            nonempty(value, name)
        if not isinstance(content, dict):
            raise MemoryError("memory:content_object")
        if (not isinstance(supporting_refs, list) or not supporting_refs
                or not isinstance(contrary_refs, list)
                or any(not isinstance(ref, str) for ref in supporting_refs + contrary_refs)):
            raise MemoryError("memory:source_refs")
        if status == "retracted" and supersedes is None:
            raise MemoryError("memory:retraction_without_prior")
        if not isinstance(provenance, dict) or "cutoff" not in provenance:
            raise MemoryError("memory:provenance_cutoff")
        if at(available_at) < at(provenance["cutoff"]):
            raise MemoryError("memory:publication_before_input")
        source_cutoff = source_cutoff or provenance["cutoff"]
        if at(source_cutoff) > at(available_at):
            raise MemoryError("memory:source_cutoff_after_publication")
        refs = set(supporting_refs + contrary_refs)
        if resolved_sources is None:
            sources = {}
            for ref in refs | ({supersedes} if supersedes is not None else set()):
                row = self.store.get(connection, self.scope, ref, cutoff=source_cutoff)
                if row is not None:
                    sources[ref] = json.loads(row["body_json"])
        else:
            sources = resolved_sources
        if any(ref not in sources for ref in refs):
            raise MemoryError("memory:source_not_available_at_input")
        body = {"schema_version": self.artifact_schema, "key": key, "status": status,
                "supersedes": supersedes, "content": deepcopy(content),
                "supporting_refs": deepcopy(supporting_refs), "contrary_refs": deepcopy(contrary_refs),
                "applicability": applicability, "limitations": limitations,
                "provenance": deepcopy(provenance),
                "source_hashes": {ref: content_sha256(sources[ref]) for ref in refs},
                "scope": self.scope_label, "interpretation_is_verified_fact": False}
        if source_records:
            body["source_records"] = deepcopy(source_records)
        ident = content_sha256({"class": kind, "body": body})
        existing = self.store.get(connection, self.scope, ident)
        if existing:
            if existing["available_at"] != available_at:
                raise MemoryError("memory:immutable_availability")
            return ident
        versions = [dict(row) for row in self.store.records(connection, self.scope, kinds=(kind,), key=key)]
        if any(at(row["available_at"]) > at(available_at) for row in versions):
            raise MemoryError("memory:backdated_revision")
        retired = {json.loads(row["body_json"]).get("supersedes") for row in versions}
        heads = [row["id"] for row in versions if row["id"] not in retired]
        if heads != ([] if supersedes is None else [supersedes]):
            raise MemoryError("memory:revision_conflict")
        if supersedes is not None and supersedes not in sources:
            raise MemoryError("memory:prior_not_available_at_input")
        self.store.insert(connection, self.scope, ident, kind, available_at, body)
        return ident

    def _versions(self, connection, cutoff, *, key=None, after=0):
        moment = at(cutoff)
        return [dict(row) for row in self.store.records(connection, self.scope,
                kinds=KINDS_MEMORY, key=key, after=after) if at(row["available_at"]) <= moment]

    def _status(self, row, versions):
        body = json.loads(row["body_json"])
        successors = [other["id"] for other in versions if other["class"] == row["class"]
                      and json.loads(other["body_json"]).get("supersedes") == row["id"]]
        return {"status": body["status"], "superseded": bool(successors), "successors": successors}

    def read(self, ident, cutoff):
        with self.store.connect() as connection:
            if not connection.in_transaction:
                connection.execute("BEGIN")
            row = self.store.get(connection, self.scope, ident, cutoff=cutoff)
            if row is None or row["class"] not in KINDS_MEMORY:
                raise MemoryError("memory:artifact_unavailable")
            versions = self._versions(connection, cutoff, key=json.loads(row["body_json"])["key"])
            return {"id": ident, "record_class": row["class"], "available_at": row["available_at"],
                    "body": json.loads(row["body_json"]), **self._status(row, versions)}

    def evidence(self, ident, cutoff):
        """Read the registered source body, without upgrading its authority."""
        with self.store.connect() as connection:
            if not connection.in_transaction:
                connection.execute("BEGIN")
            row = self.store.get(connection, self.scope, ident, cutoff=cutoff)
            if row is None:
                raise MemoryError("memory:evidence_unavailable")
            body = json.loads(row["body_json"])
            return {"id": ident, "record_class": row["class"], "available_at": row["available_at"],
                    "body": body, "source_sha256": content_sha256(body),
                    "source_sha256_scope": "registered_body_not_original_record",
                    "interpretation_is_verified_fact": False, "cutoff": cutoff}

    def list(self, cutoff, *, after=0, key=None, limit=30):
        if type(after) is not int or after < 0 or type(limit) is not int or not 1 <= limit <= 1000:
            raise MemoryError("memory:invalid_page")
        with self.store.connect() as connection:
            if not connection.in_transaction:
                connection.execute("BEGIN")
            moment = at(cutoff)
            rows = []
            for row in self.store.records(connection, self.scope, kinds=KINDS_MEMORY, key=key, after=after):
                if at(row["available_at"]) <= moment:
                    rows.append(dict(row))
                if len(rows) > limit:
                    break
            records = []
            for row in rows[:limit]:
                body = json.loads(row["body_json"])
                versions = self._versions(connection, cutoff, key=body["key"])
                records.append({"id": row["id"], "cursor": row["cursor"], "key": body["key"],
                                "record_class": row["class"], "available_at": row["available_at"],
                                "applicability": body["applicability"], **self._status(row, versions)})
            return {"records": records, "next_cursor": rows[limit-1]["cursor"] if len(rows) > limit else None}

    def view(self, cutoff):
        with self.store.connect() as connection:
            if not connection.in_transaction:
                connection.execute("BEGIN")
            versions = self._versions(connection, cutoff)
        successors = {}
        for row in versions:
            prior = json.loads(row["body_json"]).get("supersedes")
            if prior:
                successors.setdefault(prior, []).append(row["id"])
        records = []
        for row in sorted(versions, key=lambda item: (at(item["available_at"]), item["id"])):
            body = json.loads(row["body_json"])
            records.append({"id": row["id"], "record_class": row["class"], "key": body["key"],
                            "available_at": row["available_at"], "status": body["status"],
                            "superseded": row["id"] in successors,
                            "successors": successors.get(row["id"], []),
                            "applicability": body["applicability"], "limitations": body["limitations"],
                            "supporting_refs": body["supporting_refs"], "contrary_refs": body["contrary_refs"]})
        return {"schema_version": self.index_schema, "cutoff": cutoff, "records": records,
                "active_ids": [row["id"] for row in records if not row["superseded"] and row["status"] != "retracted"],
                "retrieval": "get_evidence(id); list_evidence(record_class)", "scope": self.scope_label,
                "interpretations_are_not_authoritative_state": True}
