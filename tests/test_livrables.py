"""Les quatre vues : ce que le journal dit s'y lit sans recopie, et rien de ce qu'il ne dit pas ne s'y invente."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
SCRIPT = RACINE / "plugins" / "koa" / "scripts" / "livrables.py"
MODELE = RACINE / "plugins" / "koa" / "skills" / "mener-un-chantier" / "chantier.modele.json"
sys.path.insert(0, str(SCRIPT.parent))
from livrables import render  # noqa: E402

SHA_A = "a" * 40
SHA_B = "b" * 40


def fait(n, type_, mission, auteur, texte, quand):
    return {"MessageId": n, "Version": 1, "Table": "chantier", "Quand": quand, "Auteur": auteur,
            "Destinataire": "orchestrateur", "Type": type_, "Mission": mission, "Texte": texte}


# Le format exact que sérialise KoA : décalage et sept décimales compris.
JOURNAL = [
    fait(1, "MISSION", "M1", "orchestrateur", "MISSION M1 — l'API", "2026-11-01T10:05:12.1234567+01:00"),
    fait(2, "MISSION", "M1", "orchestrateur", "MISSION M1 — l'API", "2026-11-01T10:05:12.1234567+01:00"),
    fait(3, "MISSION", "M2", "orchestrateur", "MISSION M2 — l'écran", "2026-11-01T10:05:30"),
    fait(4, "RÉSULTAT", "M1", "cluster-a-tech", "RÉSULTAT M1 — fait", "2026-11-01T10:30:00"),
    fait(5, "REVUE", "M1", "cluster-a-tech-2", f"REVUE M1 — ACCEPTÉ, sur {SHA_A}", "2026-11-01T10:40:00"),
    fait(6, "REVUE", "M1", "cluster-a-tech-2", f"REVUE M1 — ACCEPTÉ, sur {SHA_A}", "2026-11-01T10:40:00"),
    fait(7, "REVUE", "M2", "cluster-a-tech", f"REVUE M2 — ACCEPTÉ_AVEC_RÉSERVES, sur {SHA_B}", "2026-11-01T10:50:00"),
    fait(8, "MISSION", "I1", "orchestrateur", "MISSION I1 — rencontre", "2026-11-01T10:55:00"),
    fait(9, "REVUE", "I1", "cluster-a-tech", "REVUE I1 — REFUSÉ, sur " + SHA_B, "2026-11-01T11:10:00"),
    fait(10, "BLOCAGE", "I1", "cluster-a-tech-2", "BLOCAGE I1 — le jeton n'a pas le même nom", "2026-11-01T11:12:00"),
]


# Le format exact que sérialise KoA (CoutsChantier.Resultat).
COUTS = {
    "Missions": {
        "L1": {"Tours": 5, "Entree": 10, "CacheLu": 170_000, "CacheCree": 7_500, "Sortie": 3_800,
               "Modeles": ["claude-haiku-5-5"], "Efforts": ["medium"]},
        "M1": {"Tours": 15, "Entree": 30, "CacheLu": 1_230_000, "CacheCree": 12_500, "Sortie": 6_200,
               "Modeles": ["claude-sonnet-5-5"], "Efforts": ["medium", "high"]},
    },
    "HorsMission": {"Tours": 40, "Entree": 80, "CacheLu": 5_000_000, "CacheCree": 90_000, "Sortie": 30_000,
                    "Modeles": ["claude-sonnet-5-5"], "Efforts": ["medium"]},
    "Total": {"Tours": 60, "Entree": 120, "CacheLu": 6_400_000, "CacheCree": 110_000, "Sortie": 40_000,
              "Modeles": ["claude-haiku-5-5", "claude-sonnet-5-5"], "Efforts": ["medium", "high"]},
    "NonMesures": [],
}


class Livrables(unittest.TestCase):
    def setUp(self):
        self.registre = json.loads(MODELE.read_text(encoding="utf-8"))

    def test_le_modele_livre_avec_la_skill_se_genere(self):
        self.assertEqual(set(render(self.registre)), {"plan.md", "bilan.md", "rex.md", "livraison.md", "suivi.html"})

    def test_les_heures_et_les_etats_viennent_du_journal(self):
        plan = render(self.registre, JOURNAL)["plan.md"]
        self.assertIn("| M1 | 1 | socle | @cluster-a-tech | — | @cluster-a-tech-2 | C1 | acceptée | 45 min | 01/11 10:05 | 01/11 10:40 | 0 h 35 |", plan)
        self.assertIn("**État au** : 01/11 11:12, dernier fait reçu de la Cantina", plan)
        self.assertIn("| I1 | 2 |", plan)
        self.assertIn("| en reprise |", plan)
        self.assertIn("M1 :done, M1, 2026-11-01T10:05, 2026-11-01T10:40", plan)
        # Une mission sans acceptation court jusqu'au dernier fait, pas jusqu'à l'heure de génération.
        self.assertIn("I1 :active, I1, 2026-11-01T10:55, 2026-11-01T11:12", plan)
        self.assertIn("n°10", plan)

    def test_une_preuve_cite_sa_revue_et_son_sha(self):
        bilan = render(self.registre, JOURNAL)["bilan.md"]
        self.assertIn(f"REVUE n°5 de cluster-a-tech-2, sur {SHA_A}", bilan)
        self.assertIn("| I1 | en reprise |", bilan)
        self.assertIn("| Jalons d'intégration / ayant trouvé un défaut | 1 / 1 |", bilan)
        # Deux copies d'une même revue ne font pas deux revues.
        self.assertIn("| Missions au plan / parties / acceptées | 3 / 3 / 2 |", bilan)

    def test_une_revue_plus_recente_qui_refuse_annule_l_acceptation(self):
        journal = JOURNAL + [fait(11, "REVUE", "M1", "cluster-a-tech-2", "REVUE M1 — REFUSÉ, sur " + "c" * 40, "2026-11-01T11:20:00")]
        self.assertIn("| M1 | 1 | socle | @cluster-a-tech | — | @cluster-a-tech-2 | C1 | en reprise | 45 min |",
                      render(self.registre, journal)["plan.md"])

    def test_sans_journal_rien_n_est_mesure_et_c_est_dit(self):
        vues = render(self.registre)
        self.assertIn("Pas mesuré : la génération n'a pas reçu le journal", vues["bilan.md"])
        self.assertIn("| pas mesuré |", vues["plan.md"])
        self.assertNotIn("```mermaid", vues["plan.md"])

    def test_finalise_n_est_pas_livre(self):
        livraison = render(self.registre)["livraison.md"]
        self.assertIn("## Ce qui est disponible\n\nAucun.", livraison)
        self.assertIn("| Se connecter | prête, pas encore livrée |", livraison)
        registre = copy.deepcopy(self.registre)
        registre["capabilities"][0]["state"] = "delivered"
        self.assertIn("| Se connecter | depuis la page d'accueil, avec son adresse |", render(registre)["livraison.md"])

    def test_pas_verifie_absent_ne_se_lit_pas_vide(self):
        self.assertIn("| M2 | Non renseigné |", render(self.registre)["bilan.md"])

    def test_un_doublon_s_ecarte_sans_disparaitre(self):
        registre = copy.deepcopy(self.registre)
        registre["observations"].append({"id": "O2", "fact": "même attente", "duplicate_of": "O1"})
        rex = render(registre)["rex.md"]
        self.assertIn("| O2 | O1 |", rex)
        self.assertNotIn("même attente", rex)

    def test_une_barre_ne_casse_pas_un_tableau(self):
        registre = copy.deepcopy(self.registre)
        registre["decisions"][0]["reason"] = "a | b\nc"
        self.assertIn("a \\| b c", render(registre)["plan.md"])

    def test_deterministe(self):
        self.assertEqual(render(copy.deepcopy(self.registre), JOURNAL), render(copy.deepcopy(self.registre), JOURNAL))

    def test_un_registre_incoherent_est_refuse(self):
        for casse in ({"missions": []}, {"name": "x", "missions": {}},
                      {"name": "x", "missions": [{"id": "M1"}, {"id": "M1"}]},
                      {"name": "x", "missions": [{"id": "M1", "depends_on": ["M9"]}]},
                      {"name": "x", "missions": [{"id": "M 1"}]}):
            with self.assertRaises(ValueError):
                render(casse)
        with self.assertRaises(ValueError):
            render(self.registre, [{"MessageId": 1, "Quand": "hier"}])

    def test_chaque_mission_dit_son_modele_son_effort_ses_tours_et_ses_jetons(self):
        plan = render(self.registre, JOURNAL, COUTS)["plan.md"]
        self.assertIn("## Coût par mission", plan)
        self.assertIn("| M1 | claude-sonnet-5-5 | medium, high | 15 | 1,23 M | 12,5 k | 6,2 k |", plan)
        self.assertIn("| hors mission | claude-sonnet-5-5 | medium | 40 | 5,00 M | 90,0 k | 30,0 k |", plan)
        self.assertIn("| total | claude-haiku-5-5, claude-sonnet-5-5 | medium, high | 60 | 6,40 M | 110,0 k | 40,0 k |", plan)
        self.assertIn("L'attribution est approchée", plan)

    def test_une_mission_sans_tour_attribue_n_est_pas_a_zero(self):
        self.assertRegex(render(self.registre, JOURNAL, COUTS)["plan.md"], r"\| M2 \| — \| — \| — \| — \| — \| — \|")

    def test_une_mission_hors_du_registre_a_coute_quand_meme(self):
        self.assertIn("| L1 | claude-haiku-5-5 |", render(self.registre, JOURNAL, COUTS)["plan.md"])

    def test_un_agent_non_mesure_se_nomme_et_les_chiffres_sont_des_minimums(self):
        couts = dict(COUTS, NonMesures=["cluster-a-qa"])
        rendu = render(self.registre, JOURNAL, couts)
        self.assertIn("Transcript non lu, ces chiffres sont donc des minimums : cluster-a-qa", rendu["plan.md"])
        self.assertIn("Tours (minimum : un agent non mesuré)", rendu["bilan.md"])

    def test_le_bilan_et_le_rex_portent_le_total(self):
        rendu = render(self.registre, JOURNAL, COUTS)
        for vue in ("bilan.md", "rex.md"):
            self.assertIn("| Lus en cache / créés en cache / sortie | 6,40 M / 110,0 k / 40,0 k |", rendu[vue])
            self.assertIn("| Part des tours hors mission | 67 % |", rendu[vue])

    def test_sans_couts_rien_ne_s_invente(self):
        rendu = render(self.registre, JOURNAL)
        self.assertIn("Pas mesuré : la génération n'a pas reçu les coûts", rendu["plan.md"])
        self.assertIn("| Coût (tours, jetons, modèle, effort) | pas mesuré |", rendu["bilan.md"])

    def test_des_couts_illisibles_sont_refuses(self):
        with self.assertRaises(ValueError):
            render(self.registre, JOURNAL, {"Missions": []})

    def test_memes_entrees_memes_octets_avec_les_couts(self):
        self.assertEqual(render(self.registre, JOURNAL, COUTS), render(copy.deepcopy(self.registre), JOURNAL, copy.deepcopy(COUTS)))

    def test_la_ligne_de_commande_ecrit_les_quatre_vues_ou_sort_en_2(self):
        with tempfile.TemporaryDirectory() as d:
            journal = Path(d) / "evenements.json"
            journal.write_text(json.dumps(JOURNAL), encoding="utf-8")
            couts = Path(d) / "couts.json"
            couts.write_text(json.dumps(COUTS), encoding="utf-8")
            ok = subprocess.run([sys.executable, str(SCRIPT), str(MODELE), "--output", d, "--evenements", str(journal), "--couts", str(couts)],
                                capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
            self.assertTrue(all((Path(d) / n).is_file() for n in ("plan.md", "bilan.md", "rex.md", "livraison.md", "suivi.html")))
            self.assertIn("| M1 | claude-sonnet-5-5 |", (Path(d) / "plan.md").read_text(encoding="utf-8"))
            casse = Path(d) / "casse.json"
            casse.write_text("{}", encoding="utf-8")
            ko = subprocess.run([sys.executable, str(SCRIPT), str(casse), "--output", d], capture_output=True, text=True)
            self.assertEqual(ko.returncode, 2)
            self.assertIn("erreur", json.loads(ko.stdout))


def dit(n, type_, mission, auteur, a, texte, quand):
    f = fait(n, type_, mission, auteur, texte, quand)
    f["Destinataire"] = a
    return f


# Le c11 d'un cluster, réduit : une décision portée à l'humain, une permission levée par KoA, une autre qui court encore.
ATTENTES = JOURNAL + [
    dit(20, "BLOCAGE", "M2", "orchestrateur", "humain", "BLOCAGE M2 — le classifieur refuse la lecture de release", "2026-11-01T11:20:00"),
    # Le pilote coordonne en attendant : ce message ne dit rien de la réponse, il ne ferme pas l'attente.
    dit(21, "MISSION", "M3", "orchestrateur", "cluster-a-tech", "MISSION M3 — la suite", "2026-11-01T11:25:00"),
    dit(22, "RÉPONSE", "M2", "orchestrateur", "cluster-a-devops", "RÉPONSE M2 — l'humain a donné son accord", "2026-11-01T12:20:00"),
    dit(23, "BLOCAGE", None, "koa", "orchestrateur",
        "BLOCAGE — @cluster-a-tech attend une permission depuis 61 s : seul l'humain peut répondre", "2026-11-01T12:00:30"),
    dit(24, "ATTENTE LEVÉE", None, "koa", "humain",
        "ATTENTE LEVÉE — @cluster-a-tech a eu sa réponse de l'humain", "2026-11-01T13:59:00"),
    dit(25, "BLOCAGE", None, "koa", "orchestrateur",
        "BLOCAGE — @cluster-a-po attend une permission depuis 120 s : seul l'humain peut répondre", "2026-11-01T14:02:00"),
    dit(26, "RÉSULTAT", "M3", "cluster-a-tech", "orchestrateur", "RÉSULTAT M3 — fait", "2026-11-01T14:30:00"),
]


class AttentesDeLHumain(unittest.TestCase):
    """Un chantier de 22 h 47 pour sept heures de travail, et un REX qui n'en disait rien (épic 221 de KoA)."""

    def setUp(self):
        self.registre = json.loads(MODELE.read_text(encoding="utf-8"))
        self.vues = render(self.registre, ATTENTES, COUTS)

    def test_chaque_attente_se_date_par_sa_cause(self):
        rex = self.vues["rex.md"]
        self.assertIn("## Attentes de l'humain", rex)
        # La décision court jusqu'au message qui relaie la réponse, pas jusqu'au suivant.
        self.assertIn("| orchestrateur | M2 | décision | 01/11 11:20 | 01/11 12:20 | 1 h 00 | n°20 |", rex)
        # La permission part de ce que KoA a mesuré (61 s avant son message), et s'arrête à sa levée.
        self.assertIn("| cluster-a-tech | — | permission | 01/11 11:59 | 01/11 13:59 | 2 h 00 | n°23 |", rex)
        # Une attente encore ouverte court jusqu'au dernier fait.
        self.assertIn("| cluster-a-po | — | permission | 01/11 14:00 | en cours | 0 h 30 | n°25 |", rex)
        self.assertIn("## Attentes de l'humain", self.vues["plan.md"])

    def test_deux_attentes_qui_se_recouvrent_ne_comptent_qu_une_fois(self):
        # 11:20 → 13:59, puis 14:00 → 14:30 : 2 h 39 + 30 min, sur 10:05 → 14:30.
        for vue in ("rex.md", "bilan.md"):
            self.assertIn("| Attente de l'humain (au moins un agent arrêté) | 3 h 09 (71 % des 4 h 25 depuis le premier départ) |",
                          self.vues[vue])
            self.assertIn("| Attentes de l'humain : permissions / décisions | 2 / 1 |", self.vues[vue])

    def test_un_journal_d_avant_la_levee_se_ferme_au_message_suivant_de_l_agent(self):
        journal = [f for f in ATTENTES if f["MessageId"] != 24]
        rex = render(self.registre, journal)["rex.md"]
        self.assertIn("| cluster-a-tech | — | permission | 01/11 11:59 | 01/11 14:30 | 2 h 31 | n°23 |", rex)

    def test_l_humain_qui_repond_a_la_table_ferme_la_decision(self):
        journal = ATTENTES[:-6] + [dit(30, "RÉPONSE", None, "humain", "orchestrateur", "vas-y, option a", "2026-11-01T11:40:00")]
        self.assertIn("| orchestrateur | M2 | décision | 01/11 11:20 | 01/11 11:40 | 0 h 20 | n°20 |",
                      render(self.registre, journal)["rex.md"])

    def test_les_attentes_se_voient_en_rouge_au_gantt(self):
        self.assertIn("    section Attente de l'humain", self.vues["plan.md"])
        self.assertIn("    cluster-a-tech permission :crit, H2, 2026-11-01T11:59, 2026-11-01T13:59", self.vues["plan.md"])
        self.assertIn("cluster-a-tech permission :crit, H2, 2026-11-01T11:59, 2026-11-01T13:59", self.vues["suivi.html"])

    def test_la_page_dit_en_tete_que_l_equipe_attend_l_humain(self):
        page = self.vues["suivi.html"]
        self.assertIn('<div class="fraicheur attend"><span><b>L’équipe t’attend</b> : @cluster-a-po (permission, depuis 01/11 14:00)', page)
        self.assertLess(page.index("fraicheur attend"), page.index("<header>"))
        self.assertIn("<span>Attente de l’humain</span><b style=\"font-size:20px\">3 h 09</b><small>71 % du chantier</small>", page)
        self.assertIn('<div class="bloc alerte"><h2>Attentes de l’humain</h2>', page)

    def test_sans_attente_rien_ne_s_affole(self):
        vues = render(self.registre, JOURNAL, COUTS)
        self.assertIn("Aucune : personne n'a attendu l'humain.", vues["rex.md"])
        self.assertIn("| Attente de l'humain (au moins un agent arrêté) | 0 min (0 % des 1 h 07 depuis le premier départ) |", vues["rex.md"])
        self.assertNotIn("fraicheur attend", vues["suivi.html"])
        self.assertIn("Personne n'a attendu l'humain.", vues["suivi.html"])

    def test_sans_journal_rien_n_est_mesure(self):
        vues = render(self.registre)
        self.assertIn("## Attentes de l'humain\n\nPas mesuré", vues["rex.md"])


