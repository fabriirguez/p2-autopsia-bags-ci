#!/usr/bin/env python3
"""mis_comprobaciones.py - EJERCICIO 3 de la practica autonoma: extiende la herramienta con TU comprobacion.

analiza_bag.py comprueba ritmos, huecos, latencia y reloj... pero es ciega a otros fallos. Prueba:
    python3 -c "import simulador_bags as s; s.generar('mi_rango', 'bags', fuera_de_rango=(10, 12, 9.9))"
    python3 analiza_bag.py bags/mi_rango --esperado /distancia=10        # dice TODO_OK ... pero el sensor
                                                                         # publico 9.9 m con max_range = 4 m
Tu tarea (elige al menos UNA; la segunda es ampliacion):
    1. comprobar_rangos : valores de `range` fuera de [min_range, max_range]            -> ERROR  RANGO_FUERA
    2. comprobar_frames : mas de un frame_id distinto en un topic                        -> WARN   FRAME_MIXTO
Reglas de la practica:
    - NO cambies los nombres ni las firmas de las funciones (las pruebas de test_mis_comprobaciones.py las usan).
    - Cada comprobacion devuelve una LISTA de Hallazgo (la clase de analiza_bag.py); lista vacia = sin problemas.
    - Escribe, ademas, al menos DOS pruebas propias nuevas en test_mis_comprobaciones.py (clase PruebasPropias).
    - Cuando funcione, integrala (opcional): anade la llamada en analiza_bag.analizar_ruta o usa `main` de este fichero.

Uso:  python3 mis_comprobaciones.py bags/mi_rango /distancia        # codigo de salida 1 si hay ERROR
"""
import math
import sys
from collections import Counter
from pathlib import Path

from analiza_bag import Hallazgo


def leer_muestras_range(ruta_bag, topic):
    """(YA HECHA) Lee un topic sensor_msgs/Range del bag.

    Devuelve una lista de dicts: {'t': segundos desde el inicio del bag, 'range': float, 'min_range': float,
    'max_range': float, 'frame_id': str}, en orden de grabacion.
    """
    from rosbags.highlevel import AnyReader
    from rosbags.typesys import Stores, get_typestore
    ts = get_typestore(Stores.ROS2_JAZZY)
    out = []
    with AnyReader([Path(ruta_bag)], default_typestore=ts) as r:
        t0 = r.start_time / 1e9
        for conn, t_ns, raw in r.messages():
            if conn.topic != topic:
                continue
            m = r.deserialize(raw, conn.msgtype)
            out.append({'t': t_ns / 1e9 - t0, 'range': float(m.range), 'min_range': float(m.min_range),
                        'max_range': float(m.max_range), 'frame_id': m.header.frame_id})
    return out


def _tramos(indices):
    """Número de tramos consecutivos en una lista ordenada de índices de muestra ([3,4,5,9] -> 2)."""
    return sum(1 for i, x in enumerate(indices) if i == 0 or x != indices[i - 1] + 1)


