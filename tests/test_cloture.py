"""Le script de /koa:clore : ce qu'il dit vide doit l'être, puisqu'il dispense l'agent des étapes suivantes."""
import os
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "plugins", "koa", "scripts", "cloture.sh")
SH = shutil.which("sh")


def git(dossier, *arguments):
    subprocess.run(["git", "-C", dossier, *arguments], check=True, capture_output=True)


@unittest.skipUnless(SH, "sh introuvable")
class Cloture(unittest.TestCase):
    def setUp(self):
        self.foyer = tempfile.mkdtemp(prefix="koa-cloture-")
        self.addCleanup(shutil.rmtree, self.foyer, ignore_errors=True)
        self.depot = os.path.join(self.foyer, "depot")
        self.amont = os.path.join(self.foyer, ".amont.git")
        subprocess.run(["git", "init", "-q", "--bare", self.amont], check=True)
        subprocess.run(["git", "init", "-q", self.depot], check=True)
        for cle, valeur in (("user.email", "koa"), ("user.name", "koa")):
            git(self.depot, "config", cle, valeur)
        self.ecrire("a.txt")
        git(self.depot, "add", ".")
        git(self.depot, "commit", "-qm", "base")
        git(self.depot, "remote", "add", "origin", self.amont)
        git(self.depot, "push", "-q", "-u", "origin", "HEAD")

    def ecrire(self, nom):
        with open(os.path.join(self.depot, nom), "w", encoding="utf-8") as f:
            f.write("x\n")

    def lancer(self, action, **env):
        environnement = dict(os.environ, HOME=self.foyer, KOA_CLUSTER="cluster-a", KOA_QG="", **env)
        return subprocess.run([SH, SCRIPT, action], capture_output=True, encoding="utf-8", env=environnement)

    def test_un_depot_propre_et_pousse_donne_un_perimetre_vide(self):
        r = self.lancer("recenser")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("cluster=cluster-a", r.stdout)
        self.assertIn("Périmètre : vide", r.stdout)

    def test_un_fichier_modifie_entre_au_perimetre(self):
        self.ecrire("b.txt")
        r = self.lancer("recenser")
        self.assertIn("modifié : ", r.stdout)
        self.assertNotIn("Périmètre : vide", r.stdout)

    def test_un_commit_non_pousse_entre_au_perimetre(self):
        self.ecrire("b.txt")
        git(self.depot, "add", ".")
        git(self.depot, "commit", "-qm", "suite")
        r = self.lancer("recenser")
        self.assertIn("non poussé : ", r.stdout)
        self.assertIn("(1 commit(s))", r.stdout)
        self.assertNotIn("Périmètre : vide", r.stdout)

    def test_un_depot_absent_de_la_carte_du_qg_se_signale(self):
        qg = os.path.join(self.foyer, "qg")
        os.makedirs(qg)
        with open(os.path.join(qg, "CLAUDE.md"), "w", encoding="utf-8") as f:
            f.write("La carte : aucun dépôt.\n")
        environnement = dict(os.environ, HOME=self.foyer, KOA_QG=qg)
        r = subprocess.run([SH, SCRIPT, "recenser"], capture_output=True, encoding="utf-8", env=environnement)
        self.assertIn("hors de la carte du QG : ", r.stdout)

    def test_verifier_sort_en_echec_sur_un_depot_sale(self):
        self.assertEqual(self.lancer("verifier").returncode, 0)
        self.ecrire("b.txt")
        r = self.lancer("verifier")
        self.assertEqual(r.returncode, 1)
        self.assertIn("SALE", r.stdout)

    def test_verifier_sort_en_echec_sur_un_commit_non_pousse(self):
        self.ecrire("b.txt")
        git(self.depot, "add", ".")
        git(self.depot, "commit", "-qm", "suite")
        r = self.lancer("verifier")
        self.assertEqual(r.returncode, 1)
        self.assertIn("retard/avance : 0/1", r.stdout)

    def test_le_script_n_ecrit_rien(self):
        avant = subprocess.run(["git", "-C", self.depot, "status", "--porcelain"], capture_output=True, encoding="utf-8").stdout
        self.lancer("recenser")
        self.lancer("verifier")
        apres = subprocess.run(["git", "-C", self.depot, "status", "--porcelain"], capture_output=True, encoding="utf-8").stdout
        self.assertEqual(avant, apres)

    def test_une_action_inconnue_est_refusee(self):
        self.assertEqual(self.lancer("nettoyer").returncode, 2)


if __name__ == "__main__":
    unittest.main()
