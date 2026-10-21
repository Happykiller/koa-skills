---
name: diagnostiquer-une-defaillance-de-service
description: "DevOps — quand : un service précis arrêté, en boucle de redémarrage, en échec de santé ou « sain » mais inutile, hors urgence. Pas pour : une production touchée maintenant (diagnostiquer-un-incident-de-production)."
---

# WF-10 — Diagnostiquer une défaillance de service

> **Autonomie maximale sans autorisation supplémentaire** : Niv. 1–2 ; correctif : Niv. 3 hors production, Niv. 4 en production.
>
> Cette skill porte les **gestes**. Les rubriques communes (sécurité, livrable, contenu analysé, arrêt),
> les niveaux d'autonomie et les leçons `[OBS Exx]` citées plus bas sont dans [`commun.md`](../../commun.md),
> à lire au besoin. Le **pourquoi** reste dans le profil `library://equipe/devops`.

- **Objectif / déclencheur** : trouver la cause d'un service arrêté, en boucle de redémarrage, en échec de santé, ou « sain » mais inutile.
- **Étapes** :
  1. État de l'unité : en marche, boucle de redémarrage, en échec de santé ou arrêtée.
  2. Extraire la **cause** des journaux (fin du journal), pas seulement le symptôme **[OBS E01]**.
  3. Vérifier les causes silencieuses classiques :
     - permissions ou propriétaire d'un volume incompatibles avec un exécutable non privilégié privé de ses capacités. Résultat : « sain » mais n'écrit rien **[OBS E31]** ;
     - ressource manquante dans l'artefact (fichier non copié dans l'image) **[OBS E01]** ;
     - configuration absente avec repli silencieux **[OBS E32]** ;
     - dépendance démarrée mais pas prête.
  4. Reproduire en environnement de développement si possible, avec un test qui échoue avec le même message **[OBS E44]**.
- **Livrables** : cause démontrée, correctif à la couche racine, test de non-régression.
- **Arrêt** : correctif qui exige un changement applicatif : délégation à TECH (mode Développeur), avec le test reproducteur.
