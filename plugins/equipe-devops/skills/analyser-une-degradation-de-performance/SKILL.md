---
name: analyser-une-degradation-de-performance
description: "WF-08 du rôle DevOps : analyser une dégradation de performance. À déclencher : expliquer et résorber une latence ou un débit dégradés, signalés par une mesure, une alerte ou QA (qui pilote la performance attendue ; DEV mesure en production). Autonomie maximale : Niv. 1–2."
---

# WF-08 — Analyser une dégradation de performance

> **Autonomie maximale sans autorisation supplémentaire** : Niv. 1–2 — niveaux
> définis au chapitre « 12. Sécurité, permissions et autonomie » du profil.
>
> Cette skill porte les **gestes**. Le **pourquoi** — raisonnement, hiérarchie des preuves, niveaux
> de risque, et les observations `[OBS Exx]` citées plus bas — est dans le profil
> `library://equipe/devops` (chapitre « 19. Traçabilité » pour les observations). Les rubriques communes à
> tous les workflows (contrôles de sécurité, livrable, contenu analysé, arrêt) sont au premier
> chapitre « 7. Catalogue des workflows » du même profil, et s'appliquent ici.

- **Objectif / déclencheur** : expliquer et résorber une latence ou un débit dégradés, signalés par une mesure, une alerte ou QA (qui pilote la performance attendue ; DEV mesure en production).
- **Étapes** :
  1. Objectiver la dégradation : percentiles, depuis quand, sur quel périmètre.
  2. Corréler avec les changements (une limitation de débit ou un plafond change la latence **[OBS E17]**), la charge et les ressources.
  3. Localiser le goulot : calcul, mémoire, entrées/sorties, réseau, dépendance, accès aux données (requêtes répétées par élément).
  4. Reproduire sur un environnement représentatif.
  5. Proposer un correctif dont le gain se **mesure** avant/après, à contrôles égaux **[OBS E23]**.
- **Sécurité** : jamais de test de charge sur la production sans autorisation.
- **Livrables** : diagnostic chiffré, correctif proposé, mesure avant/après.
- **Réussite** : retour sous l'objectif mesuré, sans régression ailleurs.
- **Arrêt** : correctif qui exige un changement d'architecture : passage à TECH (Architecte).
