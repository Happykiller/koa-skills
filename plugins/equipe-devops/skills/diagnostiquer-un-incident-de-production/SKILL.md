---
name: diagnostiquer-un-incident-de-production
description: "WF-07 du rôle DevOps : diagnostiquer un incident de production. À déclencher : restaurer le service, puis comprendre. Déclenché par une alerte, un signalement ou une anomalie relevée par WF-05. Autonomie maximale : Niv. 1 diagnostic, Niv. 4 confinement."
---

# WF-07 — Diagnostiquer un incident de production

> **Autonomie maximale sans autorisation supplémentaire** : Niv. 1 diagnostic, Niv. 4 confinement — niveaux
> définis au chapitre « 12. Sécurité, permissions et autonomie » du profil.
>
> Cette skill porte les **gestes**. Le **pourquoi** — raisonnement, hiérarchie des preuves, niveaux
> de risque, et les observations `[OBS Exx]` citées plus bas — est dans le profil
> `library://equipe/devops` (chapitre « 19. Traçabilité » pour les observations). Les rubriques communes à
> tous les workflows (contrôles de sécurité, livrable, contenu analysé, arrêt) sont au premier
> chapitre « 7. Catalogue des workflows » du même profil, et s'appliquent ici.

- **Objectif / déclencheur** : restaurer le service, puis comprendre. Déclenché par une alerte, un signalement ou une anomalie relevée par WF-05.
- **Étapes** :
  1. **Qualifier** :
     - impact (qui est touché, depuis quand, quelles fonctions) ;
     - gravité ;
     - ouvrir une chronologie horodatée.
  2. **Écarter les faux incidents** :
     - mesure sur le mauvais environnement **[OBS E18]** ;
     - auto-sanction par ses propres sondes **[OBS E14]** ;
     - outil de mesure défaillant **[OBS E20]**.
  3. **Corréler avec les changements récents** : déploiements, configuration, redémarrage d'hôte, rotation de secret, limites ajoutées.
  4. **Formuler des hypothèses discriminantes** et les tester de la moins chère à la plus chère.
  5. **Confiner** : correction chirurgicale et réversible plutôt que redéploiement global **[OBS E13]**. Retour arrière si une régression de version est probable. En production, c'est une opération de niveau 4 : autorisation de H-Liv, sauf procédure d'urgence préalablement autorisée par lui.
  6. **Mesurer la restauration.**
  7. **Préserver les preuves** :
     - les journaux avant toute recréation d'unité, car ils disparaissent avec elle **[OBS E17]** ;
     - aucun traitement en cours ne doit être tué par une recréation.
  8. Passer en analyse post-incident (WF-20).
- **Sécurité** : en cas de suspicion de compromission, confiner avant de diagnostiquer, préserver les preuves et alerter SecOps, qui prend la direction technique de l'incident (section 13.3).
- **Livrables** : chronologie, statut, actions entreprises, prochaines étapes.
- **Réussite** : service rétabli, cause identifiée ou hypothèses explicitement ouvertes.
- **Arrêt / escalade** : perte de données possible, compromission suspectée, impact au-delà du périmètre de l'agent.
