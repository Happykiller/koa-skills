---
name: effectuer-une-analyse-post-incident
description: "DevOps — quand : un incident vient d'être clos. Chronologie, causes, actions pour qu'il ne se reproduise pas."
---

# WF-20 — Effectuer une analyse post-incident

> **Autonomie maximale sans autorisation supplémentaire** : Niv. 2.
>
> Cette skill porte les **gestes**. Les rubriques communes (sécurité, livrable, contenu analysé, arrêt),
> les niveaux d'autonomie et les leçons `[OBS Exx]` citées plus bas sont dans [`commun.md`](../../commun.md),
> à lire au besoin. Le **pourquoi** reste dans le profil `library://equipe/devops`.

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
