# koa-skills

Les skills du **framework agentique KoA**, en plugins Claude Code.

Le framework répond à une question que pose tout opérateur à sa deuxième équipe d'agents : une équipe
pour tous les projets, ou une par projet ? **Une équipe définie une fois, instanciée par frontière de
confiance**, et cloisonnée par les accès plutôt que par la consigne.
**[Le framework en schémas](https://happykiller.github.io/koa-releases/architecture.html)** ·
**[KoA](https://github.com/Happykiller/koa-releases)**

## Les plugins

| Plugin | Ce qu'il apporte |
|---|---|
| `koa` | `monter-le-qg` : monter, puis tenir conforme, le QG d'un cluster — le dépôt qui porte la carte de ses dépôts, ses environnements, sa KB, ses plugins épinglés |
| `garde-fous` | un hook qui refuse toute commande de déploiement visant une cible que le QG ne déclare pas permise, ou qu'il déclare interdite aux agents |
| `equipe-devops` | les vingt workflows du rôle DevOps : analyser une infrastructure, déployer, revenir en arrière, diagnostiquer, sauvegarder… |

## Installer

Une fois par dépôt, depuis ce dépôt :

```bash
claude plugin marketplace add Happykiller/koa-skills
claude plugin install garde-fous@koa-skills --scope project
claude plugin install koa@koa-skills --scope project
claude plugin install equipe-devops@koa-skills --scope project
```

Ou, pour que le dépôt les déclare lui-même, dans son `.claude/settings.json`, la marketplace
**épinglée sur un tag** :

```json
{
  "extraKnownMarketplaces": {
    "koa-skills": { "source": { "source": "github", "repo": "Happykiller/koa-skills", "ref": "v0.1.0" } }
  },
  "enabledPlugins": {
    "garde-fous@koa-skills": true,
    "koa@koa-skills": true,
    "equipe-devops@koa-skills": true
  }
}
```

## Le garde-fou

Il lit `.claude/garde-fous.json` dans le QG :

```json
{
  "version": 1,
  "cluster": "cluster-a",
  "deploiement": {
    "cibles_permises": ["dev-a", "recette-a"],
    "cibles_interdites": ["prod-a"]
  }
}
```

Une commande de déploiement (`kubectl apply`, `helm upgrade`, `terraform apply`… ou les motifs que
le QG déclare dans `deploiement.commandes`) doit **nommer** une cible permise. Une cible interdite, ou
aucune cible reconnue, et elle est refusée : l'agent reçoit la raison, la décision s'écrit dans le
journal du plugin. Le refus tient même quand l'agent tourne sans garde-fou de permission.

Sans `garde-fous.json`, chaque déploiement demande la confirmation de l'humain. Une configuration
illisible refuse les déploiements plutôt que de les laisser passer. Le hook demande `python3`, et
dit qu'il est inactif quand il ne le trouve pas.

## Licence

MIT — voir [LICENSE](LICENSE).
