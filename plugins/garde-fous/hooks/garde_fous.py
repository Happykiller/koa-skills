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

Une seconde section, `fusion`, est **toujours active** : c'est une règle du framework, pas un fait de
cluster, et `.claude/garde-fous.json` n'y change rien. Elle est jugée avant le déploiement. Un
`gh pr merge` est refusé :
- s'il porte `--admin`, qui passe outre les protections et la CI requise ;
- s'il ne porte pas `--match-head-commit` suivi d'un SHA complet (40 caractères hexadécimaux) : on
  fusionne la tête que la revue a acceptée, pas celle qu'on trouve en arrivant ;
- dans une distro née de KoA (`/etc/koa-seed` existe) dont le témoin `~/.local/state/koa/droits` ne
  porte pas la ligne `fusionner` : seul l'orchestrateur fusionne, et KoA ne pose ce témoin qu'à lui ;
- quand la commande est illisible (guillemets non fermés) et parle de `gh`, `pr` et `merge` : pour une
  fusion, on refuse ce qu'on n'a pas su lire.

La commande est lue segment par segment (`&&`, `||`, `;`, `|`, `&`, retours à la ligne) : une option
écrite dans un `echo` voisin ne compte pas pour la fusion.

Les limites, dites plutôt que tues : un alias de `gh`, un script qui l'appelle, `gh api …/merge` et un
`git push` sur la branche protégée ne sont pas reconnus. Ce garde tient contre la dérive, pas contre
la malveillance : l'agent a `sudo` dans sa distro, et son témoin est dans son foyer.
"""
import datetime
import json
import os
import re
import shlex
import sys

# Deux chemins de la distro, en constantes pour que les tests les remplacent. La marque est déposée
# par KoA à la naissance de toute distro ; le témoin, par KoA seul, et seulement à la distro dont la
# seed déclare le droit de fusionner.
MARQUE_KOA = "/etc/koa-seed"
TEMOIN_DROITS = os.path.expanduser("~/.local/state/koa/droits")

SHA_COMPLET = re.compile(r"[0-9a-fA-F]{40}")

# Ce qui ressemble à un déploiement quand le QG n'en dit pas plus. Une liste blanche de verbes qui
# changent un environnement : lire (get, describe, plan, status) n'est jamais un déploiement.
#
# Chaque motif est essayé sur un segment réécrit à partir de son mot de commande, et ne compte que
# s'il commence sur ce mot (ou sur une affectation qui le précède) : `grep "kubectl apply"`, un
# message de commit qui en parle ou `kubectl logs deploy/scale-worker` ne déploient rien, et la
# version 0.2.0, qui cherchait dans la commande brute, les refusait. Le verbe est la sous-commande
# (les options et leur valeur sautées), pas un mot rencontré plus loin : `plan -out=apply.tfplan`.
_OPTIONS = r"(?:\s+-\S+(?:\s+[^-\s]\S*)?)*"
COMMANDES_PAR_DEFAUT = [
    r"\bkubectl" + _OPTIONS + r"\s+(apply|create|delete|replace|patch|rollout|scale|set|edit|drain)\b",
    r"\bhelm" + _OPTIONS + r"\s+(install|upgrade|uninstall|rollback)\b",
    r"\b(terraform|tofu)(?:\s+-\S+)*\s+(apply|destroy|import)\b",
    r"\baz\b.*\s(create|update|delete|deploy|up|swap|restart)\b",
    r"\baws\b.*\s(deploy|update-service|create-deployment|put-|delete-)",
    r"\bgcloud\b.*\s(deploy|update|delete)\b",
    # Un compose local (la base de test, la clôture qui arrête ses conteneurs) n'est pas un
    # déploiement ; il le devient quand il vise un démon distant.
    r"\bDOCKER_(HOST|CONTEXT)=\S+.*\bdocker(-compose)?\b.*\s(up|down)\b",
    r"\bdocker\b.*\s(--context|-c|-H|--host)[\s=]\S+.*\s(compose\s.*\s)?(up|down)\b",
    r"\bdocker-compose\b.*\s(-H|--host)[\s=]\S+.*\s(up|down)\b",
    r"\bdocker(?:\s+-\S+(?:\s+[^-\s]\S*)?)*\s+(push|stack\s+deploy)\b",
    r"\b(vercel|netlify|fly|flyctl|railway|heroku)\b.*\s(deploy|up|--prod)\b",
    r"\bansible-playbook\b(?!.*\s--(syntax-check|check|list-hosts|list-tasks|list-tags)\b)",
]

# Ce qui précède le vrai mot de commande sans en être un, avec celles de leurs options qui prennent
# une valeur (sautée avec elles) ; `timeout` prend en plus une durée.
ENVELOPPES = {
    "sudo": {"-u", "-g", "-C", "-D", "-h", "-p", "-r", "-t", "-U"}, "doas": {"-u", "-C"},
    "env": {"-u", "-C", "-S"}, "nice": {"-n"}, "timeout": {"-s", "-k"}, "watch": {"-n", "-d"},
    "xargs": {"-n", "-P", "-I", "-L", "-s", "-d", "-a", "-E"}, "stdbuf": {"-i", "-o", "-e"},
    "time": set(), "nohup": set(), "exec": set(), "command": set(),
}
COQUILLES = {"sh", "bash", "zsh", "dash"}

# Le filet grossier, quand le jugement fin a planté : un mot d'outil de déploiement ou de fusion.
# Le même que celui de `garde-fous.sh`, qui ne lance Python que s'il le voit.
SUSPECT = (r"kubectl|helm|terraform|tofu|\baz\b|\baws\b|gcloud|docker|vercel|netlify|\bfly|railway"
           r"|heroku|ansible|\bgh\b")
AFFECTATION = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")


def dossier_journal():
    racine = os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.join(
        os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state"), "koa-garde-fous")
    os.makedirs(racine, exist_ok=True)
    return racine


def journaliser(entree, decision, motif):
    """Une ligne par décision qui n'est pas un simple passage. Jamais la commande elle-même : elle
    peut porter un secret ; le motif et la cible suffisent à retrouver ce qui s'est passé. Rend
    l'erreur quand la ligne ne s'écrit pas, pour qu'elle rejoigne la raison dite à l'agent."""
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
        return None
    except OSError as e:
        # Le journal est la seconde moitié de la loi « échouer sans bruit est interdit » : stderr
        # seul, sous un code 0, personne ne le lit — l'erreur part aussi dans la raison.
        print(f"garde-fous : journal impossible à écrire ({e})", file=sys.stderr)
        return f"journal impossible à écrire ({e})"


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
    chemin = chemin_de_configuration(projet)
    if chemin is None:
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


def mots_par_segment(commande):
    """Les mots de chaque segment de la commande. Lève ValueError quand shlex ne sait pas la lire."""
    # Une continuation de ligne n'est pas une fin de commande : ramenée à `;`, elle deviendrait un
    # `\;` échappé, donc un mot `;`, et couperait la fusion de son `--match-head-commit`.
    texte = re.sub(r"\\\r?\n", " ", commande).replace("\r\n", ";").replace("\n", ";")
    lecteur = shlex.shlex(texte, posix=True, punctuation_chars=";&|")
    lecteur.whitespace_split = True
    segments = [[]]
    for mot in lecteur:
        if mot and set(mot) <= set(";&|"):
            segments.append([])
        else:
            segments[-1].append(mot)
    return [s for s in segments if s]


def fusion_dans(mots):
    """Les mots qui suivent `gh pr merge` dans ce segment, ou None si le segment ne fusionne pas.
    `gh` est cherché partout dans le segment, pas seulement en tête : `sudo -u x gh …`, `xargs gh …`
    ou `env A=b gh …` fusionnent aussi."""
    for i, mot in enumerate(mots):
        if mot.rsplit("/", 1)[-1] != "gh":
            continue
        sous_commandes, j = [], i + 1
        while j < len(mots) and len(sous_commandes) < 2:
            if mots[j] in ("-R", "--repo"):
                j += 2  # `gh pr -R o/d merge` : la valeur de l'option n'est pas une sous-commande
                continue
            if not mots[j].startswith("-"):
                sous_commandes.append(mots[j])
            j += 1
        if sous_commandes == ["pr", "merge"]:
            return mots[j:]
    return None


def tete_nommee(mots):
    for i, mot in enumerate(mots):
        if mot.startswith("--match-head-commit="):
            valeur = mot.split("=", 1)[1]
        elif mot == "--match-head-commit" and i + 1 < len(mots):
            valeur = mots[i + 1]
        else:
            continue
        if SHA_COMPLET.fullmatch(valeur):
            return True
    return False


def droit_de_fusionner():
    """Hors d'une distro née de KoA, la question ne se pose pas : le garde ne sait pas qui est qui."""
    if not os.path.exists(MARQUE_KOA):
        return True
    try:
        with open(TEMOIN_DROITS, encoding="utf-8") as f:
            return any(ligne.strip() == "fusionner" for ligne in f)
    except OSError:
        return False


