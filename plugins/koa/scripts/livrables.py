#!/usr/bin/env python3
"""Les quatre vues d'un chantier — plan, bilan, REX, note de livraison — depuis une seule source.

Le registre `chantier.json` porte ce que seul l'orchestrateur sait : le plan, les critères, les décisions, les
observations, les capacités. Les faits datés — qui a reçu sa mission et quand, quelle revue a conclu quoi sur quel
SHA, quel blocage — viennent du journal de la Cantina (`--evenements`, exporté par KoA) : personne ne les recopie.

Déterministe : mêmes entrées, mêmes octets — aucune heure de génération, aucun ordre de dictionnaire. Un fait de la
Cantina reste une déclaration attribuée, citée par son numéro de message : rien ici ne certifie une preuve, et une
capacité n'est « livrée » que si le registre le dit après la livraison effective.
"""
import argparse
import datetime
import json
import re
import sys
import unicodedata
from pathlib import Path

PAS_MESURE = "pas mesuré"
NON_RENSEIGNE = "Non renseigné"
SHA = re.compile(r"\b[0-9a-f]{40}\b")


def clean(value):
    """Une valeur sur une ligne de tableau Markdown : ni saut de ligne, ni barre qui ouvrirait une colonne."""
    if value is None or value == "" or value == []:
        return NON_RENSEIGNE
    if isinstance(value, list):
        value = ", ".join(str(v) for v in value)
    return str(value).replace("\r", " ").replace("\n", " ").replace("|", "\\|").strip()


def sans_accents(texte):
    return "".join(c for c in unicodedata.normalize("NFD", texte) if not unicodedata.combining(c)).upper()


def minute(quand):
    """`Quand` de KoA, avec ou sans décalage ni fractions : la minute locale où le message est parti."""
    return datetime.datetime.strptime(str(quand)[:16], "%Y-%m-%dT%H:%M")


def heure(instant):
    return instant.strftime("%d/%m %H:%M") if instant else PAS_MESURE


