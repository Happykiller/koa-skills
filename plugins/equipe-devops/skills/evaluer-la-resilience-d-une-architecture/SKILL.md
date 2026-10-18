---
name: evaluer-la-resilience-d-une-architecture
description: "WF-16 du rôle DevOps : évaluer la résilience d'une architecture. À déclencher : connaître ce qui casse et ce qui ne se voit pas, avant que cela arrive. Déclenché par une nouvelle architecture, un incident de dépendance ou une revue de fiabilité. Autonomie maximale : Niv. 1–2."
---

# WF-16 — Évaluer la résilience d'une architecture

> **Autonomie maximale sans autorisation supplémentaire** : Niv. 1–2 — niveaux
> définis au chapitre « 12. Sécurité, permissions et autonomie » du profil.
>
> Cette skill porte les **gestes**. Le **pourquoi** — raisonnement, hiérarchie des preuves, niveaux
> de risque, et les observations `[OBS Exx]` citées plus bas — est dans le profil
> `library://equipe/devops` (chapitre « 19. Traçabilité » pour les observations). Les rubriques communes à
> tous les workflows (contrôles de sécurité, livrable, contenu analysé, arrêt) sont au premier
> chapitre « 7. Catalogue des workflows » du même profil, et s'appliquent ici.

- **Objectif / déclencheur** : connaître ce qui casse et ce qui ne se voit pas, avant que cela arrive. Déclenché par une nouvelle architecture, un incident de dépendance ou une revue de fiabilité.
- **Étapes** :
  1. Pour chaque composant, lister :
     - pannes possibles ;
     - effet sur les autres ;
     - détectabilité ;
     - procédure de reprise ;
     - point unique de défaillance.
  2. Pour chaque frontière : que se passe-t-il si la dépendance est absente, lente ou renvoie des erreurs ?
  3. Essais de résilience **mesurés** sur un environnement non productif : retirer une dépendance, vérifier que la dégradation reste isolée **[OBS E13]**.
  4. Pour chaque donnée : quel scénario de perte est couvert, lequel ne l'est pas.
- **Livrables** : matrice de défaillances, liste priorisée des points uniques, recommandations chiffrées.
- **Réussite** : chaque composant a son mode de défaillance silencieux identifié, et chaque point unique un propriétaire de décision.
- **Arrêt** : un essai de résilience qui exigerait la production : il n'a pas lieu sans autorisation de H-Liv.
