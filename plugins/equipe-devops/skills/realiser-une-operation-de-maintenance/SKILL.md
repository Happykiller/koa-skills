---
name: realiser-une-operation-de-maintenance
description: "WF-14 du rôle DevOps : réaliser une opération de maintenance. À déclencher : exécuter une intervention planifiée (mise à niveau, purge, migration, redémarrage) sans perte ni surprise. Autonomie maximale : Niv. 4 en production."
---

# WF-14 — Réaliser une opération de maintenance

> **Autonomie maximale sans autorisation supplémentaire** : Niv. 4 en production — niveaux
> définis au chapitre « 12. Sécurité, permissions et autonomie » du profil.
>
> Cette skill porte les **gestes**. Le **pourquoi** — raisonnement, hiérarchie des preuves, niveaux
> de risque, et les observations `[OBS Exx]` citées plus bas — est dans le profil
> `library://equipe/devops` (chapitre « 19. Traçabilité » pour les observations). Les rubriques communes à
> tous les workflows (contrôles de sécurité, livrable, contenu analysé, arrêt) sont au premier
> chapitre « 7. Catalogue des workflows » du même profil, et s'appliquent ici.

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
