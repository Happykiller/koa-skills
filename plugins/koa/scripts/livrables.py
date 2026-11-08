#!/usr/bin/env python3
"""Les quatre vues d'un chantier — plan, bilan, REX, note de livraison — et sa page de suivi, depuis une seule source.

Le registre `chantier.json` porte ce que seul l'orchestrateur sait : le plan, les critères, les décisions, les
observations, les capacités. Les faits datés — qui a reçu sa mission et quand, quelle revue a conclu quoi sur quel
SHA, quel blocage — viennent du journal de la Cantina (`--evenements`, exporté par KoA) : personne ne les recopie.

Déterministe : mêmes entrées, mêmes octets — aucune heure de génération, aucun ordre de dictionnaire. Un fait de la
Cantina reste une déclaration attribuée, citée par son numéro de message : rien ici ne certifie une preuve, et une
capacité n'est « livrée » que si le registre le dit après la livraison effective.
"""
import argparse
import datetime
import html
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


def duree_minutes(minutes):
    """Une durée prévue ou mesurée, lisible d'un coup d'œil : « 45 min », « 1 h 20 »."""
    if minutes is None:
        return "—"
    return f"{minutes // 60} h {minutes % 60:02d}" if minutes >= 60 else f"{minutes} min"


def etat_au(borne, journal):
    """Une vue ne bouge qu'à l'actualisation : elle dit de quand date ce qu'elle montre, sans quoi un état figé se lit à jour."""
    if not journal:
        return "pas mesuré : la génération n'a pas reçu le journal de la Cantina"
    if borne is None:
        return "aucun fait de la Cantina reçu"
    return f"{heure(borne)}, dernier fait reçu de la Cantina — cette vue ne bouge qu'à l'actualisation"


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


PREVU_PAR_DEFAUT = 30


def prevu(mission):
    """La durée prévue de la fiche (« Prévu »), en minutes, telle que le registre la porte : rien d'autre ne l'estime."""
    valeur = mission.get("estimate_min")
    return valeur if isinstance(valeur, int) and not isinstance(valeur, bool) and valeur > 0 else None


def ordre_vague(m):
    return (m["wave"] if isinstance(m.get("wave"), int) else 10 ** 6, m["id"])


def gantt(missions, suivi, borne):
    """Le plan entier : ce qui est parti à ses heures, ce qui reste derrière ses dépendances, à sa durée prévue.

    Ce qui n'est pas parti n'a pas d'heure : il se place après ses dépendances, ou au dernier fait du journal, jamais à
    l'heure de génération — mêmes entrées, mêmes octets."""
    lignes = ["gantt", "    dateFormat YYYY-MM-DDTHH:mm", "    axisFormat %d/%m %Hh"]
    vague = object()
    parties = 0
    for m in sorted(missions, key=ordre_vague):
        s = suivi[m["id"]]
        if m.get("wave") != vague:
            vague = m.get("wave")
            lignes.append(f"    section Vague {vague if vague is not None else '?'}")
        tache = re.sub(r"[^A-Za-z0-9_]", "_", m["id"])
        if s["debut"]:
            fin = s["fin"] or borne
            if fin <= s["debut"]:
                fin = s["debut"] + datetime.timedelta(minutes=1)
            statut = "done" if s["fin"] else "active"
            lignes.append(f"    {m['id']} :{statut}, {tache}, {s['debut']:%Y-%m-%dT%H:%M}, {fin:%Y-%m-%dT%H:%M}")
            parties += 1
            continue
        duree_prevue = f"{prevu(m) or PREVU_PAR_DEFAUT}m"
        apres = [re.sub(r"[^A-Za-z0-9_]", "_", d) for d in m.get("depends_on") or []]
        quand = f"after {' '.join(apres)}" if apres else f"{borne:%Y-%m-%dT%H:%M}"
        lignes.append(f"    {m['id']} :{tache}, {quand}, {duree_prevue}")
    if not parties:
        return "Aucune mission partie : pas de Gantt.\n"
    note = ("" if all(prevu(m) or suivi[m["id"]]["debut"] for m in missions) else
            f"\nUne mission sans `estimate_min` au registre tient {PREVU_PAR_DEFAUT} min au Gantt : ce n'est pas une estimation.\n")
    return "```mermaid\n" + "\n".join(lignes) + "\n```\n" + note


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
                m.get("reviewers"), m.get("criticality"), etat(m, s, journal), duree_minutes(prevu(m)),
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
            f"**Équipe** : {clean(data.get('team'))}  \n"
            f"**État au** : {etat_au(borne, journal)}\n\n"
            "## Features\n\n" + tableau(["Feature", "Branche", "Finalisation"],
                                        [[f.get("name"), f.get("branch"), f.get("finalize")] for f in data["features"]]) +
            "\n## Missions\n\n" + tableau(["Id", "Vague", "Feature", "Pour", "Dépend de", "Relu par", "Criticité", "État",
                                           "Prévu", "Début", "Fin", "Durée"], [ligne_plan(m) for m in missions]) +
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
    return {"plan.md": plan, "bilan.md": bilan, "rex.md": rex, "livraison.md": livraison,
            "suivi.html": page_suivi(data, missions, suivi, journal, borne, couts)}


