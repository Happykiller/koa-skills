---
name: mettre-en-place-une-strategie-d-observabilite
description: "WF-12 du rôle DevOps : mettre en place une stratégie d'observabilité. À déclencher : qu'aucune défaillance connue ne passe inaperçue. Déclenché par un nouvel environnement, un incident non détecté ou une revue de fiabilité (WF-19). Autonomie maximale : Niv. 2–3."
---

# WF-12 — Mettre en place une stratégie d'observabilité

> **Autonomie maximale sans autorisation supplémentaire** : Niv. 2–3 — niveaux
> définis au chapitre « 12. Sécurité, permissions et autonomie » du profil.
>
> Cette skill porte les **gestes**. Le **pourquoi** — raisonnement, hiérarchie des preuves, niveaux
> de risque, et les observations `[OBS Exx]` citées plus bas — est dans le profil
> `library://equipe/devops` (chapitre « 19. Traçabilité » pour les observations). Les rubriques communes à
> tous les workflows (contrôles de sécurité, livrable, contenu analysé, arrêt) sont au premier
> chapitre « 7. Catalogue des workflows » du même profil, et s'appliquent ici.

- **Objectif / déclencheur** : qu'aucune défaillance connue ne passe inaperçue. Déclenché par un nouvel environnement, un incident non détecté ou une revue de fiabilité (WF-19).
- **Étapes** :
  1. Partir des **modes de défaillance** (WF-16). Pour chacun, quel signal le révélerait, et en combien de temps ?
  2. Signaux minimaux :
     - santé applicative ;
     - taux d'erreur et latence des parcours critiques ;
     - saturation des ressources ;
     - fraîcheur des tâches périodiques, en particulier la **dernière tentative** de sauvegarde ;
     - échecs des traitements asynchrones.
  3. Journaux : structure, liste fermée de champs, minimisation des données personnelles, rétention par finalité, persistance, rotation.
  4. Ligne de configuration au démarrage, sans valeurs.
  5. Alertes : sur symptôme ou risque imminent, avec propriétaire et runbook, seuils calibrés sur des données réelles **[OBS E12]**.
  6. Sonde externe de disponibilité **[REC]**.
  7. Pour chaque indicateur : identifier qui le lit et ce qu'il compte réellement **[OBS E21]**.
- **Sécurité** : les journaux ne contiennent ni secret ni jeton. Les chemins sans paramètres de requête **[OBS E32]**.
- **Livrables** : matrice mode de défaillance → signal → alerte → runbook.
- **Réussite** : chaque incident historique aurait été détecté par un signal.
