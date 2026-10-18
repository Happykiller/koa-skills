---
name: rollback-ou-roll-forward
description: "WF-06 du rôle DevOps : rollback ou roll-forward. Objectif : rétablir le service le plus vite possible avec le moins de risque. À déclencher : régression confirmée par WF-05 ou WF-07. Autonomie maximale : Niv. 4."
---

# WF-06 — Rollback ou roll-forward

> **Autonomie maximale sans autorisation supplémentaire** : Niv. 4 — niveaux
> définis au chapitre « 12. Sécurité, permissions et autonomie » du profil.
>
> Cette skill porte les **gestes**. Le **pourquoi** — raisonnement, hiérarchie des preuves, niveaux
> de risque, et les observations `[OBS Exx]` citées plus bas — est dans le profil
> `library://equipe/devops` (chapitre « 19. Traçabilité » pour les observations). Les rubriques communes à
> tous les workflows (contrôles de sécurité, livrable, contenu analysé, arrêt) sont au premier
> chapitre « 7. Catalogue des workflows » du même profil, et s'appliquent ici.

- **Objectif** : rétablir le service le plus vite possible avec le moins de risque.
- **Déclencheur** : régression confirmée par WF-05 ou WF-07.
- **Vérifications initiales** :
  1. Artefacts de repli disponibles.
  2. Migration de données intervenue depuis la version de repli, ou non.
  3. Compatibilité du schéma de données avec l'ancienne version.
- **Décisions** :
  - **Rollback** si l'artefact précédent existe, que les données sont compatibles en arrière et que la cause n'est pas connue avec certitude.
  - **Roll-forward** si une migration irréversible est passée, si la plateforme n'offre pas de retour (magasin d'applications **[CG]**), ou si le correctif est trivial, prouvé et plus sûr.
- **Étapes (rollback)** :
  1. Annoncer l'opération.
  2. Basculer sur l'artefact conservé, sans reconstruction.
  3. Attendre la santé.
  4. Exécuter WF-05.
  5. **Corriger la source avant tout redéploiement** : un retour concerne l'artefact, pas le code, et un redéploiement reconstruirait la version cassée **[OBS E02]**.
- **Sécurité** : jamais de suppression de données pour « revenir ». Une migration inverse ne s'exécute qu'avec une sauvegarde préalable et une autorisation.
- **Livrables** : chronologie, version active, cause présumée ou démontrée, actions de suivi.
- **Réussite** : service rétabli et mesuré, plus aucune boucle de redémarrage, état documenté.
- **Arrêt / escalade** : aucun artefact de repli et pas de correctif sûr. Escalade immédiate à H-Liv avec options chiffrées.
