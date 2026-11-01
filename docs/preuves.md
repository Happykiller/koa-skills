# Registre de preuves

Outil générique `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/preuves.py`, sans dépendance tierce.

- `record` enregistre un résultat réel fourni par l'exécuteur, sans lancer de test.
- `check` retourne `REUSABLE` (code 0) uniquement si le résultat est `PASS` et si commit, environnement, empreintes de configuration, dépendances et fichiers sont identiques. Sinon code 2 et raison.
- Les identifiants et les empreintes proviennent du système de build/CI ; l'outil ne les invente pas.
- Le registre ne constitue **pas** une preuve indépendante et n'authentifie pas celui qui y écrit. Ne jamais lui confier une décision de sécurité, ni contourner une revue ou la validation de l'arbre fusionné.
- Les changements de services externes, de secrets, d'état de base ou de temps non représentés dans ces empreintes imposent une nouvelle exécution.

Exemple : `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/preuves.py record --registry preuves.json --id test-api --commit SHA --environment CI --config CFG_SHA --dependencies LOCK_SHA --files src/module.py --result PASS --command 'pytest tests/test_api.py'`. Puis remplacer `record` par `check` en omettant `--result` et `--command`.