class PageDeSuivi(unittest.TestCase):
    """La forme que l'humain a validée, figée : un chantier qui réécrivait sa page la perdait (épic 210 de KoA)."""

    def setUp(self):
        self.registre = json.loads(MODELE.read_text(encoding="utf-8"))
        # Une mission que personne n'a encore reçue : le plan entier doit se voir, pas seulement ce qui est parti.
        self.registre["missions"].append({"id": "M3", "wave": 3, "feature": "socle", "owner": "@cluster-a-tech",
                                          "depends_on": ["I1"], "estimate_min": 50, "result": "le tableau de bord"})
        self.page = render(self.registre, JOURNAL, COUTS)["suivi.html"]

    def test_la_duree_reelle_se_lit_seule_en_couleur_jamais_en_ecart(self):
        # « 24 min prévu et 36 min d'avance » ne se lisait pas : l'humain a demandé le temps mesuré en couleur, sans la différence.
        for ecart in ("que prévu", "d'avance", "de retard", "à l'heure", "comme prévu"):
            self.assertNotIn(ecart, self.page)
        self.assertIn('<b class="duree ok">35 min</b>', self.page)   # M1 : 35 min pour 45 prévues
        self.assertIn('<b class="duree hot">45 min</b>', self.page)  # M2 : 45 min pour 30 prévues

    def test_une_mission_en_cours_se_mesure_au_dernier_fait(self):
        # I1 : partie à 10:55, dernier fait à 11:12 ; 17 min pour 20 prévues.
        self.assertIn('<b class="duree ok">17 min</b><div class="note">en cours</div>', self.page)

    def test_le_cout_par_mission_est_toujours_la(self):
        self.assertIn("<h2>Coût par mission</h2>", self.page)
        self.assertIn('<td class="mono">M1</td><td class="num">claude-sonnet-5-5</td>', self.page)
        self.assertIn('<tr class="total"><td class="mono">total</td>', self.page)
        sans = render(self.registre, JOURNAL)["suivi.html"]
        self.assertIn("<h2>Coût par mission</h2>", sans)
        self.assertIn("Pas mesuré : la génération n'a pas reçu les coûts", sans)

    def test_le_gantt_montre_le_plan_entier(self):
        self.assertIn("M3 le tableau de bord :M3, after I1, 50m", self.page)
        self.assertIn("section la rencontre", self.page)
        self.assertIn("    M3 :M3, after I1, 50m", render(self.registre, JOURNAL)["plan.md"])
        self.assertIn("M1 l&#x27;API d&#x27;authentification :done, M1, 2026-11-01T10:05, 2026-11-01T10:40", self.page)

    def test_l_avancement_se_lit_en_tete(self):
        # 45 + 30 prévues faites, sur 45 + 30 + 20 + 50.
        self.assertIn("<span>Avancement</span><b>52 %</b>", self.page)
        self.assertIn("pondéré par les durées prévues", self.page)
        self.assertIn("<span>Faites</span><b>2</b><small>sur 4</small>", self.page)

    def test_l_heure_de_mise_a_jour_et_le_temps_depuis_viennent_tout_en_haut(self):
        self.assertLess(self.page.index('<div class="page">'), self.page.index('class="fraicheur"'))
        self.assertLess(self.page.index('class="fraicheur"'), self.page.index("<header>"))
        self.assertIn('data-maj="2026-11-01T11:12"><span><b>Mise à jour</b> : 01/11 11:12', self.page)
        self.assertIn('data-depuis="2026-11-01T11:12" data-prefixe="· il y a "', self.page)
        self.assertIn("<b>Chantier parti</b> : 01/11 10:05", self.page)
        self.assertIn("pas mesurée, aucun fait de la Cantina reçu", render(self.registre)["suivi.html"])

    def test_memes_entrees_memes_octets(self):
        # Aucune heure de génération : « il y a … » se calcule à l'affichage.
        self.assertEqual(self.page, render(copy.deepcopy(self.registre), copy.deepcopy(JOURNAL), copy.deepcopy(COUTS))["suivi.html"])

    def test_le_registre_ne_s_injecte_pas_dans_la_page(self):
        registre = copy.deepcopy(self.registre)
        registre["name"] = "<script>alert(1)</script>"
        registre["missions"][0]["result"] = '"><img src=x onerror=alert(1)>'
        page = render(registre, JOURNAL, COUTS)["suivi.html"]
        self.assertNotIn("<script>alert", page)
        self.assertNotIn("<img src=x", page)


