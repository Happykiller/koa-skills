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
        self.assertEqual(set(render(self.registre)), {"plan.md", "bilan.md", "rex.md", "livraison.md"})

    def test_les_heures_et_les_etats_viennent_du_journal(self):
        plan = render(self.registre, JOURNAL)["plan.md"]
        self.assertIn("| M1 | 1 | socle | @cluster-a-tech | — | @cluster-a-tech-2 | C1 | acceptée | 01/11 10:05 | 01/11 10:40 | 0 h 35 |", plan)
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
        self.assertIn("| M1 | 1 | socle | @cluster-a-tech | — | @cluster-a-tech-2 | C1 | en reprise |",
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
            self.assertTrue(all((Path(d) / n).is_file() for n in ("plan.md", "bilan.md", "rex.md", "livraison.md")))
            self.assertIn("| M1 | claude-sonnet-5-5 |", (Path(d) / "plan.md").read_text(encoding="utf-8"))
            casse = Path(d) / "casse.json"
            casse.write_text("{}", encoding="utf-8")
            ko = subprocess.run([sys.executable, str(SCRIPT), str(casse), "--output", d], capture_output=True, text=True)
            self.assertEqual(ko.returncode, 2)
            self.assertIn("erreur", json.loads(ko.stdout))


if __name__ == "__main__":
    unittest.main()
