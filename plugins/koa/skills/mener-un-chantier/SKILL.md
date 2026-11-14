---
name: mener-un-chantier
description: "Orchestrateur KoA : mener un chantier d'équipe — cadrage, tour de table qui audite, plan et Gantt au QG, missions en autonomie —, puis le finaliser et le livrer. Quand l'humain ordonne un chantier, « finalise … » ou « livre ». Par /koa:mener-un-chantier."
---

# Mener un chantier

Les **gestes** de l'orchestrateur, dans l'ordre. Le **pourquoi** et les **formats** sont au livre `equipe/table`
de la librairie KoA (`library_lire("equipe/table", "*")`), chapitres « Le chantier », « La fiche de mission » et
« Finaliser et livrer » : cette skill n'en recopie rien, elle te dit quoi faire et quand.

Tu **coordonnes, tu n'exécutes pas** : aucune ligne de code, aucun test, aucune revue à la place d'un spécialiste.

**Un chantier dure des heures, parfois des jours, et l'humain n'est pas devant son écran pendant ce temps.** Tout ce
qui demande son intervention se règle **avant le lancement** : au cadrage (§ 1), au tour de table (§ 3) et à la
validation du plan (§ 4). Une fois le plan lancé, l'équipe va **seule jusqu'à la livraison** (§ 6). Une attente de
l'humain après le lancement est un défaut de préparation, pas une étape normale.

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
heures, Gantt, blocages, attentes de l'humain), `bilan.md` (pour le pilote), `rex.md` (amélioration continue), `livraison.md` (pour les
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

## 1. Ouvrir le dossier et cadrer

Au QG, `docs/chantiers/<chantier>/demande.md` : l'ordre de l'humain, tel quel. Commite-le toi-même sur la branche
principale du QG — c'est ton registre, sans relecture. Un nom de chantier court, en minuscules et tirets.

**Puis cadre, en un message à l'humain**, avant toute consultation. Tes questions fixent le point d'arrivée :

- **les livrables, et jusqu'où** : fusionné, finalisé, livré, déployé, constaté sur un environnement ? Ce qu'il
  confirme ici est acquis : une livraison confirmée au cadrage ne se redemande pas aux §§ 7-8 ;
- **ce qu'il regardera pour dire « c'est fait »** : les critères d'acceptation du chantier ;
- **les contraintes et le hors-périmètre** ;
- **son absence** : à partir de quand, pour combien de temps. Le plan en tient compte : ce qui se fera la nuit doit
  être permis avant ;
- **ce qu'il veut trancher lui-même** quoi qu'il arrive. Le reste ira au mandat (§ 4).

Ne pose que les questions dont la demande ne donne pas déjà la réponse. Les réponses vont au registre
(`result`, `done_when`, `out_of_scope`, `framing`).

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

## 3. Le tour de table : consulter et auditer

Une `CONSULTATION`, **un seul envoi** (`cantina_dire`, `a` : toutes les adresses des spécialistes concernés).
Puis `cantina_attendre`, sans adresse : il rend chaque `AVIS` en entier, sans `cantina_courrier` derrière. Tu ne débats pas :
tu consolides dans `avis.md`, et chaque contradiction devient une **décision à l'humain**, avec ses options.

**Le tour de table n'est pas seulement consultatif : c'est un audit.** La `CONSULTATION` le demande en toutes lettres,
et chaque `AVIS` le rend dans ses rubriques « Prêt à travailler seul » et « Mandat proposé » (format au livre
`equipe/table`) :

- **chaque geste du découpage qui sort du dépôt de l'agent est essayé maintenant, à blanc** : une lecture, un
  `--dry-run`, une transaction en lecture seule, `coffre_lister`, `wsl_sante`, un outil appelé à vide. Un refus du
  classifieur doit tomber à ce moment-là, pendant que l'humain est là, et pas la nuit. Les refus ne sont pas
  constants : seul un essai réel dit si un geste passe ;
- **l'environnement aussi** : outils installés et leurs versions, ressources du poste, ce qu'un redémarrage perd,
  secrets et comptes présents au coffre, comptes de recette ;
- **un `AVIS` sans rubrique « Prêt à travailler seul » se redemande**, comme une `CLÔTURE` sans « Outillage ».

