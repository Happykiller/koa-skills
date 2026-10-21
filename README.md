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
| `koa` | `monter-le-qg` : monter, puis tenir conforme, le QG d'un cluster — le dépôt qui porte la carte de ses dépôts, ses environnements, sa KB, ses plugins épinglés · `poser-la-memoire` : le ghost — la KB et le `CLAUDE.md` d'un projet seul, ou leur répartition dans un cluster (QG, dépôt de la stack, seed d'un agent) · `capitaliser` : ranger ce qu'une session a appris au bon étage, écrit jusqu'au QG, proposé au-dessus · `clore` : la fin de session d'un agent de cluster, QG compris |
| `garde-fous` | un hook qui refuse toute commande de déploiement visant une cible que le QG ne déclare pas permise, ou qu'il déclare interdite aux agents ; et toute fusion sans `--match-head-commit`, avec `--admin`, ou hors de l'orchestrateur |
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
    "koa-skills": { "source": { "source": "github", "repo": "Happykiller/koa-skills", "ref": "v0.3.0" } }
  },
  "enabledPlugins": {
    "garde-fous@koa-skills": true,
    "koa@koa-skills": true,
    "equipe-devops@koa-skills": true
  }
}
```

## Le garde-fou

Il lit `.claude/garde-fous.json` dans le projet de la session, sinon dans le QG (`$KOA_QG`) — une
session ouverte dans un dépôt de la stack reste sous les règles de son cluster :

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

La commande se juge **segment par segment, sur son mot de commande** : `grep "kubectl apply"`, un
message de commit qui en parle, `kubectl logs deploy/scale-worker` ou `terraform plan -out=apply.tfplan`
ne déploient rien. Les enveloppes (`sudo`, `env`, `timeout`, `xargs`…), `bash -c` et `ssh hôte …` ne
cachent pas le déploiement qu'elles lancent, et chaque segment qui déploie nomme sa propre cible. Un
`docker compose` local — la base de test, la clôture qui arrête ses conteneurs — n'est pas un
déploiement ; il le devient quand il vise un démon distant (`--context`, `-H`, `DOCKER_HOST`).

Sans `garde-fous.json`, chaque déploiement demande la confirmation de l'humain. Une configuration
illisible refuse les déploiements plutôt que de les laisser passer. Un garde qui plante, ou qui ne
trouve pas `python3`, refuse ce qui ressemble à un déploiement ou à une fusion au lieu de le laisser
passer. Python ne démarre que pour les commandes qui nomment un outil de déploiement ou de fusion
(ou quand le QG déclare ses propres commandes) : les autres passent en quelques millisecondes.

### La fusion

Toujours active, sans configuration : c'est une règle du framework. Un `gh pr merge` est refusé s'il
porte `--admin`, s'il ne nomme pas la tête relue (`--match-head-commit` et son SHA complet), ou si la
distro est née de KoA sans que sa seed lui donne le droit de fusionner — seul l'orchestrateur fusionne.
Une commande qui parle de fusion sans se laisser lire est refusée aussi. Un alias de `gh`,
`gh api …/merge` ou un `git push` sur la branche protégée ne sont pas reconnus : le garde tient contre
la dérive, pas contre la malveillance.

## Licence

MIT — voir [LICENSE](LICENSE).
