#!/bin/sh
# Les temps de /koa:clore qui ne demandent aucun jugement : recenser le périmètre, puis vérifier qu'il est clos.
# Écrits ici plutôt que dans la skill : chaque commande que l'agent recopie et enchaîne est un tour de plus, relu sur tout son
# contexte, au moment où il est le plus gros (épic 200 de KoA : les clôtures pesaient 10 % du cache lu d'un chantier).
#
#   cloture.sh recenser   ce qui reste à faire ; « Périmètre : vide » dispense des étapes 3 à 7
#   cloture.sh verifier   l'état final de chaque dépôt ; sort en 1 si l'un n'est pas propre et à jour
#
# Ne lit que l'état des dépôts et des conteneurs, et n'écrit rien. POSIX : la distro n'a pas forcément bash.
set -u

depots() {
    find "$HOME" -maxdepth 3 -name .git -prune 2>/dev/null | sed 's|/\.git$||' | sort
}

# Un démon Docker absent ou figé ne doit pas tenir la clôture : borné quand la distro sait le faire.
borne() {
    if command -v timeout >/dev/null 2>&1; then timeout 10 "$@"; else "$@"; fi
}

docker_lit() {
    command -v docker >/dev/null 2>&1 || return 0
    borne docker "$@" 2>/dev/null
}

# L'écart à l'amont, ou rien si le dépôt n'en a pas.
ecart() {
    git -C "$1" rev-list --left-right --count '@{upstream}...HEAD' 2>/dev/null
}

recenser() {
    echo "cluster=${KOA_CLUSTER:-} qg=${KOA_QG:-}"
    carte=""
    if [ -n "${KOA_QG:-}" ] && [ -f "$KOA_QG/CLAUDE.md" ]; then carte="$KOA_QG/CLAUDE.md"; fi
    perimetre=0
    for r in $(depots); do
        nom=${r##*/}
        if [ -n "$(git -C "$r" status --porcelain 2>/dev/null)" ]; then
            echo "modifié : $r"
            perimetre=$((perimetre + 1))
        fi
        avance=$(ecart "$r" | awk '{print $2}')
        if [ -n "$avance" ] && [ "$avance" != "0" ]; then
            echo "non poussé : $r ($avance commit(s))"
            perimetre=$((perimetre + 1))
        fi
        if [ -n "$carte" ] && [ "$r" != "${KOA_QG:-}" ] && ! grep -qF "$nom" "$carte"; then
            echo "hors de la carte du QG : $r"
        fi
    done

    composes=$(docker_lit compose ls -q)
    if [ -n "$composes" ]; then
        echo "composes :"
        echo "$composes" | sed 's/^/  /'
        perimetre=$((perimetre + 1))
    fi
    docker_lit ps --format '{{.Names}}	{{.Label "com.docker.compose.project"}}' | sed 's/^/conteneur : /'

    # Les skills de synchro de données du projet, à lancer avant l'arrêt des conteneurs.
    for f in "$HOME"/*/.claude/skills/*/SKILL.md; do
        if [ -f "$f" ] && grep -qiE 'name: .*sync|description: .*(sync|synchro)' "$f"; then echo "synchro : $f"; fi
    done

    if [ "$perimetre" -eq 0 ]; then
        echo "Périmètre : vide. Rien à committer ni à pousser, aucun compose."
    else
        echo "Périmètre : $perimetre point(s) à traiter."
    fi
}

verifier() {
    echec=0
    for r in $(depots); do
        printf '%-28s ' "${r#"$HOME"/}"
        if [ -z "$(git -C "$r" status --porcelain 2>/dev/null)" ]; then
            printf 'propre  '
        else
            printf 'SALE    '
            echec=1
        fi
        e=$(ecart "$r")
        if [ -z "$e" ]; then
            echo "sans amont"
            continue
        fi
        set -- $e
        if [ "$1" = "0" ] && [ "$2" = "0" ]; then
            echo "à jour"
        else
            echo "retard/avance : $1/$2"
            echec=1
        fi
    done
    docker_lit ps --format '{{.Names}}	{{.Label "com.docker.compose.project"}}' | sed 's/^/conteneur : /'
    return "$echec"
}

case "${1:-}" in
    recenser) recenser ;;
    verifier) verifier ;;
    *) echo "usage : cloture.sh recenser|verifier" >&2; exit 2 ;;
esac
