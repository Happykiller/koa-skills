# Jalons d'intégration anticipée

`python3 outils/integrations.py plan.json` lit des données **déclarées au QG** et rend les jalons bloqués, à exécuter ou prouvés. Il ne lance aucune commande et n'infère pas les dépendances à partir du code.

Exemple minimal :

```json
{
  "missions": {"M1": {"state": "accepted"}, "M2": {"state": "accepted"}},
  "integrations": [{
    "id": "I1", "missions": ["M1","M2"], "owner": "TECH",
    "contract": "API et consommateur compatibles",
    "command": "commande réelle fournie par le dépôt",
    "commit": "SHA de l'arbre testé",
    "proof": {"result": "PASS", "commit": "SHA de l'arbre testé"}
  }]
}
```

Une mission non acceptée donne `BLOCKED`. Deux missions acceptées sans preuve `PASS` sur la tête désignée donnent `ACTION_REQUIRED`. L'exécution et la preuve sont sous responsabilité du rôle indiqué. `PASSED` ne remplace jamais la recette finale de la feature. Code de sortie 0 uniquement si tous les jalons sont `PASSED`, sinon 2.

Le champ `commit` est une référence obligatoire à la tête intégrée. Un état de données, environnement ou dépendance changé impose de réémettre une preuve ; une preuve déclarée n'est pas authentifiée par cet outil.
