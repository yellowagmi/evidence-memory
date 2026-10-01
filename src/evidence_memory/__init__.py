"""Persistent evidence memory for iterative agent improvement."""
from ._json import MemoryError, canonical_json, content_sha256
from .core import KINDS_MEMORY, Memory
from .storage import RecordLayout, Scope, SourceLayout, SQLiteRecords, SQLiteStore

__version__ = "0.1.0"
__all__ = ["Memory", "MemoryError", "Scope", "SQLiteStore", "SQLiteRecords",
           "RecordLayout", "SourceLayout", "KINDS_MEMORY", "canonical_json", "content_sha256"]
