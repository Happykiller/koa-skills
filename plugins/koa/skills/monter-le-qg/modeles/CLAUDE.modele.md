# QG du cluster <identifiant>

Ce dépôt porte le contexte de tout le cluster `<identifiant>` : ce qui vaut pour tous ses dépôts et
qu'aucun d'eux ne porte seul. Organisation des agents : framework agentique KoA
(`library://koa/architecture`).

## Les dépôts

| Dépôt | Rôle | Adresse |
|---|---|---|
| À renseigner | | |

## Les environnements

| Environnement | Usage |
|---|---|
| À renseigner | |

Ce qu'un agent peut viser en déploiement fait foi dans `.claude/garde-fous.json` : les cibles
`permises` s'y déploient, les cibles `interdites` sont un geste humain.

## Les interdits

- Ne jamais citer, explorer ni contacter un dépôt ou un environnement hors de ce cluster.
- Ne jamais écrire une valeur de secret dans un fichier : les secrets se nomment.
- Ne jamais déployer sur une cible interdite : préparer, puis demander.

## Où est le reste

- Décisions : `docs/KB/decisions/`, une par fichier, datée.
- Base de connaissance : `docs/KB/README.md`.
- Gestes propres au cluster : `.claude/skills/`.
