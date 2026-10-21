---
name: implementer-une-evolution
description: "Quand : ajouter une fonctionnalité ou modifier un comportement existant. Prémisse vérifiée, plus petit changement, tests au fil de l'eau, consommateurs vérifiés. Pas pour : un bug (corriger-une-anomalie), un choix d'architecture à arbitrer."
---

# Implémenter une évolution

Résoudre le problème avec **le minimum de complexité nécessaire**, et le prouver. Le plus petit
changement qui remplit les critères « Fini quand » de la mission vaut mieux qu'un changement élégant
qui en déborde.

## Étapes

1. **Confronter la demande au code**, sur une copie à jour (`git pull --ff-only` d'abord) : la prémisse
   est-elle vraie ? Ce qui existe déjà fait-il une partie du travail ? Distingue ce qui est confirmé de ce
   qui est supposé ; une ambiguïté qui change le résultat est une **question**, pas une hypothèse
   silencieuse.
2. **Lister ce que le changement touche** : contrats publiés (API, schémas, formats), données
   existantes, clients déjà en circulation, sécurité (droits, secrets). Rien de tout cela : avance.
   Un contrat ou une donnée réelle : c'est au minimum C2, dis-le à l'orchestrateur avant d'écrire.
3. **Comportement existant sans tests** : écris d'abord des tests de caractérisation, qui figent ce qu'il
   fait aujourd'hui. Sans eux, « seul le comportement visé change » ne se prouve pas.
4. **Implémenter**, une intention par commit, dans les couches et les conventions du dépôt :
   - une règle, une implémentation — offre la bonne forme plutôt que de copier ;
   - une abstraction à la **deuxième** occurrence, pas à la première ;
   - les erreurs normalisées, jamais avalées ;
   - aucune dépendance nouvelle sans justification écrite, et son API vérifiée **dans la version
     installée**.
5. **Tester au fil de l'eau** : chaque critère « Fini quand » a son test, vu échouer avant le code qui le
   fait passer. Une surface d'API se teste de bout en bout avec le rôle minimal **et** un rôle refusé.
6. **Vérifier les consommateurs** du code modifié (`grep` des appels, des champs, des types) : un diff
   correct localement peut casser ou exposer quelque chose ailleurs.
7. Livrer avec `verifier-avant-de-livrer`.

## Livrables

Le diff, les tests, et le rapport de `verifier-avant-de-livrer`.

## Réussite

Chaque critère « Fini quand » est couvert par un test vert vu rouge ; seul le comportement visé a changé.

## Arrêt / escalade

Prémisse fausse ; contrat publié ou donnée réelle touchés sans que la mission le prévoie ; décision
d'architecture à deux options sérieuses (elle se rédige en registre de décision, elle ne se tranche pas
dans un commit) ; deux tentatives sans progrès sur la même cause.
