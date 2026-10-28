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
# Ejercicio 4: mi quinto fallo (la explicación está SOLO en informe.md, sección «Solución»)
def mi_fallo(msgs, ini=15.0, fin=30.0):
    """Entre ini y fin el filtro ya no recibe /distancia, pero un temporizador sigue
    republicando a 10 Hz su ÚLTIMO mensaje (con su header original), y el controlador repite su última orden.
    El sensor sigue sano. Ritmos intactos -> analiza_bag.py no lo ve."""
    salida, ultimo = [], {}
    for topic, tipo, t, msg in sorted(msgs, key=lambda m: m[2]):
        rel = t - sim.T0
        if topic in ('/distancia_filtrada', '/cmd_vel_demo') and ini <= rel < fin and topic in ultimo:
            msg = ultimo[topic]                       # mismo objeto: mismo valor y mismo header.stamp
        elif not (ini <= rel < fin):
            ultimo[topic] = msg
        salida.append((topic, tipo, t, msg))
    return salida

sim.generar('mi_fallo',         B, post=mi_fallo)   # nombre neutro: el .mcap guarda el nombre dentro
print('bags propios regenerados en bags/mi_*')
PY