**Audite-toi aussi** : tes propres gestes sortent du dépôt — écrire un réglage, fusionner et pousser sur chaque
dépôt, supprimer des branches à la clôture, publier la page de suivi. Un orchestrateur figé sur une permission fige
toute l'équipe.

**Relis les attentes des chantiers précédents** (`genere/rex.md`, « Attentes de l'humain ») : une permission déjà
accordée dans un onglet et que la seed ne porte toujours pas reviendra.

Range l'audit au registre (`readiness` : `role`, `gesture`, `touches`, `state` = `éprouvé` | `à poser` | `impossible`,
`proof`). `genere/plan.md` en fait la **liste de départ**.

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

**Le plan validé est un contrat d'autonomie.** Pose à l'humain **toutes** les décisions prévisibles en un message,
avec `genere/plan.md`, et sa validation du plan en même temps. Ce message porte aussi, pour qu'il règle tout d'un coup
avant de partir :

- **la liste de départ** : chaque ligne « à poser » de l'audit, avec son rôle et le geste exact attendu de lui — le
  bloc `autoMode` de telle distro, un secret à verser au coffre, une commande `!` à lancer dans tel onglet. **Une
  décision n'est pas une permission** : un ordre de livrer n'autorise pas le classifieur à laisser lire
  l'environnement livré. Il faut les deux, et la liste les sépare. Un accord écrit dans un onglet ne vaut que pour
  cette session : préfère ce que la seed portera encore au chantier suivant ;
- **le mandat** : ce que tu trancheras seul, nourri des « Mandat proposé » de chaque rôle — une exception de
  dépendance courte quand la sécurité conclut à une exposition nulle, un compte de recette pour un geste
  d'administration, un écart du constat final qui se corrige s'il est dans le périmètre — et ce qui l'attendra
  toujours. Sa réponse va au registre (`decisions`) ; tu t'y réfères quand tu tranches, et tu le dis à la table ;
- **la promesse** : après sa validation et une liste de départ verte, tu ne le sollicites plus avant la livraison,
  sauf panne.

**Rien ne part avant sa validation, ni tant que la liste de départ n'est pas verte.** Chaque geste que l'humain a posé est réessayé à blanc
par l'agent concerné, qui le confirme ; la ligne passe alors à `éprouvé`. Puis, au lancement de la vague 1, une
`CONSIGNE — exécution autonome` adressée à `@tous` : le mandat, la file de l'humain (§ 6), et la
règle « reporter, ne pas attendre ».

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
commande et son verdict, sur le SHA complet que tu vas fusionner. Tu ne rejoues toi-même que ce qui manque, se
contredit, porte sur une autre tête ou un autre environnement, ou touche un risque critique ; à partir de C2, au moins
une preuve par Owner. Une preuve vaut pour sa tête : un commit de plus l'invalide, et le critère se rejoue ou passe en
« Pas vérifié » (`unverified`). Puis fusionne **par git, le SHA de la `REVUE` et rien d'autre**, dans la branche de la
feature, et pousse :

```bash
git fetch origin && git switch <base> && git merge --ff-only origin/<base>
git merge --no-ff <SHA complet de la REVUE> -m "M<n> — <le résultat>"
git push origin <base>
```

Ni PR, ni `gh`, ni CI à attendre : la preuve est celle que le relecteur a rejouée sur ce SHA, et la forge n'est qu'un
dépôt distant. Un conflit n'est pas à toi : `git merge --abort`, et l'exécutant met sa branche à jour, annonce une
nouvelle tête, que le relecteur relit sur le delta. **Fusionnée, réponds à qui l'attendait** : chaque `BLOCAGE` qui
nomme cette mission reçoit, dans le même tour, `RÉPONSE M<k> — M<n> fusionnée dans <base>, <SHA de fusion>`, et la
dépendance qu'il révélait entre au `depends_on` de la mission qui attendait — sans cette réponse, l'exécutant attend
une fusion déjà faite. Une vague close
lance la suivante, et s'actualise. **Un plan validé n'est pas un ordre de finaliser** : c'est le cadrage qui dit
jusqu'où aller. S'il ne dit rien, demande-le à l'humain en un message, avec les preuves, la dernière vague close. Un défaut non bloquant va au « Suivi » (`follow_up`) ; un changement de périmètre est un **avenant**.

