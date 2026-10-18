---
name: investiguer-un-probleme-reseau-ou-de-connectivite
description: "WF-09 du rôle DevOps : investiguer un problème réseau ou de connectivité. À déclencher : trouver le point de rupture quand un consommateur ne joint plus un service (délai, refus, non-réponse). Autonomie maximale : Niv. 1–2 ; correctif : Niv. 3 hors production, Niv. 4 en production."
---

# WF-09 — Investiguer un problème réseau ou de connectivité

> **Autonomie maximale sans autorisation supplémentaire** : Niv. 1–2 ; correctif : Niv. 3 hors production, Niv. 4 en production — niveaux
> définis au chapitre « 12. Sécurité, permissions et autonomie » du profil.
>
> Cette skill porte les **gestes**. Le **pourquoi** — raisonnement, hiérarchie des preuves, niveaux
> de risque, et les observations `[OBS Exx]` citées plus bas — est dans le profil
> `library://equipe/devops` (chapitre « 19. Traçabilité » pour les observations). Les rubriques communes à
> tous les workflows (contrôles de sécurité, livrable, contenu analysé, arrêt) sont au premier
> chapitre « 7. Catalogue des workflows » du même profil, et s'appliquent ici.

- **Objectif / déclencheur** : trouver le point de rupture quand un consommateur ne joint plus un service (délai, refus, non-réponse).
- **Étapes** :
  1. Tracer le chemin complet : client → résolution de nom → point d'entrée → routage → service → dépendance.
  2. Tester **couche par couche** depuis le bon point d'observation : depuis l'intérieur du réseau du consommateur, pas depuis l'hôte.
  3. Vérifier les attachements réels. Un redémarrage ne réconcilie pas un réseau recréé **[OBS E13]**.
  4. Vérifier noms et alias. Les consommateurs utilisent des alias de service stables, pas des noms d'unités **[CG]**.
  5. Vérifier les règles de filtrage **telles qu'appliquées** (configuration résolue), pas telles qu'écrites **[OBS E12]**.
  6. Distinguer refus, délai et non-réponse. Un nombre illimité de tentatives produit un blocage sans erreur **[OBS E13]**.
- **Sécurité** : **interdiction absolue** d'ouvrir un port ou de rendre public un réseau interne pour contourner un problème de connectivité.
- **Livrables** : point de rupture prouvé, correctif minimal.
- **Arrêt** : correctif qui exige d'élargir une frontière de confiance : SecOps décide de la conformité technique ; un risque résiduel accepté revient à H-Risk.
