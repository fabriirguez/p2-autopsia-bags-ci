#!/usr/bin/env python3
"""por_tramos.py - resumen por tramos de tiempo de la cadena sensor -> filtro -> controlador.

Para cada tramo: rango de valores de /distancia y /distancia_filtrada (y su desviación: 0 = señal congelada),
rango de la orden linear.x de /cmd_vel_demo, sellos repetidos y latencia máxima del filtro.
Uso: python3 herramientas_extra/por_tramos.py <bag> [corte1 corte2 ...]     (por defecto: 15 30)
"""
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import analiza_bag as ab  # noqa: E402
from rosbags.highlevel import AnyReader  # noqa: E402
from rosbags.typesys import Stores, get_typestore  # noqa: E402


def main(argv):
    bag = argv[0]
    cortes = [float(x) for x in argv[1:]] or [15.0, 30.0]
    limites = [0.0] + cortes + [float('inf')]
    tramos = list(zip(limites, limites[1:]))
    d = {tr: {'cmd': [], 'dist': [], 'filt': []} for tr in tramos}
    sellos = []
    with AnyReader([Path(bag)], default_typestore=get_typestore(Stores.ROS2_JAZZY)) as r:
        t0 = r.start_time / 1e9
        for c, t, raw in r.messages():
            m = r.deserialize(raw, c.msgtype)
            rel = t / 1e9 - t0
            tr = next(x for x in tramos if x[0] <= rel < x[1])
            if c.topic == '/cmd_vel_demo':
                d[tr]['cmd'].append(m.linear.x)
            elif c.topic == '/distancia':
                d[tr]['dist'].append(m.range)
            elif c.topic == '/distancia_filtrada':
                d[tr]['filt'].append(m.range)
                sellos.append((m.header.stamp.sec, m.header.stamp.nanosec))
    for (a, b), v in d.items():
        nombre = f'{a:.0f}-{b:.0f} s' if b != float('inf') else f'{a:.0f} s-fin'
        print(f"{nombre:10s} /distancia {min(v['dist']):.2f}-{max(v['dist']):.2f} m | /distancia_filtrada "
              f"{min(v['filt']):.2f}-{max(v['filt']):.2f} m (desv {st.pstdev(v['filt']):.3f}) | "
              f"cmd linear.x {min(v['cmd']):.3f}-{max(v['cmd']):.3f} m/s")
    print(f'/distancia_filtrada: {len(sellos)} mensajes, {len(set(sellos))} sellos distintos -> '
          f'{len(sellos) - len(set(sellos))} con sello repetido')
    _, stats, _, _ = ab.analizar_ruta(bag, ab.CADENA_POR_DEFECTO, {'/distancia': 10})
    s = stats['/distancia_filtrada']
    print(f'/distancia_filtrada: latencia mediana {s.lat_med:.3f} s, latencia MÁXIMA {s.lat_max:.2f} s '
          '(analiza_bag solo alerta por la mediana)')


if __name__ == '__main__':
    main(sys.argv[1:])