def juger_fusion(commande):
    """Rend (décision, raison) ; décision None quand la commande ne fusionne pas, ou fusionne bien."""
    try:
        segments = mots_par_segment(commande)
    except ValueError:
        if all(re.search(r"\b" + m + r"\b", commande) for m in ("gh", "pr", "merge")):
            return "deny", ("Garde-fous KoA : cette commande parle de fusion (gh, pr, merge) et ne se "
                            "lit pas (guillemets non fermés ?). Pour une fusion, on refuse ce qu'on n'a "
                            "pas su lire : récris-la sur une ligne lisible.")
        return None, None

    fusions = [suite for suite in map(fusion_dans, segments) if suite is not None]
    if not fusions:
        return None, None
    if not droit_de_fusionner():
        return "deny", ("Garde-fous KoA : seul l'orchestrateur fusionne (equipe/table, « Fusionner »). "
                        "Livre ta tête, et adresse ton RÉSULTAT à l'orchestrateur.")
    # `--admin` est cherché dans toute la commande, pas dans le seul segment : après shlex, un `";"`
    # entre guillemets ne se distingue plus d'un séparateur, et suffirait à l'en détacher.
    tous = [mot for segment in segments for mot in segment]
    if any(mot == "--admin" or mot.startswith("--admin=") for mot in tous):
        return "deny", ("Garde-fous KoA : jamais --admin : il passe outre les protections de la "
                        "branche et la CI requise.")
    if not all(tete_nommee(suite) for suite in fusions):
        return "deny", ("Garde-fous KoA : fusionne la tête que la REVUE a acceptée, avec "
                        "--match-head-commit et son SHA complet (40 caractères), écrit en toutes "
                        "lettres.")
    return None, None


