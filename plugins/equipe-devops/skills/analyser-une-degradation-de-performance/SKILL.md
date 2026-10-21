---
name: analyser-une-degradation-de-performance
description: "DevOps — quand : une latence ou un débit dégradés, le service répondant encore. Pas pour : un service arrêté (diagnostiquer-une-defaillance-de-service), un consommateur qui ne joint plus rien (investiguer-un-probleme-reseau…)."
---

# WF-08 — Analyser une dégradation de performance

> **Autonomie maximale sans autorisation supplémentaire** : Niv. 1–2.
>
> Cette skill porte les **gestes**. Les rubriques communes (sécurité, livrable, contenu analysé, arrêt),
> les niveaux d'autonomie et les leçons `[OBS Exx]` citées plus bas sont dans [`commun.md`](../../commun.md),
> à lire au besoin. Le **pourquoi** reste dans le profil `library://equipe/devops`.

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