def duree(debut, fin):
    if not debut or not fin:
        return PAS_MESURE
    minutes = int((fin - debut).total_seconds() // 60)
    return f"{minutes // 60} h {minutes % 60:02d}"


def verdict(texte):
    t = sans_accents(texte)
    if "NON_CONCLUANT" in t or "NON CONCLUANT" in t:
        return "non concluant"
    if "REFUSE" in t:
        return "refusé"
    if "ACCEPTE" in t:
        return "accepté"
    return "illisible"


def lire_registre(data):
    if not isinstance(data, dict):
        raise ValueError("le registre doit être un objet JSON")
    if not isinstance(data.get("name"), str) or not data["name"].strip():
        raise ValueError("name : le nom du chantier est obligatoire")
    for cle in ("missions", "decisions", "risks", "observations", "capabilities", "features", "follow_up"):
        valeur = data.setdefault(cle, [])
        if not isinstance(valeur, list):
            raise ValueError(f"{cle} doit être une liste")
    for cle in ("missions", "decisions", "risks", "observations", "capabilities", "features"):
        if any(not isinstance(x, dict) for x in data[cle]):
            raise ValueError(f"{cle} : chaque élément est un objet")
    ids = [m.get("id") for m in data["missions"]]
    if any(not isinstance(i, str) or not re.fullmatch(r"[A-Za-z0-9][\w.-]{0,31}", i) for i in ids):
        raise ValueError("missions : chaque mission a un id court (M1, I1…), celui de son message MISSION")
    if len(set(ids)) != len(ids):
        raise ValueError("missions : identifiant en double")
    for m in data["missions"]:
        dependances = m.get("depends_on", [])
        if not isinstance(dependances, list):
            raise ValueError(f"{m['id']} : depends_on doit être une liste")
        inconnues = [d for d in dependances if d not in ids]
        if inconnues:
            raise ValueError(f"{m['id']} dépend de missions absentes du plan : {', '.join(map(str, inconnues))}")
    return data


def lire_evenements(evenements):
    if not isinstance(evenements, list) or any(not isinstance(e, dict) for e in evenements):
        raise ValueError("les événements doivent être une liste d'objets, celle qu'exporte KoA")
    faits = []
    vus = set()
    for e in sorted(evenements, key=lambda e: (e.get("MessageId", 0), e.get("Version", 0))):
        try:
            quand = minute(e["Quand"])
        except (KeyError, ValueError) as erreur:
            raise ValueError(f"événement n°{e.get('MessageId')} : date illisible") from erreur
        # Une fiche part à l'exécutant et à ses relecteurs en un envoi, une revue à l'exécutant et à
        # l'orchestrateur : une copie par destinataire, un seul fait.
        cle = (e.get("Type"), e.get("Mission"), e.get("Auteur"), e.get("Texte"))
        if cle in vus:
            continue
        vus.add(cle)
        faits.append(dict(e, quand=quand))
    return faits


def suivre(missions, faits):
    """Ce que le journal dit de chaque mission : départ, revues, blocages, fin. Rien n'est déduit d'autre chose."""
    suivi = {m["id"]: {"debut": None, "fin": None, "resultats": 0, "revues": [], "blocages": []} for m in missions}
    for f in faits:
        s = suivi.get(f.get("Mission") or "")
        if s is None:
            continue
        if f.get("Type") == "MISSION":
            s["debut"] = s["debut"] or f["quand"]
        elif f.get("Type") == "RÉSULTAT":
            s["resultats"] += 1
        elif f.get("Type") == "REVUE":
            sha = SHA.search(f.get("Texte") or "")
            s["revues"].append({"n": f.get("MessageId"), "par": f.get("Auteur"), "verdict": verdict(f.get("Texte") or ""),
                                "sha": sha.group(0) if sha else None, "quand": f["quand"]})
        elif f.get("Type") == "BLOCAGE":
            s["blocages"].append(f)
    for s in suivi.values():
        derniere = s["revues"][-1] if s["revues"] else None
        s["acceptee"] = derniere if derniere and derniere["verdict"] == "accepté" else None
        s["fin"] = s["acceptee"]["quand"] if s["acceptee"] else None
        s["refus"] = sum(1 for r in s["revues"] if r["verdict"] in ("refusé", "non concluant"))
    return suivi


def etat(mission, s, avec_journal):
    if not avec_journal:
        return clean(mission.get("state") or PAS_MESURE)
    if mission.get("state") in ("abandonnée", "reportée"):
        return mission["state"]
    if s["acceptee"]:
        return "acceptée"
    if not s["debut"]:
        return "prévue"
    if s["revues"]:
        return "en reprise"
    return "en revue" if s["resultats"] else "en cours"


def gantt(missions, suivi, borne):
    lignes = ["gantt", "    dateFormat YYYY-MM-DDTHH:mm", "    axisFormat %H:%M"]
    vague = object()
    taches = 0
    for m in sorted(missions, key=lambda m: (m["wave"] if isinstance(m.get("wave"), int) else 10 ** 6, m["id"])):
        s = suivi[m["id"]]
        if not s["debut"]:
            continue
        if m.get("wave") != vague:
            vague = m.get("wave")
            lignes.append(f"    section Vague {vague if vague is not None else '?'}")
        fin = s["fin"] or borne
        if fin <= s["debut"]:
            fin = s["debut"] + datetime.timedelta(minutes=1)
        statut = "done" if s["fin"] else "active"
        tache = re.sub(r"[^A-Za-z0-9_]", "_", m["id"])
        lignes.append(f"    {m['id']} :{statut}, {tache}, {s['debut']:%Y-%m-%dT%H:%M}, {fin:%Y-%m-%dT%H:%M}")
        taches += 1
    if not taches:
        return "Aucune mission partie : pas de Gantt.\n"
    return "```mermaid\n" + "\n".join(lignes) + "\n```\n"


def tableau(entetes, lignes):
    if not lignes:
        return "Aucun.\n"
    tete = "| " + " | ".join(entetes) + " |\n|" + "---|" * len(entetes) + "\n"
    return tete + "\n".join("| " + " | ".join(clean(v) for v in ligne) + " |" for ligne in lignes) + "\n"


def jetons(nombre):
    """Assez pour comparer deux missions d'un coup d'œil ; le détail reste dans le fichier des coûts."""
    if nombre >= 1_000_000:
        return f"{nombre / 1_000_000:.2f} M".replace(".", ",")
    return f"{nombre / 1_000:.1f} k".replace(".", ",")


def valeurs(cout, cle):
    return ", ".join(str(v) for v in cout.get(cle) or []) or PAS_MESURE


def ligne_cout(libelle, cout):
    return [libelle, valeurs(cout, "Modeles"), valeurs(cout, "Efforts"), str(cout.get("Tours", 0)), jetons(cout.get("CacheLu", 0)),
            jetons(cout.get("CacheCree", 0)), jetons(cout.get("Sortie", 0))]


def lire_couts(couts):
    if couts is None:
        return None
    if not isinstance(couts, dict) or not isinstance(couts.get("Missions"), dict):
        raise ValueError("les coûts doivent être l'objet qu'exporte KoA")
    return couts


def section_couts(missions, couts):
    """Lu par KoA dans les transcripts. Ce tableau n'existe que s'il est vrai : un agent illisible se nomme, sa part n'est pas un zéro."""
    if couts is None:
        return "Pas mesuré : la génération n'a pas reçu les coûts, relevés par KoA à chaque actualisation.\n"
    par_mission = couts["Missions"]
    connues = [m["id"] for m in missions]
    # Une mission lancée hors du registre a coûté quand même : elle se voit, et l'écart avec le plan aussi.
    ids = connues + sorted(i for i in par_mission if i not in connues)
    # Pas de tour attribué : un tiret, pas un zéro, car rien ne dit que la mission n'a rien coûté.
    lignes = [ligne_cout(i, par_mission[i]) if i in par_mission else [i, *["—"] * 6] for i in ids]
    lignes.append(ligne_cout("hors mission", couts.get("HorsMission") or {}))
    lignes.append(ligne_cout("total", couts.get("Total") or {}))
    note = ("\nLes totaux sont exacts. L'attribution est approchée : un tour compte pour la mission du dernier message "
            "que son agent a envoyé ou reçu. « hors mission » : prise de poste, coordination, finalisation et clôture.\n")
    if couts.get("NonMesures"):
        note += f"\nTranscript non lu, ces chiffres sont donc des minimums : {clean(couts['NonMesures'])}.\n"
    return tableau(["Mission", "Modèle", "Effort", "Tours", "Lus en cache", "Créés en cache", "Sortie"], lignes) + note


def lignes_cout_total(couts):
    if couts is None:
        return [["Coût (tours, jetons, modèle, effort)", PAS_MESURE]]
    total = couts.get("Total") or {}
    hors = couts.get("HorsMission") or {}
    part = round(100 * hors.get("Tours", 0) / total["Tours"]) if total.get("Tours") else 0
    non_mesures = couts.get("NonMesures") or []
    return [
        ["Tours" + (" (minimum : un agent non mesuré)" if non_mesures else ""), str(total.get("Tours", 0))],
        ["Lus en cache / créés en cache / sortie", f"{jetons(total.get('CacheLu', 0))} / {jetons(total.get('CacheCree', 0))} / {jetons(total.get('Sortie', 0))}"],
        ["Modèle / effort", f"{valeurs(total, 'Modeles')} / {valeurs(total, 'Efforts')}"],
        ["Part des tours hors mission", f"{part} %"],
    ]


def mesures(missions, suivi, faits, couts=None):
    """Ce qui se compare d'un chantier à l'autre ; sans journal, rien n'est mesuré, et c'est dit."""
    if faits is None:
        return "Pas mesuré : la génération n'a pas reçu le journal de la Cantina.\n"
    jalons = [m for m in missions if m["id"].startswith("I")]
    debuts = [s["debut"] for s in suivi.values() if s["debut"]]
    fins = [s["fin"] for s in suivi.values() if s["fin"]]
    defauts = sum(1 for j in jalons if suivi[j["id"]]["refus"] or suivi[j["id"]]["blocages"])
    lignes = [
        ["Missions au plan / parties / acceptées", f"{len(missions)} / {len(debuts)} / {len(fins)}"],
        ["Revues refusées ou non concluantes (reprises)", str(sum(s["refus"] for s in suivi.values()))],
        ["Blocages remontés", str(sum(len(s["blocages"]) for s in suivi.values()))],
        ["Jalons d'intégration / ayant trouvé un défaut", f"{len(jalons)} / {defauts}"],
        ["Du premier départ à la dernière acceptation", duree(min(debuts), max(fins)) if debuts and fins else PAS_MESURE],
        *lignes_cout_total(couts),
    ]
    return tableau(["Mesure", "Valeur"], lignes)


def render(data, evenements=None, couts=None):
    data = lire_registre(data)
    faits = lire_evenements(evenements) if evenements is not None else None
    couts = lire_couts(couts)
    missions = data["missions"]
    suivi = suivre(missions, faits or [])
    borne = max((f["quand"] for f in faits), default=None) if faits else None
    journal = faits is not None
    nom = clean(data["name"])

    def ligne_plan(m):
        s = suivi[m["id"]]
        return [m["id"], m.get("wave"), m.get("feature"), m.get("owner"), m.get("depends_on") or "—",
                m.get("reviewers"), m.get("criticality"), etat(m, s, journal),
                heure(s["debut"]) if journal else m.get("start"), heure(s["fin"]) if journal else m.get("end"),
                duree(s["debut"], s["fin"]) if journal else PAS_MESURE]

    def preuve(m):
        a = suivi[m["id"]]["acceptee"]
        if not a:
            return clean(m.get("evidence"))
        source = f"REVUE n°{a['n']} de {a['par']}" + (f", sur {a['sha']}" if a["sha"] else ", SHA non cité")
        return source + (f" ; {clean(m.get('evidence'))}" if m.get("evidence") else "")

    criteres = "".join(f"- **{m['id']}** : " + "; ".join(clean(c) for c in (m.get("criteria") or [NON_RENSEIGNE])) + "\n"
                       for m in missions)
    blocages = [[b["Mission"], b.get("Auteur"), heure(b["quand"]), b.get("Texte"), f"n°{b.get('MessageId')}"]
                for s in suivi.values() for b in s["blocages"]]
    plan = (f"# Plan — {nom}\n\n"
            f"**Résultat attendu** : {clean(data.get('result'))}  \n"
            f"**Fini quand** : {clean(data.get('done_when'))}  \n"
            f"**Hors périmètre** : {clean(data.get('out_of_scope'))}  \n"
            f"**Équipe** : {clean(data.get('team'))}\n\n"
            "## Features\n\n" + tableau(["Feature", "Branche", "Finalisation"],
                                        [[f.get("name"), f.get("branch"), f.get("finalize")] for f in data["features"]]) +
            "\n## Missions\n\n" + tableau(["Id", "Vague", "Feature", "Pour", "Dépend de", "Relu par", "Criticité", "État",
                                           "Début", "Fin", "Durée"], [ligne_plan(m) for m in missions]) +
            "\n## Coût par mission\n\n" + section_couts(missions, couts) +
            "\n## Fini quand, par mission\n\n" + (criteres or "Aucune mission.\n") +
            "\n## Gantt\n\n" + (gantt(missions, suivi, borne) if faits else "Pas mesuré : aucun fait de la Cantina reçu.\n") +
            "\n## Risques\n\n" + tableau(["Risque", "Ce qui le montrerait", "État"],
                                         [[r.get("risk"), r.get("signal"), r.get("status")] for r in data["risks"]]) +
            "\n## Blocages remontés\n\n" + (tableau(["Mission", "Par", "Quand", "Message", "Source"], blocages)
                                             if journal else "Pas mesuré.\n") +
            "\n## Décisions\n\n" + tableau(["Décision", "Motif"], [[d.get("decision"), d.get("reason")] for d in data["decisions"]]) +
            "\n## Suivi\n\n" + ("".join(f"- {clean(x)}\n" for x in data["follow_up"]) or "Aucun.\n"))

    faites = [m for m in missions if suivi[m["id"]]["acceptee"] or (not journal and m.get("state") == "acceptée")]
    restantes = [m for m in missions if m not in faites]
    bilan = (f"# Bilan technico-fonctionnel — {nom}\n\n"
             "Les verdicts cités sont les déclarations des relecteurs, à leur numéro de message : ce bilan ne les certifie pas.\n\n"
             "## Réalisé\n\n" + tableau(["Mission", "Résultat", "Preuve"], [[m["id"], m.get("result"), preuve(m)] for m in faites]) +
             "\n## Non réalisé\n\n" + tableau(["Mission", "État", "Pourquoi"],
                                              [[m["id"], etat(m, suivi[m["id"]], journal), m.get("gap")] for m in restantes]) +
             "\n## Choix structurants\n\n" + tableau(["Décision", "Motif"], [[d.get("decision"), d.get("reason")] for d in data["decisions"]]) +
             "\n## Écarts\n\n" + (tableau(["Mission", "Revues refusées", "Blocages"],
                                           [[i, str(s["refus"]), str(len(s["blocages"]))] for i, s in suivi.items()
                                            if s["refus"] or s["blocages"]]) if journal else "Pas mesuré.\n") +
             "\n## Pas vérifié\n\n" + tableau(["Mission", "Pas vérifié"], [[m["id"], m.get("unverified")] for m in missions]) +
             "\n## Mesures\n\n" + mesures(missions, suivi, faits, couts))

    retenues = [o for o in data["observations"] if not o.get("duplicate_of")]
    doublons = [o for o in data["observations"] if o.get("duplicate_of")]
    rex = (f"# Retour d'expérience — {nom}\n\n"
           "## Observations\n\n" + tableau(["Id", "Fait", "Preuve", "Cause établie ou hypothèse", "Coût", "Portée", "Action"],
                                           [[o.get("id"), o.get("fact"), o.get("evidence"), o.get("cause"), o.get("cost"),
                                             o.get("scope"), o.get("action")] for o in retenues]) +
           "\n## Doublons écartés\n\n" + tableau(["Id", "Doublon de"], [[o.get("id"), o["duplicate_of"]] for o in doublons]) +
           "\n## Mesures du chantier\n\n" + mesures(missions, suivi, faits, couts))

    # La note de livraison se lit sans savoir ce qu'est un SHA : seule la déclaration « delivered », posée après la
    # livraison effective, fait passer une capacité dans « disponible ».
    libelles = {"finalized": "prête, pas encore livrée", "planned": "prévue", "dropped": "abandonnée"}
    livrees = [c for c in data["capabilities"] if c.get("state") == "delivered"]
    autres = [c for c in data["capabilities"] if c.get("state") != "delivered"]
    livraison = (f"# Note de livraison — {nom}\n\n"
                 "## Ce qui est disponible\n\n" + tableau(["Fonction", "Comment s'en servir", "Limites", "Prérequis"],
                                                          [[c.get("name"), c.get("usage"), c.get("limits"), c.get("prerequisites")]
                                                           for c in livrees]) +
                 "\n## Ce qui n'est pas encore disponible\n\n" +
                 tableau(["Fonction", "Où elle en est"], [[c.get("name"), libelles.get(c.get("state"), c.get("state") or "non livrée")]
                                                          for c in autres]))
    return {"plan.md": plan, "bilan.md": bilan, "rex.md": rex, "livraison.md": livraison}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("registry", type=Path, help="chantier.json, le registre de l'orchestrateur au QG")
    p.add_argument("--output", required=True, type=Path, help="le dossier des quatre vues")
    p.add_argument("--evenements", type=Path, help="les faits de la Cantina exportés par KoA (chantier_actualiser)")
    p.add_argument("--couts", type=Path, help="le coût par mission relevé par KoA dans les transcripts (chantier_actualiser)")
    a = p.parse_args(argv)
    try:
        data = json.loads(a.registry.read_text(encoding="utf-8"))
        evenements = json.loads(a.evenements.read_text(encoding="utf-8")) if a.evenements else None
        couts = json.loads(a.couts.read_text(encoding="utf-8")) if a.couts else None
        documents = render(data, evenements, couts)
        a.output.mkdir(parents=True, exist_ok=True)
        for nom, contenu in documents.items():
            with (a.output / nom).open("w", encoding="utf-8", newline="\n") as fichier:
                fichier.write(contenu)
        print(json.dumps({"documents": sorted(documents), "faits": evenements is not None}))
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as e:
        print(json.dumps({"erreur": str(e)}, ensure_ascii=False))
        sys.exit(2)


if __name__ == "__main__":
    main()