class ExecutionAutonome(unittest.TestCase):
    """Le c11 d'a2p : trois attentes de l'humain, toutes visibles au tour de table (revue d'autonomie du 14/11/2026)."""

    def setUp(self):
        self.registre = json.loads(MODELE.read_text(encoding="utf-8"))
        self.vues = render(self.registre, ATTENTES, COUTS)

    def test_la_liste_de_depart_ouvre_le_plan(self):
        plan = self.vues["plan.md"]
        self.assertLess(plan.index("## Liste de départ"), plan.index("## Features"))
        self.assertIn("| @cluster-a-devops | déployer en recette | environnement partagé | éprouvé | make deploy-recette DRY_RUN=1 → rc=0 |", plan)
        self.assertIn("**Cadrage** : livré et déployé en recette", plan)

    def test_un_registre_sans_audit_le_dit(self):
        registre = copy.deepcopy(self.registre)
        del registre["readiness"]
        self.assertIn("Pas d'audit au registre", render(registre)["plan.md"])

    def test_la_file_de_l_humain_se_lit_au_plan_et_au_bilan(self):
        for vue in ("plan.md", "bilan.md"):
            self.assertIn("## File de l'humain", self.vues[vue])
            self.assertIn("| désactiver le compte de recette qui a servi d'acteur d'administration | @cluster-a-devops |", self.vues[vue])
        registre = copy.deepcopy(self.registre)
        registre["human_queue"] = []
        self.assertIn("Vide : rien n'attend l'humain.", render(registre)["bilan.md"])

    def test_l_attente_apres_le_lancement_se_mesure_a_part(self):
        # Premier départ 10:05 : les trois attentes (11:20 → 13:59, 14:00 → 14:30) sont toutes après.
        self.assertIn("| Attente de l'humain après le lancement (cible : 0) | 3 h 09 |", self.vues["rex.md"])
        sans = render(self.registre, JOURNAL, COUTS)["rex.md"]
        self.assertIn("| Attente de l'humain après le lancement (cible : 0) | 0 min |", sans)

    def test_un_audit_mal_forme_est_refuse(self):
        for cle in ("readiness", "human_queue"):
            registre = copy.deepcopy(self.registre)
            registre[cle] = ["une phrase"]
            with self.assertRaises(ValueError):
                render(registre)


if __name__ == "__main__":
    unittest.main()
