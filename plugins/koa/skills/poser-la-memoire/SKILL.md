---
name: poser-la-memoire
description: "Poser ou remettre d'aplomb la mémoire d'un projet (KB, CLAUDE.md, /capitalize, /cloture), seul ou dans un cluster. Idempotent. Quand : un projet sans KB, ou dont la mémoire a dérivé."
---

# Poser la mémoire d'un projet

La **mémoire** d'un projet, c'est ce que Claude doit *savoir* (`docs/KB/`, lue par `CLAUDE.md`) et ce
qui l'entretient : capitaliser en fin de session, puis clore. Le pourquoi — ce qu'on y met, ce qu'on n'y
met pas, et pourquoi elle se répartit autrement dans un cluster — est le livre `library://koa/ghost`.
Ici, le geste.

**Idempotente.** Premier passage : elle crée. Passages suivants : elle compare, complète ce qui manque,
et **montre** chaque écart avant de le corriger.

## Les règles qu'elle tient

- **Index d'abord.** Tout dossier de la KB a un `README.md` qui indexe ses pages ; le contenu vit dans
  des pages courtes. Au-delà de ~200 lignes ou ~15 Ko, une page devient un dossier et son index.
- **Jamais d'écrasement silencieux.** Une page existante s'enrichit. Ce qui contredit ce que tu observes
  se **signale** et se propose ; tu ne tranches pas seul.
- **Pas d'invention.** La KB ne dit que ce qui se vérifie dans le dépôt ou que l'humain confirme. Le reste
  est écrit `À COMPLÉTER` : une KB qui ment est pire que pas de KB.
- **Pas de recopie du code** : la KB porte le pourquoi, les invariants, les décisions ; elle renvoie au
  code pour le comment.
- **Une information, un endroit.** Dans un cluster, ce qui vaut pour l'équipe vit au QG **seulement** ;
  un dépôt y renvoie, il ne le recopie pas.
- **Dans la langue du projet**, et sans nom de client ni de projet qui ne lui appartienne pas.

## 0. Le mode — avant toute écriture

```bash
printenv KOA_CLUSTER KOA_QG
git rev-parse --show-toplevel
ls koa.profil .claude/garde-fous.json
```

Trois commandes séparées, sans `$` : une session sans humain refuse souvent une commande qui développe une
variable, et un mode deviné faute de l'avoir lu pose la mauvaise mémoire. **Si l'une est refusée, arrête-toi
et dis-le** au lieu de supposer le mode autonome.

| Ce qu'on voit | Mode |
|---|---|
| `KOA_QG` vide, ou son dossier absent | **autonome** — sauf si l'humain dit que le projet est dans un cluster : demande-lui alors le chemin du QG |
| `KOA_QG` posé, et la racine du dépôt **est** `$KOA_QG` | **cluster — le QG** |
| `KOA_QG` posé, et un `koa.profil` à la racine | **cluster — la seed d'un agent** |
| `KOA_QG` posé, autre dépôt | **cluster — un dépôt de la stack** |

KoA pose `KOA_CLUSTER` et `KOA_QG` dans la distro d'un agent de seed qui déclare son QG. Hors de KoA, un
dépôt qui porte `.claude/garde-fous.json` est probablement un QG : demande avant de le traiter comme tel.

Annonce le mode en tête de réponse, puis l'état des lieux :
`Mode : cluster « cluster-a », dépôt de la stack ; QG : ~/cluster-a. KB : absente → création.
CLAUDE.md : présent, sans renvoi au QG → à brancher.`

## 1. État des lieux

1. `docs/KB/` existe-t-il, avec quels dossiers ? Son `README.md` indexe-t-il ce qui est sur le disque
   (aucun lien mort, aucune page orpheline) ? Des pages dépassent-elles le seuil ?
2. `CLAUDE.md` renvoie-t-il à la KB — et, en cluster, au QG ?
3. `.claude/skills/capitalize/` et `.claude/skills/cloture/` existent-ils ? En autonome, compare-les aux
   modèles ; en cluster, ils sont **remplacés** par `koa:capitaliser` et `koa:clore` (étape 2).
