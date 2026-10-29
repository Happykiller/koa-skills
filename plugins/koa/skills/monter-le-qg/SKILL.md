---
name: monter-le-qg
description: "Monter, compléter ou vérifier le QG d'un cluster KoA : carte des dépôts, environnements, KB, plugins épinglés, garde-fou. Idempotent. Quand : un cluster démarre, ou on ouvre son dépôt QG."
---

# Monter le QG d'un cluster

Le **QG** est le dépôt qui porte le contexte d'un **cluster** (niveau N3 du framework agentique KoA,
`library://koa/architecture`, chapitre « Le QG d'un cluster ») : ce qui vaut pour tous ses dépôts et
qu'aucun d'eux ne porte seul. Les agents de l'instance d'équipe y démarrent et y lisent la carte.

Cette skill est **idempotente**. Premier passage : elle crée. Passages suivants : elle compare, complète
ce qui manque, et **montre** chaque écart avant de le corriger. Elle n'écrase jamais un contenu écrit
par un humain sans le dire.

## Les règles qu'elle tient

- **Générique.** Aucun nom de client ni de projet qui n'appartienne pas à ce cluster. Le QG d'un
  cluster ne cite jamais un autre cluster.
- **Aucune valeur de secret**, nulle part : les secrets se nomment (`${NOM}` dans `.mcp.json`), leurs
  valeurs vivent hors du dépôt.
- **`CLAUDE.md` court** : la carte et les interdits, le reste en lien. Un fichier de contexte trop riche
  fait baisser la réussite et monter le coût.
- **Une information, un endroit.** Les cibles de déploiement font foi dans `.claude/garde-fous.json` ;
  `CLAUDE.md` y renvoie au lieu de les recopier.

## 1. État des lieux

Dans le dossier courant :

1. Vérifie que c'est un dépôt git. Sinon, demande s'il faut l'initialiser ; ne le fais pas sans réponse.
2. Lis ce qui existe : `CLAUDE.md`, `docs/KB/`, `.claude/settings.json`, `.claude/garde-fous.json`,
   `.mcp.json`, `.claude/skills/`.
3. Dresse la liste : **présent et conforme**, **présent à compléter**, **absent**.

## 2. Ce qu'il faut demander — une seule fois, groupé

Ce que le dépôt ne dit pas encore, et seulement cela :

- l'**identifiant** du cluster (court, minuscules : `cluster-a`) ;
- ses **dépôts** : nom, rôle en une ligne, adresse ;
- ses **environnements** : nom, usage, et pour chacun si un agent peut y déployer (`permis`) ou si c'est
  un geste humain (`interdit` — la production l'est par défaut) ;
- les **rôles** de l'équipe qui y travaillent, pour savoir quels plugins activer ;
- les **serveurs MCP** du cluster, et le **nom** des variables qui portent leurs secrets.

Ne devine jamais un environnement ni un secret. Une réponse absente laisse une ligne `À renseigner`.

## 3. Écrire, ou compléter

Les modèles sont dans `${CLAUDE_SKILL_DIR}/modeles/`. Pour chaque fichier : s'il est absent, écris-le
depuis son modèle ; s'il existe, **fusionne** — ajoute ce qui manque, garde ce qui y est, et signale ce
qui contredit le framework sans le réécrire.

| Fichier | Modèle | Fusion |
|---|---|---|
| `CLAUDE.md` | `CLAUDE.modele.md` | sections manquantes ajoutées ; le texte existant reste |
| `docs/KB/README.md` | `KB-README.md` | index complété |
| `docs/KB/glossaire.md` | `glossaire.md` | créé s'il manque ; un glossaire existant reste |
| `docs/KB/decisions/` | — | dossier créé vide s'il manque (une décision = un fichier daté) |
| `.claude/settings.json` | `settings.json` | clés `extraKnownMarketplaces.koa-skills` et `enabledPlugins` ajoutées ; `permissions` existantes gardées |
| `.claude/garde-fous.json` | `garde-fous.json` | cibles tirées des environnements déclarés |
| `.mcp.json` | — | seulement si des serveurs ont été déclarés ; secrets en `${NOM}` |

Dans `.claude/settings.json`, active les plugins des rôles déclarés (`equipe-devops@koa-skills` pour le
DevOps, `equipe-tech@koa-skills` pour qui code ou relit, …) et **toujours** `garde-fous@koa-skills`. Épingle la marketplace sur un tag (`"ref": "v…"`),
jamais sur une branche : un cluster ne suit pas `main` à son insu.

**Claude Code protège le dossier `.claude/`** : y écrire demande l'accord de l'humain, même quand
les autres écritures passent sans question. C'est voulu — ces fichiers décident de ce que les agents
ont le droit de faire. Demande-le ; s'il est refusé ou que personne ne peut répondre, donne le contenu
exact de chaque fichier dans le compte rendu, pour qu'il le pose lui-même.

Les skills qui nomment un environnement du cluster (déployer, restaurer, migrer) vont dans
`.claude/skills/` de ce QG. N'en crée aucune d'office : propose-les quand un geste revient.

## 4. Contrôler

- Les JSON se relisent sans erreur (`python3 -m json.tool` sur chacun).
- Aucune valeur qui ressemble à un secret (jeton, clé, mot de passe) dans les fichiers écrits.
- `CLAUDE.md` tient sous 80 lignes.
- Chaque environnement `interdit` est dans `cibles_interdites`, chaque `permis` dans `cibles_permises`.
- Un second passage, maintenant, ne changerait rien. Si si, c'est que le premier n'a pas fini.

## 5. Rendre compte

En quelques lignes : ce qui a été **créé**, **complété**, laissé **tel quel**, et ce qui reste
**à renseigner**. Puis ce que l'humain doit faire lui-même :

- installer les plugins une fois pour ce dépôt :
  `claude plugin marketplace add https://github.com/Happykiller/koa-skills.git#v0.7.2` puis
  `claude plugin install <plugin>@koa-skills --scope project` pour chacun ;
- relire et committer.

Ne committe pas et ne pousse pas toi-même.
