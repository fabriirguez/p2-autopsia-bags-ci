#!/usr/bin/env python3
"""simulador_bags.py - fabrica rosbag2 sinteticos del sistema de la S7 (sensor -> filtro -> controlador).

Sirve para los ejercicios 2 y 4 de la practica autonoma: generar tus PROPIOS bags, sanos o con un fallo
que tu decidas, y analizarlos con analiza_bag.py (no necesita ROS2; escribe MCAP, el formato por defecto
de ROS2 Jazzy).

Uso rapido:
    import simulador_bags as sim
    sim.generar('mi_sano', 'bags')                                   # sistema sano (10 Hz, 40 s)
    sim.generar('mi_hueco', 'bags', hueco=(10, 14))                  # el sensor calla entre 10 s y 14 s
    sim.generar('mi_float', 'bags', tipo_mensaje='Float32')          # mensajes SIN cabecera
    sim.generar('mi_fallo', 'bags', post=mi_funcion)                 # tu propio fallo (ver abajo)

Parametros de generar():
    frecuencia        Hz del sensor (10 por defecto)
    duracion          segundos de grabacion (40)
    hueco             (inicio, fin) en s: el sensor no publica en ese intervalo
    retardo_filtro    segundos que tarda el callback del filtro por mensaje (0 = rapido)
    profundidad       profundidad de la cola del filtro (10)
    reloj_filtro_cero True: el filtro estampa sus mensajes con tiempo 0
    topic_cmd         nombre del topic del controlador ('/cmd_vel_demo')
    tipo_mensaje      'Range' (con cabecera) o 'Float32' (sin cabecera) en /distancia y /distancia_filtrada
    fuera_de_rango    (inicio, fin, valor) en s: el sensor publica 'valor' (solo con Range)
    frame_id          frame del sensor ('sensor_link')
    post              funcion opcional: recibe la lista de mensajes y devuelve la lista modificada.
                      Cada mensaje es una tupla (topic, tipo, instante_absoluto_s, mensaje). Aqui esta
                      tu libertad para inventar un fallo nuevo (duplicar, retrasar, borrar, reordenar...).
    semilla           semilla del ruido (7): mismo valor -> mismo bag
"""
import math
import random
import shutil
from collections import deque
from pathlib import Path

from rosbags.rosbag2 import StoragePlugin, Writer
from rosbags.typesys import Stores, get_typestore

TS = get_typestore(Stores.ROS2_JAZZY)
Range = TS.types['sensor_msgs/msg/Range']
Float32 = TS.types['std_msgs/msg/Float32']
Twist = TS.types['geometry_msgs/msg/Twist']
Vector3 = TS.types['geometry_msgs/msg/Vector3']
Header = TS.types['std_msgs/msg/Header']
Time = TS.types['builtin_interfaces/msg/Time']
T0 = 1_791_900_000.0      # instante absoluto de inicio (s)


