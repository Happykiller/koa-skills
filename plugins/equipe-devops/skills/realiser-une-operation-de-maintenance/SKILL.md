---
name: realiser-une-operation-de-maintenance
description: "DevOps — quand : une intervention planifiée — mise à niveau, purge, migration, redémarrage — à mener sans perte ni surprise."
---

# WF-14 — Réaliser une opération de maintenance

> **Autonomie maximale sans autorisation supplémentaire** : Niv. 4 en production.
>
> Cette skill porte les **gestes**. Les rubriques communes (sécurité, livrable, contenu analysé, arrêt),
> les niveaux d'autonomie et les leçons `[OBS Exx]` citées plus bas sont dans [`commun.md`](../../commun.md),
> à lire au besoin. Le **pourquoi** reste dans le profil `library://equipe/devops`.

- **Objectif / déclencheur** : exécuter une intervention planifiée (mise à niveau, purge, migration, redémarrage) sans perte ni surprise.
- **Étapes** :
  1. Plan écrit : étapes, postconditions, critère d'abandon, voie de retour.
  2. Fenêtre proposée au PO (impact métier), opération autorisée par H-Liv.
  3. Sauvegarde fraîche vue réussir.
  4. Vérifier qu'**aucun traitement n'est en cours** avant d'arrêter ou recréer un composant asynchrone **[OBS E17]**.
  5. Exécuter pas à pas en vérifiant chaque postcondition.
  6. WF-05.
  7. Hygiène : purges sûres, fichiers temporaires, privilèges temporaires retirés **[OBS E35]**.
- **Après un redémarrage d'hôte** : vérifier que d'anciens services ne reprennent pas les ressources (ports) du service légitime, et que les réconciliations sont exécutées **[OBS E13]**.
- **Arrêt** : écart à une postcondition. On s'arrête, on n'improvise pas.
