---
name: effectuer-une-analyse-post-incident
description: "WF-20 du rôle DevOps : effectuer une analyse post-incident. À déclencher : qu'un incident ne se reproduise pas. Déclenché par la clôture d'un incident (section 13.3). Autonomie maximale : Niv. 2."
---

# WF-20 — Effectuer une analyse post-incident

> **Autonomie maximale sans autorisation supplémentaire** : Niv. 2 — niveaux
> définis au chapitre « 12. Sécurité, permissions et autonomie » du profil.
>
> Cette skill porte les **gestes**. Le **pourquoi** — raisonnement, hiérarchie des preuves, niveaux
> de risque, et les observations `[OBS Exx]` citées plus bas — est dans le profil
> `library://equipe/devops` (chapitre « 19. Traçabilité » pour les observations). Les rubriques communes à
> tous les workflows (contrôles de sécurité, livrable, contenu analysé, arrêt) sont au premier
> chapitre « 7. Catalogue des workflows » du même profil, et s'appliquent ici.

- **Objectif / déclencheur** : qu'un incident ne se reproduise pas. Déclenché par la clôture d'un incident (section 13.3).
- **Étapes** :
  1. Chronologie factuelle.
  2. Impact.
  3. Cause racine, en marquant ce qui est démontré et ce qui est inféré.
  4. **Pourquoi les garde-fous existants ne l'ont pas vu.**
  5. Principe généralisable.
  6. Invariant structurel qui empêche la récidive : test, assertion, contrôle bloquant, statut honnête.
  7. Mise à jour des runbooks et de la base de connaissances, **proposée** puis validée **[OBS E25]**.
- **Ton** : sans culpabilité. On analyse le système, pas la personne.
- **Livrables** : post-mortem, actions préventives avec propriétaire et échéance.
- **Réussite** : l'invariant est en place et a été vu échouer sur le cas de l'incident.
