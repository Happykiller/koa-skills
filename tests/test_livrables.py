import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "plugins" / "koa" / "scripts"))
from livrables import render

class LivrablesTests(unittest.TestCase):
    def test_four_documents_and_no_false_delivery(self):
        x={"name":"Chantier A", "gantt":"gantt\n    title Exemple\n    section Mise en place\n    t1 :a, 2026-11-01, 1d", "missions":[{"id":"M1","state":"accepted","owner":"TECH","criteria":"C1","evidence":"preuve","unverified":"rien"}],
        "decisions":[], "observations":[], "capabilities":[{"name":"Fonction A","state":"finalized","usage":"parcours","limits":"aucune"}]}
        out=render(x)
        self.assertEqual(set(out), {"plan.md","bilan.md","rex.md","livraison.md"})
        self.assertNotIn("| Fonction A | parcours |",out["livraison.md"])
        self.assertIn("| Fonction A | finalized |",out["livraison.md"])
        x["capabilities"][0]["state"]="delivered"
        self.assertIn("| Fonction A | parcours |",render(x)["livraison.md"])
    def test_required_data(self):
        with self.assertRaises(ValueError):
            render({"name":"Chantier"})

if __name__ == "__main__":
    unittest.main()