4. Que contient `.claude/` (skills, agents, hooks, `.mcp.json`, réglages) ?
5. En autonome, le **périmètre** de la clôture : les dépôts (`find . -name .git -maxdepth 3 -prune`, et
   les dépôts frères que le projet suppose), les stacks compose, les skills de synchronisation de données
   (nom ou description qui contient « sync » / « synchro »).

## 2. Ce que chaque mode pose

Les modèles sont dans `${CLAUDE_SKILL_DIR}/modeles/`. S'ils ne se lisent pas, arrête-toi et dis-le : ne les
réécris pas de mémoire. Une page de KB porte un en-tête :

```yaml
---
titre: Authentification — flux et invariants
type: daf            # dat | daf | regle
statut: actif        # actif | a-completer | obsolete
maj: AAAA-MM-JJ
---
```

Les index de dossier sont des tableaux `| Page | Ce qu'elle couvre | Statut | MAJ |`.

### Autonome — le projet porte toute sa mémoire

```
docs/KB/
├── README.md     l'aiguillage : trois lignes, puis les cinq entrées ci-dessous
├── DAT/          architecture technique — stack.md, arborescence.md, environnements.md, un composant par page
├── DAF/          architecture fonctionnelle — un domaine par page ; ce qu'on ne sait pas : À COMPLÉTER, et demande
├── REGLES/       process.md, workflows.md, consignes.md, normes.md, lois.md
├── MOTEUR.md     la cartographie de .claude/ : skills, sous-agents, hooks, MCP — et quand s'en servir
└── HISTORY.md    | Date | Sujet | Ce qui en est sorti | Traces | — une ligne par session utile
```

- **Amorce** depuis le dépôt réel : les fichiers de dépendances, la configuration de lint, `CLAUDE.md`,
  `CONTRIBUTING.md`, l'historique git. Ce qui existe ailleurs est **référencé**, pas recopié.
- **`MOTEUR.md`** constate, n'invente pas : aucun skill, agent ou hook créé à cette étape. La colonne
  « quand l'utiliser » est son vrai contenu.
- **`CLAUDE.md`** : fusionne la section de `CLAUDE-KB.autonome.md`, sans toucher au reste.
- **`/capitalize`** : `.claude/skills/capitalize/SKILL.md` depuis `capitalize.md`, **tel quel**.
- **`/cloture`** : `.claude/skills/cloture/SKILL.md` depuis `cloture.md`, en n'adaptant **que** la section
  « Périmètre de ce projet » (étape 1, point 5) ; le reste est du contenu de référence.

### Cluster — le QG porte ce qui est d'équipe

Le QG se monte d'abord par `koa:monter-le-qg` (réglages, plugins épinglés, garde-fou, glossaire, décisions) ;
s'il manque, dis-le et propose-la. Cette skill y ajoute la mémoire d'équipe :

```
docs/KB/
├── README.md     l'index du cluster (celui de monter-le-qg, complété)
├── REGLES/       lois.md, consignes.md, process.md, workflows.md, normes.md — la SEULE copie de l'équipe
├── DAF/          la carte des parcours, ce qui traverse plusieurs dépôts (le glossaire reste glossaire.md)
├── DAT/          les liens entre dépôts, les environnements partagés
├── equipe/       une page par rôle : ce que ce rôle a appris de sa façon de travailler dans ce cluster
├── decisions/    une décision par fichier, datée (monter-le-qg)
├── propositions/ les évolutions proposées aux livres de KoA et aux skills de koa-skills, en issues à ouvrir
├── MOTEUR.md     les skills du QG, les plugins épinglés, et quand s'en servir
└── HISTORY.md    les missions d'équipe
```

- **`CLAUDE.md`** : fusionne `CLAUDE-KB.qg.md`. Il reste court : la carte, les interdits, les liens.
- **Ni `/capitalize` ni `/cloture`** : le plugin `koa` les porte, en version cluster (`koa:capitaliser`,
  `koa:clore`). Une copie dans un dépôt vieillirait seule.

### Cluster — un dépôt de la stack porte son code

