---
name: clore
description: "Fin de session d'un agent de cluster KoA : capitaliser, tester, committer, pousser (QG par une branche), arrêter ses conteneurs, vérifier. Autonome, proportionnée à la session. Par /koa:clore, ou quand ta mission est close. Hors cluster : /cloture."
---

# Clore la session

Une session close, c'est trois choses vraies en même temps : **rien d'appris qui soit perdu, rien d'écrit
qui reste non poussé, rien qui tourne encore dans le vide.** Tant que l'une est fausse, la session n'est
pas close — et tu le dis au lieu de conclure.

Dans un cluster, le périmètre ne s'écrit pas dans une table qui vieillirait : il se **recense** à chaque
fois, depuis le disque et la carte du QG. Sans `KOA_QG`, ce n'est pas un cluster : utilise la clôture du
projet (`/cloture`).

| Variante | Action |
|---|---|
| `/koa:clore` | le rituel complet |
| `/koa:clore check` | ce qui *serait* fait, dépôt par dépôt, sans rien écrire ni arrêter |
| `/koa:clore sans-capi` | la capitalisation est déjà faite |
| `/koa:clore sans-push` | committe et arrête, ne pousse pas |

## Ordre — non négociable

```
1. recenser → 2. capitaliser → 3. committer → 4. pousser → 5. synchroniser les données → 6. arrêter → 7. vérifier
```

Les conteneurs tombent **en dernier** : un hook de pre-commit, une suite de tests ou une synchro peut
encore avoir besoin de la base. Dans l'équipe, **l'orchestrateur clôt en dernier**, après les autres
rôles (voir « Pousser »).

## Arrêts — et seulement ceux-là

Tu enchaînes sans demander de validation. Tu t'arrêtes, exposes et attends si :

- un **secret** (`.env`, clé, jeton, dump, identifiants) est sur le point d'être committé — sa place est le
  coffre du cluster (`coffre_ecrire`, `depuis_fichier`) ;
- un fichier modifié **n'a aucun rapport** avec la session ;
- un acquis **contredit** une page existante, au QG surtout — une loi d'équipe ne se réécrit pas en clôture ;
- un **push est rejeté**, ou la forge du QG prend des PR et refuse celle que tu ouvres ;
- une **synchro de données** échoue ou signale un conflit ;
- un **conteneur** tourne sans appartenir à un compose d'un dépôt du périmètre ;
- un dépôt **reste sale** après commit, ou est en rebase, merge ou cherry-pick ;
- les **tests du dépôt échouent** sur ce que tu t'apprêtes à committer.

**La clôture se proportionne à la session.** Rien de modifié ni de non poussé, rien appris, aucun compose
qui tourne : le recensement suffit, et le rapport tient en une ligne. Le QG n'entre au périmètre que si
la capitalisation y a **écrit** : sans écriture, pas de branche `capitalisation/…`, pas de PR, rien à
fusionner pour l'orchestrateur. Une étape sans objet se dit en un mot et se saute.

## Interdits absolus

- `git push --force` / `--force-with-lease` ; fusionner **ta propre** PR ; `gh pr merge --admin` ;
- `git add -A` / `git add .` sans avoir lu ce que ça ajoute ;
- `git reset --hard`, `git checkout .`, `git clean -fd`, `git stash` silencieux ;
- `docker compose down -v`, `docker system prune`, `docker stop $(docker ps -q)` ;
- committer sur une branche que les règles du cluster réservent aux PR ;
- pousser sur `main` du QG quand tu n'es pas l'orchestrateur — même « faute de PR ».

## 1. Recenser

```bash
echo "cluster=$KOA_CLUSTER qg=$KOA_QG"
find "$HOME" -maxdepth 3 -name .git -prune 2>/dev/null | sed 's|/\.git$||' | sort
for r in $(find "$HOME" -maxdepth 3 -name .git -prune 2>/dev/null | sed 's|/\.git$||'); do
  [ -n "$(git -C "$r" status --porcelain)" ] && echo "modifié : $r"
  git -C "$r" rev-list --count @{upstream}..HEAD 2>/dev/null | grep -qv '^0$' && echo "non poussé : $r"
done
docker compose ls 2>/dev/null
docker ps --format '{{.Names}}\t{{.Label "com.docker.compose.project"}}'
grep -ril -E 'name: .*sync|description: .*(sync|synchro)' "$HOME"/*/.claude/skills/*/SKILL.md 2>/dev/null
```

Le périmètre : **les dépôts modifiés ou non poussés** — le QG compris, s'il l'est après l'étape 2. Confronte-le à la carte des dépôts du
QG (`$KOA_QG/CLAUDE.md`) : un dépôt sur le disque absent de la carte se traite **et** se signale. Ordre :
les dépôts de la stack, puis la seed, puis **le QG en dernier** — la capitalisation y écrit.

