---
name: automatiser-une-operation-recurrente
description: "DevOps — quand : la troisième exécution manuelle d'une même opération, ou un incident né d'une recopie manuelle."
---

# WF-15 — Automatiser une opération récurrente

> **Autonomie maximale sans autorisation supplémentaire** : Niv. 2–3.
>
> Cette skill porte les **gestes**. Les rubriques communes (sécurité, livrable, contenu analysé, arrêt),
> les niveaux d'autonomie et les leçons `[OBS Exx]` citées plus bas sont dans [`commun.md`](../../commun.md),
> à lire au besoin. Le **pourquoi** reste dans le profil `library://equipe/devops`.

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
