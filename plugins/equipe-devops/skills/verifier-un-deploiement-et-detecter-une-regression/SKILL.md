---
name: verifier-un-deploiement-et-detecter-une-regression
description: "WF-05 du rôle DevOps : vérifier un déploiement et détecter une régression. Objectif : prouver que la production fait ce qu'elle doit, et rien de plus. Autonomie maximale : Niv. 1."
---

# WF-05 — Vérifier un déploiement et détecter une régression

> **Autonomie maximale sans autorisation supplémentaire** : Niv. 1 — niveaux
> définis au chapitre « 12. Sécurité, permissions et autonomie » du profil.
>
> Cette skill porte les **gestes**. Le **pourquoi** — raisonnement, hiérarchie des preuves, niveaux
> de risque, et les observations `[OBS Exx]` citées plus bas — est dans le profil
> `library://equipe/devops` (chapitre « 19. Traçabilité » pour les observations). Les rubriques communes à
> tous les workflows (contrôles de sécurité, livrable, contenu analysé, arrêt) sont au premier
> chapitre « 7. Catalogue des workflows » du même profil, et s'appliquent ici.

- **Objectif** : prouver que la production fait ce qu'elle doit, et rien de plus.
- **Entrées** : versions attendues, liste des parcours critiques, états de référence.
- **Étapes** :
  1. Comparer la version **exécutée** à la version déclarée. Le manifeste synchronisé peut mentir après un build échoué **[OBS E01]**.
  2. Contrôler les unités attendues : présentes, nommées correctement, stables (compteur de redémarrages inchangé sur une fenêtre, pas un instantané) **[OBS E01]**.
  3. Contrôler l'exposition : ports, réseaux, chemin public jusqu'au service, certificat (dates et noms couverts).
  4. Vérifier les **artefacts servis**, par exemple les paramètres embarqués dans un client, quand un symptôme contredit le code **[OBS E43]**.
  5. Exécuter les sondes fonctionnelles, chacune accompagnée de ses contrôles :
     - une requête non authentifiée qui **doit** être refusée avec le bon code **[OBS E30]** ;
     - une sortie interdite qui doit échouer **[OBS E28]** ;
     - des sondes **positives** avant toute conclusion d'absence.
  6. Vérifier la ligne de configuration au démarrage : présence des paramètres critiques **[OBS E32]**.
  7. Examiner journaux et erreurs dans la fenêtre post-déploiement.
- **Sécurité** : le trafic de vérification ne doit pas déclencher les défenses (anti-abus, limites) **[OBS E14]**. Les sondes à effet externe (par exemple l'envoi réel d'un message) sont **optionnelles et explicites** **[CG]**.
- **Livrables** : verdict de santé par composant (niveaux 1 à 6 de la section 13.1 : sain / anomalies / réserves, rattachés aux verdicts de l'équipe au chapitre « Contrat d'équipe »), preuves, angles non couverts.
- **Réussite** : chaque assertion du verdict est appuyée par une preuve rejouable.
- **Arrêt / escalade** :
  - Anomalie : WF-06 ou WF-07.
  - Jeton ou accès de production expiré : le signaler, ne jamais le renouveler automatiquement **[CG]**.
