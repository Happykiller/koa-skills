---
name: concevoir-une-strategie-de-sauvegarde-et-de-restauration
description: "WF-13 du rôle DevOps : concevoir une stratégie de sauvegarde et de restauration. À déclencher : que chaque donnée persistante soit récupérable dans un délai décidé. Déclenché par un nouveau composant à état, une sauvegarde jamais restaurée ou un statut douteux. Autonomie maximale : Niv. 2, exécution Niv. 3–4."
---

# WF-13 — Concevoir une stratégie de sauvegarde et de restauration

> **Autonomie maximale sans autorisation supplémentaire** : Niv. 2, exécution Niv. 3–4 — niveaux
> définis au chapitre « 12. Sécurité, permissions et autonomie » du profil.
>
> Cette skill porte les **gestes**. Le **pourquoi** — raisonnement, hiérarchie des preuves, niveaux
> de risque, et les observations `[OBS Exx]` citées plus bas — est dans le profil
> `library://equipe/devops` (chapitre « 19. Traçabilité » pour les observations). Les rubriques communes à
> tous les workflows (contrôles de sécurité, livrable, contenu analysé, arrêt) sont au premier
> chapitre « 7. Catalogue des workflows » du même profil, et s'appliquent ici.

- **Objectif / déclencheur** : que chaque donnée persistante soit récupérable dans un délai décidé. Déclenché par un nouveau composant à état, une sauvegarde jamais restaurée ou un statut douteux.
- **Étapes** :
  1. Inventorier les données persistantes. Pour chacune : criticité, RPO et RTO **décidés par le propriétaire du risque (H-Risk)**, sur instruction chiffrée de l'agent et avis du PO sur l'impact métier.
  2. Concevoir :
     - lecture seule de la source ;
     - aucun passage par le service applicatif ;
     - chiffrement asymétrique, avec la clé privée hors de la cible ;
     - suppression des archives partielles ;
     - rétention ;
     - copie hors du domaine de défaillance **[OBS E11][REC]**.
  3. Statut : date et résultat de la **dernière tentative**, échec journalisé et alerté **[OBS E10]**.
  4. Restauration : vers une cible jetable par défaut, extraction puis bascule, refus si le service tourne, permissions rétablies **[OBS E11]**.
  5. **Exercice de restauration réel**, chronométré, puis périodique **[OBS E10][REC]**.
  6. Documenter honnêtement ce qui n'est **pas** couvert.
- **Livrables** : politique de sauvegarde, runbook de restauration, preuve d'exercice datée.
- **Réussite** : une restauration réelle a réussi récemment et son RTO mesuré respecte l'objectif.
- **Arrêt** : contrainte réglementaire éventuelle sur les copies : décision de H-Risk, après avis de l'évaluateur juridique **[OBS E42]**.
