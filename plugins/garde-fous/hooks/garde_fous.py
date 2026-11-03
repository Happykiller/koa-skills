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
cluster, et `.claude/garde-fous.json` n'en choisit que les branches protégées. Elle est jugée avant le
déploiement. Un
`gh pr merge` est refusé :
- s'il porte `--admin`, qui passe outre les protections et la CI requise ;
- s'il ne porte pas `--match-head-commit` suivi d'un SHA complet (40 caractères hexadécimaux) : on
  fusionne la tête que la revue a acceptée, pas celle qu'on trouve en arrivant ;
- dans une distro née de KoA (`/etc/koa-seed` existe) dont le témoin `~/.local/state/koa/droits` ne
  porte pas la ligne `fusionner` : seul l'orchestrateur fusionne, et KoA ne pose ce témoin qu'à lui ;
- quand la commande est illisible (guillemets non fermés) et parle de `gh`, `pr` et `merge` : pour une
  fusion, on refuse ce qu'on n'a pas su lire.

Sans le même témoin, deux autres chemins vers une branche protégée sont refusés (0.4.0) — ils
fusionnaient sans rien demander à qui partage l'identité GitHub de l'équipe :
- `gh api` qui **écrit** une fusion : `repos/…/pulls/…/merge`, `…/merges`, `…/git/refs/heads/…`,
  `…/branches/…/protection…`, ou `graphql` avec `mergePullRequest`, `enablePullRequestAutoMerge`,
  `updateRef`. Écrire, c'est une méthode autre que GET, ou un champ (`-f`, `-F`, `--input`) sans
  méthode : gh passe alors de lui-même en POST ;
- `git push` dont une destination est une branche protégée — `fusion.branches_protegees` du QG, par
  défaut `develop`, `master`, `main` —, résolue comme git le fait : `src:dst`, `+dst`,
  `refs/heads/dst`, un nom seul ; sans destination ou avec `HEAD`, la branche courante et sa
  destination de poussée. `--all`, `--mirror` et `push.default=matching` pousseraient les protégées
  avec le reste ; `--delete` d'une protégée aussi. Un `cd` d'un segment précédent est suivi.
L'orchestrateur, qui a le témoin, n'est pas visé : il pousse son registre de chantier sur la branche
principale du QG (`equipe/table`, « Le chantier »).

La commande est lue segment par segment (`&&`, `||`, `;`, `|`, `&`, retours à la ligne) : une option
écrite dans un `echo` voisin ne compte pas pour la fusion.

Les limites, dites plutôt que tues : un alias de `gh` ou de `git`, un script ou un interpréteur
(`node`, `python`) qui les appelle, `curl` vers l'API, un `--input` de graphql qu'on ne lit pas. Ce
garde tient contre la dérive, pas contre la malveillance : l'agent a `sudo` dans sa distro, et son
témoin est dans son foyer. La vraie cloison est une identité GitHub propre à l'orchestrateur, seule à
pouvoir contourner le ruleset de ses branches.
"""
import datetime
import json
import os
import re
import shlex
import subprocess
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
           r"|heroku|ansible|\bgh\b|\bpush\b")

BRANCHES_PROTEGEES = ["develop", "master", "main"]

# Ce que `gh api` écrit quand il vise une fusion. Le chemin se lit sans son `/` de tête ni sa requête ;
# `{owner}/{repo}`, que gh remplace lui-même, passe pour un segment comme un autre.
API_FUSION = re.compile(r"repos/[^/]+/[^/]+/(pulls/[^/]+/merge|merges|git/refs/heads/.+|branches/[^/]+/protection.*)")
GRAPHQL_FUSION = re.compile(r"mergePullRequest|enablePullRequestAutoMerge|updateRef")
API_OPTIONS_A_VALEUR = {"-X", "--method", "-H", "--header", "-f", "--raw-field", "-F", "--field", "--input",
                        "-q", "--jq", "-t", "--template", "--hostname", "--cache", "-p", "--preview"}
API_CHAMPS = {"-f", "--raw-field", "-F", "--field", "--input"}

# Les options de git avant la sous-commande, et celles de `git push`, qui prennent une valeur séparée.
GIT_OPTIONS_A_VALEUR = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env"}
PUSH_OPTIONS_A_VALEUR = {"--repo", "-o", "--push-option", "--receive-pack", "--exec"}
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


def branches_protegees(projet):
    """Celles du QG (`fusion.branches_protegees`), qui remplacent la liste par défaut. Une configuration
    illisible ne lève pas la protection : elle rend la liste par défaut."""
    chemin = chemin_de_configuration(projet) if projet else None
    if chemin:
        try:
            with open(chemin, encoding="utf-8") as f:
                liste = ((json.load(f).get("fusion") or {}).get("branches_protegees"))
            if isinstance(liste, list) and liste and all(isinstance(b, str) and b for b in liste):
                return liste
        except (OSError, ValueError, AttributeError):
            pass
    return BRANCHES_PROTEGEES


def sous_commande(mots, outil, options_a_valeur):
    """L'indice du mot qui suit la sous-commande de `outil` dans ce segment, et cette sous-commande,
    ou (None, None). Les options de l'outil et leur valeur sont sautées ; le dossier de `-C` est rendu."""
    for i, mot in enumerate(mots):
        if mot.rsplit("/", 1)[-1] != outil:
            continue
        j, dossier = i + 1, None
        while j < len(mots) and mots[j].startswith("-"):
            if mots[j] in options_a_valeur:
                if mots[j] == "-C" and j + 1 < len(mots):
                    dossier = mots[j + 1]
                j += 1
            j += 1
        if j < len(mots):
            return j + 1, mots[j], dossier
    return None, None, None


