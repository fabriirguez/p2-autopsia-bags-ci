#!/usr/bin/env bash
# generar_mis_bags.sh - regenera TODOS los bags propios de la práctica con un solo comando
# (reproducibilidad: mismos parámetros + semilla fija del simulador -> mismos bags).
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")"
python3 - <<'PY'
import simulador_bags as sim
B = 'bags'
# Ejercicio 2: sano / con fallo (callback lento 0,15 s) / sin cabecera (Float32)
sim.generar('mi_sano',          B)
sim.generar('mi_lento',         B, retardo_filtro=0.15)
sim.generar('mi_lento_cola1',   B, retardo_filtro=0.15, profundidad=1)
sim.generar('mi_float_sano',    B, tipo_mensaje='Float32')
sim.generar('mi_float_lento',   B, tipo_mensaje='Float32', retardo_filtro=0.15)
# Ejercicio 3: el sensor publica 9,9 m (max_range = 4 m) entre 10 s y 12 s
sim.generar('mi_rango',         B, fuera_de_rango=(10, 12, 9.9))
print('bags propios regenerados en bags/mi_*')
PY
