---
name: mener-un-chantier
description: "Orchestrateur KoA : mener un chantier d'équipe — inventaire, tour de table, plan en vagues et Gantt au QG, missions —, puis le finaliser et le livrer. Quand l'humain ordonne un chantier, « finalise … » ou « livre ». Par /koa:mener-un-chantier."
---

# Mener un chantier

Les **gestes** de l'orchestrateur, dans l'ordre. Le **pourquoi** et les **formats** sont au livre `equipe/table`
de la librairie KoA (`library_lire("equipe/table", "*")`), chapitres « Le chantier », « La fiche de mission » et
« Finaliser et livrer » : cette skill n'en recopie rien, elle te dit quoi faire et quand.

Tu **coordonnes, tu n'exécutes pas** : aucune ligne de code, aucun test, aucune revue à la place d'un spécialiste.

| Variante | Quand |
|---|---|
| `/koa:mener-un-chantier` | l'humain ordonne un chantier : les étapes 1 à 6 |
| `/koa:mener-un-chantier finaliser <feature>` | « finalise … » : l'étape 7 |
| `/koa:mener-un-chantier livrer` | « livre » : l'étape 8 |

## Le registre et les quatre vues

Le chantier tient dans **une source** : `docs/chantiers/<chantier>/chantier.json`, au format de
`${CLAUDE_PLUGIN_ROOT}/skills/mener-un-chantier/chantier.modele.json` — le plan, les « Fini quand », les risques, les
décisions, les observations, les capacités. Tu n'y écris **ni heure ni état** : qui a reçu sa mission et quand, quelle
`REVUE` a conclu quoi sur quel SHA, quel `BLOCAGE`, KoA les tient dans le journal de la table.

**Actualiser** = `chantier_actualiser` (`table`, `chantier`, `generateur` : `${CLAUDE_PLUGIN_ROOT}/scripts/livrables.py`).
KoA y joint les faits de la Cantina et écrit sous `docs/chantiers/<chantier>/genere/` : `plan.md` (missions, états,
heures, Gantt, blocages), `bilan.md` (pour le pilote), `rex.md` (amélioration continue) et `livraison.md` (pour les
autres métiers). Il y joint aussi le **coût par mission** (modèle, effort, tours, jetons), qu'il lit dans les transcripts :
ne le compte pas, ne le recopie pas, il ne te coûte rien. Il ne rend que les chemins : ne relis pas les vues pour les recopier,
cite-les. Sans cet outil, `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/livrables.py" <chantier.json> --output <dossier>/genere` rend
les mêmes vues, heures et coûts « pas mesuré », états tirés d'un champ `state` que tu tiens alors toi-même.

Actualise **aux jalons**, jamais à chaque message : plan soumis, vague close, finalisation, livraison, clôture. Ne
retouche pas une vue à la main : la suivante l'écraserait — corrige le registre. Commite le registre et `genere/`.

## 1. Ouvrir le dossier

Au QG, `docs/chantiers/<chantier>/demande.md` : l'ordre de l'humain, tel quel. Commite-le toi-même sur la branche
principale du QG — c'est ton registre, sans PR. Un nom de chantier court, en minuscules et tirets.

**Ta session porte encore un chantier clos ?** Demande d'abord à l'humain une session neuve (`/clear`) : ce contexte
se relit à chaque appel du chantier qui commence, et il en a pesé plus de la moitié des jetons. Ta `REPRISE` et le QG
portent ce qu'il faut savoir.

## 2. L'inventaire

`agents_lister` puis `cantina_tables` : qui est là, **combien de chaque rôle**, ce qui reste du budget. Écris-le au
registre (`team`). Deux sessions du même rôle sont deux files de travail. Un rôle qui manque s'ouvre
(`agent_ouvrir`) ou se demande à l'humain — jamais supposé présent. **Un chantier neuf part d'agents neufs** : une
prise de poste coûte peu, le contexte d'un chantier clos coûte à chaque appel. Dans le même chantier, un rôle passé et
fermé **se reprend** : `agent_ouvrir` avec `reprendre` et l'identifiant de conversation noté au registre. **Sur ce
poste seulement** : une conversation reste dans la distro où elle a tourné, et le registre, lui, voyage par git. Sur un
autre poste que celui noté, ne passe pas `reprendre` — KoA le refuserait — : ouvre un agent neuf avec une fiche qui
porte le contexte utile, et remplace l'identifiant et le poste au registre à sa fermeture.