def textes_a_juger(mots, profondeur=0):
    """Les textes d'un segment qu'un motif de déploiement doit juger, chacun avec la fin de son mot
    de commande : un motif ne compte que s'il commence avant. Les affectations de tête restent dans
    le texte (`DOCKER_HOST=… docker compose up`), les enveloppes en sortent (`sudo kubectl …`), et
    ce qu'une coquille (`bash -c "…"`) ou `ssh hôte …` exécute est jugé à son tour."""
    affectations, i = [], 0
    while i < len(mots):
        mot = mots[i]
        if AFFECTATION.match(mot):
            affectations.append(mot)
        elif mot.rsplit("/", 1)[-1] in ENVELOPPES:
            nom = mot.rsplit("/", 1)[-1]
            i += 1
            while i < len(mots) and (mots[i].startswith("-") or AFFECTATION.match(mots[i])):
                if mots[i] in ENVELOPPES[nom]:
                    i += 1  # la valeur de l'option, pas une commande
                elif AFFECTATION.match(mots[i]):
                    affectations.append(mots[i])
                i += 1
            if nom == "timeout" and i < len(mots):
                i += 1  # la durée
            continue
        else:
            break
        i += 1
    if i >= len(mots):
        return []
    nom = mots[i].rsplit("/", 1)[-1]
    reste = mots[i + 1:]
    if profondeur < 3 and nom in COQUILLES and "-c" in reste and reste.index("-c") + 1 < len(reste):
        return textes_internes(reste[reste.index("-c") + 1], profondeur + 1)
    if profondeur < 3 and nom == "ssh":
        # Les options de ssh, puis l'hôte : ce qui suit est une commande lancée là-bas.
        j = 0
        while j < len(reste) and reste[j].startswith("-"):
            j += 2 if reste[j] in ("-i", "-p", "-l", "-o", "-F", "-J") else 1
        if j + 1 < len(reste):
            return textes_internes(" ".join(reste[j + 1:]), profondeur + 1)
        return []
    tete = " ".join(affectations + [mots[i]])
    return [(" ".join([tete] + reste), len(tete))]


