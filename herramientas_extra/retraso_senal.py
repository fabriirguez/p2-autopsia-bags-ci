#!/usr/bin/env python3
"""retraso_senal.py - retraso de la SEÑAL entre dos topics Range (no del mensaje).

analiza_bag.py mide la latencia de cada mensaje (grabación - header.stamp). Pero un filtro puede
publicar mensajes "frescos" cuyo contenido va retrasado (p. ej. una media móvil de N muestras).
Aquí se estima ese retraso con la correlación cruzada de los valores de `range`.

Uso: python3 herramientas_extra/retraso_senal.py <bag> [/entrada /salida]
"""
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import analiza_bag as ab  # noqa: E402


def retraso(xs, ys, max_lag):
    """Desplazamiento k (en muestras) que maximiza la correlación de x[i] con y[i+k]."""
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    mejor, k_mejor = float('-inf'), 0
    for k in range(0, max_lag + 1):
        pares = list(zip(xs[:len(xs) - k], ys[k:]))
        c = sum((a - mx) * (b - my) for a, b in pares) / len(pares)
        if c > mejor:
            mejor, k_mejor = c, k
    return k_mejor


def main(argv):
    bag = argv[0]
    a, b = (argv[1], argv[2]) if len(argv) >= 3 else ('/distancia', '/distancia_filtrada')
    series, _ = ab.leer_bag(bag)
    xs, ys = series[a].valores, series[b].valores
    periodo = statistics.median(d2 - d1 for d1, d2 in zip(series[a].recv, series[a].recv[1:]))
    k = retraso(xs, ys, max_lag=min(len(xs) // 3, 50))
    print(f'{Path(bag).name}: periodo {periodo:.3f} s -> retraso de la señal {a} -> {b}: '
          f'{k} muestras = {k * periodo:.2f} s')


if __name__ == '__main__':
    main(sys.argv[1:])