# --- La page de suivi ---------------------------------------------------------------------------------------------
# Ce que l'humain a validé au fil des chantiers, figé ici pour qu'aucun chantier ne le refasse, et donc ne le perde.
# Chaque cluster réécrivait sa page à chaque changement d'outil, et un réglage obtenu un soir disparaissait le
# chantier suivant (épic 210 de KoA). Les tests de cette forme sont dans tests/test_livrables.py.
# - La durée réelle seule, en couleur : verte si elle tient dans le prévu, rouge sinon. Jamais d'écart écrit en mots :
#   « 24 min prévu et 36 min d'avance » ne se lit pas, et « 1 h 18 de plus que prévu » non plus.
# - Le coût par mission, toujours : il avait disparu avec un changement d'outil.
# - Un bandeau d'avancement, et le Gantt du plan entier, missions à venir comprises.
# - L'heure de l'état : la page ne bouge qu'à l'actualisation, et un état figé ne doit pas se lire à jour.

MERMAID = "https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs"
# état de la vue → (libellé, pastille, case du bandeau)
CATEGORIES = {
    "acceptée": ("Faite", "ok", "fait"),
    "en cours": ("En cours", "run", "en_cours"),
    "en revue": ("En revue", "run", "en_cours"),
    "en reprise": ("En reprise", "run", "en_cours"),
    "prévue": ("À venir", "todo", "a_venir"),
    "abandonnée": ("Abandonnée", "off", "off"),
    "reportée": ("Reportée", "off", "off"),
}
ANCRE_SANS_JOURNAL = datetime.datetime(2000, 1, 1, 9, 0)


def h(valeur):
    if valeur is None or valeur == "" or valeur == []:
        return ""
    if isinstance(valeur, list):
        valeur = ", ".join(str(v) for v in valeur)
    return html.escape(str(valeur), quote=True)


def texte_mermaid(texte):
    return re.sub(r"\s+", " ", re.sub(r"[:;#]", " ", texte)).strip()


