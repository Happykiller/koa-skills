import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "outils"))
from integrations import evaluate

class IntegrationTests(unittest.TestCase):
    def test_gate(self):
        p = {"missions":{"M1":{"state":"accepted"},"M2":{"state":"running"}},
             "integrations":[{"id":"I1","missions":["M1","M2"],"owner":"TECH",
                              "contract":"API response","command":"test-integration",
                              "commit":"sha"}]}
        self.assertEqual(evaluate(p)[0]["status"], "BLOCKED")
        p["missions"]["M2"]["state"]="accepted"
        self.assertEqual(evaluate(p)[0]["status"], "ACTION_REQUIRED")
        p["integrations"][0]["proof"]={"result":"PASS","commit":"sha"}
        self.assertEqual(evaluate(p)[0]["status"], "PASSED")
        p["integrations"][0]["commit"]="newsha"
        self.assertEqual(evaluate(p)[0]["status"], "ACTION_REQUIRED")
    def test_unknown(self):
        with self.assertRaises(ValueError):
            evaluate({"missions":{},"integrations":[{"id":"I","missions":["M1","M2"]}]})
