"""Le garde-fou de déploiement, éprouvé comme Claude Code l'appelle : un JSON sur l'entrée standard,
un processus, une sortie lue. La fusion, elle, est éprouvée en important le module : ses deux chemins
de distro y sont des constantes qu'on remplace. Lancer : python3 -m unittest discover -s tests"""
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

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
        # Sous Windows, un processus fils écrit sa sortie en cp1252 : les accents des raisons ne se
        # liraient pas en UTF-8. La distro, elle, est déjà en UTF-8.
        env = dict(os.environ, CLAUDE_PROJECT_DIR=self.projet, CLAUDE_PLUGIN_DATA=self.donnees,
                   PYTHONIOENCODING="utf-8")
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

    # La 0.2.0 cherchait ses motifs dans la commande brute, et refusait tout ce qui suit — dont
    # `docker compose down`, geste prescrit par koa:clore. Avec et sans configuration.
    LEGITIMES = [
        'grep -rn "kubectl apply" docs/',
        'git commit -m "doc : quand lancer terraform apply"',
        "kubectl logs deploy/scale-worker",
        "kubectl -n recette get pods",
        "terraform plan -out=apply.tfplan",
        "ansible-playbook --syntax-check site.yml",
        "ansible-playbook site.yml --check",
        "docker compose up -d db",
        "docker compose -f compose.test.yml down",
        "docker-compose down -v",
        "helm template app ./chart",
        "echo helm upgrade",
        "cat notes.txt | grep 'docker push'",
    ]

    def test_ce_qui_ne_fait_que_parler_d_un_deploiement_passe(self):
        for commande in self.LEGITIMES:
            with self.subTest(commande=commande):
                self.assertIsNone(self.appeler(commande))
        self.configurer(self.CONF)
        for commande in self.LEGITIMES:
            with self.subTest(commande=commande, configure=True):
                self.assertIsNone(self.appeler(commande))
        self.assertEqual(self.journal(), [])

    def test_une_enveloppe_ne_cache_pas_le_deploiement(self):
        self.configurer(self.CONF)
        for commande in ["sudo -u ops kubectl apply -f x.yaml --context prod-a",
                         "env KUBECONFIG=k timeout 30 helm upgrade app ./chart --kube-context prod-a",
                         "bash -c 'kubectl -n app apply -f x.yaml --context prod-a'",
                         "ssh -i cle bastion kubectl delete pod x --context prod-a",
                         "xargs -n 1 kubectl apply --context prod-a -f",
                         "/usr/local/bin/terraform -chdir=infra apply -var env=prod-a",
                         "ansible-playbook -i prod-a site.yml"]:
            with self.subTest(commande=commande):
                self.assertEqual(self.appeler(commande)["permissionDecision"], "deny")

    def test_un_compose_qui_vise_un_demon_distant_deploie(self):
        self.configurer(self.CONF)
        for commande in ["docker --context prod-a compose up -d",
                         "DOCKER_HOST=ssh://prod-a docker compose up -d",
                         "docker -H ssh://hote compose down"]:
            with self.subTest(commande=commande):
                self.assertEqual(self.appeler(commande)["permissionDecision"], "deny")

    def test_chaque_segment_qui_deploie_nomme_sa_cible(self):
        self.configurer(self.CONF)
        d = self.appeler("kubectl apply -f a.yaml --context recette-a && helm upgrade app ./chart")
        self.assertEqual(d["permissionDecision"], "deny")
        self.assertIsNone(self.appeler(
            "kubectl apply -f a.yaml --context recette-a && kubectl rollout status deploy/a --context recette-a"))

    def test_une_session_dans_un_depot_de_la_stack_suit_le_qg(self):
        qg = tempfile.mkdtemp()
        os.makedirs(os.path.join(qg, ".claude"))
        with open(os.path.join(qg, ".claude", "garde-fous.json"), "w", encoding="utf-8") as f:
            json.dump(self.CONF, f)
        with mock.patch.dict(os.environ, {"KOA_QG": qg}):
            self.assertEqual(self.appeler("kubectl apply -f x.yaml --context prod-a")["permissionDecision"],
                             "deny")
            self.assertIsNone(self.appeler("kubectl apply -f x.yaml --context recette-a"))


