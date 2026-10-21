---
name: preparer-et-realiser-un-deploiement
description: "DevOps — quand : l'approbateur de livraison (H-Liv) demande explicitement de déployer ce lot. Jamais de ta propre initiative. Pas pour : vérifier après coup (verifier-un-deploiement…)."
---

# WF-04 — Préparer et réaliser un déploiement

> **Autonomie maximale sans autorisation supplémentaire** : Niv. 2 préparation, Niv. 4 exécution en production.
>
> Cette skill porte les **gestes**. Les rubriques communes (sécurité, livrable, contenu analysé, arrêt),
> les niveaux d'autonomie et les leçons `[OBS Exx]` citées plus bas sont dans [`commun.md`](../../commun.md),
> à lire au besoin. Le **pourquoi** reste dans le profil `library://equipe/devops`.

- **Objectif** : mettre en production un artefact traçable, sans régression, avec une voie de retour.
- **Déclencheur** : **demande explicite** de l'approbateur de livraison (H-Liv), pour ce lot. L'agent peut proposer de déployer, il ne déploie jamais de sa propre initiative ; l'avis du PO sur la fenêtre ou une recommandation de QA ne valent pas autorisation **[OBS E35]**.
- **Entrées** : composants ciblés, version, contenu de la branche, état de la production.
- **Vérifications initiales** :
  1. Inventaire du **contenu réel** à livrer (et non du seul ticket demandé), y compris le retard accumulé par les autres composants **[OBS E19]**.
  2. Analyse d'impact entre composants (WF-18).
  3. Version incrémentée et cohérente avec la nature du changement **[OBS E36]**.
  4. Gates verts, sans contournement.
  5. Variables de configuration nouvelles présentes sur la cible, vérifiées par leur nom **[OBS E16]**.
  6. Ressources de la cible sous les seuils **[OBS E33]**.
  7. Sauvegarde fraîche **vue réussir** si des données sont en jeu.
- **Étapes** :
  1. Release : étiquette immuable, avec des assertions sur le dépôt, la branche et la cible. Cette étape a sa **propre approbation** de H-Liv, distincte de celle du déploiement **[OBS E35]**.
  2. Conserver l'artefact sortant pour le retour arrière, **avant** toute synchronisation **[OBS E02]**.
  3. Déployer dans l'ordre des dépendances **[OBS E34]**.
  4. Attendre la santé déclarée, en détectant la boucle de redémarrage, avec un délai propre à chaque composant **[OBS E01]**.
  5. Réconcilier les éléments dérivés (attachements réseau, routes) en tolérant les versions anciennes, pour éviter un faux échec **[OBS E37]**.
  6. Vérifier le déploiement (WF-05).
  7. Faire l'hygiène de la cible : caches, fichiers temporaires.
- **Décisions** :
  - Gate rouge : arrêt. Proposer une correction, jamais un contournement.
  - Changement de contrat cassant : déploiement additif, ou ordre par exposition réelle, ou réduction de la fenêtre **[OBS E34]**.
  - Composant point d'entrée : remise en service manuelle si elle implique une fenêtre d'indisponibilité **[OBS E13]**.
- **Sécurité** : secrets transmis hors ligne de commande. Fichiers non versionnés jamais synchronisés **[OBS E16]**. Fichiers temporaires supprimés dans la même session **[OBS E33]**.
- **Vérification** : WF-05 complet.
- **Livrables** : compte-rendu de déploiement avec versions avant et après, gates, preuves et réserves.
- **Réussite** : version servie égale à la version visée, santé prouvée, parcours critiques valides, aucune exposition nouvelle non prévue.
- **Récupération** : WF-06. Le plan de retour est rédigé avant l'étape 1.
- **Arrêt / escalade** :
  - Cible ambiguë.
  - Retour arrière indisponible sur une opération à risque élevé.
  - Données à migrer sans sauvegarde vérifiée.
  - Demande de contourner un gate.
