---
name: verifier-avant-de-livrer
description: "Quand : avant d'annoncer « fini », de livrer une tête ou de demander une revue. Diff relu, tests et build lancés et cités, critères cochés, « Pas vérifié » écrit. Pas pour : relire le travail d'un autre (relire-une-modification)."
---

# Vérifier avant de livrer

**Aucune modification n'est annoncée faite si ses vérifications n'ont pas été exécutées.** Une compilation
verte n'est pas une preuve, un test qu'on n'a pas lancé n'existe pas, et ce qu'on n'a pas vérifié se dit.
Ce geste coûte quelques minutes ; un « fini » faux coûte une revue refusée, une relance et un tour de plus
pour toute l'équipe.

## Étapes

1. **Relire le diff réel** (`git diff` contre la base, pas sa mémoire de ce qu'on a écrit) :
   - une seule intention ; aucun fichier hors sujet, aucun reste de débogage, aucun `TODO` nouveau
     non dit ;
   - aucun secret, aucun chemin personnel — un secret vit au coffre du cluster, et le code ne le lit que
     depuis l'environnement ;
   - aucun test supprimé, affaibli ou marqué « ignoré » pour obtenir du vert.
2. **Lancer, pour de vrai**, les contrôles du dépôt (sa `CLAUDE.md` ou son README les nomme) :
   analyse statique, typage — tests compris —, **les tests de ce que tu as touché** (modules modifiés et ce
   qui en dépend directement), build. La suite complète se joue à la **finalisation** de la feature, pas à
   chaque mission (livre `equipe/table`, « Finaliser et livrer »). Garde la dernière ligne de chaque sortie. Avant de croire un vert, vide les caches de compilation des tests.
3. **Cocher chaque critère « Fini quand »** de la mission, un par un, avec sa preuve : le test qui le
   couvre, la commande qui le montre, la capture d'un écran cliqué. Un critère sans preuve n'est pas
   coché.
4. **Selon ce qui a changé** :
   - un contrat publié : régénéré, et ses consommateurs vérifiés ;
   - une surface d'API : un bout-en-bout réel avec le rôle minimal et un rôle refusé ;
   - un écran : le scénario cliqué ;
   - des données : migration prouvée aller, retour, idempotente.
5. **Écrire « Pas vérifié »** : ce que tu n'as pas pu exécuter, et pourquoi. Jamais vide par politesse :
   « rien » se justifie.
6. **Livrer la tête** (le SHA complet) avec ce rapport, en un seul message — c'est lui que le relecteur
   rejoue.

## Livrable — le rapport, tel quel

```
Tête : <sha complet>
Fini quand : [x] <critère> — <preuve> · [x] … · [ ] <critère> — pas fait : <raison>
Contrôles : tests « <dernière ligne> » · build « … » · lint « … »
Pas vérifié : <ce qui ne l'a pas été, et pourquoi> | rien — <pourquoi rien>
Risques : <ce qu'un relecteur doit regarder en premier>
```

## Réussite

Le relecteur n'a rien à reconstruire : il rejoue les contrôles et trouve les mêmes sorties.

## Arrêt

Un contrôle rouge que tu ne sais pas corriger dans ta mission : livre-le **rouge, dit comme tel**, avec ce
que tu as essayé — jamais vert par omission.