def minutes_entre(debut, fin):
    return int((fin - debut).total_seconds() // 60)


def colore(minutes, prevue):
    """La durée mesurée, en couleur face au prévu, et rien d'autre."""
    if minutes is None:
        return "—"
    if prevue is None:
        return duree_minutes(minutes)
    return f'<b class="duree {"ok" if minutes <= prevue else "hot"}">{duree_minutes(minutes)}</b>'


def titres_vagues(data):
    vagues = data.get("waves")
    if isinstance(vagues, dict):
        return {str(k): str(v) for k, v in vagues.items()}
    if isinstance(vagues, list):
        return {str(v.get("id")): str(v.get("title")) for v in vagues if isinstance(v, dict) and v.get("title")}
    return {}


def missions_suivies(missions, suivi, journal, borne):
    rangs = []
    for m in missions:
        s = suivi[m["id"]]
        e = etat(m, s, journal)
        lib, cls, cat = CATEGORIES.get(e, (e, "todo", "a_venir"))
        if s["blocages"] and cat in ("en_cours", "a_venir"):
            lib, cls, cat = f"{lib} · blocage", "hot", "bloque"
        reel = minutes_entre(s["debut"], s["fin"]) if s["debut"] and s["fin"] else None
        # Une mission en cours se mesure jusqu'au dernier fait reçu, jamais jusqu'à l'heure de génération.
        ecoule = minutes_entre(s["debut"], borne) if s["debut"] and not s["fin"] and borne and cat != "off" else None
        rangs.append({"m": m, "s": s, "lib": lib, "cls": cls, "cat": cat, "prevu": prevu(m), "reel": reel, "ecoule": ecoule})
    return rangs


def gantt_suivi(rangs, vagues, borne):
    ancre = borne or ANCRE_SANS_JOURNAL
    lignes = ["gantt", "  dateFormat YYYY-MM-DDTHH:mm", "  axisFormat %d/%m %Hh"]
    vague = object()
    for r in sorted(rangs, key=lambda r: ordre_vague(r["m"])):
        m, s = r["m"], r["s"]
        if m.get("wave") != vague:
            vague = m.get("wave")
            lignes.append(f"  section {texte_mermaid(vagues.get(str(vague)) or f'Vague {vague}')}")
        duree_prevue = r["prevu"] or PREVU_PAR_DEFAUT
        depasse = r["ecoule"] is not None and r["prevu"] is not None and r["ecoule"] > r["prevu"]
        tag = {"fait": "done, ", "off": "done, ", "bloque": "crit, active, "}.get(
            r["cat"], "crit, active, " if depasse else "active, " if r["cat"] == "en_cours" else "")
        titre = str(m.get("result") or "")
        nom = texte_mermaid(f"{m['id']} {titre[:55].rstrip() + '…' if len(titre) > 56 else titre}")
        tache = re.sub(r"[^A-Za-z0-9_]", "_", m["id"])
        if s["debut"] and s["fin"]:
            quand = f"{s['debut']:%Y-%m-%dT%H:%M}, {max(s['fin'], s['debut'] + datetime.timedelta(minutes=1)):%Y-%m-%dT%H:%M}"
        elif s["debut"]:
            # En cours : jusqu'au dernier fait, ou jusqu'à la fin prévue si elle est plus loin.
            fin = max(borne or s["debut"], s["debut"] + datetime.timedelta(minutes=duree_prevue))
            quand = f"{s['debut']:%Y-%m-%dT%H:%M}, {fin:%Y-%m-%dT%H:%M}"
        elif m.get("depends_on"):
            quand = "after " + " ".join(re.sub(r"[^A-Za-z0-9_]", "_", d) for d in m["depends_on"]) + f", {duree_prevue}m"
        else:
            quand = f"{ancre:%Y-%m-%dT%H:%M}, {duree_prevue}m"
        lignes.append(f"  {nom} :{tag}{tache}, {quand}")
    return "\n".join(lignes)


def couts_suivi(missions, couts):
    if couts is None:
        return '<p class="meta">Pas mesuré : la génération n\'a pas reçu les coûts, relevés par KoA à chaque actualisation.</p>'
    par_mission = couts["Missions"]
    connues = [m["id"] for m in missions]
    ids = connues + sorted(i for i in par_mission if i not in connues)
    corps = []
    for libelle, cout, classe in ([(i, par_mission.get(i), "") for i in ids] +
                                  [("hors mission", couts.get("HorsMission") or {}, ' class="total"'),
                                   ("total", couts.get("Total") or {}, ' class="total"')]):
        cellules = ([valeurs(cout, "Modeles"), valeurs(cout, "Efforts"), str(cout.get("Tours", 0)), jetons(cout.get("CacheLu", 0)),
                     jetons(cout.get("CacheCree", 0)), jetons(cout.get("Sortie", 0))] if cout is not None else ["—"] * 6)
        corps.append(f'<tr{classe}><td class="mono">{h(libelle)}</td>' + "".join(f'<td class="num">{h(c)}</td>' for c in cellules) + "</tr>")
    note = ("Les totaux sont exacts. L'attribution est approchée : un tour compte pour la mission du dernier message que son "
            "agent a envoyé ou reçu. « hors mission » : prise de poste, coordination, finalisation et clôture.")
    if couts.get("NonMesures"):
        note += f" Transcript non lu, ces chiffres sont donc des minimums : {h(couts['NonMesures'])}."
    return ('<div class="cadre"><table class="serre"><thead><tr><th>Mission</th><th>Modèle</th><th>Effort</th><th>Tours</th>'
            '<th>Lus en cache</th><th>Créés en cache</th><th>Sortie</th></tr></thead><tbody>' + "".join(corps) +
            f'</tbody></table></div><p class="meta">{note}</p>')


def indicateur_fraicheur(borne, journal, premier_depart):
    """Tout en haut : de quand date ce que la page montre, et depuis combien de temps — demandé le 08/11/2026.

    L'heure est celle du dernier fait reçu de la Cantina, la seule que porte la génération : une heure de génération
    changerait les octets à chaque actualisation. « Il y a … » se calcule donc dans le navigateur ; sans script, l'heure
    seule reste lisible. Au-delà de 30 min, le bandeau change de couleur."""
    if not journal or borne is None:
        return ('<div class="fraicheur"><span><b>Mise à jour</b> : pas mesurée, aucun fait de la Cantina reçu</span>'
                '<span class="note">la page ne bouge qu’à l’actualisation</span></div>')
    iso = f"{borne:%Y-%m-%dT%H:%M}"
    depart = (f'<span><b>Chantier parti</b> : {heure(premier_depart)} '
              f'<span data-depuis="{premier_depart:%Y-%m-%dT%H:%M}" data-prefixe="· depuis "></span></span>') if premier_depart else ""
    return (f'<div class="fraicheur" data-maj="{iso}"><span><b>Mise à jour</b> : {heure(borne)} '
            f'<span data-depuis="{iso}" data-prefixe="· il y a "></span></span>{depart}'
            '<span class="note">au dernier fait reçu de la Cantina ; la page ne bouge qu’à l’actualisation</span></div>')


def puces(items, vide):
    return "".join(f"<li>{x}</li>" for x in items) or f"<li>{vide}</li>"


def page_suivi(data, missions, suivi, journal, borne, couts):
    vagues = titres_vagues(data)
    rangs = missions_suivies(missions, suivi, journal, borne)
    actives = [r for r in rangs if r["cat"] != "off"]
    compte = {k: sum(1 for r in rangs if r["cat"] == k) for k in ("fait", "en_cours", "a_venir", "bloque")}
    if actives and all(r["prevu"] for r in actives):
        total = sum(r["prevu"] for r in actives)
        avance = round(100 * sum(r["prevu"] for r in actives if r["cat"] == "fait") / total)
        base = "pondéré par les durées prévues"
    else:
        avance = round(100 * compte["fait"] / len(actives)) if actives else 0
        base = "au nombre de missions"
    faites = [r for r in rangs if r["cat"] == "fait" and r["reel"] is not None]
    if faites:
        reel = sum(r["reel"] for r in faites)
        prevues = [r["prevu"] for r in faites if r["prevu"]]
        duree_reelle = colore(reel, sum(prevues) if len(prevues) == len(faites) else None)
    else:
        duree_reelle = "—"

    restantes = [r for r in actives if r["cat"] != "fait"]
    if not actives:
        phase = "aucune mission au plan"
    elif not restantes:
        phase = "toutes les missions acceptées"
    else:
        premiere = min(restantes, key=lambda r: ordre_vague(r["m"]))["m"].get("wave")
        partie = any(r["s"]["debut"] for r in restantes if r["m"].get("wave") == premiere)
        phase = f"Vague {premiere} {'en cours' if partie else 'à venir'}"

    lignes = []
    for v in sorted({r["m"].get("wave") for r in rangs}, key=lambda w: (0, w) if isinstance(w, int) else (1, str(w))):
        lignes.append(f'<tr class="vague"><th colspan="9">{h(vagues.get(str(v)) or f"Vague {v}")}</th></tr>')
        for r in [r for r in rangs if r["m"].get("wave") == v]:
            m, s = r["m"], r["s"]
            criteres = "".join(f"<li>{h(c)}</li>" for c in (m.get("criteria") or []))
            details = f"<details><summary>Fini quand</summary><ul>{criteres}</ul></details>" if criteres else ""
            note = f'<div class="note">{h(m.get("note"))}</div>' if m.get("note") else ""
            titre = f"<strong>{h(m.get('result'))}</strong>" if m.get("result") else ""
            if r["reel"] is not None:
                mesure = colore(r["reel"], r["prevu"])
            elif r["ecoule"] is not None:
                mesure = colore(r["ecoule"], r["prevu"]) + '<div class="note">en cours</div>'
            else:
                mesure = "—"
            debut = heure(s["debut"]) if s["debut"] else "—"
            fin = heure(s["fin"]) if s["fin"] else ""
            lignes.append(
                f'<tr><td class="mono">{h(m["id"])}<div class="note">{h(m.get("criticality"))}</div></td>'
                f"<td>{titre}{note}{details}</td>"
                f'<td class="mono">{h(m.get("owner"))}</td><td class="mono">{h(m.get("reviewers")) or "—"}</td>'
                f'<td class="mono">{h(m.get("depends_on")) or "—"}</td>'
                f'<td class="num">{duree_minutes(r["prevu"])}</td><td class="num">{h(debut)}<br>{h(fin)}</td>'
                f'<td class="num">{mesure}</td><td><span class="pill {r["cls"]}">{h(r["lib"])}</span></td></tr>')

    blocs = [b for s in suivi.values() for b in s["blocages"]]
    if not journal:
        blocages = "<li>Pas mesuré.</li>"
    else:
        blocages = puces([f"<b>{h(b['Mission'])}</b> · {h(b.get('Auteur'))} · {h(heure(b['quand']))} : {h(b.get('Texte'))} "
                          f'<span class="mono">(n°{h(b.get("MessageId"))})</span>' for b in blocs], "Aucun.")
    jalons = puces([f'<span class="pill {r["cls"]}">{h(r["lib"])}</span> <b>{h(r["m"]["id"])}</b> {h(r["m"].get("result"))}'
                    for r in rangs if r["m"]["id"].startswith("I")], "Aucun jalon d'intégration au plan.")
    equipe = data.get("team")
    equipe = puces([h(x) for x in equipe] if isinstance(equipe, list) else [h(equipe)] if equipe else [], "Non renseignée.")
    decisions = puces([f"{h(d.get('decision'))}<div class=\"note\">{h(d.get('reason'))}</div>" for d in data["decisions"]], "Aucune.")
    a_suivre = puces([h(x) for x in data["follow_up"]], "Rien pour l'instant.")
    risques = ('<div class="cadre"><table class="serre"><thead><tr><th>Risque</th><th>Ce qui le montrerait</th><th>État</th>'
               "</tr></thead><tbody>" + "".join(f"<tr><td>{h(x.get('risk'))}</td><td>{h(x.get('signal'))}</td><td>{h(x.get('status'))}</td></tr>"
                                                 for x in data["risks"]) + "</tbody></table></div>") if data["risks"] else '<p class="meta">Aucun.</p>'

    meta = f"<b>Résultat attendu</b> : {h(data.get('result')) or NON_RENSEIGNE}<br><b>Fini quand</b> : {h(data.get('done_when')) or NON_RENSEIGNE}"
    if data.get("out_of_scope"):
        meta += f"<br><b>Hors périmètre</b> : {h(data['out_of_scope'])}"
    fraicheur = indicateur_fraicheur(borne, journal, min((r["s"]["debut"] for r in rangs if r["s"]["debut"]), default=None))
    sans_date = "" if borne else ('<p class="meta">Aucune mission partie : le Gantt montre l\'enchaînement prévu, '
                                  "sans date réelle.</p>")
    return GABARIT_SUIVI.format(
        titre=h(data["name"]), phase=h(phase), meta=meta, fraicheur=fraicheur, avance=avance, base=h(base),
        fait=compte["fait"], en_cours=compte["en_cours"], a_venir=compte["a_venir"], bloque=compte["bloque"], total=len(rangs),
        duree_reelle=duree_reelle, gantt=h(gantt_suivi(rangs, vagues, borne)), sans_date=sans_date, lignes="\n".join(lignes),
        couts=couts_suivi(missions, couts), risques=risques, blocages=blocages, jalons=jalons, equipe=equipe,
        decisions=decisions, suivi=a_suivre, alerte=" alerte" if blocs else "", mermaid=MERMAID)


GABARIT_SUIVI = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{titre}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;800&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root {{
  --bg: #f5f6f4; --surface: #ffffff; --fg: #1d2421; --muted: #5d6963; --rule: #d9dfdb;
  --accent: #2f6f5e; --accent-soft: #e2efe9;
  --ok: #2c7a4b; --ok-bg: #e3f2e8; --run: #8a5a00; --run-bg: #fbefd5; --hot: #b3261e; --hot-bg: #fbe3e1;
  --todo: #4f5b66; --todo-bg: #e8ecef;
  --display: "Archivo", "Helvetica Neue", Arial, sans-serif;
  --body: "IBM Plex Sans", "Segoe UI", Roboto, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace;
  color-scheme: light;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #141917; --surface: #1c2320; --fg: #e4ebe7; --muted: #9aa8a1; --rule: #2e3833;
  --accent: #7cc4ad; --accent-soft: #20352e;
  --ok: #7fd19c; --ok-bg: #1d3426; --run: #f0c063; --run-bg: #3a2e14; --hot: #f19a93; --hot-bg: #3d1f1d;
  --todo: #aab6c0; --todo-bg: #262e33; color-scheme: dark }} }}
:root[data-theme="dark"] {{
  --bg: #141917; --surface: #1c2320; --fg: #e4ebe7; --muted: #9aa8a1; --rule: #2e3833;
  --accent: #7cc4ad; --accent-soft: #20352e;
  --ok: #7fd19c; --ok-bg: #1d3426; --run: #f0c063; --run-bg: #3a2e14; --hot: #f19a93; --hot-bg: #3d1f1d;
  --todo: #aab6c0; --todo-bg: #262e33; color-scheme: dark }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--bg); color: var(--fg); font-family: var(--body); font-size: 15px; line-height: 1.5; }}
.page {{ max-width: 1180px; margin: 0 auto; padding-block: 28px 56px; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); display: grid; gap: 28px; }}
.page > * {{ min-width: 0; }}
header {{ display: grid; gap: 6px; }}
.eyebrow {{ font-family: var(--mono); font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: var(--accent); }}
h1 {{ font-family: var(--display); font-weight: 800; font-size: clamp(24px, 4vw, 38px); line-height: 1.15; margin: 0; text-wrap: balance; overflow-wrap: anywhere; }}
h2 {{ font-family: var(--display); font-weight: 700; font-size: 19px; margin: 0 0 12px; }}
.meta {{ color: var(--muted); font-size: 13.5px; max-width: 80ch; margin: 0; overflow-wrap: anywhere; }}
.meta b {{ color: var(--fg); font-weight: 600; }}
.fraicheur {{ display: flex; flex-wrap: wrap; gap: 6px 22px; align-items: baseline; font-family: var(--mono); font-size: 13px; background: var(--surface); border: 1px solid var(--rule); border-left: 4px solid var(--accent); border-radius: 4px; padding: 8px 12px; }}
.fraicheur b {{ font-weight: 600; }} .fraicheur .note {{ margin: 0; }}
.fraicheur.vieille {{ border-left-color: var(--run); }}
.bandeau {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; }}
.kpi {{ background: var(--surface); border: 1px solid var(--rule); border-radius: 6px; padding: 12px 14px; display: grid; gap: 2px; align-content: start; }}
.kpi > b {{ font-family: var(--display); font-size: 26px; font-variant-numeric: tabular-nums; }}
.kpi span {{ color: var(--muted); font-size: 12.5px; letter-spacing: .03em; text-transform: uppercase; }}
.kpi small {{ color: var(--muted); font-size: 11.5px; }}
.barre {{ height: 6px; border-radius: 3px; background: var(--todo-bg); overflow: hidden; margin-top: 6px; }}
.barre i {{ display: block; height: 100%; background: var(--accent); }}
section {{ min-width: 0; }}
.cadre {{ background: var(--surface); border: 1px solid var(--rule); border-radius: 6px; padding: 16px; overflow-x: auto; -webkit-overflow-scrolling: touch; }}
pre.mermaid {{ margin: 0; min-width: 760px; background: transparent; }}
table {{ border-collapse: collapse; width: 100%; min-width: 860px; font-size: 13.5px; }}
table.serre {{ min-width: 640px; }}
th, td {{ text-align: left; vertical-align: top; padding: 9px 10px; border-bottom: 1px solid var(--rule); }}
thead th {{ font-size: 11.5px; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); font-weight: 600; white-space: nowrap; }}
tbody tr:last-child td {{ border-bottom: 0; }}
tr.vague th {{ background: var(--accent-soft); color: var(--fg); font-family: var(--display); font-size: 13.5px; letter-spacing: .02em; }}
tr.total td {{ font-weight: 600; }}
.mono {{ font-family: var(--mono); font-size: 12.5px; }}
.num {{ font-family: var(--mono); font-size: 12.5px; font-variant-numeric: tabular-nums; white-space: nowrap; }}
.duree.ok {{ color: var(--ok); }} .duree.hot {{ color: var(--hot); }}
.note {{ color: var(--muted); font-size: 12.5px; margin-top: 2px; }}
details {{ margin-top: 4px; font-size: 12.5px; color: var(--muted); }}
details summary {{ cursor: pointer; }}
details ul {{ margin: 4px 0 0; padding-left: 18px; }}
.pill {{ display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: 12px; font-weight: 600; white-space: nowrap; }}
.pill.ok {{ color: var(--ok); background: var(--ok-bg); }} .pill.run {{ color: var(--run); background: var(--run-bg); }}
.pill.hot {{ color: var(--hot); background: var(--hot-bg); }} .pill.todo, .pill.off {{ color: var(--todo); background: var(--todo-bg); }}
.colonnes {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(min(280px, 100%), 1fr)); gap: 16px; }}
.colonnes ul {{ margin: 0; padding-left: 18px; display: grid; gap: 6px; font-size: 14px; }}
.colonnes li {{ min-width: 0; overflow-wrap: anywhere; }}
.bloc {{ background: var(--surface); border: 1px solid var(--rule); border-radius: 6px; padding: 16px; min-width: 0; }}
.bloc.alerte {{ border-color: var(--hot); }}
section > .meta {{ margin-top: 8px; }}
</style></head><body>
<div class="page">
  {fraicheur}
  <header>
    <div class="eyebrow">Chantier · {phase}</div>
    <h1>{titre}</h1>
    <p class="meta">{meta}</p>
  </header>
  <div class="bandeau">
    <div class="kpi"><span>Avancement</span><b>{avance} %</b><div class="barre"><i style="width: {avance}%"></i></div><small>{base}</small></div>
    <div class="kpi"><span>Faites</span><b>{fait}</b><small>sur {total}</small></div>
    <div class="kpi"><span>En cours</span><b>{en_cours}</b></div>
    <div class="kpi"><span>À venir</span><b>{a_venir}</b></div>
    <div class="kpi"><span>Bloquées</span><b>{bloque}</b></div>
    <div class="kpi"><span>Durée réelle, en tout</span><b style="font-size:20px">{duree_reelle}</b><small>missions faites</small></div>
  </div>
  <section>
    <h2>Gantt</h2>
    <div class="cadre"><pre class="mermaid">{gantt}</pre></div>
    {sans_date}
  </section>
  <section>
    <h2>Missions</h2>
    <div class="cadre">
      <table>
        <thead><tr><th>Id</th><th>Résultat attendu</th><th>Pour</th><th>Relu par</th><th>Dépend de</th><th>Durée prévue</th><th>Début / fin</th><th>Durée réelle</th><th>État</th></tr></thead>
        <tbody>
{lignes}
        </tbody>
      </table>
    </div>
  </section>
  <section>
    <h2>Coût par mission</h2>
    {couts}
  </section>
  <div class="colonnes">
    <div class="bloc{alerte}"><h2>Blocages</h2><ul>{blocages}</ul></div>
    <div class="bloc"><h2>Jalons</h2><ul>{jalons}</ul></div>
    <div class="bloc"><h2>Équipe</h2><ul>{equipe}</ul></div>
  </div>
  <div class="colonnes">
    <div class="bloc"><h2>Décisions</h2><ul>{decisions}</ul></div>
    <div class="bloc"><h2>Suivi</h2><ul>{suivi}</ul></div>
  </div>
  <section>
    <h2>Risques</h2>
    {risques}
  </section>