def charger_le_module():
    spec = importlib.util.spec_from_file_location("garde_fous", HOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SHA = "0123456789abcdef0123456789abcdef01234567"


class Fusion(unittest.TestCase):
    def setUp(self):
        self.gf = charger_le_module()
        self.distro = tempfile.mkdtemp()
        # Hors d'une distro KoA par défaut, même quand la suite tourne dans l'une d'elles.
        self.gf.MARQUE_KOA = os.path.join(self.distro, "koa-seed")
        self.gf.TEMOIN_DROITS = os.path.join(self.distro, "droits")
        self.projet = tempfile.mkdtemp()

    def naitre_de_koa(self, droits=None):
        open(self.gf.MARQUE_KOA, "w").close()
        if droits is not None:
            with open(self.gf.TEMOIN_DROITS, "w", encoding="utf-8") as f:
                f.write(droits)

    def juger(self, commande):
        entree = {"session_id": "s1", "tool_name": "Bash", "tool_input": {"command": commande}}
        return self.gf.decider(entree, self.projet)

    def refuse(self, commande, extrait):
        decision, raison = self.juger(commande)
        self.assertEqual(decision, "deny", commande)
        self.assertIn(extrait, raison)

    def test_une_fusion_sur_le_sha_complet_passe_sans_un_mot(self):
        self.assertEqual(self.juger(f"gh pr merge 12 --squash --match-head-commit {SHA}"), (None, None))
        self.assertEqual(self.juger(f"gh pr merge 12 --match-head-commit={SHA.upper()}"), (None, None))

    def test_une_continuation_de_ligne_ne_coupe_pas_la_fusion(self):
        self.assertEqual(self.juger(f"gh pr merge 12 --squash \\\n  --match-head-commit {SHA}"),
                         (None, None))

    def test_un_sha_court_est_refuse(self):
        self.refuse("gh pr merge 12 --match-head-commit 0123456", "SHA complet")

    def test_un_sha_absent_est_refuse(self):
        self.refuse("gh pr merge 12 --squash", "--match-head-commit")
        self.refuse("gh pr merge 12 --match-head-commit", "--match-head-commit")
        # Une tête calculée au moment de fusionner n'est pas celle que la revue a lue.
        self.refuse("gh pr merge 12 --match-head-commit $(git rev-parse HEAD)", "SHA complet")

    def test_admin_est_refuse_meme_avec_la_tete(self):
        self.refuse(f"gh pr merge 12 --admin --match-head-commit {SHA}", "--admin")
        self.refuse(f"gh pr merge 12 --admin=true --match-head-commit {SHA}", "--admin")
        # Un « ; » entre guillemets ne le détache pas de la fusion.
        self.refuse(f'gh pr merge 12 --match-head-commit {SHA} --subject ";" --admin', "--admin")

    def test_un_segment_voisin_ne_prete_pas_sa_tete(self):
        self.refuse(f"echo --match-head-commit {SHA} ; gh pr merge 12", "--match-head-commit")
        self.refuse(f"echo --match-head-commit {SHA}\ngh pr merge 12", "--match-head-commit")

    def test_un_segment_voisin_qui_lit_ne_gene_pas(self):
        self.assertEqual(self.juger(f"gh pr view 12 && gh pr merge 12 --match-head-commit {SHA}"),
                         (None, None))
        self.assertEqual(self.juger("gh pr view 12 --json mergeable | jq ."), (None, None))

    def test_un_prefixe_ne_cache_pas_la_fusion(self):
        self.refuse("sudo -u agent /usr/bin/gh pr merge 12", "--match-head-commit")
        self.refuse("GH_TOKEN=x env gh pr -R o/depot merge 12", "--match-head-commit")

    def test_des_guillemets_non_fermes_sont_refuses(self):
        self.refuse(f'gh pr merge 12 --match-head-commit {SHA} --body "pas fermé', "ne se lit pas")
        # Illisible mais sans fusion : ce n'est pas l'affaire de cette section.
        self.assertEqual(self.juger('echo "pas fermé'), (None, None))

    def test_une_distro_koa_sans_temoin_ne_fusionne_pas(self):
        self.naitre_de_koa()
        self.refuse(f"gh pr merge 12 --match-head-commit {SHA}", "seul l'orchestrateur fusionne")

    def test_un_temoin_sans_le_droit_ne_suffit_pas(self):
        self.naitre_de_koa("autre\nfusionner-tout\n")
        self.refuse(f"gh pr merge 12 --match-head-commit {SHA}", "seul l'orchestrateur fusionne")

    def test_une_distro_koa_qui_a_le_droit_fusionne(self):
        self.naitre_de_koa("fusionner\n")
        self.assertEqual(self.juger(f"gh pr merge 12 --match-head-commit {SHA}"), (None, None))
        # Le droit ne lève pas les deux autres refus.
        self.refuse(f"gh pr merge 12 --admin --match-head-commit {SHA}", "--admin")

    def test_la_fusion_ne_depend_pas_de_la_configuration_du_qg(self):
        os.makedirs(os.path.join(self.projet, ".claude"))
        with open(os.path.join(self.projet, ".claude", "garde-fous.json"), "w") as f:
            f.write("{ pas du json")
        self.refuse("gh pr merge 12", "--match-head-commit")

    def test_le_refus_se_journalise_sans_la_commande(self):
        donnees = tempfile.mkdtemp()
        entree = {"session_id": "s1", "tool_name": "Bash",
                  "tool_input": {"command": "gh pr merge 12 --body SECRET-456"}}
        sortie = io.StringIO()
        with mock.patch.dict(os.environ, {"CLAUDE_PLUGIN_DATA": donnees,
                                          "CLAUDE_PROJECT_DIR": self.projet}), \
                mock.patch.object(sys, "stdin", io.StringIO(json.dumps(entree))), \
                mock.patch.object(sys, "stdout", sortie):
            self.assertEqual(self.gf.main(), 0)
        self.assertEqual(json.loads(sortie.getvalue())["hookSpecificOutput"]["permissionDecision"], "deny")
        with open(os.path.join(donnees, "decisions.log"), encoding="utf-8") as f:
            journal = f.read()
        self.assertIn('"deny"', journal)
        self.assertNotIn("SECRET-456", journal)


class GardeQuiPlante(unittest.TestCase):
    """Un garde qui plante sortait en code 1 : Claude Code le lit comme une erreur non bloquante, et
    le déploiement passait."""

    def lancer(self, commande):
        gf = charger_le_module()
        entree = {"session_id": "s1", "tool_name": "Bash", "tool_input": {"command": commande}}
        sortie = io.StringIO()
        with mock.patch.dict(os.environ, {"CLAUDE_PLUGIN_DATA": tempfile.mkdtemp(),
                                          "CLAUDE_PROJECT_DIR": tempfile.mkdtemp()}), \
                mock.patch.object(gf, "decider", side_effect=RuntimeError("panne")), \
                mock.patch.object(sys, "stdin", io.StringIO(json.dumps(entree))), \
                mock.patch.object(sys, "stdout", sortie), \
                mock.patch.object(sys, "stderr", io.StringIO()):
            code = gf.main()
        return code, sortie.getvalue()

    def test_sur_un_deploiement_il_refuse(self):
        code, sortie = self.lancer("kubectl apply -f x.yaml")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(sortie)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_ailleurs_il_le_dit_sans_bloquer(self):
        self.assertEqual(self.lancer("ls -la"), (1, ""))


@unittest.skipUnless(shutil.which("sh") and os.name != "nt", "le tri en sh se joue dans la distro")
class TriEnSh(unittest.TestCase):
    """`garde-fous.sh` ne démarre Python que si la commande nomme un outil de déploiement ou de
    fusion, ou si le QG déclare ses propres commandes."""
    SH = os.path.join(os.path.dirname(HOOK), "garde-fous.sh")

    def lancer(self, commande, chemin=None, projet=None):
        entree = {"tool_name": "Bash", "tool_input": {"command": commande}}
        env = dict(os.environ, CLAUDE_PROJECT_DIR=projet or tempfile.mkdtemp(),
                   CLAUDE_PLUGIN_DATA=tempfile.mkdtemp())
        env.pop("KOA_QG", None)
        if chemin is not None:
            env["PATH"] = chemin
        r = subprocess.run([shutil.which("sh"), self.SH], input=json.dumps(entree), capture_output=True,
                           text=True, encoding="utf-8", env=env)
        return r.returncode, r.stdout

    @staticmethod
    def sans_python():
        """Un PATH qui a tout ce qu'il faut au script, sauf python3."""
        outils = tempfile.mkdtemp()
        for outil in ("cat", "grep", "dirname"):
            os.symlink(shutil.which(outil), os.path.join(outils, outil))
        return outils

    def test_une_commande_ordinaire_ne_lance_pas_python(self):
        # Sans python3, seul le tri peut répondre : s'il laisse passer sans un mot, c'est lui.
        self.assertEqual(self.lancer("ls -la", chemin=self.sans_python()), (0, ""))

    def test_sans_python_un_deploiement_est_refuse(self):
        code, sortie = self.lancer("kubectl apply -f x.yaml", chemin=self.sans_python())
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(sortie)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_avec_python_le_jugement_fin_reprend(self):
        self.assertEqual(self.lancer("docker compose down"), (0, ""))
        code, sortie = self.lancer("terraform apply")
        self.assertEqual(json.loads(sortie)["hookSpecificOutput"]["permissionDecision"], "ask")

    def test_un_qg_qui_declare_ses_commandes_est_toujours_lu(self):
        projet = tempfile.mkdtemp()
        os.makedirs(os.path.join(projet, ".claude"))
        with open(os.path.join(projet, ".claude", "garde-fous.json"), "w", encoding="utf-8") as f:
            json.dump({"deploiement": {"commandes": [r"\bdeployer\.sh\b"], "cibles_permises": ["r"]}}, f)
        code, sortie = self.lancer("./deployer.sh prod", projet=projet)
        self.assertEqual(json.loads(sortie)["hookSpecificOutput"]["permissionDecision"], "deny")


if __name__ == "__main__":
    unittest.main()
