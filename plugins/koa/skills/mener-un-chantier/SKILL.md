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

## Le registre, les quatre vues et la page de suivi

Le chantier tient dans **une source** : `docs/chantiers/<chantier>/chantier.json`, au format de
`${CLAUDE_PLUGIN_ROOT}/skills/mener-un-chantier/chantier.modele.json` — le plan, les « Fini quand », les risques, les
décisions, les observations, les capacités, le titre de chaque vague (`waves`) et la **durée prévue de chaque mission**
(`estimate_min`, le « Prévu » de sa fiche). Tu n'y écris **ni heure ni état** : qui a reçu sa mission et quand, quelle
`REVUE` a conclu quoi sur quel SHA, quel `BLOCAGE`, KoA les tient dans le journal de la table.

**Actualiser** = `chantier_actualiser` (`table`, `chantier`, `generateur` : `${CLAUDE_PLUGIN_ROOT}/scripts/livrables.py`).
KoA y joint les faits de la Cantina et écrit sous `docs/chantiers/<chantier>/genere/` : `plan.md` (missions, états,
heures, Gantt, blocages), `bilan.md` (pour le pilote), `rex.md` (amélioration continue), `livraison.md` (pour les
autres métiers) et **`suivi.html`, la page de suivi de l'humain**. Il y joint aussi le **coût par mission** (modèle,
effort, tours, jetons), qu'il lit dans les transcripts : ne le compte pas, ne le recopie pas, il ne te coûte rien. Il ne
rend que les chemins : ne relis pas les vues pour les recopier, cite-les. Sans cet outil,
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/livrables.py" <chantier.json> --output <dossier>/genere` rend les mêmes vues,
heures et coûts « pas mesuré », états tirés d'un champ `state` que tu tiens alors toi-même.

**La page de suivi se publie telle quelle, elle ne se refait pas.** `genere/suivi.html` porte la forme que l'humain a
validée : l'heure de mise à jour et le temps écoulé tout en haut, l'avancement, le Gantt du plan entier, la durée réelle
en couleur face au prévu, le coût par mission. Publie-la en artefact (même URL à chaque fois), sans la réécrire ni la
retoucher : chaque page refaite par un chantier a perdu un réglage obtenu au précédent. Une forme à changer se demande
dans koa-skills, pas dans un outil du QG.

Actualise **à chaque fusion d'une mission**, à chaque vague lancée, et aux jalons : plan soumis, finalisation,
livraison, clôture. Les états ne bougent qu'à l'actualisation : entre deux, la page montre un état figé, et son
indicateur le dit. Ne retouche pas une vue à la main : la suivante l'écraserait — corrige le registre. Passe
`committer: true` : KoA committe le registre et `genere/`, sans tour de plus, et ne pousse pas. Pousse avec ton
prochain envoi de fiches, au plus tard à la clôture ; une réponse sans `commit` veut dire que c'est à toi de committer.

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
Puis `cantina_attendre`, sans adresse : il rend chaque `AVIS` en entier, sans `cantina_courrier` derrière. Tu ne débats pas :
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
et numérotés, atteignable par son seul exécutant, des « Contraintes », un « Prévu » — reporté en `estimate_min` au
registre, faute de quoi ni l'avancement ni la couleur des durées ne se lisent —, commitée ; un message
`MISSION M<n>` qui en donne l'adresse au SHA, envoyé **à l'exécutant et à ses relecteurs ensemble**. La fiche dit à qui répondre : le `RÉSULTAT` aux relecteurs
qu'elle nomme, **pas à toi** tant qu'il y en a un, et à toi `BLOCAGE` et `QUESTION`. Te mettre en copie te réveille pour
un message sur lequel tu n'as rien à faire. Les missions d'une vague partent ensemble. Un secret se cite par son identifiant au coffre (`coffre_lister`), jamais par sa valeur.
L'heure de départ est celle du message : ne la note pas.

## 6. Superviser et clore les missions