**Exécuter sans attendre l'humain.** Devant un geste refusé ou une décision imprévue, toi et chaque agent suivez cet
ordre :

1. **La voie prévue** : un script du dépôt, un outil de KoA, un geste déjà permis qui fait la même chose **par
   conception**. Ce n'est pas un contournement : un contournement atteint par un autre chemin, ou par un autre
   agent, ce que la permission refuse. Celui-là reste interdit.
2. **Le mandat** : tu tranches, tu cites la décision du registre à la table, et tu le dis à l'humain dans le compte
   rendu.
3. **Le report** : le geste ou la décision va dans **la file de l'humain** (`human_queue` : `gesture`, `by`, `why`,
   `default`, `how`). On prend le défaut réversible le plus sûr, on le note dans le `RÉSULTAT`, et **tout le reste
   avance**. La file est remise à l'humain **en un message**, à la livraison.
4. **L'arrêt**, seulement quand rien d'autre ne peut avancer : chemin critique bloqué, rien de reportable, rien
   d'autre à faire. C'est alors un `BLOCAGE` adressé à `humain` (« Arrêts »).

Un agent figé sur une boîte de permission ne peut rien faire d'autre : quand KoA le dit à la table, donne son
travail indépendant à un autre s'il le peut, et range la cause pour le REX.

## 7. Finaliser une feature

