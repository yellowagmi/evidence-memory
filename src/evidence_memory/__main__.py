"""Inspect and publish local memory through the same library API."""
import argparse
import json
from pathlib import Path
import sys

from . import Memory, Scope, SQLiteStore


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--namespace", required=True)
    parser.add_argument("--stream", required=True)
    actions = parser.add_subparsers(dest="action", required=True)
    register = actions.add_parser("register", help="Retain a JSON evidence file")
    register.add_argument("file", type=Path)
    register.add_argument("--available-at", required=True)
    register.add_argument("--record-class", default="evidence")
    publish = actions.add_parser("publish", help="Publish a JSON publication request")
    publish.add_argument("file", type=Path)
    read = actions.add_parser("read", help="Read a memory version and its status as of a cutoff")
    read.add_argument("id")
    read.add_argument("--cutoff", required=True)
    evidence = actions.add_parser("evidence", help="Read a registered source body as of a cutoff")
    evidence.add_argument("id")
    evidence.add_argument("--cutoff", required=True)
    listing = actions.add_parser("list", help="List memory versions as of a cutoff")
    listing.add_argument("--cutoff", required=True)
    listing.add_argument("--after", type=int, default=0)
    listing.add_argument("--key")
    args = parser.parse_args(argv)
    try:
        scope = Scope(args.namespace, args.stream)
        store = SQLiteStore(args.database)
        memory = Memory(store, scope)
        if args.action == "register":
            result = {"id": store.register(scope, json.loads(args.file.read_text()),
                                          available_at=args.available_at, record_class=args.record_class)}
        elif args.action == "publish":
            values = json.loads(args.file.read_text())
            result = {"id": memory.publish(**values)}
        elif args.action == "read":
            result = memory.read(args.id, args.cutoff)
        elif args.action == "evidence":
            result = memory.evidence(args.id, args.cutoff)
        else:
            result = memory.list(args.cutoff, after=args.after, key=args.key)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
