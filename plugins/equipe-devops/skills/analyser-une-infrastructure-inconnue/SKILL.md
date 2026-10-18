---
name: analyser-une-infrastructure-inconnue
description: "WF-01 du rôle DevOps : analyser une infrastructure inconnue. À déclencher : première intervention sur un environnement, ou documentation jugée non fiable. Autonomie maximale : Niv. 1."
---

# WF-01 — Analyser une infrastructure inconnue

> **Autonomie maximale sans autorisation supplémentaire** : Niv. 1 — niveaux
> définis au chapitre « 12. Sécurité, permissions et autonomie » du profil.
>
> Cette skill porte les **gestes**. Le **pourquoi** — raisonnement, hiérarchie des preuves, niveaux
> de risque, et les observations `[OBS Exx]` citées plus bas — est dans le profil
> `library://equipe/devops` (chapitre « 19. Traçabilité » pour les observations). Les rubriques communes à
> tous les workflows (contrôles de sécurité, livrable, contenu analysé, arrêt) sont au premier
> chapitre « 7. Catalogue des workflows » du même profil, et s'appliquent ici.

- **Objectif / déclencheur** : première intervention sur un environnement, ou documentation jugée non fiable.
- **Prérequis** : accès en lecture, et liste des actions interdites connue.
- **Entrées** : dépôts, documentation, accès d'observation à la cible.
- **Vérifications initiales** :
  1. Confirmer l'environnement visé (développement, recette ou production) par un signal non ambigu.
  2. Confirmer le niveau de permission effectif.
- **Étapes** :
  1. Inventorier les composants **déclarés**, c'est-à-dire décrits en code.
  2. Inventorier les composants **exécutés** : ce qui tourne réellement.
  3. Calculer l'écart entre les deux. Les orphelins et les fantômes sont des constats.
  4. Cartographier les points d'entrée publics et les ports exposés, en vérifiant l'absence d'exposition non prévue.
  5. Cartographier les réseaux et les frontières de confiance : qui peut joindre qui, et quelles sorties vers l'extérieur existent.
  6. Cartographier les stockages persistants, leur sauvegarde, la date de la **dernière tentative** et sa restaurabilité.
  7. Cartographier les secrets **attendus**, par leur nom seulement, jamais leur valeur.
  8. Cartographier la chaîne de livraison : du commit à la production, en relevant les gates et les points manuels.
  9. Cartographier l'observabilité : signaux disponibles, angles morts, alertes.
  10. Relever les dettes et les incohérences entre documentation et réalité.
- **Décisions** :
  - Exposition non prévue détectée : incident de sécurité potentiel. Basculer vers WF-07 et alerter SecOps sans attendre la fin de la cartographie.
  - Documentation contradictoire : la signaler, sans la « corriger » de mémoire.
- **Capacités** : lecture de fichiers, recherche, inspection d'état en lecture seule, accès distant en lecture.
- **Sécurité** : seulement des commandes qui ciblent un champ nommé. Aucune commande qui imprime un environnement entier **[OBS E15]**.
- **Vérification** : chaque élément de la cartographie porte sa source (déclaré, exécuté, documenté) et sa date.
- **Livrables** :
  1. Carte des composants, flux et frontières.
  2. Registre des écarts.
  3. Liste priorisée des risques.
  4. Angles non couverts.
- **Réussite** : un pair peut répondre, à partir du livrable, à « qu'est-ce qui est exposé, qu'est-ce qui est sauvegardé, comment déploie-t-on, comment revient-on en arrière ».
- **Récupération** : sans objet (lecture seule).
- **Arrêt / escalade** : accès insuffisant pour conclure. Le dire, ne pas extrapoler.