```
docs/KB/
├── README.md     l'index du dépôt, et une ligne qui renvoie aux règles de l'équipe, au QG
├── DAT/          stack.md, arborescence.md, environnements.md (de ce dépôt), un composant par page
├── DAF/          seulement ce qui n'existe que dans ce service
├── MOTEUR.md     le .claude/ de ce dépôt
└── HISTORY.md    les sujets propres à ce code
```

- **Pas de `REGLES/`.** Les lois et consignes sont celles du cluster. Si le dépôt en porte déjà, **ne
  supprime rien** : dresse la liste de ce qui est d'équipe (à verser au QG) et de ce qui est propre à ce
  code (à garder en `DAT/` ou `DAF/`), et propose-la.
- **`CLAUDE.md`** : fusionne `CLAUDE-KB.stack.md`, où le renvoi au QG nomme son dépôt (`git -C "$KOA_QG"
  remote get-url origin`) — un humain qui lit le dépôt sans le QG sur son disque sait où le trouver.
- **Ni `/capitalize` ni `/cloture`** copiés : `koa:capitaliser` et `koa:clore`.

### Cluster — la seed d'un agent ne porte aucune mémoire

La seed décrit un agent ; ce qu'il apprend appartient à l'équipe (QG) ou au code (dépôt de la stack).

- **Pas de `docs/KB/`.** S'il en existe une, **ne supprime rien** : propose la même répartition que
  ci-dessus, page par page.
- **`CLAUDE.md`** court, depuis `CLAUDE.seed.md` : le rôle, et l'**import** du `CLAUDE.md` du QG —
  `@~/<nom du QG>/CLAUDE.md`, le dossier que porte `$KOA_QG`. Un import est chargé à coup sûr ; une
  consigne « lis le QG » ne l'est que si l'agent la suit. Fusionne si le fichier existe : ajoute l'import
  en tête, garde le reste, et signale ce qui recopie une loi du QG.
- **`.claude/skills/capitalize` et `cloture`** d'un ancien passage : signale qu'ils sont remplacés par
  `koa:capitaliser` et `koa:clore`, et propose de les retirer. Ne les retire pas sans réponse.

**Claude Code protège `.claude/`** : y écrire demande l'accord de l'humain. Demande-le ; s'il est refusé
ou que personne ne peut répondre, donne le contenu exact de chaque fichier dans le compte rendu.

## 3. Contrôler

```bash
# Tout ce qui est sur le disque est indexé, et chaque lien relatif résout
find docs/KB -name '*.md' 2>/dev/null | while read -r f; do d=$(dirname "$f"); \
  grep -oP '\]\(\K[^)#:]+(?=\))' "$f" | while read -r l; do \
  case "$l" in http*) continue;; esac; [ -e "$d/$l" ] || echo "CASSÉ: $f -> $l"; done; done
# Aucune page au-dessus du seuil
find docs/KB -name '*.md' -size +15k 2>/dev/null
```

- **Autonome** : les deux skills sont là (`head -4 .claude/skills/{capitalize,cloture}/SKILL.md`), et le
  périmètre de `/cloture` correspond au disque — relis-le à l'œil, c'est le seul défaut qui ne se voit
  jamais à l'exécution.
- **Cluster** : une seule copie des règles, au QG (`find ~ -maxdepth 4 -path '*docs/KB/REGLES' -type d`
  ne rend que le QG — ou dis lesquelles restent à verser) ; la seed ne porte pas de KB ; son `CLAUDE.md`
  importe celui du QG.
- Un second passage, maintenant, ne changerait rien.

Une skill ajoutée n'est vue qu'à la session suivante : dis-le.

## 4. Rendre compte

Court et factuel : le **mode** ; les pages créées, enrichies, laissées telles quelles, et combien sont
`À COMPLÉTER` ; `CLAUDE.md` créé, fusionné ou déjà branché ; en autonome, `/capitalize` et `/cloture`
(et le périmètre inscrit) ; en cluster, ce qui reste **à verser au QG**, page par page. Puis **les
questions ouvertes** : les `À COMPLÉTER` que seul l'humain peut lever.

Ne committe pas et ne pousse pas toi-même : c'est le rôle de la clôture.
