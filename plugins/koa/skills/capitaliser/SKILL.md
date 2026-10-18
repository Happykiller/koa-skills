---
name: capitaliser
description: "Capitaliser une session dans un cluster du framework agentique KoA : relire ce qui s'est passé, et ranger chaque acquis au bon étage — le dépôt de la stack, le QG du cluster, ou une proposition d'évolution d'un livre de KoA ou d'une skill de la marketplace, rédigée en issue que l'humain ouvre. Écrit jusqu'au QG, propose au-dessus, toujours sans nom de client ni de projet. Propose avant d'écrire. À déclencher en fin de session d'un agent d'équipe, ou par /koa:clore."
---

# Capitaliser au bon étage

Une session qui s'achève sans capitalisation, c'est un apprentissage perdu qu'on repaiera. Dans un cluster,
c'en est un aussi quand l'acquis finit **au mauvais endroit** : une décision d'équipe enfermée dans le
dépôt d'un rôle, une méthode générale dans un seul projet. Le pourquoi : `library://koa/ghost`.

Le cluster et son QG : `$KOA_CLUSTER`, `$KOA_QG`. Sans `KOA_QG`, ce n'est pas un cluster : utilise la
capitalisation du projet (`/capitalize`), ou `koa:poser-la-memoire` s'il n'en a pas.

## 1. Relire la session

Liste, sans filtrer encore :

- ce qui a été **découvert** (un comportement, une contrainte, une dépendance cachée) ;
- ce qui a été **décidé**, et **pourquoi** — l'alternative écartée compte autant ;
- ce que l'humain ou un autre agent a **corrigé** chez toi : le signal le plus fort, une correction non
  capitalisée se reproduira ;
- les gestes **répétés** ou laborieux.

## 2. Filtrer

Ne garde que ce qui est **durable** (vrai dans trois mois), **non déductible** (pas déjà dans le code, un
README ou l'historique git) et **réutilisable**. Le reste est **écarté**, et dit comme tel.

## 3. Ranger — le tamis, dans cet ordre

La première réponse oui décide. **Une chose monte aussi haut que sa généralité prouvée, jamais plus haut.**

| Question | Étage | Geste |
|---|---|---|
| Vrai seulement pour **ce code** ? | N4 — le dépôt de la stack | **écrit** dans sa `docs/KB/` (`DAT/`, `DAF/`, `HISTORY.md`) |
| Vrai pour **tout le cluster** — un environnement, une décision, un terme métier, une règle d'équipe ? | N3 — le QG | **écrit** dans `$KOA_QG/docs/KB/` |
| Un **geste** refait trois fois, ou qui le sera — ou une skill de `koa-skills` à corriger ? | N2 — la marketplace | **proposé** : une issue rédigée pour `Happykiller/koa-skills` |
| Vrai pour **tout agent de ce rôle**, quel que soit le projet ? | N1 — la librairie | **proposé** : une issue rédigée pour `Happykiller/koa-releases` quand le livre est de KoA (`koa/…`, `equipe/…`) ; `library_ecrire` pour un livre de l'opérateur |

Au QG, la destination dépend de la nature :

| Nature | Destination |
|---|---|
| Invariant non négociable de l'équipe | `REGLES/lois.md` |
| Correction ou préférence de l'humain envers l'équipe | `REGLES/consignes.md` |
| Process, workflow, norme | `REGLES/process.md`, `workflows.md`, `normes.md` |
| Décision transverse | `decisions/AAAA-MM-JJ-sujet.md` |
| Terme métier | `glossaire.md` |
| Ce que **ton rôle** a appris de sa façon de travailler ici | `equipe/<rôle>.md` |
| La mission elle-même | une ligne de `HISTORY.md` |

**Ce qui monte en N1 passe trois gardes** — sinon, il reste au QG :

- **anonymisé** : aucun nom de client, de projet, de dépôt ni de cluster. La librairie sert tous les
  clusters, et ses livres livrés sont publics ;
- **prouvé** : une mesure, un incident, un avant/après — pas une impression ;
- **vu deux fois** : une fois, c'est une anecdote du projet.

**Les livres de KoA et les skills de la marketplace sont verrouillés** : ils évoluent dans leur dépôt, pour
tous les clusters, pas dans le tien — `library_ecrire` les refuse. Une proposition à leur sujet est une
**issue rédigée**, que l'humain relit et ouvre ; tu ne l'ouvres jamais toi-même : elle est publique.

1. Lis d'abord ce que tu veux faire évoluer (`library_lire` pour un chapitre, le `SKILL.md` pour une skill).
2. Écris la proposition au QG, `docs/KB/propositions/AAAA-MM-JJ-sujet.md` (index dans le `README.md` du
   dossier), avec : la **cible** (`equipe/tech`, chapitre « … », v… ; ou `equipe-devops:…`), le **constat**,
   la **preuve**, les **deux occurrences**, le **changement proposé** — un texte qu'on peut reprendre tel
   quel —, et une ligne `statut: à ouvrir`.
3. Donne dans le compte rendu le **lien prérempli** qui l'ouvre, titre et corps encodés :

```bash
python3 -c 'import sys, urllib.parse as u; print(f"https://github.com/{sys.argv[1]}/issues/new?" + u.urlencode({"title": sys.argv[2], "body": open(sys.argv[3]).read()}))'   Happykiller/koa-releases "Librairie — equipe/tech : …" docs/KB/propositions/AAAA-MM-JJ-sujet.md
```

Pour un livre **de l'opérateur** (une armoire à lui), lis le chapitre puis propose-le **entier réécrit** par
`library_ecrire` : il l'accepte ou le refuse dans la Librairie de KoA.

## 4. Écrire comme au QG

- **Enrichir avant de créer** : cherche d'abord la page qui couvre le sujet.
- **Index d'abord** : toute page nouvelle rejoint le `README.md` de son dossier dans le même geste.
- Le **pourquoi**, jamais le seul quoi ; le champ `maj:` des pages touchées ; une ligne d'`HISTORY.md`.
- Ce qui **contredit** une page existante — surtout une loi — est un arrêt : propose, ne tranche pas.

## 5. Proposer, puis écrire

**N'écris rien avant validation**, sauf appelé par `/koa:clore`, qui écrit ce qui passe les filtres et
s'arrête sur une contradiction. Présente :

```
## Écrit au dépôt <nom>      - [DAT/cache.md] … → pourquoi
## Écrit au QG               - [REGLES/consignes.md] … → la correction qui l'a fait naître
## Proposé (issue à ouvrir) - equipe/<livre>, chapitre « … » : … — preuve : …, vu : …, … → <lien prérempli>
## Candidat skill            - « … » : refait 3 fois (…, …, …) → <lien prérempli>
## Écarté                    - … : temporaire
```

Puis rends compte : fichiers créés, enrichis, index mis à jour, propositions déposées. Ne committe pas :
`/koa:clore` le fait, dépôt par dépôt, QG compris.
