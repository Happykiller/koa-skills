---
name: analyser-les-risques-d-un-changement
description: "WF-18 du rôle DevOps : analyser les risques d'un changement. À déclencher : connaître, avant de livrer, l'angle opérationnel d'un changement : ordre, simultanéité, réversibilité, rayon d'impact. Déclenché par toute préparation de déploiement (WF-04). L'impact technique sur le code et les contrats est le livrable de TECH : l'agent le consomme, il ne le refait pas. Autonomie maximale : Niv. 1."
---

# WF-18 — Analyser les risques d'un changement

> **Autonomie maximale sans autorisation supplémentaire** : Niv. 1 — niveaux
> définis au chapitre « 12. Sécurité, permissions et autonomie » du profil.
>
> Cette skill porte les **gestes**. Le **pourquoi** — raisonnement, hiérarchie des preuves, niveaux
> de risque, et les observations `[OBS Exx]` citées plus bas — est dans le profil
> `library://equipe/devops` (chapitre « 19. Traçabilité » pour les observations). Les rubriques communes à
> tous les workflows (contrôles de sécurité, livrable, contenu analysé, arrêt) sont au premier
> chapitre « 7. Catalogue des workflows » du même profil, et s'appliquent ici.

- **Objectif / déclencheur** : connaître, avant de livrer, l'angle **opérationnel** d'un changement : ordre, simultanéité, réversibilité, rayon d'impact. Déclenché par toute préparation de déploiement (WF-04). L'impact technique sur le code et les contrats est le livrable de TECH : l'agent le consomme, il ne le refait pas.
- **Entrées** : un diff ou une intention, et l'analyse d'impact de TECH quand elle existe.
- **Étapes** :
  1. Composants touchés, directement et par couplage :
     - formats partagés ;
     - routes consommées par d'autres composants ;
     - fichiers montés entre composants ;
     - modèles de messages ;
     - rattachements réseau ;
     - contenus servis par plusieurs composants.
  2. Changements à livrer **ensemble** (lockstep).
  3. Grille de risque de la section 5.3.
  4. Ordre de déploiement et compatibilité de contrat.
  5. Seuil de déclenchement des revues annexes (juridique, sécurité) : uniquement si le changement modifie **substantiellement** ce que l'utilisateur voit, confie ou se voit promettre **[OBS E35]**.
- **Livrables** : liste d'impacts priorisée avec preuves (références de fichiers), changements couplés, ordre recommandé, angles non couverts.
- **Réussite** : aucun couplage connu omis ; chaque changement à livrer ensemble est nommé.
- **Arrêt** : couplage dont la compatibilité ne peut être établie : NON_CONCLUANT, remonté à TECH.
