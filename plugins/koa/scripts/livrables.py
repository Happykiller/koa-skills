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
    for cle in ("missions", "decisions", "risks", "observations", "capabilities", "features", "follow_up",
                "readiness", "human_queue", "acceptance", "resolved"):
        valeur = data.setdefault(cle, [])
        if not isinstance(valeur, list):
            raise ValueError(f"{cle} doit être une liste")
    for cle in ("missions", "decisions", "risks", "observations", "capabilities", "features", "readiness", "human_queue",
                "acceptance", "resolved"):
        if any(not isinstance(x, dict) for x in data[cle]):
            raise ValueError(f"{cle} : chaque élément est un objet")
    lire_note(data)
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


# Une capture se publie avec la page, sous ce chemin relatif : rien hors de `captures/`, aucun lien qui sortirait du QG.
CAPTURE = re.compile(r"captures/[A-Za-z0-9][\w.-]{0,80}\.(png|jpe?g|webp|gif)")
ENCARTS = ("info", "astuce", "attention", "nouveau")


def lire_note(data):
    """La note métier (épic 233 de KoA) : tout y est facultatif, pour qu'un registre déjà écrit reste valide, mais ce
    qui est donné a la bonne forme — une capture mal nommée échoue ici plutôt que de laisser un trou dans la page."""
    note = data.setdefault("delivery_note", {})
    if not isinstance(note, dict):
        raise ValueError("delivery_note doit être un objet")
    for cle in ("highlights", "rules", "faq", "next"):
        if not isinstance(note.setdefault(cle, []), list):
            raise ValueError(f"delivery_note.{cle} doit être une liste")
    for cle in ("rules", "faq"):
        if any(not isinstance(x, dict) for x in note[cle]):
            raise ValueError(f"delivery_note.{cle} : chaque élément est un objet")
    for c in data["capabilities"]:
        for cle in ("steps", "screenshots", "notes"):
            if not isinstance(c.setdefault(cle, []), list):
                raise ValueError(f"capabilities : {cle} doit être une liste ({c.get('name')})")
        for capture in c["screenshots"]:
            if not isinstance(capture, dict) or not CAPTURE.fullmatch(str(capture.get("file", ""))):
                raise ValueError(f"capabilities : capture refusée pour {c.get('name')} — un objet "
                                 '{"file": "captures/<nom>.png", "caption": …}, publié avec la page')
        for e in c["notes"]:
            if not isinstance(e, dict) or e.get("kind") not in ENCARTS:
                raise ValueError(f"capabilities : notes de {c.get('name')} — kind parmi {', '.join(ENCARTS)}")


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


# --- Les attentes de l'humain -------------------------------------------------------------------------------------
# Le chantier c11 d'un cluster a duré 22 h 47 pour sept heures de travail : deux permissions restées sans réponse,
# l'une la nuit, l'autre une journée entière, ont arrêté l'équipe 14 h 30 — et le REX n'en disait rien, il comptait
# « du premier départ à la dernière acceptation » (épic 221 de KoA). Une attente qu'on ne mesure pas ne se réduit pas.
KOA = "koa"
HUMAIN = "humain"
PERMISSION = re.compile(r"@([\w.-]+) attend une permission depuis (\d+) s")
LEVEE = "ATTENTE LEVÉE"
LEVEE_QUI = re.compile(r"@([\w.-]+)")