</div>
<script>
// L'écart à maintenant se calcule à l'affichage : la page, elle, reste la même pour les mêmes faits.
(function () {{
  function ecart(iso) {{
    var m = Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
    if (!(m >= 0)) return null;
    return m < 60 ? m + " min" : Math.floor(m / 60) + " h " + String(m % 60).padStart(2, "0");
  }}
  function maj() {{
    try {{
      document.querySelectorAll("[data-depuis]").forEach(function (el) {{
        var e = ecart(el.getAttribute("data-depuis"));
        if (e) el.textContent = el.getAttribute("data-prefixe") + e;
      }});
      var bloc = document.querySelector(".fraicheur[data-maj]");
      if (bloc) {{
        var m = (Date.now() - new Date(bloc.getAttribute("data-maj")).getTime()) / 60000;
        bloc.classList.toggle("vieille", m > 30);
      }}
    }} catch (e) {{}}
  }}
  maj();
  setInterval(maj, 60000);
}})();
</script>
<script type="module">
import mermaid from "{mermaid}";
const t = document.documentElement.dataset.theme;
const sombre = t === "dark" || (t !== "light" && matchMedia("(prefers-color-scheme: dark)").matches);
// Le thème sombre de Mermaid peint les missions faites en gris clair sous un texte clair : illisible.
const sombres = {{ doneTaskBkgColor: "#2f5b47", doneTaskBorderColor: "#7fd19c", taskTextDarkColor: "#e4ebe7",
                  taskTextColor: "#e4ebe7", activeTaskBkgColor: "#3a2e14", activeTaskBorderColor: "#f0c063" }};
mermaid.initialize({{ startOnLoad: true, theme: sombre ? "dark" : "neutral", themeVariables: sombre ? sombres : {{}},
                     gantt: {{ useWidth: 1100 }} }});
</script>
</body></html>
"""


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("registry", type=Path, help="chantier.json, le registre de l'orchestrateur au QG")
    p.add_argument("--output", required=True, type=Path, help="le dossier des vues et de la page de suivi")
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
