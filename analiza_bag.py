#!/usr/bin/env python3
"""analiza_bag.py - autopsia de un rosbag2 sin necesidad de ROS2 (Sesion 8, Tema 2).

Lee un bag (rosbag2: sqlite3 o MCAP) con la libreria `rosbags` y responde a las preguntas del metodo
de depuracion 'de fuera adentro', pero DESPUES del fallo:
  - existe cada topic esperado y llegan datos?          (SIN_DATOS, TOPIC_INESPERADO)
  - a que ritmo? hay huecos?                            (RITMO_BAJO, HUECOS, HUECO_ORIGEN)
  - donde se pierde el ritmo en la cadena de nodos?     (CAIDA_EN_CADENA)
  - cuanto tarda un dato en llegar (si lleva cabecera)? (LATENCIA_ALTA)
  - los sellos de tiempo son coherentes con el reloj?   (RELOJ_DESFASADO)

Requisitos:  pip install rosbags matplotlib      (matplotlib solo para --png)

Uso:
  python3 analiza_bag.py bags/caso_0_linea_base
  python3 analiza_bag.py bags/caso_1 --png informe.png
  python3 analiza_bag.py mi_bag --cadena /a,/b,/c --esperado /a=10
Codigo de salida: 1 si hay algun hallazgo de severidad ERROR (util para CI).
"""
import argparse
import difflib
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path

CADENA_POR_DEFECTO = ['/distancia', '/distancia_filtrada', '/cmd_vel_demo']
TOPICS_SISTEMA = {'/parameter_events', '/rosout', '/clock', '/tf', '/tf_static'}


@dataclass
class Serie:
    """Datos crudos de un topic: instantes de grabacion y (si hay cabecera) sellos del mensaje, en segundos."""
    topic: str
    tipo: str
    recv: list = field(default_factory=list)
    stamps: list = None          # None si el mensaje no tiene header
    valores: list = None         # campo 'range' si existe (para dibujar)


@dataclass
class Stats:
    topic: str
    tipo: str
    n: int
    t_ini: float                 # relativo al inicio del bag
    t_fin: float
    ritmo: float                 # Hz medio
    periodo_med: float
    periodo_max: float
    periodo_std: float
    huecos: list                 # [(inicio_rel, fin_rel)]
    tiene_header: bool
    reloj_ok: bool = True
    lat_med: float = None
    lat_max: float = None
    motivo_reloj: str = ''


@dataclass
class Hallazgo:
    severidad: str               # ERROR | WARN | INFO
    codigo: str
    topic: str
    detalle: str


# ------------------------------------------------------------------ lectura
def leer_bag(ruta):
    """Devuelve ({topic: Serie}, t0_abs). Requiere la libreria `rosbags`."""
    from rosbags.highlevel import AnyReader
    from rosbags.typesys import Stores, get_typestore
    ts = get_typestore(Stores.ROS2_JAZZY)
    series = {}
    with AnyReader([Path(ruta)], default_typestore=ts) as r:
        t0 = r.start_time / 1e9
        for conn, t_ns, raw in r.messages():
            s = series.setdefault(conn.topic, Serie(conn.topic, conn.msgtype))
            s.recv.append(t_ns / 1e9)
            try:
                msg = r.deserialize(raw, conn.msgtype)
            except Exception:                       # tipo desconocido: solo contamos mensajes
                continue
            h = getattr(msg, 'header', None)
            if h is not None:
                if s.stamps is None:
                    s.stamps = []
                s.stamps.append(h.stamp.sec + h.stamp.nanosec / 1e9)
            if hasattr(msg, 'range'):
                if s.valores is None:
                    s.valores = []
                s.valores.append(float(msg.range))
    return series, t0


# ------------------------------------------------------------------ estadisticas
def _regresion_pendiente(xs, ys):
    n = len(xs)
    if n < 3:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else 0.0