def comprobar_rangos(muestras, topic='', margen=0.0):
    """Devuelve [] si todas las muestras cumplen min_range - margen <= range <= max_range + margen.

    Si alguna no cumple, devuelve UN solo Hallazgo('ERROR', 'RANGO_FUERA', topic, detalle) con cuántas
    muestras fallan (de cuántas), el intervalo de tiempo (t de la primera y de la última), en cuántos tramos
    y entre qué valores.

    Decisiones (justificadas en el informe, ejercicio 3):
      - Los límites son los de CADA mensaje (Range trae min_range/max_range propios), con intervalo cerrado.
      - +Inf / -Inf NO son error: en sensor_msgs/Range significan «sin detección dentro del alcance» y
        «detección por debajo del mínimo». Se cuentan en un Hallazgo INFO 'RANGO_INFINITO' (visible, no
        rompe la CI). Así se evita el falso positivo típico de sensores que publican inf fuera de alcance.
      - NaN SÍ es error: es una medida inválida (y además NaN no cumple ninguna comparación).
      - margen < 0 (o NaN) lanza ValueError: estrecharía el rango sin que nadie lo note.
    """
    if not margen >= 0.0:                                   # también rechaza NaN
        raise ValueError(f'margen debe ser >= 0 (recibido {margen!r})')
    fuera, infinitos, n_nan = [], 0, 0
    for i, s in enumerate(muestras):
        r = s['range']
        if math.isinf(r):
            infinitos += 1
        elif math.isnan(r):
            n_nan += 1
            fuera.append(i)
        elif not (s['min_range'] - margen <= r <= s['max_range'] + margen):
            fuera.append(i)

    hallazgos = []
    if fuera:
        primera, ultima = muestras[fuera[0]], muestras[fuera[-1]]
        finitos = [muestras[i]['range'] for i in fuera if not math.isnan(muestras[i]['range'])]
        valores = f'; valores de {min(finitos):.2f} a {max(finitos):.2f} m' if finitos else ''
        nan = f'; {n_nan} NaN (medida inválida)' if n_nan else ''
        detalle = (f'{len(fuera)} de {len(muestras)} muestras fuera de [min_range - {margen:g}, '
                   f'max_range + {margen:g}] (p. ej. [{primera["min_range"]:.2f}, {primera["max_range"]:.2f}] m) '
                   f'entre {primera["t"]:.1f} s y {ultima["t"]:.1f} s, en {_tramos(fuera)} tramo(s){valores}{nan}')
        hallazgos.append(Hallazgo('ERROR', 'RANGO_FUERA', topic, detalle))
    if infinitos:
        hallazgos.append(Hallazgo('INFO', 'RANGO_INFINITO', topic,
                                  f'{infinitos} de {len(muestras)} muestras con ±Inf (convenio de Range: sin '
                                  'detección / demasiado cerca); no se cuentan como error'))
    return hallazgos


def comprobar_frames(muestras, topic=''):
    """Devuelve [] si todas las muestras tienen el mismo frame_id.

    Si hay más de uno, devuelve UN Hallazgo('WARN', 'FRAME_MIXTO', topic, detalle) con los frame_id distintos
    (en orden de aparición, con cuántas muestras tiene cada uno). El frame vacío '' cuenta como uno más:
    tf2 no puede transformar un dato sin marco.
    """
    cuenta = Counter(s['frame_id'] for s in muestras)        # Counter conserva el orden de aparición
    if len(cuenta) <= 1:
        return []
    lista = ', '.join(f"'{f}' ({n})" if f else f'(vacío) ({n})' for f, n in cuenta.items())
    return [Hallazgo('WARN', 'FRAME_MIXTO', topic,
                     f'{len(cuenta)} frame_id distintos en {len(muestras)} muestras: {lista}')]


def comprobar_bag(ruta_bag, topics, margen=0.0):
    """Ejecuta las comprobaciones de este fichero sobre los topics Range indicados (lo usa analiza_bag)."""
    hallazgos = []
    for topic in topics:
        muestras = leer_muestras_range(ruta_bag, topic)
        hallazgos += comprobar_rangos(muestras, topic, margen) + comprobar_frames(muestras, topic)
    return hallazgos


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print('uso: mis_comprobaciones.py <carpeta_bag> <topic_range>')
        return 2
    muestras = leer_muestras_range(argv[0], argv[1])
    hallazgos = list(comprobar_rangos(muestras, argv[1]))
    hallazgos += comprobar_frames(muestras, argv[1])
    if not any(h.severidad in ('ERROR', 'WARN') for h in hallazgos):
        print(f'[INFO ] {argv[1]}: sin problemas de rango ni de frame ({len(muestras)} muestras)')
    for h in hallazgos:
        print(f'[{h.severidad:5s}] {h.codigo:14s} {h.topic}  {h.detalle}')
    return 1 if any(h.severidad == 'ERROR' for h in hallazgos) else 0


if __name__ == '__main__':
    sys.exit(main())
