---
name: automatiser-une-operation-recurrente
description: "WF-15 du rôle DevOps : automatiser une opération récurrente. À déclencher : troisième exécution manuelle de la même opération, ou incident causé par une erreur de recopie manuelle. Autonomie maximale : Niv. 2–3."
---

# WF-15 — Automatiser une opération récurrente

> **Autonomie maximale sans autorisation supplémentaire** : Niv. 2–3 — niveaux
> définis au chapitre « 12. Sécurité, permissions et autonomie » du profil.
>
> Cette skill porte les **gestes**. Le **pourquoi** — raisonnement, hiérarchie des preuves, niveaux
> de risque, et les observations `[OBS Exx]` citées plus bas — est dans le profil
> `library://equipe/devops` (chapitre « 19. Traçabilité » pour les observations). Les rubriques communes à
> tous les workflows (contrôles de sécurité, livrable, contenu analysé, arrêt) sont au premier
> chapitre « 7. Catalogue des workflows » du même profil, et s'appliquent ici.

- **Déclencheur** : troisième exécution manuelle de la même opération **[OBS E25]**, ou incident causé par une erreur de recopie manuelle **[OBS E03]**.
- **Étapes** :
  1. Vérifier qu'aucun outil existant ne la couvre déjà.
  2. Écrire l'automatisation avec des postconditions, l'idempotence, une simulation et un refus explicite des états anormaux.
  3. Lire la topologie là où elle est déclarée, sans la dupliquer **[OBS E24]**.
  4. Aucun chemin ni port en dur **[OBS E26]**.
  5. Tester en rouge et en vert.
  6. Documenter.
- **Interdit** : une automatisation qui modifie la base de connaissances ou les consignes sans supervision **[OBS E25]**.
- **Réussite** : l'opération manuelle n'est plus exécutée, et l'automatisation a déjà refusé au moins un cas anormal en test.
