"""SQLite records, with configurable layouts for existing application journals."""
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3

from ._json import MemoryError, at, canonical_json, content_sha256, nonempty


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise MemoryError("memory:invalid_sql_identifier")
    return '"' + value + '"'


@dataclass(frozen=True)
class Scope:
    namespace: str
    stream: str

    def __post_init__(self):
        nonempty(self.namespace, "namespace")
        nonempty(self.stream, "stream")


@dataclass(frozen=True)
class RecordLayout:
    table: str = "memory_records"
    namespace: str = "namespace"
    stream: str = "stream"
    record_class: str = "record_class"

    def __post_init__(self):
        for value in (self.table, self.namespace, self.stream, self.record_class):
            identifier(value)


@dataclass(frozen=True)
class SourceLayout:
    """An existing source table with id, available_at and body_json columns."""
    table: str
    record_class: str
    namespace: str = "namespace"
    stream: str = "stream"

    def __post_init__(self):
        for value in (self.table, self.namespace, self.stream):
            identifier(value)
        nonempty(self.record_class, "source_class")


class SQLiteRecords:
    """Adapt a context-managed connection factory without creating a schema.

    The factory must yield a sqlite3.Connection with sqlite3.Row row_factory,
    commit on success, roll back on failure, and close after use. Host-provided
    layouts are trusted configuration; callers cannot supply arbitrary SQL.
    """
    def __init__(self, connect, *, layout=None, extra_sources=()):
        self.connect = connect
        self.layout = layout or RecordLayout()
        self.extra_sources = tuple(extra_sources)

    def records(self, connection, scope, *, kinds=None, key=None, after=0):
        layout = self.layout
        query = (f'SELECT rowid AS cursor,id,{identifier(layout.record_class)} AS class,'
                 f'available_at,body_json FROM {identifier(layout.table)} WHERE '
                 f'{identifier(layout.namespace)}=? AND {identifier(layout.stream)}=? AND rowid>?')
        args = [scope.namespace, scope.stream, after]
        if kinds is not None:
            if not kinds:
                return iter(())
            query += f' AND {identifier(layout.record_class)} IN (' + ','.join('?' for _ in kinds) + ')'
            args.extend(kinds)
        if key is not None:
            query += " AND json_extract(body_json,'$.key')=?"
            args.append(key)
        return connection.execute(query + " ORDER BY rowid", args)

    def get(self, connection, scope, ident, *, cutoff=None):
        layout = self.layout
        row = connection.execute(
            f'SELECT id,{identifier(layout.record_class)} AS class,available_at,body_json '
            f'FROM {identifier(layout.table)} WHERE {identifier(layout.namespace)}=? '
            f'AND {identifier(layout.stream)}=? AND id=?',
            (scope.namespace, scope.stream, ident)).fetchone()
        if row is None:
            for source in self.extra_sources:
                row = connection.execute(
                    f'SELECT id,? AS class,available_at,body_json FROM {identifier(source.table)} '
                    f'WHERE {identifier(source.namespace)}=? AND {identifier(source.stream)}=? AND id=?',
                    (source.record_class, scope.namespace, scope.stream, ident)).fetchone()
                if row is not None:
                    break
        if row is not None and (cutoff is None or at(row["available_at"]) <= at(cutoff)):
            return dict(row)
        return None

    def insert(self, connection, scope, ident, kind, available_at, body):
        layout = self.layout
        connection.execute(
            f'INSERT INTO {identifier(layout.table)} '
            f'({identifier(layout.namespace)},{identifier(layout.stream)},id,available_at,'
            f'{identifier(layout.record_class)},body_json) VALUES (?,?,?,?,?,?)',
            (scope.namespace, scope.stream, ident, available_at, kind, canonical_json(body)))


class SQLiteStore(SQLiteRecords):
    """A standalone local store. Initialization creates only library-owned tables."""
    def __init__(self, path, *, timeout=15):
        self.path = Path(path)
        self.timeout = timeout
        self.path.parent.mkdir(parents=True, exist_ok=True)
        super().__init__(self._connect)
        with self.connect() as connection:
            connection.executescript('''
                CREATE TABLE IF NOT EXISTS memory_records (
                  namespace TEXT NOT NULL, stream TEXT NOT NULL, id TEXT NOT NULL,
                  available_at TEXT NOT NULL, record_class TEXT NOT NULL, body_json TEXT NOT NULL,
                  PRIMARY KEY(namespace,stream,id));
                CREATE INDEX IF NOT EXISTS memory_records_key
                  ON memory_records(namespace,stream,record_class,json_extract(body_json,'$.key'));
            ''')

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.path, timeout=self.timeout)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def register(self, scope, body, *, record_class="evidence", available_at):
        """Retain supplied JSON; identity hashes that JSON, not an external file."""
        nonempty(record_class, "source_class")
        if record_class in ("research_dossier", "workflow_memory"):
            raise MemoryError("memory:reserved_source_class")
        at(available_at)
        ident = content_sha256({"class": record_class, "body": body})
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = self.get(connection, scope, ident)
            if existing:
                if existing["available_at"] != available_at or existing["body_json"] != canonical_json(body):
                    raise MemoryError("memory:immutable_availability")
            else:
                self.insert(connection, scope, ident, record_class, available_at, body)
        return ident
