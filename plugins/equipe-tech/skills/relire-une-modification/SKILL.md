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
6. **Classer chaque constat** :

| Gravité | Quand | Effet |
|---|---|---|
| BLOQUANT | comportement faux, faille, perte de données, contrat cassé, test faux | refus |
| MAJEUR | faux dans un cas réaliste ; erreur avalée ; règle dupliquée | refus, sauf décision écrite du propriétaire |
| MINEUR | dette, lisibilité | ne bloque pas |
| INFO | préférence | dite comme telle, jamais imposée |

Un constat : `gravité · fichier:ligne · attente violée · preuve · correction proposée`.

## Livrable

```
REVUE de <sha complet> — ACCEPTÉE | REFUSÉE
Rejoué : tests « … » · build « … »
Constats : <un par ligne, classés> | aucun
Fini quand : [x] … · [ ] …
Non couvert : <angles que la revue n'a pas regardés>
```

Une revue se rend **en un message**, sur la tête relue : c'est elle que l'orchestrateur fusionne.

## Réussite

Le verdict tient sur des preuves rejouées, et l'auteur sait quoi corriger sans reposer de question.

## Arrêt

La tête a bougé : repars de la nouvelle, ne rends pas un verdict mêlé. Un constat de sécurité hors de ta
compétence : signale-le, et demande la revue du rôle qui la tient.
