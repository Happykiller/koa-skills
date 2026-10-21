#!/usr/bin/env sh
# Le garde-fou est écrit en Python, et Python coûte 80 à 400 ms à démarrer — à chaque appel Bash de
# l'agent. Ce tri grossier le réserve aux commandes qui nomment un outil de déploiement ou de
# fusion (le même filet que SUSPECT dans garde_fous.py), et à tout QG qui déclare ses propres
# commandes : celles-là, seul Python sait les lire.
entree=$(cat)

conf_propre() {
  for racine in "$CLAUDE_PROJECT_DIR" "$KOA_QG"; do
    [ -n "$racine" ] && [ -f "$racine/.claude/garde-fous.json" ] \
      && grep -q '"commandes"' "$racine/.claude/garde-fous.json" && return 0
  done
  return 1
}

if ! printf '%s' "$entree" | grep -Eq 'kubectl|helm|terraform|tofu|[^a-z]az[^a-z]|[^a-z]aws[^a-z]|gcloud|docker|vercel|netlify|[^a-z]fly|railway|heroku|ansible|[^a-z]gh[^a-z]' \
   && ! conf_propre; then
  exit 0
fi

if command -v python3 >/dev/null 2>&1; then
  # Pas d'`exec` dans un tube : il ne remplacerait que le sous-shell, et la suite s'exécuterait.
  printf '%s' "$entree" | python3 "$(dirname "$0")/garde_fous.py"
  exit $?
fi

# Sans Python, rien ne se lit : une commande qui ressemble à un déploiement ou à une fusion est
# refusée plutôt que laissée passer — un garde absent ne doit pas se faire passer pour un garde.
echo "garde-fous KoA inactif : python3 est absent de cet environnement." >&2
printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Garde-fous KoA : python3 est absent, le garde ne peut pas lire cette commande qui ressemble à un déploiement ou à une fusion. Refusée : demande à l humain d installer python3 dans la distro."}}'
exit 0