def attentes_humain(faits):
    """Chaque attente de l'humain, datée : qui, sur quelle mission, pour quoi, de quand à quand.

    Deux causes, toutes deux écrites au journal :
    - **permission** : KoA dit l'agent figé sur une permission (« @x attend une permission depuis N s »), et la lève
      par « ATTENTE LEVÉE — @x … » à la réponse. Un journal d'avant cette ligne se ferme au message suivant de l'agent :
      figé sur sa permission, il ne pouvait rien écrire d'autre.
    - **décision** : un agent écrit sa QUESTION ou son BLOCAGE à @humain. L'attente court jusqu'à ce que l'humain lui
      écrive à la table, ou jusqu'à son premier message qui nomme l'humain — celui qui relaie sa réponse (« l'humain a
      décidé… ») — ou sa clôture. Un pilote coordonne en attendant : son message suivant ne dit rien de la réponse.
    Une attente encore ouverte au dernier fait a `fin` à None : elle se mesure jusqu'au dernier fait, et se dit en cours."""
    attentes, ouvertes = [], {}

    def fermer(qui, quand, causes):
        for cause in causes:
            a = ouvertes.pop((qui, cause), None)
            if a:
                a["fin"] = max(quand, a["debut"])

    for f in faits:
        auteur, texte, type_ = f.get("Auteur"), f.get("Texte") or "", f.get("Type")
        if auteur == KOA:
            if (p := PERMISSION.search(texte)) and (p.group(1), "permission") not in ouvertes:
                # À la seconde : retrancher 61 s d'une minute tronquée avancerait le début d'une minute.
                try:
                    envoi = datetime.datetime.strptime(str(f["Quand"])[:19], "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    envoi = f["quand"]
                debut = (envoi - datetime.timedelta(seconds=int(p.group(2)))).replace(second=0)
                a = {"qui": p.group(1), "cause": "permission", "mission": f.get("Mission"), "debut": debut, "fin": None,
                     "n": f.get("MessageId")}
                ouvertes[(a["qui"], "permission")] = a
                attentes.append(a)
            elif type_ == LEVEE and (q := LEVEE_QUI.search(texte)):
                fermer(q.group(1), f["quand"], ["permission"])
            continue
        if auteur == HUMAIN:
            if f.get("Destinataire"):
                fermer(f["Destinataire"], f["quand"], ["décision"])
            continue
        fermer(auteur, f["quand"], ["permission"])
        if HUMAIN in texte.lower() or type_ in ("CLÔTURE", "COMPTE RENDU"):
            fermer(auteur, f["quand"], ["décision"])
        if f.get("Destinataire") == HUMAIN and type_ in ("QUESTION", "BLOCAGE"):
            a = {"qui": auteur, "cause": "décision", "mission": f.get("Mission"), "debut": f["quand"], "fin": None,
                 "n": f.get("MessageId")}
            ouvertes[(auteur, "décision")] = a
            attentes.append(a)
    return sorted(attentes, key=lambda a: (a["debut"], a["qui"]))


def temps_d_attente(attentes, borne):
    """Les minutes où au moins un agent attendait l'humain : deux attentes qui se recouvrent ne comptent qu'une fois."""
    total, courant = 0, None
    for debut, fin in sorted((a["debut"], a["fin"] or borne or a["debut"]) for a in attentes):
        if courant and debut <= courant[1]:
            courant[1] = max(courant[1], fin)
            continue
        if courant:
            total += minutes_entre(*courant)
        courant = [debut, fin]
    if courant:
        total += minutes_entre(*courant)
    return total


def ligne_attente(a, borne):
    fin = heure(a["fin"]) if a["fin"] else "en cours"
    return [a["qui"], a["mission"] or "—", a["cause"], heure(a["debut"]), fin, duree(a["debut"], a["fin"] or borne),
            f"n°{a['n']}"]


def section_attentes(attentes, borne, journal):
    if not journal:
        return "Pas mesuré : la génération n'a pas reçu le journal de la Cantina.\n"
    if not attentes:
        return "Aucune : personne n'a attendu l'humain.\n"
    return (tableau(["Qui", "Mission", "Cause", "Début", "Fin", "Durée", "Source"], [ligne_attente(a, borne) for a in attentes]) +
            "\nUne permission se pose au tour de table, éprouvée à blanc ; une décision prévisible se met au mandat. "
            "Après le lancement, un obstacle se résout, et seul l'impossible va à la file de l'humain. Chaque attente "
            "après le lancement appelle une observation au REX.\n")


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


def gantt(missions, suivi, borne, attentes=()):
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
    lignes += lignes_gantt_attentes(attentes, borne, "    ")
    note = ("" if all(prevu(m) or suivi[m["id"]]["debut"] for m in missions) else
            f"\nUne mission sans `estimate_min` au registre tient {PREVU_PAR_DEFAUT} min au Gantt : ce n'est pas une estimation.\n")
    return "```mermaid\n" + "\n".join(lignes) + "\n```\n" + note


def lignes_gantt_attentes(attentes, borne, retrait):
    """Les attentes de l'humain sous le plan, en rouge : un trou dans les barres se lit comme une équipe lente, pas
    comme une équipe arrêtée."""
    if not attentes:
        return []
    lignes = [f"{retrait}section Attente de l'humain"]
    for i, a in enumerate(attentes, 1):
        fin = max(a["fin"] or borne or a["debut"], a["debut"] + datetime.timedelta(minutes=1))
        nom = re.sub(r"[:#;]", " ", f"{a['qui']} {a['cause']}")
        lignes.append(f"{retrait}{nom} :crit, H{i}, {a['debut']:%Y-%m-%dT%H:%M}, {fin:%Y-%m-%dT%H:%M}")
    return lignes


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


def lignes_attente(faits, depart=None):
    """La part du chantier passée à attendre l'humain, du premier départ au dernier fait — la base de la page de suivi."""
    if not faits:
        return [["Attente de l'humain", "aucun fait"]]
    attentes = attentes_humain(faits)
    debut, borne = depart or min(f["quand"] for f in faits), max(f["quand"] for f in faits)
    attendu, etendue = temps_d_attente(attentes, borne), minutes_entre(debut, borne)
    part = f" ({round(100 * attendu / etendue)} % des {duree_minutes(etendue)} depuis le premier départ)" if etendue else ""
    permissions = sum(1 for a in attentes if a["cause"] == "permission")
    # Ce qui attend avant le premier départ appartient au cadrage et au tour de table, où l'humain est là exprès. Après,
    # le chantier s'exécute sans lui : chaque minute de cette ligne est un geste que l'audit n'a pas posé.
    apres = [dict(a, debut=max(a["debut"], debut)) for a in attentes if depart and (a["fin"] or borne) > debut]
    lignes = [
        ["Attente de l'humain (au moins un agent arrêté)", duree_minutes(attendu) + part],
        ["Attentes de l'humain : permissions / décisions", f"{permissions} / {len(attentes) - permissions}"],
    ]
    if depart:
        lignes.append(["Attente de l'humain après le lancement (cible : 0)", duree_minutes(temps_d_attente(apres, borne))])
    return lignes


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
        *lignes_attente(faits, min(debuts) if debuts else None),
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
    attentes = attentes_humain(faits) if faits else []
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
    # La liste de départ est l'audit du tour de table : tant qu'une ligne n'est pas éprouvée, rien ne part.
    depart = ("Chaque geste qui sort du dépôt de son agent, éprouvé au tour de table. Rien ne part tant qu'une ligne "
              "n'est pas « éprouvé ».\n\n" + tableau(["Rôle", "Geste", "Ce qu'il touche", "État", "Preuve ou ce qu'il faut"],
                                                    [[r.get("role"), r.get("gesture"), r.get("touches"), r.get("state"),
                                                      r.get("proof")] for r in data["readiness"]])
              if data["readiness"] else "Pas d'audit au registre : le tour de table n'a rien écrit.\n")
    file_humain = ("Ce que l'équipe n'a pas pu résoudre seule, présenté à l'humain à la fin du chantier.\n\n" +
                   tableau(["Geste ou décision", "Pour", "Pourquoi impossible", "Défaut pris", "Comment le faire"],
                           [[q.get("gesture"), q.get("by"), q.get("why"), q.get("default"), q.get("how")]
                            for q in data["human_queue"]])
                   if data["human_queue"] else "Vide : rien n'attend l'humain.\n")
    plan = (f"# Plan — {nom}\n\n"
            f"**Résultat attendu** : {clean(data.get('result'))}  \n"
            f"**Fini quand** : {clean(data.get('done_when'))}  \n"
            f"**Hors périmètre** : {clean(data.get('out_of_scope'))}  \n"
            f"**Cadrage** : {clean(data.get('framing'))}  \n"
            f"**Équipe** : {clean(data.get('team'))}  \n"
            f"**État au** : {etat_au(borne, journal)}\n\n"
            "## Liste de départ\n\n" + depart +
            "\n## Features\n\n" + tableau(["Feature", "Branche", "Finalisation"],
                                        [[f.get("name"), f.get("branch"), f.get("finalize")] for f in data["features"]]) +
            "\n## Missions\n\n" + tableau(["Id", "Vague", "Feature", "Pour", "Dépend de", "Relu par", "Criticité", "État",
                                           "Prévu", "Début", "Fin", "Durée"], [ligne_plan(m) for m in missions]) +
            "\n## Coût par mission\n\n" + section_couts(missions, couts) +
            "\n## Fini quand, par mission\n\n" + (criteres or "Aucune mission.\n") +
            "\n## Gantt\n\n" + (gantt(missions, suivi, borne, attentes) if faits else "Pas mesuré : aucun fait de la Cantina reçu.\n") +
            "\n## Risques\n\n" + tableau(["Risque", "Ce qui le montrerait", "État"],
                                         [[r.get("risk"), r.get("signal"), r.get("status")] for r in data["risks"]]) +
            "\n## Blocages remontés\n\n" + (tableau(["Mission", "Par", "Quand", "Message", "Source"], blocages)
                                             if journal else "Pas mesuré.\n") +
            "\n## Attentes de l'humain\n\n" + section_attentes(attentes, borne, journal) +
            "\n## File de l'humain\n\n" + file_humain +
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
             "\n## File de l'humain\n\n" + file_humain +
             "\n## Mesures\n\n" + mesures(missions, suivi, faits, couts))

    retenues = [o for o in data["observations"] if not o.get("duplicate_of")]
    doublons = [o for o in data["observations"] if o.get("duplicate_of")]
    rex = (f"# Retour d'expérience — {nom}\n\n"
           "## Observations\n\n" + tableau(["Id", "Fait", "Preuve", "Cause établie ou hypothèse", "Coût", "Portée", "Action"],
                                           [[o.get("id"), o.get("fact"), o.get("evidence"), o.get("cause"), o.get("cost"),
                                             o.get("scope"), o.get("action")] for o in retenues]) +
           "\n## Doublons écartés\n\n" + tableau(["Id", "Doublon de"], [[o.get("id"), o["duplicate_of"]] for o in doublons]) +
           "\n## Attentes de l'humain\n\n" + section_attentes(attentes, borne, journal) +
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
            "livraison.html": note_livraison(data),
            "suivi.html": page_suivi(data, missions, suivi, journal, borne, couts, attentes)}


# --- La note de livraison -------------------------------------------------------------------------------------------
# Épic 233 de KoA : la note des autres métiers n'était qu'un inventaire en deux tableaux, qu'un opérateur a dû reprendre
# à la main avant de la diffuser — « un document destiné au métier, pour lui expliquer les mises à jour, les nouveaux
# process, règles, screens à l'appui, pédagogique ». Le gabarit est celui de la note reprise, figé par des tests :
# public en tête, un geste par sous-titre, une capture par geste, rien de ce que seule l'équipe comprend.

def t(valeur):
    """Un texte de la note : échappé, et sans SHA — le métier ne sait pas ce que c'est, et n'a pas à l'apprendre."""
    if valeur is None or valeur == "" or valeur == []:
        return ""
    texte = ", ".join(map(str, valeur)) if isinstance(valeur, list) else str(valeur)
    return h(re.sub(r"\s{2,}", " ", SHA.sub("", texte)).strip())


def ancre(titre, deja):
    base = re.sub(r"[^a-z0-9]+", "-", sans_accents(titre).lower()).strip("-") or "section"
    cle, n = base, 2
    while cle in deja:
        cle, n = f"{base}-{n}", n + 1
    deja.add(cle)
    return cle


ETIQUETTES = {"info": "Bon à savoir", "astuce": "Astuce", "attention": "Attention", "nouveau": "Nouveau"}


def encart(kind, texte):
    return f'<div class="encart {kind}"><p class="etiq">{ETIQUETTES[kind]}</p><p>{texte}</p></div>'


def geste(c, numero):
    """Un geste de « Ce qui change pour vous » : qui, les étapes, la capture. Une capture absente se dit (loi 4)."""
    morceaux = []
    if c.get("who"):
        morceaux.append(f'<p class="qui"><strong>Qui :</strong> {t(c["who"])}</p>')
    etapes = [t(e) for e in c["steps"] if e] or ([t(c["usage"])] if c.get("usage") else [])
    if etapes:
        morceaux.append("<ol>" + "".join(f"<li>{e}</li>" for e in etapes) + "</ol>")
    for capture in c["screenshots"]:
        numero[0] += 1
        legende = t(capture.get("caption")) or "Légende non renseignée."
        morceaux.append(f'<figure><img src="{h(capture["file"])}" alt="{legende}" loading="lazy">'
                        f'<figcaption><span class="num">Figure {numero[0]}.</span>{legende}</figcaption></figure>')
    if not c["screenshots"]:
        morceaux.append(encart("attention", f"Pas de capture : {t(c.get('no_screenshot')) or 'non renseigné'}."))
    for e in c["notes"]:
        morceaux.append(encart(e["kind"], t(e.get("text"))))
    pieds = [f"<strong>{libelle} :</strong> {t(c.get(cle))}" for cle, libelle in
             (("rules", "Règles"), ("limits", "Limites"), ("prerequisites", "Prérequis")) if c.get(cle)]
    if pieds:
        morceaux.append('<p class="pied">' + " · ".join(pieds) + "</p>")
    return "".join(morceaux)


def note_livraison(data):
    note, nom = data["delivery_note"], t(data["name"])
    livrees = [c for c in data["capabilities"] if c.get("state") == "delivered"]
    autres = [c for c in data["capabilities"] if c.get("state") != "delivered"]
    libelles = {"finalized": "prête, pas encore livrée", "planned": "prévue", "dropped": "abandonnée"}
    deja, sections, numero = set(), [], [0]

    def section(titre, corps):
        sections.append((titre, ancre(titre, deja), corps))

    points = [f"<li>{t(p)}</li>" for p in note["highlights"] if p]
    if not livrees:
        points.insert(0, "<li><strong>Rien n’est encore livré</strong> : cette note se complète à la livraison.</li>")
    verifie = (f'<p>{t(note["verified"])}</p>' if note.get("verified")
               else f'<p class="non-renseigne">Ce qui a été vérifié, où et avec quels comptes : {NON_RENSEIGNE.lower()}.</p>')
    section("En bref", (f"<ul>{''.join(points)}</ul>" if points else "") + verifie)
    if livrees:
        corps = []
        for c in livrees:
            titre = str(c.get("name") or NON_RENSEIGNE)
            corps.append(f'<h3 id="{ancre(titre, deja)}">{t(titre)}</h3>{geste(c, numero)}')
        section("Ce qui change pour vous", "".join(corps))
    if note["rules"]:
        section("Ce que fait l’application", "".join(
            (f"<h3>{t(r.get('title'))}</h3>" if r.get("title") else "") + f"<p>{t(r.get('text'))}</p>" for r in note["rules"]))
    if note["faq"]:
        section("Questions fréquentes", "".join(
            f"<h3>{t(q.get('question'))}</h3><p>{t(q.get('answer'))}</p>" for q in note["faq"]))
    if autres:
        section("Ce qui n’est pas encore là", "<ul>" + "".join(
            f"<li><strong>{t(c.get('name'))}</strong> — {t(libelles.get(c.get('state'), c.get('state') or 'non livrée'))}"
            + (f" : {t(c['limits'])}" if c.get("limits") else "") + "</li>" for c in autres) + "</ul>")
    else:
        section("Ce qui n’est pas encore là", "<p>Tout ce qui était prévu est livré.</p>")
    if note["next"]:
        section("Et ensuite", "<ul>" + "".join(f"<li>{t(n)}</li>" for n in note["next"] if n) + "</ul>")

    meta = "".join(f"<li>{v}</li>" for v in (t(note.get("date")),
                                             f"Pour : {t(data['audience'])}" if data.get("audience") else "") if v)
    public = ("" if data.get("audience")
              else '<p class="alerte">Public non renseigné : il se demande au cadrage (audience).</p>')
    sommaire = "".join(f'<li><a href="#{a}">{h(titre)}</a></li>' for titre, a, _ in sections)
    corps = "".join(f'<h2 id="{a}">{h(titre)}</h2>{c}' for titre, a, c in sections)
    return NOTE_GABARIT.format(titre=t(note.get("title")) or nom, nom=nom, sous_titre=t(note.get("subtitle")),
                               meta=meta, public=public, sommaire=sommaire, corps=corps)


NOTE_GABARIT = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{nom}</title>
<style>
:root {{
  --fond: #f6f5f2; --papier: #ffffff; --encre: #1d2330; --doux: #5b6372; --trait: #e3e1dc;
  --accent: #2f5bd3; --accent-doux: #e8eefc; --vert: #1f7a4d; --vert-doux: #e6f4ec;
  --ambre: #9a6400; --ambre-doux: #fbf1dc; --violet: #6a3fb5; --violet-doux: #f0eafb;
  --ombre: 0 1px 2px rgba(20,24,33,.06), 0 8px 24px rgba(20,24,33,.06);
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --fond: #14171d; --papier: #1b1f27; --encre: #e7e9ee; --doux: #a3aab8; --trait: #2c323d;
    --accent: #8aa8ff; --accent-doux: #1f2a45; --vert: #6fd3a0; --vert-doux: #17302a;
    --ambre: #f0c060; --ambre-doux: #33290f; --violet: #c3a6ff; --violet-doux: #2a2140;
    --ombre: 0 1px 2px rgba(0,0,0,.3), 0 8px 24px rgba(0,0,0,.25);
  }}
}}
:root[data-theme="dark"] {{
  --fond: #14171d; --papier: #1b1f27; --encre: #e7e9ee; --doux: #a3aab8; --trait: #2c323d;
  --accent: #8aa8ff; --accent-doux: #1f2a45; --vert: #6fd3a0; --vert-doux: #17302a;
  --ambre: #f0c060; --ambre-doux: #33290f; --violet: #c3a6ff; --violet-doux: #2a2140;
  --ombre: 0 1px 2px rgba(0,0,0,.3), 0 8px 24px rgba(0,0,0,.25);
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--fond); color: var(--encre);
  font: 17px/1.65 system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }}
