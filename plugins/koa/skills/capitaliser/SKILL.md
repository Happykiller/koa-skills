---
name: capitaliser
description: "Ranger ce qu'une session de cluster KoA a appris au bon étage (dépôt, QG, proposition) et outiller ce qu'elle a refait : script, hook, skill, sous-agent, comptés au QG. Écrit sans faire valider. Par /koa:capitaliser ou /koa:clore. Hors cluster : /capitalize."
---

# Capitaliser au bon étage

Une session qui s'achève sans capitalisation, c'est un apprentissage perdu qu'on repaiera. Dans un cluster,
c'en est un aussi quand l'acquis finit **au mauvais endroit** : une décision d'équipe enfermée dans le
dépôt d'un rôle, une méthode générale dans un seul projet. Le pourquoi : `library://koa/ghost`.

Deux volets, et le second n'est pas facultatif :

- **Faire mieux** → une connaissance rejoint la page que le prochain lira (§ 3).
- **Faire plus efficacement** → un geste refait devient un outil, et un outil qui a trompé se corrige (§ 3 bis).

Une clôture qui ne range que des documents laisse l'équipe refaire à la main, au chantier suivant, ce
qu'elle a déjà refait à ce chantier-ci. Relevé sur une équipe de cinq rôles : toutes les clôtures avaient
rangé des leçons, aucune n'avait cherché le geste répété — alors que l'orchestrateur avait enchaîné une
quinzaine de fois la même séquence de fusion à la main.

Le cluster et son QG : `$KOA_CLUSTER`, `$KOA_QG`. Sans `KOA_QG`, ce n'est pas un cluster : utilise la
capitalisation du projet (`/capitalize`), ou `koa:poser-la-memoire` s'il n'en a pas.

## 1. Relire la session

Liste, sans filtrer encore :

- ce qui a été **découvert** (un comportement, une contrainte, une dépendance cachée) ;
- ce qui a été **décidé**, et **pourquoi** — l'alternative écartée compte autant ;
- ce que l'humain ou un autre agent a **corrigé** chez toi : le signal le plus fort, une correction non
  capitalisée se reproduira ;
- ce qui t'a **induit en erreur** : une page, une consigne, un script, un hook, une skill ;
- les gestes **répétés** ou laborieux, **chiffrés** : combien de fois, où (fiche, message, commit), et ce que
  cela a coûté — tours, minutes, une reprise. Une séquence de commandes refaite, une vérification rejouée à
  chaque revue, une fiche réécrite à la main, un contrôle qu'on oublie et qu'un incident a rappelé.

## 2. Filtrer

