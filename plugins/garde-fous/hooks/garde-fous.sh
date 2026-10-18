#!/usr/bin/env sh
# Le garde-fou est écrit en Python ; sans Python, il ne peut rien lire. Il le dit au lieu de laisser
# croire qu'il protège : code 1, que Claude Code affiche comme erreur de hook sans bloquer l'agent.
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$(dirname "$0")/garde_fous.py"
fi
echo "garde-fous KoA inactif : python3 est absent de cet environnement. Aucun déploiement n'est contrôlé." >&2
exit 1