## 3. Le tour de table

Une `CONSULTATION`, **un seul envoi** (`cantina_dire`, `a` : toutes les adresses des spécialistes concernés).
Puis `cantina_attendre`, une fois, sans adresse ; relève chaque `AVIS` par `cantina_courrier`. Tu ne débats pas :
tu consolides dans `avis.md`, et chaque contradiction devient une **décision à l'humain**, avec ses options.

## 4. Le plan et son Gantt

Le plan au format de « Le chantier », écrit dans `chantier.json` : features et leurs branches `feature/<nom>`,
missions rangées en **vagues** (`wave`, `depends_on`), « Relu par » tiré de la matrice « Qui intervient ».
Actualise : `genere/plan.md` porte le tableau et le Gantt.

**Jalons d'intégration.** Quand deux missions se rencontrent — une API et son consommateur, un schéma et ce qui le
lit, une configuration, une migration —, le plan porte un **jalon** : une petite mission `I<n>` de la vague qui suit,
qui dépend des deux, avec son contrat en une phrase, son exécutant (celui qui consomme, en général) et la commande
ciblée du projet qui prouve la rencontre, sur la tête de la feature où les deux sont fusionnées. Elle part dès que
les deux sont closes, comme toute vague ; un `BLOQUANT` y ouvre une correction tout de suite, pas en finalisation.
Pas de jalon sans risque d'incompatibilité nommé (`risks`), et un jalon ne remplace ni la suite complète ni la recette
finales.

Pose à l'humain **toutes** les décisions prévisibles en un message, avec `genere/plan.md`, et sa validation du plan
en même temps. Rien ne part avant sa réponse.

## 5. Les missions

Pour chaque mission de la vague : sa fiche `missions/M<n>.md`, **SMART** — un résultat, des « Fini quand » mesurables
et numérotés, atteignable par son seul exécutant, des « Contraintes », un « Prévu » —, commitée ; un message
`MISSION M<n>` qui en donne l'adresse au SHA, envoyé **à l'exécutant et à ses relecteurs ensemble**. Les missions d'une
vague partent ensemble. Un secret se cite par son identifiant au coffre (`coffre_lister`), jamais par sa valeur.
L'heure de départ est celle du message : ne la note pas.

## 6. Superviser et clore les missions

`cantina_attendre` une fois, puis `cantina_courrier`. Une mission qui dépasse son « Prévu » de moitié sans nouvelle
est une dérive : fais le point avec l'exécutant — recadrer, découper ou replanifier. Un `RÉSULTAT` est un indice :
c'est la `REVUE` qui prouve. À chaque `REVUE` acceptée, **contrôle sans rejouer** : chaque « Fini quand » y porte sa
commande et son verdict, sur le SHA complet que tu vas fusionner — un critère que la CI requise a vérifié sur ce SHA
est prouvé aussi. Tu ne rejoues toi-même que ce qui manque, se contredit, porte sur une autre tête ou un autre
environnement, ou touche un risque critique ; à partir de C2, au moins une preuve par Owner. Une preuve vaut pour sa
tête : un commit de plus l'invalide, et le critère se rejoue ou passe en « Pas vérifié » (`unverified`). Puis fusionne
(`gh pr merge … --match-head-commit … --squash`) dans la branche de la feature — **`--merge` si la PR porte une
fusion** (`git log --merges <base>..<tête>`) ou un SHA épinglé ailleurs (workflow, action) : le squash coupe
l'ascendance, la fusion suivante rejoue les conflits déjà résolus, et l'épingle devient injoignable. Une vague close
lance la suivante, et s'actualise. Un défaut non bloquant va au « Suivi » (`follow_up`) ; un changement de périmètre est un **avenant**.

## 7. Finaliser une feature

