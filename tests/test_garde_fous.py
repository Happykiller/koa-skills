"""Le garde-fou de déploiement, éprouvé comme Claude Code l'appelle : un JSON sur l'entrée standard,
un processus, une sortie lue. Lancer : python3 -m unittest discover -s tests"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HOOK = os.path.join(os.path.dirname(__file__), "..", "plugins", "garde-fous", "hooks", "garde_fous.py")


class GardeFous(unittest.TestCase):
    def setUp(self):
        self.projet = tempfile.mkdtemp()
        self.donnees = tempfile.mkdtemp()

    def configurer(self, contenu):
        os.makedirs(os.path.join(self.projet, ".claude"), exist_ok=True)
        with open(os.path.join(self.projet, ".claude", "garde-fous.json"), "w", encoding="utf-8") as f:
            f.write(contenu if isinstance(contenu, str) else json.dumps(contenu))

    def appeler(self, commande, outil="Bash"):
        entree = {"session_id": "s1", "cwd": self.projet, "hook_event_name": "PreToolUse",
                  "tool_name": outil, "tool_input": {"command": commande}}
        env = dict(os.environ, CLAUDE_PROJECT_DIR=self.projet, CLAUDE_PLUGIN_DATA=self.donnees)
        r = subprocess.run([sys.executable, HOOK], input=json.dumps(entree), capture_output=True,
                           text=True, encoding="utf-8", env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        sortie = json.loads(r.stdout) if r.stdout.strip() else None
        return sortie["hookSpecificOutput"] if sortie else None

    def journal(self):
        chemin = os.path.join(self.donnees, "decisions.log")
        if not os.path.exists(chemin):
            return []
        with open(chemin, encoding="utf-8") as f:
            return [json.loads(l) for l in f]

    CONF = {"version": 1, "cluster": "cluster-a",
            "deploiement": {"cibles_permises": ["recette-a"], "cibles_interdites": ["prod-a"]}}

    def test_une_commande_qui_ne_deploie_pas_passe_sans_un_mot(self):
        self.configurer(self.CONF)
        self.assertIsNone(self.appeler("kubectl get pods --context prod-a"))
        self.assertIsNone(self.appeler("git status"))
        self.assertEqual(self.journal(), [])

    def test_un_autre_outil_que_bash_n_est_pas_regarde(self):
        self.assertIsNone(self.appeler("kubectl apply -f x.yaml", outil="Write"))

    def test_une_cible_permise_passe_et_se_journalise(self):
        self.configurer(self.CONF)
        self.assertIsNone(self.appeler("kubectl apply -f app.yaml --context recette-a"))
        self.assertEqual([e["decision"] for e in self.journal()], ["permis"])

    def test_une_cible_interdite_est_refusee_et_la_raison_la_nomme(self):
        self.configurer(self.CONF)
        d = self.appeler("helm upgrade app ./chart --kube-context prod-a")
        self.assertEqual(d["permissionDecision"], "deny")
        self.assertIn("prod-a", d["permissionDecisionReason"])
        self.assertEqual([e["decision"] for e in self.journal()], ["deny"])

    def test_la_cible_d_un_autre_cluster_est_refusee(self):
        # Le critère de l'épic 125 : dans le cluster A, viser le cluster B est refusé.
        self.configurer(self.CONF)
        d = self.appeler("kubectl apply -f app.yaml --context recette-b")
        self.assertEqual(d["permissionDecision"], "deny")
        self.assertIn("recette-a", d["permissionDecisionReason"])

    def test_un_mot_qui_contient_la_cible_ne_la_nomme_pas(self):
        self.configurer(self.CONF)
        # « preprod-a » n'est pas « prod-a », et ne permet pas non plus « recette-a » par accident.
        d = self.appeler("terraform apply -var env=preprod-a")
        self.assertEqual(d["permissionDecision"], "deny")
        self.assertNotIn("interdite", d["permissionDecisionReason"])

    def test_la_cible_interdite_l_emporte_sur_la_permise(self):
        self.configurer(self.CONF)
        d = self.appeler("az containerapp update --name recette-a --target prod-a")
        self.assertEqual(d["permissionDecision"], "deny")
        self.assertIn("interdite", d["permissionDecisionReason"])

    def test_sans_configuration_l_humain_confirme(self):
        d = self.appeler("terraform apply")
        self.assertEqual(d["permissionDecision"], "ask")
        self.assertIn("garde-fous.json", d["permissionDecisionReason"])

    def test_une_configuration_illisible_refuse_au_lieu_de_laisser_passer(self):
        self.configurer("{ pas du json")
        d = self.appeler("helm install app ./chart")
        self.assertEqual(d["permissionDecision"], "deny")
        self.assertIn("illisible", d["permissionDecisionReason"])

    def test_une_liste_mal_formee_est_illisible_aussi(self):
        self.configurer({"deploiement": {"cibles_permises": "recette-a"}})
        d = self.appeler("helm install app ./chart --kube-context recette-a")
        self.assertEqual(d["permissionDecision"], "deny")

    def test_le_qg_peut_declarer_ses_propres_commandes(self):
        self.configurer({"cluster": "c", "deploiement": {"commandes": [r"\bdeployer\.sh\b"],
                                                          "cibles_permises": ["recette-c"]}})
        self.assertEqual(self.appeler("./deployer.sh prod-c")["permissionDecision"], "deny")
        self.assertIsNone(self.appeler("./deployer.sh recette-c"))
        # Ses commandes remplacent la liste par défaut : kubectl n'est plus regardé ici.
        self.assertIsNone(self.appeler("kubectl apply -f x.yaml"))

    def test_le_journal_ne_porte_jamais_la_commande(self):
        self.configurer(self.CONF)
        self.appeler("kubectl apply --token=SECRET-123 --context prod-a")
        self.assertNotIn("SECRET-123", json.dumps(self.journal()))


if __name__ == "__main__":
    unittest.main()
