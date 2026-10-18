---
name: traiter-une-anomalie-de-configuration
description: "WF-11 du rôle DevOps : traiter une anomalie de configuration. À déclencher : rétablir une configuration qui ne fait pas ce qu'elle annonce (protection inopérante, repli silencieux, écart entre environnements). Autonomie maximale : Niv. 2–3 hors production, Niv. 4 en production."
---

# WF-11 — Traiter une anomalie de configuration

> **Autonomie maximale sans autorisation supplémentaire** : Niv. 2–3 hors production, Niv. 4 en production — niveaux
> définis au chapitre « 12. Sécurité, permissions et autonomie » du profil.
>
> Cette skill porte les **gestes**. Le **pourquoi** — raisonnement, hiérarchie des preuves, niveaux
> de risque, et les observations `[OBS Exx]` citées plus bas — est dans le profil
> `library://equipe/devops` (chapitre « 19. Traçabilité » pour les observations). Les rubriques communes à
> tous les workflows (contrôles de sécurité, livrable, contenu analysé, arrêt) sont au premier
> chapitre « 7. Catalogue des workflows » du même profil, et s'appliquent ici.

- **Objectif / déclencheur** : rétablir une configuration qui ne fait pas ce qu'elle annonce (protection inopérante, repli silencieux, écart entre environnements).
- **Étapes** :
  1. Comparer quatre états : écrit, résolu, appliqué, observé.
  2. Chercher les champs qui ne font pas ce que leur nom annonce (un paramètre jamais transmis) **[OBS E16]**.
  3. Chercher les gardes qui laissent passer une valeur vide **[OBS E16]**.
  4. Vérifier le statut de versionnement : un fichier ignoré par le gestionnaire de version mais déployé quand même rend la production dépendante du poste qui déploie **[OBS E16]**.
  5. Corriger à la source. Rendre la configuration manquante **bloquante au démarrage** si elle est critique.
- **Vérification** : un test prouve que le contrôle **bloque**, pas seulement qu'il est câblé.
- **Arrêt** : configuration de sécurité dont la valeur cible n'est pas tranchée : SecOps.