def estadisticas(serie, t0, hueco_min=0.5, factor_hueco=5.0):
    recv = sorted(serie.recv)
    n = len(recv)
    rel = [t - t0 for t in recv]
    dts = [b - a for a, b in zip(recv, recv[1:])]
    med = statistics.median(dts) if dts else 0.0
    huecos = []
    umbral = max(hueco_min, factor_hueco * med) if dts else hueco_min
    for a, b, dt in zip(rel, rel[1:], dts):
        if dt > umbral:
            huecos.append((a, b))
    span = (recv[-1] - recv[0]) if n > 1 else 0.0
    st = Stats(serie.topic, serie.tipo, n, rel[0] if rel else 0.0, rel[-1] if rel else 0.0,
               (n - 1) / span if span > 0 else 0.0, med, max(dts) if dts else 0.0,
               statistics.pstdev(dts) if len(dts) > 1 else 0.0, huecos, serie.stamps is not None)
    if serie.stamps:
        stamps = serie.stamps
        if len(set(stamps)) <= 1:
            st.reloj_ok, st.motivo_reloj = False, 'todos los sellos son iguales (reloj parado o a cero)'
        else:
            desfases = [r - s for r, s in zip(serie.recv, stamps)]
            off = statistics.median(desfases)
            if abs(off) > 1000.0 or off < -1.0:
                st.reloj_ok, st.motivo_reloj = False, f'sellos desfasados {off:.0f} s respecto al reloj de grabacion'
            else:
                st.lat_med = off
                st.lat_max = max(desfases)
    return st


# ------------------------------------------------------------------ diagnostico
def diagnosticar(stats, cadena=None, esperado=None, lat_max=0.1, caida=0.8):
    """stats: {topic: Stats}. Devuelve lista de Hallazgo ordenada por severidad."""
    h = []
    esperado = dict(esperado or {})
    cadena = list(cadena or [])
    objetivo = set(cadena) | set(esperado)

    for t in sorted(objetivo):
        if t not in stats or stats[t].n == 0:
            h.append(Hallazgo('ERROR', 'SIN_DATOS', t, 'no hay ningun mensaje en el bag'))
    for t in sorted(set(stats) - objetivo - TOPICS_SISTEMA):
        if cadena:
            falta = [c for c in cadena if c not in stats]
            sug = difflib.get_close_matches(t, falta, n=1, cutoff=0.5)
            extra = f'; se parece a {sug[0]} (que no aparece): nombre de topic mal escrito?' if sug else ''
            h.append(Hallazgo('WARN', 'TOPIC_INESPERADO', t, f'{stats[t].n} mensajes en un topic que no esta en la cadena{extra}'))

    for t, hz in esperado.items():
        s = stats.get(t)
        if s and s.n and s.ritmo < 0.8 * hz:
            h.append(Hallazgo('ERROR', 'RITMO_BAJO', t, f'{s.ritmo:.2f} Hz medidos frente a {hz:g} Hz esperados'))

    for t, s in sorted(stats.items()):
        if t in TOPICS_SISTEMA:
            continue
        for a, b in s.huecos:
            h.append(Hallazgo('ERROR' if b - a >= 1.0 else 'WARN', 'HUECOS', t,
                              f'sin mensajes entre {a:.1f} s y {b:.1f} s ({b - a:.1f} s)'))
        if s.tiene_header and not s.reloj_ok:
            h.append(Hallazgo('ERROR', 'RELOJ_DESFASADO', t,
                              f'{s.motivo_reloj}; sospecha: use_sim_time distinto entre nodos o falta /clock'))
        elif s.lat_med is not None and s.lat_med > lat_max:
            h.append(Hallazgo('ERROR', 'LATENCIA_ALTA', t,
                              f'latencia mediana {s.lat_med:.2f} s (maxima {s.lat_max:.2f} s) > {lat_max:g} s: '
                              'los datos llegan viejos (cola llena o callback lento aguas arriba)'))

    presentes = [c for c in cadena if c in stats and stats[c].n > 0]
    for a, b in zip(presentes, presentes[1:]):
        ra, rb = stats[a].ritmo, stats[b].ritmo
        if ra > 0 and rb < caida * ra:
            h.append(Hallazgo('ERROR', 'CAIDA_EN_CADENA', b,
                              f'{a} {ra:.1f} Hz -> {b} {rb:.1f} Hz: el ritmo cae en el nodo que une ambos topics'))

    # origen de los huecos: el que empieza antes en la cadena
    inicios = {c: stats[c].huecos[0][0] for c in presentes if stats[c].huecos}
    if len(inicios) > 1:
        origen = min(inicios, key=lambda c: inicios[c])
        h.append(Hallazgo('INFO', 'HUECO_ORIGEN', origen,
                          f'el hueco empieza primero en {origen} ({inicios[origen]:.1f} s): mirad aguas arriba '
                          '(sensor, driver, cable), el resto es consecuencia'))
    if not any(x.severidad in ('ERROR', 'WARN') for x in h):
        h.append(Hallazgo('INFO', 'TODO_OK', '-', 'ritmos, huecos, latencias y reloj dentro de lo esperado'))
    orden = {'ERROR': 0, 'WARN': 1, 'INFO': 2}
    return sorted(h, key=lambda x: (orden[x.severidad], x.codigo, x.topic))



