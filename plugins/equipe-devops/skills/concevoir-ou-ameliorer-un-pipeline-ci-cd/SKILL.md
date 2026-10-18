---
name: concevoir-ou-ameliorer-un-pipeline-ci-cd
description: "WF-03 du rôle DevOps : concevoir ou améliorer un pipeline CI/CD. Objectif : un pipeline qui bloque ce qu'il doit bloquer, laisse passer le reste, et dont les échecs sont lisibles. Autonomie maximale : Niv. 2, application Niv. 3."
---

# WF-03 — Concevoir ou améliorer un pipeline CI/CD

> **Autonomie maximale sans autorisation supplémentaire** : Niv. 2, application Niv. 3 — niveaux
> définis au chapitre « 12. Sécurité, permissions et autonomie » du profil.
>
> Cette skill porte les **gestes**. Le **pourquoi** — raisonnement, hiérarchie des preuves, niveaux
> de risque, et les observations `[OBS Exx]` citées plus bas — est dans le profil
> `library://equipe/devops` (chapitre « 19. Traçabilité » pour les observations). Les rubriques communes à
> tous les workflows (contrôles de sécurité, livrable, contenu analysé, arrêt) sont au premier
> chapitre « 7. Catalogue des workflows » du même profil, et s'appliquent ici.

- **Objectif** : un pipeline qui bloque ce qu'il doit bloquer, laisse passer le reste, et dont les échecs sont lisibles.
- **Entrées** : pipeline existant, historique d'échecs et de contournements, incidents passés.
- **Vérifications initiales** :
  1. Compter les contournements utilisés. Un contournement fréquent signale un contrôle mal formulé **[OBS E05]**.
  2. Mesurer le taux de faux rouges et de faux verts.
- **Étapes** :
  1. Construire un socle déterministe :
     - fraîcheur de version, par rapport à la version **réellement déployée**, lue avant toute synchronisation, et comparée par ordre (« supérieure à »), pas par différence **[OBS E07]** ;
     - intégrité de release ;
     - constructibilité, par un contrôle rapide de cohérence du verrouillage ;
     - vulnérabilités.
  2. Pour chaque contrôle, distinguer trois sorties : défaut constaté (ÉCHOUÉ), conforme (RÉUSSI), contrôle impossible (NON_CONCLUANT, bloquant).
  3. Gérer les exceptions de manière granulaire : par identifiant, avec motif, mitigation prouvée, date, condition de retrait et date d'expiration **contrôlée par le code**. Exceptions réaffichées à chaque exécution ; chacune est acceptée par H-Risk.
  4. Prévoir un contournement unique, humain, journalisé, qu'un agent ne déclenche jamais **[OBS E09]**.
  5. Placer les contrôles coûteux là où ils ne dupliquent pas un build ultérieur. Arbitrer coût contre valeur **[OBS E07]**.
  6. Exécuter les contrôles sur un exécuteur neutre plutôt que sur un poste personnel **[REC]**.
- **Décisions** : un contrôle rapide en amont peut éviter un échec tardif après des gestes irréversibles ; dans ce cas il est prioritaire **[OBS E07]**.
- **Sécurité** : secrets du pipeline au moindre privilège. Clés de publication hors de la chaîne de build **[CG]**.
- **Vérification** : chaque contrôle est joué en rouge (cas piégé) et en vert. Le pipeline est exécuté sur un changement réel.
- **Livrables** : définition du pipeline, matrice des contrôles (but, bloquant ou non, contournement), fichier d'exceptions.
- **Réussite** :
  1. Zéro contournement rituel.
  2. Les incidents historiques seraient détectés.
  3. Temps de rétroaction connu.
- **Récupération** : version précédente du pipeline conservée et réactivable.
- **Arrêt / escalade** : désaccord sur le caractère bloquant d'un contrôle. SecOps et TECH instruisent ; affaiblir ou retirer un contrôle bloquant est une décision du propriétaire du risque (H-Risk).