def _t(seg):
    ns = int(round(seg * 1e9))
    return Time(sec=ns // 10**9, nanosec=ns % 10**9)


def _range(stamp_s, valor, frame):
    return Range(header=Header(stamp=_t(stamp_s), frame_id=frame), radiation_type=1,
                 field_of_view=0.1, min_range=0.02, max_range=4.0, range=float(valor), variance=0.0)


def _twist(x):
    return Twist(linear=Vector3(x=float(x), y=0.0, z=0.0), angular=Vector3(x=0.0, y=0.0, z=0.0))


def _muestras(rnd, frecuencia, duracion, hueco, fuera):
    dt = 1.0 / frecuencia
    out, k = [], 0
    while k * dt < duracion:
        t = max(k * dt + rnd.uniform(-0.001, 0.001) * (frecuencia / 10.0), 0.0)
        if not (hueco and hueco[0] <= t < hueco[1]):
            valor = 1.0 + 0.8 * math.sin(t / 3.0) + rnd.gauss(0.0, 0.03)
            if fuera and fuera[0] <= t < fuera[1]:
                valor = fuera[2]
            out.append((T0 + t, valor))
        k += 1
    return out


def _filtrar(muestras, retardo=0.0, profundidad=10, proc=0.003):
    """Cola del filtro (KEEP_LAST): devuelve [(instante_publicacion, sello_entrada, media)]."""
    ventana, salidas = deque(maxlen=5), []
    pendientes, libre_en = deque(maxlen=profundidad), 0.0
    servicio = retardo if retardo > 0 else proc

    def servir(hasta):
        nonlocal libre_en
        while pendientes and max(libre_en, pendientes[0][0] + 0.002) <= hasta:
            recv, sello, valor = pendientes.popleft()
            fin = max(libre_en, recv + 0.002) + servicio
            libre_en = fin
            ventana.append(valor)
            salidas.append((fin, sello, sum(ventana) / len(ventana)))

    for sello, valor in muestras:
        servir(sello + 0.002)
        pendientes.append((sello, sello, valor))
    servir(float('inf'))
    return salidas


def mensajes(*, frecuencia=10.0, duracion=40.0, hueco=None, retardo_filtro=0.0, profundidad=10,
             reloj_filtro_cero=False, topic_cmd='/cmd_vel_demo', tipo_mensaje='Range',
             fuera_de_rango=None, frame_id='sensor_link', semilla=7):
    """Lista de mensajes (topic, tipo, instante_abs, mensaje) ordenada por instante de grabacion."""
    if tipo_mensaje not in ('Range', 'Float32'):
        raise ValueError("tipo_mensaje debe ser 'Range' o 'Float32'")
    rnd = random.Random(semilla)
    muestras = _muestras(rnd, frecuencia, duracion, hueco, fuera_de_rango)
    tipo = 'sensor_msgs/msg/Range' if tipo_mensaje == 'Range' else 'std_msgs/msg/Float32'

    def crea(stamp, valor):
        return _range(stamp, valor, frame_id) if tipo_mensaje == 'Range' else Float32(data=float(valor))

    msgs = [('/distancia', tipo, s + 0.002, crea(s, v)) for s, v in muestras]
    for fin, sello, media in _filtrar(muestras, retardo_filtro, profundidad):
        stamp_msg = 0.0 if reloj_filtro_cero else sello
        msgs.append(('/distancia_filtrada', tipo, fin + 0.002, crea(stamp_msg, media)))
        msgs.append((topic_cmd, 'geometry_msgs/msg/Twist', fin + 0.007, _twist(0.0 if media < 0.5 else 0.5)))
    msgs = [m for m in msgs if m[2] <= T0 + duracion]
    msgs.sort(key=lambda m: m[2])
    return msgs


def escribir_bag(nombre, destino, msgs):
    """Escribe una lista de mensajes como bag rosbag2 (MCAP) en destino/nombre. Devuelve (ruta, n)."""
    ruta = Path(destino) / nombre
    shutil.rmtree(ruta, ignore_errors=True)
    Path(destino).mkdir(parents=True, exist_ok=True)
    msgs = sorted(msgs, key=lambda m: m[2])
    with Writer(ruta, version=9, storage_plugin=StoragePlugin.MCAP) as w:
        conexiones = {}
        for topic, tipo, _, _ in msgs:
            if topic not in conexiones:
                conexiones[topic] = w.add_connection(topic, tipo, typestore=TS)
        for topic, tipo, t, msg in msgs:
            w.write(conexiones[topic], int(round(t * 1e9)), TS.serialize_cdr(msg, tipo))
    return ruta, len(msgs)


def generar(nombre, destino='bags', *, post=None, **opciones):
    """Genera el bag destino/nombre. Ver la cabecera del fichero para las opciones."""
    msgs = mensajes(**opciones)
    if post is not None:
        msgs = post(msgs)
    ruta, n = escribir_bag(nombre, destino, msgs)
    print(f'{nombre}: {n} mensajes -> {ruta}')
    return ruta


if __name__ == '__main__':
    generar('mi_sano', 'bags')
