# Travailler sur koa-skills

La marketplace publique de plugins Claude Code du **framework agentique KoA** : une équipe d'agents
définie une fois, instanciée par cluster, cloisonnée par les accès. Le framework lui-même est le livre
`koa/architecture` de la librairie KoA, et la page
https://happykiller.github.io/koa-releases/architecture.html — ce dépôt n'en recopie rien.

## Ce qui se range ici, et ce qui n'y entre jamais

Le niveau **N2** du framework : des gestes génériques. Une skill nomme une plateforme ou un outil,
jamais un compte, une URL, un secret ni un nom d'environnement réel. Ce qui nomme un environnement va
dans le QG du cluster, pas ici.

**Aucun nom de projet ni de client**, dans les skills, les exemples, les tests : cluster A, B, C,
petits SaaS. Le dépôt est public.

**Typé Claude** : plugins, skills, hooks et sous-agents de Claude Code. Aucun format pensé pour
d'autres outils.

## Le livre et la skill ne se recopient pas

Les skills de rôle (`equipe-*`) portent les **gestes** des workflows d'un profil ; le **pourquoi**
reste dans le profil de la librairie KoA (`library://equipe/<rôle>`), qui renvoie à la skill par son
nom. Corriger une étape se fait ici ; corriger un raisonnement se fait dans le profil, dans le dépôt de
KoA.

## Vérifier, versionner

```bash
python3 -m unittest discover -s tests -v
claude plugin validate --strict .
for p in plugins/*/; do claude plugin validate --strict "$p"; done
```

Un plugin modifié monte sa `version` dans son `plugin.json` ; la marketplace monte
`metadata.version` et reçoit le tag `v<version>`. Les QG épinglent ce tag : sans nouveau tag, rien
n'atteint les clusters. Après un tag, KoA reprend le catalogue : `python3 outils/verifier.py --catalogue`
remplace `src/Koa.Core/Librairie/koa-skills.txt` dans le dépôt de KoA.