## 2. Capitaliser

`/koa:capitaliser`, en autonomie : ce qui passe ses filtres est écrit ou proposé ; une contradiction est
un arrêt. S'il n'est pas disponible, dis-le et poursuis sans ce volet.

## 3. Committer, dépôt par dépôt

1. `git status --porcelain` et `git diff` — **lis** avant de stager.
2. Du **code** a changé : lance les tests du dépôt (la commande de son `CLAUDE.md`, de son README ou de
   la carte du QG), et garde la dernière ligne de leur sortie pour le rapport. Pas de commande connue :
   dis-le, ne l'invente pas.
3. Les fichiers non suivis **un par un** : un artefact de build ou un log rejoint `.gitignore`.
4. **Un commit par sujet**, avec la convention du dépôt (`git log --oneline -20`) et les règles de
   `$KOA_QG/docs/KB/REGLES/process.md`. Décris l'effet, pas la liste des fichiers.
5. Pas de commit vide pour « marquer la fin ».

## 4. Pousser

Sur la branche courante, jamais de force. **Au QG, seul l'orchestrateur pousse sur `main`** : plusieurs
agents y écrivent en même temps, et une capitalisation que personne ne relit avant `main` y installe ses
doublons et ses contradictions. Tout autre rôle pousse une branche courte, à son nom :

```bash
b="capitalisation/<rôle>-$(date +%Y%m%d-%H%M)"
git switch -c "$b" && git push -u origin "$b"
```

La suite dépend de la forge, que la carte du QG nomme (`$KOA_QG/CLAUDE.md`) — ne la devine pas :

- **une forge à PR** (GitHub, GitLab…) : `gh pr create --fill --base main`, ou son équivalent. La PR est
  relue et fusionnée **par un autre rôle** que toi ; donne son lien.
- **pas de PR possible** (un `git daemon` local, un dépôt nu partagé) : la branche poussée **est** la
  demande de relecture. L'orchestrateur la relit et la fusionne ; donne son nom. Ce n'est pas une raison
  de pousser sur `main` : l'absence de PR ne lève pas la relecture, elle la confie à l'orchestrateur.

**L'orchestrateur clôt en dernier.** Il relit et fusionne d'abord les branches `capitalisation/…` des
autres — avant son étape 2, pas à la 4 —, puis **relit le QG fusionné** avant de capitaliser : des clôtures parallèles n'ont pas vu les
pages l'une de l'autre, et un même fait peut y être arrivé deux fois — il le ramène à un seul endroit. Il
pousse ensuite sur `main` ; sur une forge à PR qui protège `main`, il passe lui aussi par une PR. Une
branche qu'il fusionne a été relue par lui, pas par son auteur : c'est ce qui la distingue de
« fusionner ta propre PR ».

Un push rejeté : rapporte l'écart (`git rev-list --left-right --count @{upstream}...HEAD`), ne rebase
pas d'office.

## 5. Synchroniser les données

Chaque skill de sync data trouvée, **avant** l'arrêt des conteneurs. Aucune : dis-le, c'est un no-op.
`sans-push` la saute aussi : elle pousse vers un remote.

## 6. Arrêter les conteneurs

`docker compose ls` vide au recensement : l'étape se saute. Sinon, seulement ceux des composes du
périmètre, depuis leur dossier : `docker compose -f <fichier> down`, sans `-v`. Ce qui n'est pas
identifié reste en vie et part dans le rapport.

## 7. Vérifier, puis rendre compte

```bash
for r in <dépôts du périmètre> "$KOA_QG"; do
  printf '%-28s ' "${r#$HOME/}"
  [ -z "$(git -C "$r" status --porcelain)" ] && printf 'propre  ' || printf 'SALE    '
  git -C "$r" rev-list --left-right --count @{upstream}...HEAD 2>/dev/null \
    | awk '{print ($1==0 && $2==0) ? "à jour" : "retard/avance : "$1"/"$2}'
done
docker ps --format '{{.Names}}\t{{.Label "com.docker.compose.project"}}'
```

```
## Clôture — <rôle>, cluster <cluster>
Capitalisation : 1 page au dépôt, 1 consigne au QG, 1 issue rédigée à ouvrir (<lien prérempli>) — ou « rien ».
Tests : <dépôt> « <dernière ligne de la sortie> », par dépôt dont le code a changé.
| Dépôt | Commits | Push | État final |
QG : PR <lien>, à relire par un autre rôle — ou branche capitalisation/<rôle>-…, à fusionner par l'orchestrateur.
Conteneurs : …
Non refermé : … (ou « rien »)
```

**« La session est close »** est une affirmation vérifiée, pas une formule de politesse.
