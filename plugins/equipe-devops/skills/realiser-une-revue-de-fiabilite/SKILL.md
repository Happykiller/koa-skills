---
name: realiser-une-revue-de-fiabilite
description: "WF-19 du rôle DevOps : réaliser une revue de fiabilité. À déclencher : vérifier périodiquement que les garde-fous protègent encore. Déclenché par une échéance, un incident récidivant ou une dérive documentaire constatée. Autonomie maximale : Niv. 1."
---

# WF-19 — Réaliser une revue de fiabilité

> **Autonomie maximale sans autorisation supplémentaire** : Niv. 1 — niveaux
> définis au chapitre « 12. Sécurité, permissions et autonomie » du profil.
>
> Cette skill porte les **gestes**. Le **pourquoi** — raisonnement, hiérarchie des preuves, niveaux
> de risque, et les observations `[OBS Exx]` citées plus bas — est dans le profil
> `library://equipe/devops` (chapitre « 19. Traçabilité » pour les observations). Les rubriques communes à
> tous les workflows (contrôles de sécurité, livrable, contenu analysé, arrêt) sont au premier
> chapitre « 7. Catalogue des workflows » du même profil, et s'appliquent ici.

- **Objectif / déclencheur** : vérifier périodiquement que les garde-fous protègent encore. Déclenché par une échéance, un incident récidivant ou une dérive documentaire constatée.
- **Étapes** :
  1. Vérifier les garde-fous **en les faisant échouer**.
  2. Contrôler la restaurabilité réelle et la fraîcheur des sauvegardes.
  3. Contrôler l'homogénéité du durcissement : relever les composants en écart au profil de référence **[OBS E31]**.
  4. Rapprocher documentation et réalité : affirmations datées, affirmations périmées, compteurs faux **[OBS E40]**.
  5. Relire la dette acceptée : conditions de retrait remplies ?
  6. Vérifier la couverture d'observabilité contre l'historique des incidents.
- **Livrables** : rapport de constats priorisés (gravité BLOQUANT · MAJEUR · RISQUE · MINEUR · INFO, confiance, preuve, recommandation, propriétaire proposé).
- **Réussite** : chaque garde-fou revu a été vu échouer, ou il est signalé comme non prouvé.
- **Arrêt** : un garde-fou qu'on ne peut faire échouer sans risque sur la cible : NON_CONCLUANT, avec la raison.
