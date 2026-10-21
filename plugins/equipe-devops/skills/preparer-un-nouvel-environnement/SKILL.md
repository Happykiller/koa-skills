---
name: preparer-un-nouvel-environnement
description: "DevOps — quand : créer un environnement (dev, recette, production) reproductible, isolé, observable et documenté avant sa mise en service."
---

# WF-02 — Préparer un nouvel environnement

> **Autonomie maximale sans autorisation supplémentaire** : Niv. 3 hors production, 4 en production.
>
> Cette skill porte les **gestes**. Les rubriques communes (sécurité, livrable, contenu analysé, arrêt),
> les niveaux d'autonomie et les leçons `[OBS Exx]` citées plus bas sont dans [`commun.md`](../../commun.md),
> à lire au besoin. Le **pourquoi** reste dans le profil `library://equipe/devops`.

- **Objectif** : un environnement reproductible, isolé, observable et documenté avant toute mise en service.
- **Entrées** : besoins fonctionnels, criticité, données hébergées, dépendances.
- **Vérifications initiales** :
  1. Fiche d'admission remplie : rôle, exposition publique ou privée, nom des unités, mode de build, ports internes, réseaux, dépendances, secrets attendus, procédure de déploiement et de vérification, impact sécurité **[OBS E46]**.
  2. Collision de noms ou de ports avec l'existant vérifiée.
- **Étapes** :
  1. Décrire l'environnement en code.
  2. Isoler le réseau : rejoindre uniquement les réseaux justifiés, aucune exposition directe si un point d'entrée suffit.
  3. Appliquer le profil de durcissement d'exécution, en justifiant chaque écart.
  4. Définir la sonde de santé (réelle, applicative) et son délai de démarrage.
  5. Prévoir les journaux persistants, leur rotation et la minimisation des données.
  6. Définir la sauvegarde et la restauration si le composant a un état.
  7. Évaluer le côté hôte pour les composants à état : paramètres système requis, limites de descripteurs.
  8. **Déclarer le composant dans tous les outillages et listes** qui énumèrent les composants **[OBS E46]**.
- **Décisions** :
  - Besoin de sortie internet : la cantonner au sous-composant qui l'exige, jamais au composant qui détient les données **[OBS E28]**.
- **Sécurité** : secrets propres à chaque environnement, jamais réutilisés entre développement et production.
- **Vérification** :
  1. Démarrage à froid sain.
  2. Isolement **prouvé** : une sortie interdite échoue, une sortie autorisée réussit **[OBS E28]**.
  3. Restauration testée.
- **Livrables** : code d'environnement, fiche d'admission, runbook, entrée dans les listes d'outillage.
- **Réussite** : quelqu'un qui ne l'a pas construit peut le recréer depuis le code et la fiche.
- **Récupération** : destruction et recréation depuis le code, hors données.
- **Arrêt / escalade** : donnée sensible soumise à une contrainte réglementaire éventuelle non instruite : décision du propriétaire du risque (H-Risk), après avis de l'évaluateur juridique **[OBS E42]**.