def textes_internes(commande, profondeur):
    try:
        segments = mots_par_segment(commande)
    except ValueError:
        return [(commande, len(commande))]
    return [t for s in segments for t in textes_a_juger(s, profondeur)]


def deploie(texte_et_borne, motifs):
    texte, borne = texte_et_borne
    return any((m := re.search(motif, texte)) and m.start() < borne for motif in motifs)


def segments_qui_deploient(commande, motifs):
    """Les textes des segments qui déploient. Une commande que shlex ne lit pas est jugée entière,
    comme avant la 0.3.0 : pour un déploiement, on ne passe pas sur ce qu'on n'a pas su lire."""
    try:
        segments = mots_par_segment(commande)
    except ValueError:
        return [commande] if any(re.search(m, commande) for m in motifs) else []
    textes = [t for s in segments for t in textes_a_juger(s)]
    return [t[0] for t in textes if deploie(t, motifs)]


def chemin_de_configuration(projet):
    """Celle du projet, sinon celle du QG : une session ouverte dans un dépôt de la stack reste sous
    les règles de son cluster (`KOA_QG`, posée par KoA dans les distros d'une seed)."""
    for racine in (projet, os.environ.get("KOA_QG")):
        if racine:
            chemin = os.path.join(racine, ".claude", "garde-fous.json")
            if os.path.isfile(chemin):
                return chemin
    return None


def decider(entree, projet):
    """Rend (décision, raison) ; décision None quand la commande n'est ni une fusion à refuser, ni un
    déploiement."""
    commande = (entree.get("tool_input") or {}).get("command") or ""
    decision, raison = juger_fusion(commande)
    if decision:
        return decision, raison
    conf, erreur = lire_configuration(projet)
    dep = (conf or {}).get("deploiement") or {}
    motifs = dep.get("commandes") or COMMANDES_PAR_DEFAUT
    segments = segments_qui_deploient(commande, motifs)
    if not segments:
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
    # Chaque segment qui déploie nomme sa cible : `… recette-a && helm upgrade x` ne prête pas la
    # cible du premier au second.
    if all(any(nomme(s, c) for c in permises) for s in segments):
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
    try:
        decision, raison = decider(entree, projet)
    except Exception as e:  # noqa: BLE001 — un garde qui plante ne doit pas laisser passer
        commande = (entree.get("tool_input") or {}).get("command") or ""
        print(f"garde-fous : erreur interne ({type(e).__name__}: {e})", file=sys.stderr)
        if not re.search(SUSPECT, commande):
            return 1
        decision, raison = "deny", (f"Garde-fous KoA : erreur interne du garde ({type(e).__name__}), "
                                    "sur une commande qui ressemble à un déploiement ou à une fusion. "
                                    "Refusée plutôt que laissée passer : signale-le à l'humain.")
    if decision is None:
        return 0
    if decision == "allow-implicite":
        # On ne dit pas « allow » : le flux normal des permissions continue, et un deny du projet
        # garde le dernier mot.
        erreur = journaliser(entree, "permis", "cible permise nommée")
        if erreur:
            print(f"garde-fous : {erreur}", file=sys.stderr)
            return 1
        return 0
    erreur = journaliser(entree, decision, raison)
    repondre(decision, raison + (f" (garde-fous : {erreur})" if erreur else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