# ------------------------------------------------------------------ equivalente a `ros2 bag info`
def info_bag(ruta):
    """Texto parecido a la salida de `ros2 bag info` (formato aproximado)."""
    import re
    import time as _time
    from rosbags.highlevel import AnyReader
    from rosbags.typesys import Stores, get_typestore
    ruta = Path(ruta)
    meta = (ruta / 'metadata.yaml').read_text() if (ruta / 'metadata.yaml').exists() else ''
    m = re.search(r'storage_identifier:\s*(\S+)', meta)
    storage = m.group(1) if m else '?'
    ficheros = sorted(p for p in ruta.iterdir() if p.suffix in ('.mcap', '.db3'))
    tam = sum(p.stat().st_size for p in ficheros)

    def fecha(ns):
        seg = ns / 1e9
        return f"{_time.strftime('%b %d %Y %H:%M:%S', _time.gmtime(seg))}.{int(ns % 1e9 / 1e6):03d} ({seg:.2f})"

    with AnyReader([ruta], default_typestore=get_typestore(Stores.ROS2_JAZZY)) as r:
        l = [f"Files:             {', '.join(p.name for p in ficheros)}",
             f"Bag size:          {tam / 1024:.1f} KiB",
             f"Storage id:        {storage}",
             f"Duration:          {r.duration / 1e9:.3f}s",
             f"Start:             {fecha(r.start_time)}",
             f"End:               {fecha(r.end_time)}",
             f"Messages:          {r.message_count}"]
        filas = [f"Topic: {c.topic} | Type: {c.msgtype} | Count: {c.msgcount} | Serialization Format: cdr"
                 for c in sorted(r.connections, key=lambda c: c.topic)]
    l.append('Topic information: ' + filas[0] if filas else 'Topic information:')
    l += [' ' * 19 + f for f in filas[1:]]
    return '\n'.join(l)

# ------------------------------------------------------------------ salida
def informe(stats, hallazgos, nombre=''):
    l = [f'== Informe de {nombre or "bag"} ==', '',
         f'{"topic":24s} {"tipo":26s} {"n":>5s} {"Hz":>7s} {"max dt":>7s} {"lat med":>8s}']
    for t, s in sorted(stats.items()):
        lat = f'{s.lat_med:.3f}' if s.lat_med is not None else ('(reloj)' if s.tiene_header and not s.reloj_ok else '-')
        l.append(f'{t:24s} {s.tipo.split("/")[-1]:26s} {s.n:5d} {s.ritmo:7.2f} {s.periodo_max:7.2f} {lat:>8s}')
    l += ['', 'Hallazgos:']
    for x in hallazgos:
        l.append(f'  [{x.severidad:5s}] {x.codigo:17s} {x.topic:22s} {x.detalle}')
    return '\n'.join(l)


