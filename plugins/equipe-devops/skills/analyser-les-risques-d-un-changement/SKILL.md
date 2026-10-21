---
name: analyser-les-risques-d-un-changement
description: "DevOps — quand : avant de livrer, juger l'ordre, la simultanéité, la réversibilité et le rayon d'impact d'un changement. Pas pour : l'impact sur le code et les contrats (rôle Tech)."
---

# WF-18 — Analyser les risques d'un changement

> **Autonomie maximale sans autorisation supplémentaire** : Niv. 1.
>
> Cette skill porte les **gestes**. Les rubriques communes (sécurité, livrable, contenu analysé, arrêt),
> les niveaux d'autonomie et les leçons `[OBS Exx]` citées plus bas sont dans [`commun.md`](../../commun.md),
> à lire au besoin. Le **pourquoi** reste dans le profil `library://equipe/devops`.

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