Ne garde que ce qui est **durable** (vrai dans trois mois), **non déductible** (pas déjà dans le code, un
README ou l'historique git) et **réutilisable**. Le reste est **écarté**, et dit comme tel.

**Rien ne passe : n'écris aucune page**, pas même une ligne d'`HISTORY.md` ni un `maj:` — une ligne « rien à
capitaliser » dans le compte rendu. C'est l'issue normale d'une session courte, pas un manque. Le § 3 bis se
fait quand même ; s'il n'écrit rien non plus, aucune branche au QG.

## 3. Ranger — le tamis, dans cet ordre

La première réponse oui décide. **Une chose monte aussi haut que sa généralité prouvée, jamais plus haut.**

| Question | Étage | Geste |
|---|---|---|
| Vrai seulement pour **ce code** ? | N4 — le dépôt de la stack | **écrit** dans sa `docs/KB/` (`DAT/`, `DAF/`, `HISTORY.md`) |
| Vrai pour **tout le cluster** — un environnement, une décision, un terme métier, une règle d'équipe ? | N3 — le QG | **écrit** dans `$KOA_QG/docs/KB/`, ou son `CLAUDE.md` |
| Un **geste** refait trois fois **par tous les clusters**, ou une skill de `koa-skills` à corriger ? | N2 — la marketplace | **proposé** : une issue rédigée pour `Happykiller/koa-skills` — un geste propre à ce cluster s'outille ici (§ 3 bis) |
| Vrai pour **tout agent de ce rôle**, quel que soit le projet ? | N1 — la librairie | **proposé** : une issue rédigée pour `Happykiller/koa-releases` quand le livre est de KoA (`koa/…`, `equipe/…`) ; `library_ecrire` pour un livre de l'opérateur |

Au QG, la destination dépend de la nature :

| Nature | Destination |
|---|---|
| Invariant non négociable de l'équipe | `REGLES/lois.md` |
| Correction ou préférence de l'humain envers l'équipe | `REGLES/consignes.md` |
| Process, workflow, norme | `REGLES/process.md`, `workflows.md`, `normes.md` |
| Décision transverse | `decisions/AAAA-MM-JJ-sujet.md` |
| Terme métier | `glossaire.md` |
| Fait d'environnement commun : la distro, un outil présent ou absent, la forge | la section « Les environnements » de `$KOA_QG/CLAUDE.md`, une fois pour l'équipe |
| Ce que **ton rôle** a appris de sa façon de travailler ici | `equipe/<rôle>.md` |
| Une mission **livrée** (sa fiche close) — pas la session | une ligne de `HISTORY.md`, écrite par l'orchestrateur qui la clôt : un seul rédacteur, pas de conflit |

Un fait d'environnement **n'est pas un acquis de rôle**, même découvert en jouant le tien : « `python`
n'existe pas, seulement `python3` » vaut pour chaque agent de la distro. Rangé dans `equipe/<rôle>.md`,
chaque rôle le redécouvre et l'écrit dans sa page — trois fois pour un seul chantier. Le `CLAUDE.md` du
QG, lui, est lu par tous à la prise de poste.

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

## 3 bis. Outiller — faire plus efficacement

Reprends la liste des gestes répétés et de ce qui t'a induit en erreur (§ 1). **Ce volet se fait même quand le
§ 2 n'a rien retenu** : une session courte peut n'avoir rien appris et avoir tout refait.

**Corriger ce qui a trompé n'attend pas de compteur** : un outil qui a menti une fois mentira encore.

| Ce qui a trompé | Geste |
|---|---|
| Un script, un hook, une skill ou un sous-agent de **ton étage** (ta seed, un dépôt de la stack, le QG) | corrigé, et éprouvé : un hook se déclenche sans que personne le relise |
| Une page ou une **consigne** du cluster qui fait faire autrement qu'une skill de `koa-skills` | un arrêt (§ 4) : dis l'écart dans ton compte rendu, la skill et la page citées. Une consigne périmée qui l'emporte sur la skill fait refaire à la main ce que le framework fait déjà, et rien ne le signale |
| Une skill de `koa-skills` ou un livre de KoA | proposé (§ 3, N2 ou N1) |

**Créer attend trois occurrences, tous rôles confondus.** Une fois, c'est un geste ; deux fois, on le note ;
trois fois, on l'outille. Le compte se tient au QG, dans `$KOA_QG/docs/KB/MOTEUR.md`, section « Candidats » —
une ligne par geste : ce qu'il fait, chaque occurrence (rôle, chantier, preuve), son coût observé, la forme
pressentie. C'est là que trois rôles qui ont fait la même chose une fois chacun se voient : chacun seul n'en
aurait compté qu'une.

Trois occurrences : choisis la forme, puis l'étage.

| Forme | Quand c'est le bon choix |
|---|---|
| **Script** | un enchaînement mécanique, sans jugement, qu'on relance tel quel |
| **Hook** | ça doit se déclencher tout seul, de façon déterministe, sans que personne y pense |
| **Skill** | une procédure qu'on redemande et qui demande du jugement |
| **Sous-agent** | un travail volumineux ou une expertise à part, qui encombrerait le contexte de la session |
| **Règle** | ça ne s'automatise pas, ça se rappelle : une page du QG (§ 3) |

| Il sert à… | Il vit… |
|---|---|
| ce code seulement | dans ce dépôt de la stack : `tools/`, ou son `.claude/` — **écrit** |
| ton rôle, dans ce cluster | dans ta seed : `tools/`, `.claude/hooks/`, `.claude/skills/`, `.claude/agents/` — **écrit** |
| toute l'équipe | un script au QG, `tools/` — **écrit** ; un hook, une skill ou un sous-agent pour tous les rôles se **propose** en N2 : seul un plugin le porte à chaque seed |
| tous les clusters | **proposé** : une issue rédigée pour `Happykiller/koa-skills` (§ 3) |

Garde-fous :

- **Vérifie que ça n'existe pas déjà** : ta seed, le QG (`MOTEUR.md`, `tools/`), les plugins installés.
- **Un outil dont tu ne sais pas dire quand il se déclenchera la prochaine fois est une règle**, pas un outil.
- **Tout outil créé rejoint `MOTEUR.md`** — celui du QG pour ce qui sert à l'équipe, celui du dépôt sinon —
  avec sa colonne « quand s'en servir » ; sa ligne de candidat en sort.
- **Le gain se chiffre** : occurrences, coût évité par fois, coût de fabrication. Un outil qui coûte plus à
  écrire qu'il ne rendra en trois chantiers reste un candidat.

## 4. Écrire comme au QG

- **Enrichir avant de créer** : cherche d'abord la page qui couvre le sujet — sur le QG à jour
  (`git -C "$KOA_QG" pull --ff-only`), pas sur la copie de ta prise de poste.
- **Des clôtures parallèles ne se voient pas** : chacune écrit sur sa branche, et ce qu'un autre rôle
  capitalise en même temps que toi n'est sur aucune page que tu peux lire. Le doublon ne se rattrape
  qu'**après fusion** : l'orchestrateur, qui clôt en dernier, relit le QG fusionné et ramène un même fait
  à un seul endroit (`koa:clore`, « Pousser »).
- **Index d'abord** : toute page nouvelle rejoint le `README.md` de son dossier dans le même geste.
- Le **pourquoi**, jamais le seul quoi ; le champ `maj:` des pages touchées — et d'elles seules.
- Ce qui **contredit** une page existante — surtout une loi — est un arrêt : propose, ne tranche pas.

## 5. Écrire, puis rendre compte

**Écris sans faire valider**, appelé seul comme par `/koa:clore` : jusqu'au QG, le tri **est** le travail,
et un agent de cluster qui attend une validation attend souvent un humain absent. Ce qui contredit une
page existante s'arrête (§ 4) ; ce qui vise N2 ou N1 se propose, toujours. Le compte rendu :

```
## Écrit au dépôt <nom>      - [DAT/cache.md] … → pourquoi
## Écrit au QG               - [REGLES/consignes.md] … → la correction qui l'a fait naître
## Corrigé (ce qui a trompé) - [seed .claude/hooks/suivi.sh] … → ce qu'il faisait faire de faux
## Outillé                   - [tools/fusionner.sh] script, 3 occurrences (…, …, …), ~4 tours évités par fusion
## Candidat (n/3)            - « contrôler la CI puis fusionner » : 2/3 (orchestrateur c6, c7), noté à MOTEUR.md
## Proposé (issue à ouvrir) - equipe/<livre>, chapitre « … » : … — preuve : …, vu : …, … → <lien prérempli>
## Écart à une skill         - la consigne « … » fait faire autrement que koa:<skill> : … → à trancher par l'humain
## Écarté                    - … : temporaire
```

Le volet outillage se dit toujours, même vide : « Outillage : rien de répété » est une réponse ; son absence
dit qu'il n'a pas été cherché. Puis rends compte : fichiers créés, enrichis, index mis à jour, outils et
propositions déposés. Ne committe pas : `/koa:clore` le fait, dépôt par dépôt, QG compris.