`cantina_attendre`, sans adresse : il rend le courrier. Une mission qui dépasse son « Prévu » de moitié sans nouvelle
est une dérive : fais le point avec l'exécutant — recadrer, découper ou replanifier. Le `RÉSULTAT` va aux relecteurs de la
fiche, et c'est la `REVUE` qui te réveille et qui prouve ; une fiche sans relecteur te l'adresse, et **la `REVUE` est alors
la tienne** : consigne-la dès ton contrôle (`cantina_dire`, `REVUE M<n> — ACCEPTÉ, sur <SHA>`), car c'est elle qui clôt la
mission au journal — oubliée, la mission court au suivi et sa durée gonfle jusqu'à ce que tu y penses. À chaque `REVUE` acceptée, **contrôle sans rejouer** : chaque « Fini quand » y porte sa
commande et son verdict, sur le SHA complet que tu vas fusionner — un critère que la CI requise a vérifié sur ce SHA
est prouvé aussi. Tu ne rejoues toi-même que ce qui manque, se contredit, porte sur une autre tête ou un autre
environnement, ou touche un risque critique ; à partir de C2, au moins une preuve par Owner. Une preuve vaut pour sa
tête : un commit de plus l'invalide, et le critère se rejoue ou passe en « Pas vérifié » (`unverified`). Puis fusionne
(`gh pr merge … --match-head-commit … --squash`) dans la branche de la feature — **`--merge` si la PR porte une
fusion** (`git log --merges <base>..<tête>`) ou un SHA épinglé ailleurs (workflow, action) : le squash coupe
l'ascendance, la fusion suivante rejoue les conflits déjà résolus, et l'épingle devient injoignable. La CI d'une PR
s'attend en arrière-plan par `gh pr checks <n> --watch`, jamais par une boucle de `sleep`. **Fusionnée, réponds à qui
l'attendait** : chaque `BLOCAGE` qui nomme cette mission reçoit, dans le même tour, `RÉPONSE M<k> — M<n> fusionnée dans
<base>, <SHA de fusion>`, et la dépendance qu'il révélait entre au `depends_on` de la mission qui attendait — sans
cette réponse, l'exécutant attend une fusion déjà faite. Une vague close
lance la suivante, et s'actualise. **Un plan validé n'est pas un ordre de finaliser** : la dernière vague close, demande-le
à l'humain en un message, avec les preuves, sauf si sa demande ou sa validation le dit déjà. Un défaut non bloquant va au « Suivi » (`follow_up`) ; un changement de périmètre est un **avenant**.

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

**La livraison se règle avant** : faite, ou écartée par l'humain, à qui tu poses la question. Rouvrir un agent clos pour
livrer coûte une prise de poste de plus.

`cantina_releve` pour les chiffres de la table. Range au registre les observations du chantier (`observations` : le
fait, sa preuve, la cause établie ou l'hypothèse, le coût s'il se mesure, la portée, l'action ; un doublon porte
`duplicate_of`), puis actualise : `genere/rex.md` est la rétrospective, `genere/bilan.md` le bilan du pilote, avec les
mesures que le journal permet. Un `COMPTE RENDU` consigné sans destinataire : réalisé, non réalisé, « Pas vérifié »,
en citant ces chemins plutôt qu'en les recopiant. Puis :

1. **Demande la clôture à tous, en un envoi** : `CLORE — fin du chantier <chantier>` (`cantina_dire`, `a` : toutes les
   adresses). Chacun lance `/koa:clore` et te répond `CLÔTURE — <rôle>`.
2. `cantina_attendre` : il rend le courrier, jusqu'à une `CLÔTURE` par agent. Fusionne au QG les branches
   `capitalisation/…` qu'elles annoncent, après les avoir relues. Une `CLÔTURE` sans sa ligne `Outillage` se
   redemande. Relis ensuite les « Candidats » du `MOTEUR.md` fusionné : chaque rôle n'y a compté que ses propres
   occurrences, et un geste qui atteint trois en les additionnant ne s'est vu chez aucun. Il s'outille à ta propre
   clôture, ou se propose ; ton `COMPTE RENDU` dit ce que le chantier a outillé.
3. **Ferme chaque agent** (`agent_fermer`). KoA refuse celui qui n'a pas posté sa `CLÔTURE` : redemande-la. Un agent
   qui ne peut plus clore se ferme avec `sans_cloture` et la raison — elle reste à la table, et va aux observations.
   Note au registre (`team`) l'identifiant de conversation **et le poste** que KoA rend pour chacun : il sert à le
   reprendre **dans ce chantier, sur ce poste**.
4. **Laisse les dépôts sans orphelin** : chaque PR ouverte du chantier a une décision — fusionnée, fermée avec sa
   raison, ou reportée au « Suivi » ; chaque branche fusionnée ou abandonnée est supprimée, son SHA dit dans ton
   `COMPTE RENDU` ; une trace à garder devient une étiquette `archive/<branche>`. Une PR ou une branche laissée sans
   décision se lit, au chantier suivant, comme un travail en cours.
5. **Clos en dernier** (`/koa:clore`), même si tu as écrit ta capitalisation à la main : ton travail ne s'arrête pas au
   `COMPTE RENDU`. Tu capitalises ce que le chantier t'a appris, à toi. Ta `REPRISE` tient en un
   écran — l'état courant ; l'historique est au QG —, et ton `COMPTE RENDU` dit à l'humain que le chantier suivant
   s'ouvre sur une session neuve.

Une fermeture en cours de chantier — un rôle qui n'a plus de mission avant longtemps — suit les mêmes 1 à 3 : fermer
pour reprendre plus tard n'est pas une raison de ne pas clore, rien ne garantit la reprise.

## Arrêts

Tu t'arrêtes et portes la question à l'humain — une fois, avec les options — quand : une décision lui revient ; un
rôle nécessaire manque et le budget ne permet pas de l'ouvrir ; une fusion est refusée (jamais contournée) ; deux
tentatives sur la même cause ont échoué ; `chantier_actualiser` refuse le registre (corrige-le, ne contourne pas).
