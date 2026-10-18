#!/usr/bin/env python3
"""Garde-fou de déploiement du framework agentique KoA (hook PreToolUse sur Bash).

Une consigne n'est pas un contrôle : un agent à qui l'on a écrit « ne touche pas à la production »
l'atteint quand même si ses accès le lui permettent. Ce hook regarde chaque commande Bash au moment
où l'agent va la lancer. Si c'est une commande de déploiement, elle doit nommer une cible que le QG
du cluster déclare permise ; une cible interdite, ou aucune cible reconnue, et la commande est
refusée — raison dite à l'agent, trace écrite dans le journal.

La configuration vit dans le QG : `.claude/garde-fous.json` (voir `exemple/garde-fous.json`).

Trois états, jamais deux : un QG qui a configuré le garde-fou est protégé ; un QG qui ne l'a pas fait
voit chaque déploiement passer par la confirmation humaine (« ask »), avec la raison ; une
configuration illisible refuse les déploiements, plutôt que de laisser passer en silence.
"""
import datetime
import json
import os
import re
import sys

# Ce qui ressemble à un déploiement quand le QG n'en dit pas plus. Une liste blanche de verbes qui
# changent un environnement : lire (get, describe, plan, status) n'est jamais un déploiement.
COMMANDES_PAR_DEFAUT = [
    r"\bkubectl\b.*\b(apply|create|delete|replace|patch|rollout|scale|set)\b",
    r"\bhelm\b.*\b(install|upgrade|uninstall|rollback)\b",
    r"\bterraform\b.*\b(apply|destroy|import)\b",
    r"\btofu\b.*\b(apply|destroy|import)\b",
    r"\baz\b.*\b(create|update|delete|deploy|up|swap|restart)\b",
    r"\baws\b.*\b(deploy|update-service|create-deployment|put-|delete-)",
    r"\bgcloud\b.*\b(deploy|update|delete)\b",
    r"\bdocker\b.*\bcompose\b.*\b(up|down)\b",
    r"\bdocker\b.*\b(push|stack deploy)\b",
    r"\b(vercel|netlify|fly|flyctl|railway|heroku)\b.*\b(deploy|up|--prod)\b",
    r"\bansible-playbook\b",
]


def dossier_journal():
    racine = os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.join(
        os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state"), "koa-garde-fous")
    os.makedirs(racine, exist_ok=True)
    return racine


def journaliser(entree, decision, motif):
    """Une ligne par décision qui n'est pas un simple passage. Jamais la commande elle-même : elle
    peut porter un secret ; le motif et la cible suffisent à retrouver ce qui s'est passé."""
    try:
        ligne = {
            "quand": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "session": entree.get("session_id"),
            "projet": os.environ.get("CLAUDE_PROJECT_DIR") or entree.get("cwd"),
            "decision": decision,
            "motif": motif,
        }
        with open(os.path.join(dossier_journal(), "decisions.log"), "a", encoding="utf-8") as f:
            f.write(json.dumps(ligne, ensure_ascii=False) + "\n")
    except OSError as e:
        # Le journal est la seconde moitié de la loi « échouer sans bruit est interdit » : s'il ne
        # s'écrit pas, on le dit sur stderr, que Claude Code relaie comme erreur de hook.
        print(f"garde-fous : journal impossible à écrire ({e})", file=sys.stderr)


def repondre(decision, raison):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": raison,
    }}, ensure_ascii=False))


def nomme(commande, cible):
    """Une cible est nommée quand elle apparaît comme un mot entier : « prod-a » ne se trouve pas
    dans « preprod-a »."""
    return re.search(r"(?<![\w.-])" + re.escape(cible) + r"(?![\w-])", commande) is not None


def lire_configuration(projet):
    chemin = os.path.join(projet, ".claude", "garde-fous.json")
    if not os.path.isfile(chemin):
        return None, None
    try:
        with open(chemin, encoding="utf-8") as f:
            conf = json.load(f)
        dep = conf.get("deploiement") or {}
        for cle in ("commandes", "cibles_permises", "cibles_interdites"):
            valeur = dep.get(cle, [])
            if not isinstance(valeur, list) or not all(isinstance(v, str) and v for v in valeur):
                raise ValueError(f"« deploiement.{cle} » doit être une liste de textes non vides")
        for motif in dep.get("commandes", []):
            re.compile(motif)
        return conf, None
    except (OSError, ValueError, re.error) as e:
        return None, f"{chemin} : {e}"


def decider(entree, projet):
    """Rend (décision, raison) ; décision None quand la commande n'est pas un déploiement."""
    commande = (entree.get("tool_input") or {}).get("command") or ""
    conf, erreur = lire_configuration(projet)
    dep = (conf or {}).get("deploiement") or {}
    motifs = dep.get("commandes") or COMMANDES_PAR_DEFAUT
    if not any(re.search(m, commande) for m in motifs):
        return None, None

    if erreur:
        return "deny", (f"Garde-fous KoA : configuration illisible ({erreur}). Les déploiements sont "
                        "refusés tant qu'elle ne l'est plus : demande à l'humain de la corriger.")
    if conf is None:
        return "ask", ("Garde-fous KoA : ce dépôt ne déclare pas ses cibles de déploiement "
                       "(.claude/garde-fous.json absent). Cette commande ressemble à un déploiement : "
                       "l'humain confirme.")

    cluster = conf.get("cluster") or "ce cluster"
    interdites = [c for c in dep.get("cibles_interdites", []) if nomme(commande, c)]
    if interdites:
        return "deny", (f"Garde-fous KoA : « {interdites[0]} » est une cible interdite aux agents dans "
                        f"{cluster}. Ce déploiement est un geste humain : prépare-le, et demande.")
    permises = dep.get("cibles_permises", [])
    if any(nomme(commande, c) for c in permises):
        return "allow-implicite", None
    liste = ", ".join(permises) if permises else "aucune"
    return "deny", (f"Garde-fous KoA : cette commande de déploiement ne nomme aucune cible permise de "
                    f"{cluster} (permises : {liste}). Nomme la cible explicitement, ou demande à "
                    "l'humain si elle doit être ajoutée au QG.")


def main():
    try:
        entree = json.load(sys.stdin)
    except ValueError as e:
        print(f"garde-fous : entrée du hook illisible ({e})", file=sys.stderr)
        return 1
    if entree.get("tool_name") != "Bash":
        return 0
    projet = os.environ.get("CLAUDE_PROJECT_DIR") or entree.get("cwd") or os.getcwd()
    decision, raison = decider(entree, projet)
    if decision is None:
        return 0
    if decision == "allow-implicite":
        # On ne dit pas « allow » : le flux normal des permissions continue, et un deny du projet
        # garde le dernier mot.
        journaliser(entree, "permis", "cible permise nommée")
        return 0
    journaliser(entree, decision, raison)
    repondre(decision, raison)
    return 0


if __name__ == "__main__":
    sys.exit(main())
