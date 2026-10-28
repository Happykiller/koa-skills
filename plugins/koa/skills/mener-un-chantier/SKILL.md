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

## 1. Ouvrir le dossier

Au QG, `docs/chantiers/<chantier>/demande.md` : l'ordre de l'humain, tel quel. Commite-le toi-même sur la branche
principale du QG — c'est ton registre, sans PR. Un nom de chantier court, en minuscules et tirets.

**Ta session porte encore un chantier clos ?** Demande d'abord à l'humain une session neuve (`/clear`) : ce contexte
se relit à chaque appel du chantier qui commence, et il en a pesé plus de la moitié des jetons. Ta `REPRISE` et le QG
portent ce qu'il faut savoir.

## 2. L'inventaire

`agents_lister` puis `cantina_tables` : qui est là, **combien de chaque rôle**, ce qui reste du budget. Écris-le au
plan (« Équipe »). Deux sessions du même rôle sont deux files de travail. Un rôle qui manque s'ouvre
(`agent_ouvrir`) ou se demande à l'humain — jamais supposé présent. **Un chantier neuf part d'agents neufs** : une
prise de poste coûte peu, le contexte d'un chantier clos coûte à chaque appel. Dans le même chantier, un rôle passé et
fermé **se reprend** : `agent_ouvrir` avec `reprendre` et l'identifiant de conversation noté au plan.

## 3. Le tour de table

Une `CONSULTATION`, **un seul envoi** (`cantina_dire`, `a` : toutes les adresses des spécialistes concernés).
Puis `cantina_attendre`, une fois, sans adresse ; relève chaque `AVIS` par `cantina_courrier`. Tu ne débats pas :
tu consolides dans `avis.md`, et chaque contradiction devient une **décision à l'humain**, avec ses options.

## 4. Le plan et son Gantt

`plan.md` au format de « Le chantier » : features et leurs branches `feature/<nom>`, missions rangées en **vagues**,
« Relu par » tiré de la matrice « Qui intervient », le Gantt en Mermaid. Pose à l'humain **toutes** les décisions
prévisibles en un message, et sa validation du plan en même temps. Rien ne part avant sa réponse.

## 5. Les missions

Pour chaque mission de la vague : sa fiche `missions/M<n>.md`, **SMART** — un résultat, des « Fini quand » mesurables
et numérotés, atteignable par son seul exécutant, des « Contraintes », un « Prévu » —, commitée ; un message
`MISSION M<n>` qui en donne l'adresse au SHA, envoyé **à l'exécutant et à ses relecteurs ensemble**. Les missions d'une vague partent ensemble.
Un secret se cite par son identifiant au coffre (`coffre_lister`), jamais par sa valeur.

Note au plan l'heure de début de chaque mission ; republie le suivi (artefact) si ta plateforme le permet.

## 6. Superviser et clore les missions

`cantina_attendre` une fois, puis `cantina_courrier`. Une mission qui dépasse son « Prévu » de moitié sans nouvelle
est une dérive : fais le point avec l'exécutant — recadrer, découper ou replanifier. À chaque `RÉSULTAT` : **rejoue
toi-même** chaque « Fini quand » sur le commit livré ; à chaque `REVUE` acceptée, fusionne (`gh pr merge … --match-head-commit … --squash`)
dans la branche de la feature. Note l'heure de fin et l'état au plan, dans le tableau et le Gantt. Une vague close
lance la suivante. Un défaut non bloquant va au « Suivi » ; un changement de périmètre est un **avenant**.

## 7. Finaliser une feature

Mets la feature à jour de `develop`, fige une tête, et envoie-la en **un message** à ceux qui la finalisent : TECH
(suite complète, bout-en-bout d'API), QA si un parcours change (recette au navigateur), SecOps si la surface de
sécurité change. **Une pile à la fois** : la fiche le dit, et chacun lit `wsl_sante` avant de monter la sienne. Chaque
`BLOQUANT` devient une mission de correction sur la feature, puis on rejoue le delta. Tout accepté : PR de la feature vers `develop`, `--squash`, `--match-head-commit`.

## 8. Livrer

Sur l'ordre de l'humain seulement. Une mission au SecOps : sa passe sur tout ce que `develop` porte depuis la
dernière livraison ; ses `BLOQUANT` ouvrent une vague de corrections, finalisée, avant de reprendre. Une mission
au DevOps : la version de **chaque composant touché**, et d'eux seuls, sur `release/<version>`, que tu fusionnes
dans `develop`. Puis PR de `develop` vers `master`, `--merge` (sans squash), `--match-head-commit` ; DevOps pose
l'étiquette. Déployer n'est fait que si l'ordre le dit.

## 9. Clore le chantier

`cantina_releve` pour les chiffres de la table ; `retro.md` : ce qui a tenu, ce qui a coincé, ce qui change pour
le prochain passage, avec les heures du plan. Un `COMPTE RENDU` consigné sans destinataire : réalisé, non
réalisé, « Pas vérifié ». Puis :

1. **Demande la clôture à tous, en un envoi** : `CLORE — fin du chantier <chantier>` (`cantina_dire`, `a` : toutes les
   adresses). Chacun lance `/koa:clore` et te répond `CLÔTURE — <rôle>`.
2. `cantina_attendre`, une fois, puis `cantina_courrier` : une `CLÔTURE` par agent. Fusionne au QG les branches
   `capitalisation/…` qu'elles annoncent, après les avoir relues.
3. **Ferme chaque agent** (`agent_fermer`). KoA refuse celui qui n'a pas posté sa `CLÔTURE` : redemande-la. Un agent
   qui ne peut plus clore se ferme avec `sans_cloture` et la raison — elle reste à la table, et va dans `retro.md`.
   Note au plan l'identifiant de conversation que KoA rend pour chacun : il sert à le reprendre **dans ce chantier**.
4. **Clos en dernier** (`/koa:clore`) : tu capitalises ce que le chantier t'a appris, à toi. Ta `REPRISE` tient en un
   écran — l'état courant ; l'historique est au QG —, et ton `COMPTE RENDU` dit à l'humain que le chantier suivant
   s'ouvre sur une session neuve.

Une fermeture en cours de chantier — un rôle qui n'a plus de mission avant longtemps — suit les mêmes 1 à 3 : fermer
pour reprendre plus tard n'est pas une raison de ne pas clore, rien ne garantit la reprise.

## Arrêts

Tu t'arrêtes et portes la question à l'humain — une fois, avec les options — quand : une décision lui revient ; un
rôle nécessaire manque et le budget ne permet pas de l'ouvrir ; une fusion est refusée (jamais contournée) ; deux
tentatives sur la même cause ont échoué.
