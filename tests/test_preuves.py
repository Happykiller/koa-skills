import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "plugins" / "koa" / "scripts" / "preuves.py"

class PreuvesTests(unittest.TestCase):
    def test_validity_and_invalidation(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            file = root / "source.txt"
            file.write_text("v1")
            registry = root / "registry.json"
            common = ["--registry", str(registry), "--id", "T1", "--commit", "abc", "--environment", "local",
                      "--config", "cfg", "--dependencies", "deps", "--files", str(file)]
            def run(action, extra=[]):
                return subprocess.run([sys.executable, str(SCRIPT), action] + common + extra,
                                      capture_output=True, text=True)
            self.assertEqual(run("check").returncode, 2)
            self.assertEqual(run("record", ["--result", "PASS", "--command", "pytest"]).returncode, 0)
            self.assertEqual(run("check").returncode, 0)
            file.write_text("v2")
            self.assertEqual(json.loads(run("check").stdout)["status"], "INVALIDATED")
            self.assertEqual(run("check").returncode, 2)

if __name__ == "__main__":
    unittest.main()
