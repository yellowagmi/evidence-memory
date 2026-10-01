import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class CLITests(unittest.TestCase):
    def setUp(self):
        self.temp = self.enterContext(tempfile.TemporaryDirectory())
        self.root = Path(self.temp)
        self.command = [sys.executable, "-m", "evidence_memory", "--database", str(self.root / "memory.sqlite3"),
                        "--namespace", "work", "--stream", "iteration"]

    def run_cli(self, *args, expected=0):
        result = subprocess.run([*self.command, *args], capture_output=True, text=True, env=os.environ.copy(), timeout=10)
        self.assertEqual(result.returncode, expected, result.stderr)
        return result

    def test_register_publish_read_source_and_list_through_entrypoint(self):
        source = self.root / "source.json"
        source.write_text(json.dumps({"result": "Failed restoration check"}))
        ref = json.loads(self.run_cli("register", str(source), "--available-at", "2026-01-01T00:00:00Z").stdout)["id"]
        publication = self.root / "publication.json"
        publication.write_text(json.dumps(dict(kind="workflow_memory", key="restore", content={"lesson": "Inspect evidence"},
            supporting_refs=[ref], contrary_refs=[], applicability="Resumed work", limitations="Requires verification",
            provenance={"cutoff": "2026-01-01T00:00:00Z"}, available_at="2026-01-01T00:01:00Z")))
        memory_id = json.loads(self.run_cli("publish", str(publication)).stdout)["id"]
        cutoff = "2026-01-01T00:02:00Z"
        self.assertEqual(json.loads(self.run_cli("read", memory_id, "--cutoff", cutoff).stdout)["id"], memory_id)
        self.assertEqual(json.loads(self.run_cli("evidence", ref, "--cutoff", cutoff).stdout)["body"],
                         {"result": "Failed restoration check"})
        self.assertEqual(json.loads(self.run_cli("list", "--cutoff", cutoff).stdout)["records"][0]["id"], memory_id)

    def test_invalid_publication_returns_error_and_preserves_empty_memory(self):
        publication = self.root / "invalid.json"
        publication.write_text('{"kind":"workflow_memory"}')
        self.run_cli("publish", str(publication), expected=2)
        listing = self.run_cli("list", "--cutoff", "2026-01-01T00:00:00Z")
        self.assertEqual(json.loads(listing.stdout)["records"], [])


if __name__ == "__main__":
    unittest.main()
