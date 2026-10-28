#!/usr/bin/env bash
# ci_local.sh - "CI de bolsillo": lo mismo que hace .github/workflows/ci.yml, pero a mano.
# Util como comprobacion antes de hacer commit (un hook pre-commit/pre-push podria llamarlo).
set -u
export PYTHONDONTWRITEBYTECODE=1   # evita .pyc obsoletos al cambiar de commit
cd "$(dirname "$0")"
fallos=0
paso() { echo; echo "== $1"; shift; "$@" || { echo "   -> FALLO"; fallos=$((fallos+1)); }; }
paso "Pruebas unitarias"             python3 -m unittest discover
paso "Regresion con bags"            python3 regresion_bags.py
paso "Bag sano debe dar TODO_OK"     python3 analiza_bag.py bags/caso_0_linea_base
echo
if [ "$fallos" -eq 0 ]; then echo "VERDE: todo pasa"; else echo "ROJO: $fallos paso(s) fallan"; fi
exit $((fallos > 0))
