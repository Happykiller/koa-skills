---
name: corriger-une-anomalie
description: "Quand : un bug, un comportement faux, un test rouge à expliquer. Test rouge d'abord, cause racine, correction à la source, tests touchés. Pas pour : une évolution (implementer-une-evolution), un incident en production (equipe-devops)."
---

# Corriger une anomalie

Une correction sans test qui l'a vue échouer est une supposition. Celle-ci se prouve en deux sorties :
**rouge avant, vert après**, sans que le test ait bougé entre les deux.

## Étapes

1. **Reproduire par un test** qui échoue **avec le message observé** — pas un test qui passe déjà, pas un
   test qui affirme le défaut. Lance-le, et garde sa sortie rouge.
   - Impossible à reproduire après deux tentatives : arrête-toi, dis ce qui a été essayé, demande
     (données, environnement, étapes). Ne corrige pas à l'aveugle.
2. **Remonter à la couche racine.** Le symptôme apparaît souvent loin de la cause : une frontière qui
   n'a pas validé, une règle de données, une hypothèse d'instance unique. Cherche **plusieurs** causes
   possibles avant d'en retenir une.
3. **Corriger à la source**, une seule intention, dans les conventions du dépôt. Pas de contournement au
   point d'apparition qui laisserait la cause en place.
   - La cause est dans la **donnée** existante : la correction comprend une règle de données et une
     migration prouvée en développement (aller, retour, idempotente) — jamais exécutée en production
     par toi.
4. **Le même test passe, inchangé.** Le modifier pour obtenir du vert annule la preuve.
5. **Les tests touchés passent**, et le build — ceux des modules modifiés et de ce qui en dépend directement ; la
   suite complète se joue à la **finalisation** (livre `equipe/table`, « Finaliser et livrer »). Une suite qui ne
   compile plus est absente, pas verte : vide les caches de compilation des tests avant de croire un vert.
6. Livrer avec `verifier-avant-de-livrer`.

## Livrables

- Le diff, une intention.
- Les deux sorties : le test rouge avant la correction, les tests touchés verts après.
- La cause racine en une phrase, et les autres causes écartées.

## Réussite

Test rouge avant, vert après sans retouche ; tests touchés verts ; aucun contournement résiduel.

## Arrêt / escalade

Non reproductible après deux tentatives ; correction qui change un contrat publié ou des données réelles ;
cause hors de ton périmètre (autre dépôt, infrastructure, sécurité).
