"""Un motif de fuite qui n'attrape rien protège moins que pas de motif : il rassure."""
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "outils"))
import verifier  # noqa: E402


class MotifsDeFuite(unittest.TestCase):
    def attrape(self, texte):
        return [quoi for motif, quoi in verifier.FUITES
                for m in re.finditer(motif, texte) if not verifier.FAUX_POSITIFS.match(m.group(0))]

    def test_chaque_motif_attrape_ce_qu_il_vise(self):
        self.assertIn("chemin personnel", self.attrape("voir /home/alice/projet"))
        self.assertIn("chemin personnel", self.attrape(r"C:\Users\alice\x"))
        self.assertIn("jeton", self.attrape("export GH_TOKEN=ghp_abcdefgh12345678"))
        self.assertIn("adresse électronique", self.attrape("écrire à alice@example.com"))
        self.assertIn("format d'un autre outil", self.attrape("lire AGENTS.md"))

    def test_l_adresse_d_un_plugin_n_est_pas_une_fuite(self):
        self.assertEqual(self.attrape("claude plugin install garde-fous@koa-skills"), [])

    def test_une_description_dit_quand_se_declencher(self):
        self.assertTrue(verifier.DECLENCHEUR.search("DevOps — quand : un service arrêté."))
        self.assertTrue(verifier.DECLENCHEUR.search("Rituel de fin de session. Par /koa:clore."))
        # Un objectif n'est pas un déclencheur : c'était le défaut des descriptions de la 0.3.0.
        self.assertIsNone(verifier.DECLENCHEUR.search("Objectif : un pipeline qui bloque ce qu'il doit."))

    def test_l_epinglage_se_lit_sur_une_ligne_comme_sur_plusieurs(self):
        une = '{ "source": "github", "repo": "Happykiller/koa-skills", "ref": "v0.4.0" }'
        plusieurs = '"repo": "Happykiller/koa-skills",\n      "ref": "v0.4.0"'
        self.assertEqual([m.group(1) for m in verifier.EPINGLAGE.finditer(une + plusieurs)], ["v0.4.0", "v0.4.0"])

    def test_le_depot_est_propre(self):
        self.assertEqual(verifier.verifier(), [])


if __name__ == "__main__":
    unittest.main()