.page {{ max-width: 860px; margin: 0 auto; padding: 0 16px 64px; }}
header.couverture {{ margin: 32px 0 28px; padding: 40px 40px 32px; border-radius: 18px; color: #fff;
  background: linear-gradient(135deg, #22356f 0%, #2f5bd3 60%, #4f7cf0 100%); box-shadow: var(--ombre); }}
.couverture .surtitre {{ margin: 0 0 12px; font-size: 13px; letter-spacing: .08em; text-transform: uppercase; opacity: .85; }}
.couverture h1 {{ margin: 0 0 10px; font-size: clamp(28px, 5vw, 40px); line-height: 1.15; }}
.couverture .sous-titre {{ margin: 0 0 24px; font-size: 19px; opacity: .92; max-width: 40em; }}
.couverture .sous-titre:empty {{ display: none; }}
.couverture .meta {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 0; padding: 0; list-style: none; font-size: 14px; }}
.couverture .meta li {{ padding: 4px 12px; border-radius: 999px; background: rgba(255,255,255,.16); }}
.alerte {{ margin: 16px 0 0; padding: 8px 12px; border-radius: 8px; background: rgba(0,0,0,.25); font-size: 14px; }}
nav.sommaire {{ margin: 0 0 32px; padding: 20px 24px; background: var(--papier); border: 1px solid var(--trait); border-radius: 14px; }}
nav.sommaire p {{ margin: 0 0 8px; font-size: 13px; letter-spacing: .06em; text-transform: uppercase; color: var(--doux); }}
nav.sommaire ol {{ margin: 0; padding-left: 20px; columns: 2; column-gap: 32px; }}
nav.sommaire li {{ break-inside: avoid; }}
nav.sommaire a {{ color: var(--encre); text-decoration: none; }}
nav.sommaire a:hover {{ color: var(--accent); text-decoration: underline; }}
main {{ background: var(--papier); border: 1px solid var(--trait); border-radius: 18px; padding: 8px 40px 32px; box-shadow: var(--ombre); }}
h2 {{ margin: 40px 0 12px; padding-top: 24px; border-top: 1px solid var(--trait); font-size: 26px; line-height: 1.25; }}
main > h2:first-child {{ border-top: 0; padding-top: 16px; margin-top: 16px; }}
h3 {{ margin: 28px 0 8px; font-size: 20px; line-height: 1.3; }}
p {{ margin: 0 0 14px; }}
ul, ol {{ margin: 0 0 16px; padding-left: 24px; }}
li {{ margin: 4px 0; }}
strong {{ font-weight: 650; }}
a {{ color: var(--accent); }}
.qui, .pied {{ color: var(--doux); }}
.pied {{ font-size: 15px; }}
.non-renseigne {{ color: var(--ambre); }}
figure {{ margin: 22px 0 26px; break-inside: avoid; }}
figure img {{ display: block; width: 100%; height: auto; border-radius: 10px; border: 1px solid var(--trait);
  box-shadow: var(--ombre); background: #fff; }}
figcaption {{ margin-top: 10px; font-size: 14.5px; color: var(--doux); }}
figcaption .num {{ font-weight: 650; color: var(--encre); margin-right: 6px; }}
.encart {{ margin: 18px 0 22px; padding: 14px 18px; border-radius: 12px; border-left: 4px solid; break-inside: avoid; }}
.encart p {{ margin: 0; }}
.encart .etiq {{ margin-bottom: 4px; font-size: 12.5px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }}
.encart.info {{ background: var(--accent-doux); border-color: var(--accent); }} .encart.info .etiq {{ color: var(--accent); }}
.encart.astuce {{ background: var(--vert-doux); border-color: var(--vert); }} .encart.astuce .etiq {{ color: var(--vert); }}
.encart.attention {{ background: var(--ambre-doux); border-color: var(--ambre); }} .encart.attention .etiq {{ color: var(--ambre); }}
.encart.nouveau {{ background: var(--violet-doux); border-color: var(--violet); }} .encart.nouveau .etiq {{ color: var(--violet); }}
@media (max-width: 640px) {{
  body {{ font-size: 16px; }}
  header.couverture {{ padding: 28px 22px 24px; border-radius: 14px; }}
  main {{ padding: 4px 18px 24px; border-radius: 14px; }}
  nav.sommaire ol {{ columns: 1; }}
  h2 {{ font-size: 22px; }}
}}
@page {{ size: A4; margin: 16mm 14mm; }}
@media print {{
  :root {{ --fond: #fff; --papier: #fff; --ombre: none; }}
  body {{ font-size: 11.5pt; background: #fff; }}
  .page {{ max-width: none; padding: 0; }}
  header.couverture, .encart {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  header.couverture {{ margin-top: 0; }}
  main {{ border: 0; box-shadow: none; padding: 0; }}
  h2 {{ break-before: page; border-top: 0; padding-top: 0; }}
  main > h2:first-child {{ break-before: auto; }}
  h2, h3 {{ break-after: avoid; }}
}}
</style>
</head>
<body>
<div class="page">
  <header class="couverture">
    <p class="surtitre">Note de livraison</p>
    <h1>{titre}</h1>
    <p class="sous-titre">{sous_titre}</p>
    <ul class="meta">{meta}</ul>{public}
  </header>
  <nav class="sommaire" aria-label="Sommaire"><p>Sommaire</p><ol>{sommaire}</ol></nav>
  <main>{corps}</main>
</div>
</body>
</html>
"""


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


def gantt_suivi(rangs, vagues, borne, attentes=()):
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
    lignes += lignes_gantt_attentes(attentes, borne, "  ")
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


def attente_suivi(attentes, borne, journal, premier):
    """Le bandeau et le bloc des attentes de l'humain. Une attente ouverte se dit en tête : c'est l'humain qui lit la page,
    et c'est lui que l'équipe attend."""
    if not journal:
        return "pas mesurée", "", "<li>Pas mesuré.</li>", ""
    attendu = temps_d_attente(attentes, borne)
    etendue = minutes_entre(premier, borne) if premier and borne else 0
    part = f"{round(100 * attendu / etendue)} % du chantier" if etendue else "rien à rapporter"
    items = puces([f"<b>{h(a['qui'])}</b> · {h(a['cause'])}{' · ' + h(a['mission']) if a['mission'] else ''} · "
                   f"{h(heure(a['debut']))} → {h(heure(a['fin'])) if a['fin'] else 'en cours'} · "
                   f"{h(duree(a['debut'], a['fin'] or borne))} <span class=\"mono\">(n°{h(a['n'])})</span>"
                   for a in attentes], "Personne n'a attendu l'humain.")
    ouvertes = [a for a in attentes if not a["fin"]]
    alerte = ""
    if ouvertes:
        qui = ", ".join(f"@{a['qui']} ({a['cause']}, depuis {heure(a['debut'])})" for a in ouvertes)
        alerte = f'<div class="fraicheur attend"><span><b>L’équipe t’attend</b> : {h(qui)}</span></div>'
    return duree_minutes(attendu), part, items, alerte


# La page de fin (épic 228 de KoA) : les livrables de fin n'étaient que des .md au QG, qu'il fallait cloner pour les lire.
# Chantier clos, la page de suivi devient le bilan, à la même URL : ce que l'humain lit en revenant, en tête.
VERDICTS = {"réalisé": "ok", "non réalisé": "hot", "pas vérifié": "run"}


def tableau_html(entetes, lignes):
    if not lignes:
        return '<p class="meta">Aucun.</p>'
    tete = "".join(f"<th>{h(e)}</th>" for e in entetes)
    corps = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in ligne) + "</tr>" for ligne in lignes)
    return f'<div class="cadre"><table class="serre"><thead><tr>{tete}</tr></thead><tbody>{corps}</tbody></table></div>'


def bilan_suivi(data):
    if not data.get("closed"):
        return ""
    def verdict_critere(etat):
        cle = str(etat or "").strip().lower()
        return f'<span class="pill {VERDICTS.get(cle, "todo")}">{h(etat) or "—"}</span>'
    criteres = tableau_html(["Critère", "Verdict", "Preuve"],
                            [[h(c.get("criterion")), verdict_critere(c.get("state")), h(c.get("evidence"))]
                             for c in data["acceptance"]])
    resolus = tableau_html(["Obstacle", "Solution prise", "Créé puis retiré"],
                           [[h(r.get("obstacle")), h(r.get("solution")), h(r.get("removed")) or "—"] for r in data["resolved"]])
    file_humain = tableau_html(["Geste ou décision", "Pour", "Pourquoi impossible", "Comment le faire"],
                               [[h(q.get("gesture")), h(q.get("by")), h(q.get("why")), f'<span class="mono">{h(q.get("how"))}</span>']
                                for q in data["human_queue"]])
    libelles = {"delivered": ("disponible", "ok"), "finalized": ("prête, pas encore livrée", "run"),
                "planned": ("prévue", "todo"), "dropped": ("abandonnée", "off")}
    capacites = tableau_html(["Fonction", "État", "Comment s'en servir", "Limites", "Prérequis"],
                             [[h(c.get("name")),
                               '<span class="pill {1}">{0}</span>'.format(*map(h, libelles.get(c.get("state"), (c.get("state") or "non livrée", "todo")))),
                               h(c.get("usage")), h(c.get("limits")), h(c.get("prerequisites"))] for c in data["capabilities"]])
    rex = tableau_html(["Fait", "Cause", "Action"],
                       [[h(o.get("fact")), h(o.get("cause")), h(o.get("action"))]
                        for o in data["observations"] if not o.get("duplicate_of")])
    return ('<section class="bilan"><h2>Bilan du chantier</h2>'
            '<p class="meta">Chantier clos : cette page est le compte rendu de fin. Les vues détaillées restent au QG.</p></section>'
            f"<section><h2>Critères d’acceptation</h2>{criteres}</section>"
            f"<section><h2>Livraison</h2>{capacites}</section>"
            f"<section><h2>Ce que l’équipe a résolu seule</h2>{resolus}</section>"
            f"<section><h2>File de l’humain</h2>{file_humain}</section>"
            f"<section><h2>Retour d’expérience</h2>{rex}</section>")


def page_suivi(data, missions, suivi, journal, borne, couts, attentes=()):
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
    if data.get("closed"):
        phase = "clos · bilan"
    elif not actives:
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
    premier = min((r["s"]["debut"] for r in rangs if r["s"]["debut"]), default=None)
    fraicheur = indicateur_fraicheur(borne, journal, premier)
    attente, part_attente, attentes_li, attend = attente_suivi(attentes, borne, journal, premier)
    sans_date = "" if borne else ('<p class="meta">Aucune mission partie : le Gantt montre l\'enchaînement prévu, '
                                  "sans date réelle.</p>")
    return GABARIT_SUIVI.format(
        titre=h(data["name"]), phase=h(phase), meta=meta, fraicheur=fraicheur, avance=avance, base=h(base),
        fait=compte["fait"], en_cours=compte["en_cours"], a_venir=compte["a_venir"], bloque=compte["bloque"], total=len(rangs),
        duree_reelle=duree_reelle, gantt=h(gantt_suivi(rangs, vagues, borne, attentes)), attente=attente,
        part_attente=h(part_attente), attentes=attentes_li, attend=attend, alerte_attente=" alerte" if attend else "", sans_date=sans_date, lignes="\n".join(lignes),
        couts=couts_suivi(missions, couts), risques=risques, blocages=blocages, jalons=jalons, equipe=equipe,
        decisions=decisions, suivi=a_suivre, alerte=" alerte" if blocs else "", mermaid=MERMAID, bilan=bilan_suivi(data))


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
.fraicheur.attend {{ border-left-color: var(--hot); margin-top: 8px; }}
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
  {attend}
  <header>
    <div class="eyebrow">Chantier · {phase}</div>
    <h1>{titre}</h1>
    <p class="meta">{meta}</p>
  </header>
  {bilan}
  <div class="bandeau">
    <div class="kpi"><span>Avancement</span><b>{avance} %</b><div class="barre"><i style="width: {avance}%"></i></div><small>{base}</small></div>
    <div class="kpi"><span>Faites</span><b>{fait}</b><small>sur {total}</small></div>
    <div class="kpi"><span>En cours</span><b>{en_cours}</b></div>
    <div class="kpi"><span>À venir</span><b>{a_venir}</b></div>
    <div class="kpi"><span>Bloquées</span><b>{bloque}</b></div>
    <div class="kpi"><span>Durée réelle, en tout</span><b style="font-size:20px">{duree_reelle}</b><small>missions faites</small></div>
    <div class="kpi"><span>Attente de l’humain</span><b style="font-size:20px">{attente}</b><small>{part_attente}</small></div>
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
    <div class="bloc{alerte_attente}"><h2>Attentes de l’humain</h2><ul>{attentes}</ul></div>
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