Mets la feature à jour de `develop`, fige une tête, et envoie-la en **un message** à ceux qui la finalisent : TECH
(suite complète, bout-en-bout d'API), QA si un parcours change (recette au navigateur), SecOps si la surface de
sécurité change. **Une pile à la fois** : la fiche le dit, et chacun lit `wsl_sante` avant de monter la sienne. Chaque
`BLOQUANT` devient une mission de correction sur la feature, puis on rejoue le delta. Tout accepté : PR de la feature
vers `develop`, `--squash` — ou `--merge` si elle porte une fusion, ce que la mise à jour de `develop` fait souvent
(§ 6) —, `--match-head-commit`. Tiens les capacités de la feature au registre (`capabilities`,
`finalized`) et actualise.

## 8. Livrer

Sur l'ordre de l'humain seulement. Une mission au SecOps : sa passe sur tout ce que `develop` porte depuis la
dernière livraison ; ses `BLOQUANT` ouvrent une vague de corrections, finalisée, avant de reprendre. Une mission
au DevOps : la version de **chaque composant touché**, et d'eux seuls, sur `release/<version>`, que tu fusionnes
dans `develop`. Puis PR de `develop` vers `master`, `--merge` (sans squash), `--match-head-commit` ; DevOps pose
l'étiquette. Déployer n'est fait que si l'ordre le dit. **Une fois la livraison faite** — et elle seule —, passe ses
capacités en `delivered`, avec leur usage, leurs limites et leurs prérequis dits pour quelqu'un qui ne code pas, et
actualise : `genere/livraison.md` est la note des autres métiers.

## 9. Clore le chantier

`cantina_releve` pour les chiffres de la table. Range au registre les observations du chantier (`observations` : le
fait, sa preuve, la cause établie ou l'hypothèse, le coût s'il se mesure, la portée, l'action ; un doublon porte
`duplicate_of`), puis actualise : `genere/rex.md` est la rétrospective, `genere/bilan.md` le bilan du pilote, avec les
mesures que le journal permet. Un `COMPTE RENDU` consigné sans destinataire : réalisé, non réalisé, « Pas vérifié »,
en citant ces chemins plutôt qu'en les recopiant. Puis :

1. **Demande la clôture à tous, en un envoi** : `CLORE — fin du chantier <chantier>` (`cantina_dire`, `a` : toutes les
   adresses). Chacun lance `/koa:clore` et te répond `CLÔTURE — <rôle>`.
2. `cantina_attendre`, une fois, puis `cantina_courrier` : une `CLÔTURE` par agent. Fusionne au QG les branches
   `capitalisation/…` qu'elles annoncent, après les avoir relues.
3. **Ferme chaque agent** (`agent_fermer`). KoA refuse celui qui n'a pas posté sa `CLÔTURE` : redemande-la. Un agent
   qui ne peut plus clore se ferme avec `sans_cloture` et la raison — elle reste à la table, et va aux observations.
   Note au registre (`team`) l'identifiant de conversation **et le poste** que KoA rend pour chacun : il sert à le
   reprendre **dans ce chantier, sur ce poste**.
4. **Laisse les dépôts sans orphelin** : chaque PR ouverte du chantier a une décision — fusionnée, fermée avec sa
   raison, ou reportée au « Suivi » ; chaque branche fusionnée ou abandonnée est supprimée, son SHA dit dans ton
   `COMPTE RENDU` ; une trace à garder devient une étiquette `archive/<branche>`. Une PR ou une branche laissée sans
   décision se lit, au chantier suivant, comme un travail en cours.
5. **Clos en dernier** (`/koa:clore`) : tu capitalises ce que le chantier t'a appris, à toi. Ta `REPRISE` tient en un
   écran — l'état courant ; l'historique est au QG —, et ton `COMPTE RENDU` dit à l'humain que le chantier suivant
   s'ouvre sur une session neuve.

Une fermeture en cours de chantier — un rôle qui n'a plus de mission avant longtemps — suit les mêmes 1 à 3 : fermer
pour reprendre plus tard n'est pas une raison de ne pas clore, rien ne garantit la reprise.

## Arrêts

Tu t'arrêtes et portes la question à l'humain — une fois, avec les options — quand : une décision lui revient ; un
rôle nécessaire manque et le budget ne permet pas de l'ouvrir ; une fusion est refusée (jamais contournée) ; deux
tentatives sur la même cause ont échoué ; `chantier_actualiser` refuse le registre (corrige-le, ne contourne pas).