def api_qui_fusionne(mots):
    """Vrai quand ce segment est un `gh api` qui écrit une fusion."""
    suite, nom, _ = sous_commande(mots, "gh", {"-R", "--repo"})
    if nom != "api":
        return False
    methode, champs, chemin, valeurs = None, False, None, []
    i = suite
    while i < len(mots):
        mot = mots[i]
        option, egal, attachee = mot.partition("=")
        if mot.startswith("-X") and len(mot) > 2:
            methode = mot[2:]
        elif option in API_OPTIONS_A_VALEUR:
            valeur = attachee if egal else (mots[i + 1] if i + 1 < len(mots) else "")
            i += 0 if egal else 1
            if option in ("-X", "--method"):
                methode = valeur
            elif option in API_CHAMPS:
                champs = True
                valeurs.append(valeur)
        elif not mot.startswith("-") and chemin is None:
            chemin = mot
        i += 1
    if chemin is None:
        return False
    chemin = chemin.lstrip("/").split("?", 1)[0]
    if chemin == "graphql":
        return any(GRAPHQL_FUSION.search(v) for v in valeurs)
    ecrit = (methode or ("POST" if champs else "GET")).upper() != "GET"
    return ecrit and API_FUSION.fullmatch(chemin) is not None


def git_lit(dossier, *args):
    """Une ligne que git rend, ou None : un dépôt absent ou une tête détachée ne disent rien."""
    try:
        r = subprocess.run(["git", "-C", dossier, *args], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() or None if r.returncode == 0 else None


def poussee_protegee(mots, dossier, protegees):
    """La raison du refus quand ce segment est un `git push` qui atteint une branche protégée, ou None."""
    suite, nom, dossier_c = sous_commande(mots, "git", GIT_OPTIONS_A_VALEUR)
    if nom != "push":
        return None
    if dossier_c:
        dossier = os.path.join(dossier, os.path.expanduser(dossier_c))
    positionnels, supprime, i = [], False, suite
    while i < len(mots):
        mot = mots[i]
        if mot in ("--all", "--mirror", "--branches"):
            return f"{mot} pousserait aussi les branches protégées"
        if mot == "--delete" or (re.fullmatch(r"-[a-zA-Z]+", mot) and "d" in mot):
            supprime = True
        elif mot in PUSH_OPTIONS_A_VALEUR:
            i += 1
        elif not mot.startswith("-"):
            positionnels.append(mot)
        i += 1

    if "--tags" in mots[suite:] and len(positionnels) < 2:
        return None  # des étiquettes, aucune branche
    destinations = []
    for spec in positionnels[1:]:
        spec = spec.lstrip("+")
        source, deux_points, dst = spec.partition(":")
        destinations.append(dst if deux_points else source)
        supprime = supprime or (deux_points and not source)  # `:dst` supprime dst
    if not destinations or "HEAD" in destinations:
        # Sans destination, git suit `push.default` : `matching` pousse toutes les branches qui
        # existent des deux côtés, les protégées comprises.
        if not supprime and not destinations and git_lit(dossier, "config", "push.default") == "matching":
            return "push.default=matching pousserait aussi les branches protégées"
        destinations = [d for d in destinations if d != "HEAD"]
        courante = git_lit(dossier, "symbolic-ref", "--short", "HEAD")
        if courante:
            destinations.append(courante)
        poussee = git_lit(dossier, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{push}")
        if poussee and "/" in poussee:
            destinations.append(poussee.split("/", 1)[1])
    for dst in destinations:
        nom_branche = dst[len("refs/heads/"):] if dst.startswith("refs/heads/") else dst
        if nom_branche in protegees:
            return (f"« {nom_branche} » est une branche protégée" + (" : on ne la supprime pas" if supprime else ""))
    return None


def dossiers_par_segment(segments, depart):
    """Le dossier où chaque segment s'exécute : un `cd` change celui des segments qui le suivent."""
    dossier, dossiers = depart, []
    for mots in segments:
        dossiers.append(dossier)
        if mots and mots[0] == "cd" and len(mots) > 1:
            dossier = os.path.join(dossier, os.path.expanduser(mots[1]))
    return dossiers


SEUL_L_ORCHESTRATEUR = ("Garde-fous KoA : seul l'orchestrateur fusionne (equipe/table, « Fusionner »). "
                        "Livre ta tête, et adresse ton RÉSULTAT à l'orchestrateur.")


def juger_branches_protegees(segments, dossier, projet):
    """Les chemins de `gh api` et de `git push` vers une branche protégée, pour qui n'a pas le témoin."""
    if any(api_qui_fusionne(s) for s in segments):
        return "deny", ("Garde-fous KoA : seul l'orchestrateur fusionne, par l'API comme par gh pr merge "
                        "(equipe/table, « Fusionner »). Livre ta tête, et adresse ton RÉSULTAT à "
                        "l'orchestrateur.")
    protegees = branches_protegees(projet)
    for mots, ici in zip(segments, dossiers_par_segment(segments, dossier)):
        motif = poussee_protegee(mots, ici, protegees)
        if motif:
            return "deny", (f"Garde-fous KoA : {motif}. On n'y pousse pas, on y fusionne, et seul "
                            "l'orchestrateur fusionne (equipe/table, « Fusionner ») : pousse la branche "
                            "de ta mission, et adresse ton RÉSULTAT à l'orchestrateur.")
    return None, None


def juger_fusion(commande, dossier=None, projet=None):
    """Rend (décision, raison) ; décision None quand la commande ne fusionne pas, ou fusionne bien."""
    try:
        segments = mots_par_segment(commande)
    except ValueError:
        if all(re.search(r"\b" + m + r"\b", commande) for m in ("gh", "pr", "merge")):
            return "deny", ("Garde-fous KoA : cette commande parle de fusion (gh, pr, merge) et ne se "
                            "lit pas (guillemets non fermés ?). Pour une fusion, on refuse ce qu'on n'a "
                            "pas su lire : récris-la sur une ligne lisible.")
        # La même règle pour les deux autres chemins, mais seulement pour qui n'a pas le droit : chez
        # l'orchestrateur, une poussée illisible n'atteint rien qu'il n'ait le droit d'atteindre.
        if ((all(re.search(m, commande) for m in (r"\bgh\b", r"\bapi\b", r"[Mm]erge"))
             or all(re.search(m, commande) for m in (r"\bgit\b", r"\bpush\b")))
                and not droit_de_fusionner()):
            return "deny", ("Garde-fous KoA : cette commande parle de poussée ou de fusion et ne se lit "
                            "pas (guillemets non fermés ?). On refuse ce qu'on n'a pas su lire : "
                            "récris-la sur une ligne lisible.")
        return None, None

    fusions = [suite for suite in map(fusion_dans, segments) if suite is not None]
    if not fusions:
        if droit_de_fusionner():
            return None, None
        return juger_branches_protegees(segments, dossier or os.getcwd(), projet)
    if not droit_de_fusionner():
        return "deny", SEUL_L_ORCHESTRATEUR
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
    decision, raison = juger_fusion(commande, entree.get("cwd") or projet, projet)
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