def dibujar(series, stats, t0, ruta_png):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    colores = {t: f'C{i}' for i, t in enumerate(sorted(x for x in series if x not in TOPICS_SISTEMA))}
    for t, s in sorted(series.items()):
        if t in TOPICS_SISTEMA:
            continue
        rel = [x - t0 for x in s.recv]
        top = int(max(rel)) + 1 if rel else 1
        cuenta = [0] * top
        for x in rel:
            cuenta[min(int(x), top - 1)] += 1
        ax[0].plot(range(top), cuenta, label=t, color=colores[t])
    ax[0].set_ylabel('mensajes por segundo'); ax[0].legend(fontsize=8); ax[0].set_title('Ritmo por topic')
    for t, s in sorted(series.items()):
        st = stats[t]
        if s.stamps and st.reloj_ok:
            ax[1].plot([r - t0 for r in s.recv], [r - x for r, x in zip(s.recv, s.stamps)], label=t, color=colores[t])
    ax[1].set_ylabel('latencia (s)'); ax[1].legend(fontsize=8); ax[1].set_title('Latencia = grabacion - header.stamp')
    for t, s in sorted(series.items()):
        if s.valores:
            ax[2].plot([x - t0 for x in s.recv], s.valores, label=t, lw=1, color=colores[t])
    ax[2].set_ylabel('range (m)'); ax[2].set_xlabel('tiempo (s)'); ax[2].legend(fontsize=8)
    ax[2].set_title('Valores (sustituto de RViz sin pantalla)')
    fig.tight_layout(); fig.savefig(ruta_png, dpi=110); plt.close(fig)


def _parse_esperado(items):
    out = {}
    for it in items or []:
        k, _, v = it.partition('=')
        out[k] = float(v)
    return out


def analizar_ruta(ruta, cadena=None, esperado=None, lat_max=0.1):
    series, t0 = leer_bag(ruta)
    stats = {t: estadisticas(s, t0) for t, s in series.items()}
    return series, stats, t0, diagnosticar(stats, cadena, esperado, lat_max)


def main(argv=None):
    ap = argparse.ArgumentParser(description='Autopsia de un rosbag2 sin ROS2')
    ap.add_argument('bag', help='carpeta del bag (con metadata.yaml)')
    ap.add_argument('--cadena', default=','.join(CADENA_POR_DEFECTO),
                    help='topics en orden entrada->salida separados por comas ("" para ninguna)')
    ap.add_argument('--esperado', action='append', help='ritmo esperado: /topic=10 (repetible)')
    ap.add_argument('--lat-max', type=float, default=0.1, help='latencia maxima aceptable en s (0.1)')
    ap.add_argument('--png', help='guarda graficas en este PNG')
    ap.add_argument('--info', action='store_true', help='solo muestra un resumen tipo `ros2 bag info`')
    a = ap.parse_args(argv)
    if a.info:
        print(info_bag(a.bag))
        return 0
    cadena = [c for c in a.cadena.split(',') if c]
    esperado = _parse_esperado(a.esperado)
    if cadena and not esperado:
        esperado = {cadena[0]: 10.0}
    series, stats, t0, hallazgos = analizar_ruta(a.bag, cadena, esperado, a.lat_max)
    print(informe(stats, hallazgos, Path(a.bag).name))
    if a.png:
        dibujar(series, stats, t0, a.png)
        print(f'\nGraficas guardadas en {a.png}')
    return 1 if any(x.severidad == 'ERROR' for x in hallazgos) else 0


if __name__ == '__main__':
    sys.exit(main())
