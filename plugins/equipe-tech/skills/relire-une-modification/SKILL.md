---
name: relire-une-modification
description: "Quand : on te demande la REVUE d'une tête ou d'une PR. Preuves rejouées, lecture du diff et de ses consommateurs, constats classés, verdict. Pas pour : vérifier ton propre travail (verifier-avant-de-livrer)."
---

# Relire une modification

Une revue vaut par ce qu'elle **rejoue**, pas par ce qu'elle lit dans le rapport de l'auteur. Elle porte
sur **une tête figée** : si la tête bouge pendant la revue, la revue repart de la nouvelle tête, ou se
rend sur l'ancienne en le disant.

## Étapes

1. **Fixer la tête** : le SHA complet que l'auteur a livré, `git fetch` puis `git checkout <sha>`.
2. **Rejouer les contrôles** du rapport — tests, build, lint — et comparer les sorties. Un test qui
   couvre un défaut corrigé se voit échouer **sans** la correction avant d'être cru : un test peut
   affirmer le défaut au lieu de le détecter.
3. **Lire le diff** : correction, cas limites, erreurs avalées, sécurité (autorisation unique et au bon
   endroit, secrets), compatibilité, complexité ajoutée, tests.
4. **Lire en travers** : qui consomme le contrat, le type, le champ touché ? Certains défauts — une donnée
   exposée ailleurs — ne se voient qu'en dehors du diff.
5. **Cocher les « Fini quand »** de la mission contre leurs preuves.
6. **Classer chaque constat** dans les deux classes de la table :

| Classe | Quand | Effet |
|---|---|---|
| BLOQUANT | comportement faux, faille, perte de données, contrat cassé, test faux ; faux dans un cas réaliste, erreur avalée, règle dupliquée | refus |
| SUIVI | dette, lisibilité ; une préférence, dite comme telle | va au plan, ne bloque pas |

Un constat : `gravité · fichier:ligne · attente violée · preuve · correction proposée`.

## Livrable

La `REVUE` au format du livre `equipe/table` (« La revue »), qui fait foi : ce geste ne le recopie pas. Deux
points s'y perdent le plus :

- elle **commence par l'identifiant de la mission** — `REVUE M3 — <verdict>, sur <SHA complet>` : sans lui, KoA
  ne clôt pas ta mission de relecture ;
- son verdict est l'un de ceux de la table — `ACCEPTÉ`, `ACCEPTÉ_AVEC_RÉSERVES`, `REFUSÉ`, `NON_CONCLUANT` —,
  aucun autre.

Une revue se rend **en un message**, sur la tête relue : c'est elle que l'orchestrateur fusionne. Hors d'une
table, les mêmes rubriques, sans l'identifiant.

## Réussite

Le verdict tient sur des preuves rejouées, et l'auteur sait quoi corriger sans reposer de question.

## Arrêt

La tête a bougé : repars de la nouvelle, ne rends pas un verdict mêlé. Un constat de sécurité hors de ta
compétence : signale-le, et demande la revue du rôle qui la tient.