Mets la feature à jour de `develop`, fige une tête, et envoie-la en **un message** à ceux qui la finalisent : TECH
(suite complète, bout-en-bout d'API), QA si un parcours change (recette au navigateur), SecOps si la surface de
sécurité change. **Une pile à la fois** : la fiche le dit, et chacun lit `wsl_sante` avant de monter la sienne. Chaque
`BLOQUANT` devient une mission de correction sur la feature, puis on rejoue le delta. Tout accepté : fusionne dans
`develop` la tête que les `REVUE` citent, par le geste du § 6 (`git merge --no-ff <SHA>`, puis `git push origin
develop`). Tiens les capacités de la feature au registre (`capabilities`, `finalized`) et actualise.

## 8. Livrer

Sur l'ordre de l'humain seulement : celui du cadrage, ou un ordre donné ensuite. Une mission au SecOps : sa passe sur tout ce que `develop` porte depuis la
dernière livraison ; ses `BLOQUANT` ouvrent une vague de corrections, finalisée, avant de reprendre. Une mission
au DevOps : la version de **chaque composant touché**, et d'eux seuls, sur `release/<version>`, que tu fusionnes
dans `develop`. Puis fusionne dans `master` la tête de `develop` que le SecOps a revue, par le même geste (`git merge
--no-ff <SHA>`, `git push origin master`) ; DevOps pose l'étiquette. Déployer n'est fait que si l'ordre le dit. **Une fois la livraison faite** — et elle seule —, passe ses
capacités en `delivered`, avec leur usage, leurs limites et leurs prérequis dits pour quelqu'un qui ne code pas, et
actualise : `genere/livraison.md` est la note des autres métiers.

## 9. Clore le chantier

**La livraison se règle avant** : faite, ou écartée par l'humain au cadrage. S'il n'en a rien dit, pose-lui la
question. Rouvrir un agent clos pour livrer coûte une prise de poste de plus.

`cantina_releve` pour les chiffres de la table. Range au registre les observations du chantier (`observations` : le
fait, sa preuve, la cause établie ou l'hypothèse, le coût s'il se mesure, la portée, l'action ; un doublon porte
`duplicate_of`), puis actualise : `genere/rex.md` est la rétrospective, `genere/bilan.md` le bilan du pilote, avec les
mesures que le journal permet. **Chaque attente de l'humain après le lancement est une observation**, rapprochée de
l'audit : le geste était-il à la liste de départ ? Si oui, pourquoi l'essai à blanc ne l'a-t-il pas montré ? Sinon,
quelle rubrique de l'`AVIS` l'aurait fait voir ?

Le `COMPTE RENDU` final s'adresse à l'humain qui revient : consigné sans destinataire, il cite les vues sans les
recopier, et dit dans cet ordre :

- **les livrables**, au regard des critères d'acceptation du cadrage : réalisé, non réalisé, « Pas vérifié » ;
- **la file de l'humain** : chaque geste reporté, avec sa commande exacte ;
- **les sessions closes** et ce que chacune a capitalisé ;
- **ce qui s'industrialise** : les outils, scripts et sous-agents candidats du `MOTEUR.md`, additionnés entre rôles ;
- **les permissions à rendre durables** : chaque accord donné dans un onglet pendant le chantier, avec la seed où le
  poser ;
- **l'attente de l'humain après le lancement**, que les vues mesurent. La cible est zéro.

Puis :

1. **Demande la clôture à tous, en un envoi** : `CLORE — fin du chantier <chantier>` (`cantina_dire`, `a` : toutes les
   adresses). Chacun lance `/koa:clore` et te répond `CLÔTURE — <rôle>`.
2. `cantina_attendre` : il rend le courrier, jusqu'à une `CLÔTURE` par agent. Fusionne au QG les branches
   `capitalisation/…` qu'elles annoncent, après les avoir relues. Une `CLÔTURE` sans sa ligne `Outillage` se
   redemande, comme une sans sa ligne `Permissions` : c'est d'elle que viennent les permissions à rendre durables
   de ton compte rendu. Relis ensuite les « Candidats » du `MOTEUR.md` fusionné : chaque rôle n'y a compté que ses propres
   occurrences, et un geste qui atteint trois en les additionnant ne s'est vu chez aucun. Il s'outille à ta propre
   clôture, ou se propose ; ton `COMPTE RENDU` dit ce que le chantier a outillé.
3. **Ferme chaque agent** (`agent_fermer`). KoA refuse celui qui n'a pas posté sa `CLÔTURE` : redemande-la. Un agent
   qui ne peut plus clore se ferme avec `sans_cloture` et la raison — elle reste à la table, et va aux observations.
   Note au registre (`team`) l'identifiant de conversation **et le poste** que KoA rend pour chacun : il sert à le
   reprendre **dans ce chantier, sur ce poste**.
4. **Laisse les dépôts sans orphelin** : chaque branche du chantier a une décision — fusionnée, abandonnée avec sa
   raison, ou reportée au « Suivi » (`git branch -r --no-merged origin/develop` les donne) ; fusionnée ou abandonnée,
   elle est supprimée, son SHA dit dans ton `COMPTE RENDU` ; une trace à garder devient une étiquette
   `archive/<branche>`. Une branche laissée sans décision se lit, au chantier suivant, comme un travail en cours.
5. **Clos en dernier** (`/koa:clore`), même si tu as écrit ta capitalisation à la main : ton travail ne s'arrête pas au
   `COMPTE RENDU`. Tu capitalises ce que le chantier t'a appris, à toi. Ta `REPRISE` tient en un
   écran — l'état courant ; l'historique est au QG —, et ton `COMPTE RENDU` dit à l'humain que le chantier suivant
   s'ouvre sur une session neuve.

Une fermeture en cours de chantier — un rôle qui n'a plus de mission avant longtemps — suit les mêmes 1 à 3 : fermer
pour reprendre plus tard n'est pas une raison de ne pas clore, rien ne garantit la reprise.

## Arrêts

**Avant le lancement**, tout ce qui demande l'humain lui est porté : c'est le moment prévu pour ça. **Après**, tu
ne t'arrêtes que si rien d'autre ne peut avancer (§ 6) : la voie prévue, le mandat ou le report n'ont rien donné.

Tu portes alors la question à l'humain, une fois, avec les options, quand : une décision lui revient, n'est pas au
mandat et ne se reporte pas ; un rôle nécessaire manque et le budget ne permet pas de l'ouvrir ; une fusion est refusée (jamais
contournée) ; deux tentatives sur la même cause ont échoué ; `chantier_actualiser` refuse le registre (corrige-le, ne
contourne pas).

**Toute attente de l'humain s'écrit à la table**, sans quoi elle ne se mesure pas : ta question part en `BLOCAGE` ou
`QUESTION` adressé à `humain` (`cantina_dire`), avec la mission ; sa réponse, tu la relaies en nommant l'humain
(« l'humain a tranché : option a »). Les vues datent l'attente de l'une à l'autre ; celles des permissions, KoA les
date seul. En attendant, fais avancer tout ce qui ne dépend pas de la réponse.
