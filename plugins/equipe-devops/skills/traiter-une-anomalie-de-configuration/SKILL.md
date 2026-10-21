---
name: traiter-une-anomalie-de-configuration
description: "DevOps — quand : une configuration ne fait pas ce qu'elle annonce : protection inopérante, repli silencieux, écart entre environnements."
---

# WF-11 — Traiter une anomalie de configuration

> **Autonomie maximale sans autorisation supplémentaire** : Niv. 2–3 hors production, Niv. 4 en production.
>
> Cette skill porte les **gestes**. Les rubriques communes (sécurité, livrable, contenu analysé, arrêt),
> les niveaux d'autonomie et les leçons `[OBS Exx]` citées plus bas sont dans [`commun.md`](../../commun.md),
> à lire au besoin. Le **pourquoi** reste dans le profil `library://equipe/devops`.

- **Objectif / déclencheur** : rétablir une configuration qui ne fait pas ce qu'elle annonce (protection inopérante, repli silencieux, écart entre environnements).
- **Étapes** :
  1. Comparer quatre états : écrit, résolu, appliqué, observé.
  2. Chercher les champs qui ne font pas ce que leur nom annonce (un paramètre jamais transmis) **[OBS E16]**.
  3. Chercher les gardes qui laissent passer une valeur vide **[OBS E16]**.
  4. Vérifier le statut de versionnement : un fichier ignoré par le gestionnaire de version mais déployé quand même rend la production dépendante du poste qui déploie **[OBS E16]**.
  5. Corriger à la source. Rendre la configuration manquante **bloquante au démarrage** si elle est critique.
- **Vérification** : un test prouve que le contrôle **bloque**, pas seulement qu'il est câblé.
- **Arrêt** : configuration de sécurité dont la valeur cible n'est pas tranchée : SecOps.
