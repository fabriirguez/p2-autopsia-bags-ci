# P2 · Autopsia de sistemas con rosbag2, herramienta propia y CI

[![CI](https://github.com/fabriirguez/p2-autopsia-bags-ci/actions/workflows/ci.yml/badge.svg)](https://github.com/fabriirguez/p2-autopsia-bags-ci/actions/workflows/ci.yml)

**Arquitecturas Software para Robótica · UCJC · Tema 2 (sesiones 7, 8 y 9)**
Práctica P2 individual evaluable · **Fabricio Andree Rodriguez** · noviembre de 2026

Este repositorio contiene la práctica completa. El documento principal es **[`informe.md`](informe.md)**: diagnósticos, decisiones, evidencias, memoria conceptual y declaración de uso de IA. Este README explica cómo está organizado el repositorio y cómo reproducirlo.

---

## Qué hay aquí

El sistema analizado es el de la S7, una cadena de tres nodos:

```
sensor ──/distancia──▶ filtro ──/distancia_filtrada──▶ controlador ──/cmd_vel_demo──▶
        (Range, 10 Hz)          (Range)                              (Twist)
```

Los fallos se estudian **después de que ocurran**, a partir de grabaciones rosbag2 (MCAP, ROS 2 Jazzy), con una herramienta de análisis que no necesita ROS 2. El método es siempre el mismo: **hipótesis escrita antes de medir → medida → eslabón y familia → causa → arreglo comprobable**.

| Ejercicio | Resultado | Dónde verlo |
|---|---|---|
| **1 · Caso 5** | Ritmo bajo **en origen**: el sensor publica a 1 Hz (familia dinámica, como el caso D de la S7). Además, la señal filtrada va 2 s retrasada aunque cada mensaje tarde 7 ms. | [`informe.md`](informe.md) §1 · [`evidencias/ej1/`](evidencias/ej1) |
| **2 · Bags propios** | Sano / callback lento (0,15 s) con cola 10 y cola 1 / sin cabecera (`Float32`). Sin cabecera se pierde `LATENCIA_ALTA` y no se distingue la cola 10 (1,10 s) de la cola 1 (0,20 s). | §2 · [`evidencias/ej2/`](evidencias/ej2) |
| **3 · Herramienta** | Nuevas comprobaciones `RANGO_FUERA` (ERROR) y `FRAME_MIXTO` (WARN), con 10 pruebas propias escritas antes que el código (TDD) e integradas en `analiza_bag.py`. | [`mis_comprobaciones.py`](mis_comprobaciones.py) · [`test_mis_comprobaciones.py`](test_mis_comprobaciones.py) · [`evidencias/ej3/`](evidencias/ej3) |
| **4 · Quinto fallo** | `reto_1`: un filtro «zombi» republica un dato viejo durante 15 s y el robot se para sin motivo. La herramienta da `TODO_OK` (punto ciego documentado). | [`reto/`](reto) · §4 · [`evidencias/ej4/`](evidencias/ej4) |
| **5 · Lista ampliada** | Tres preguntas nuevas: contenido físicamente posible, dato nuevo frente a republicado y retraso de la señal. | §5 |
| **6 · Autoformación S8** | Etapas 0-3 en **ROS 2 Jazzy** (VM): `ros2 bag` record/info/play, compresión, partición, QoS overrides, tf2 y RViz2. | §6 · [`evidencias/ej6/`](evidencias/ej6) |
| **7 · Git y CI** | Historial con ramas y 5 *pull requests*, CI en GitHub Actions, rojo provocado y arreglado con un commit nuevo, y contrato de regresión ampliado. | §7 · [Actions](https://github.com/fabriirguez/p2-autopsia-bags-ci/actions) · [PRs](https://github.com/fabriirguez/p2-autopsia-bags-ci/pulls?q=is%3Apr) |
| **M · Memoria** | M1-M4: familias de fallo, pruebas de herramientas, conflictos de fusión y qué garantiza una CI en verde. | §Memoria |

## Cómo reproducirlo

Requisitos: Python 3.9 o superior y Git. ROS 2 **no** hace falta.

```bash
git clone https://github.com/fabriirguez/p2-autopsia-bags-ci && cd p2-autopsia-bags-ci
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONDONTWRITEBYTECODE=1

bash ci_local.sh                     # lo mismo que la CI: pruebas + regresión con bags + bag sano  → VERDE
```

Comandos útiles:

```bash
python3 analiza_bag.py bags/caso_5_casa --info                                         # resumen tipo «ros2 bag info»
python3 analiza_bag.py bags/caso_5_casa --esperado /distancia=10 --png informe_caso5.png   # autopsia + gráfica
python3 mis_comprobaciones.py bags/mi_rango /distancia                                 # ej. 3 → RANGO_FUERA (salida 1)
python3 -m unittest -v test_mis_comprobaciones                                         # 19 pruebas (10 propias)
python3 regresion_bags.py                                                              # contrato esperado.json → 7/7
bash generar_mis_bags.sh                                                               # regenera todos los bags mi_* (semilla fija)
python3 herramientas_extra/retraso_senal.py bags/caso_5_casa                           # retraso de la señal entre topics
python3 herramientas_extra/por_tramos.py bags/mi_fallo 15 30                           # valores, sellos y latencia por tramos
```

## Estructura

| Ruta | Contenido |
|---|---|
| [`informe.md`](informe.md) | **Informe de la práctica** (todos los ejercicios, memoria y declaración de IA) |
| [`analiza_bag.py`](analiza_bag.py) | Herramienta de autopsia de bags (kit de la S8) con las comprobaciones del ej. 3 integradas en `analizar_ruta` |
| [`mis_comprobaciones.py`](mis_comprobaciones.py) | `comprobar_rangos` (`RANGO_FUERA`), `comprobar_frames` (`FRAME_MIXTO`) y `comprobar_bag` |
| `test_analiza_bag.py`, [`test_mis_comprobaciones.py`](test_mis_comprobaciones.py) | Pruebas del kit y pruebas del ejercicio 3 (`PruebasPropias`) |
| [`herramientas_extra/`](herramientas_extra) | `retraso_senal.py` (correlación cruzada) y `por_tramos.py` (análisis por intervalos), usados como evidencia |
| [`bags/`](bags) | `caso_0` … `caso_5_casa` (kit) y mis bags `mi_*` (MCAP, pequeños, versionados) |
| [`generar_mis_bags.sh`](generar_mis_bags.sh) | Regenera todos los bags propios con un comando (`simulador_bags.py`) |
| [`reto/`](reto) | Quinto fallo empaquetado sin pistas (`reto_1`) y su ficha (solo el síntoma) |
| [`esperado.json`](esperado.json) + [`regresion_bags.py`](regresion_bags.py) | Contrato de regresión: diagnóstico esperado de cada bag (incluye `mi_rango` y `mi_fallo`) |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | CI: pruebas unitarias, regresión con bags y bag sano en cada *push* y *pull request* |
| `ci_local.sh`, `simula_ci.py` | La misma CI ejecutada en local |
| [`evidencias/`](evidencias) | Salidas y gráficas por ejercicio, capturas de la CI en rojo y en verde, `git_log.txt` |
| `simulador_bags.py`, `empaquetar_reto.py`, `entrega.py` | Utilidades del kit (simulador de bags, empaquetado del reto, autocomprobación y zip) |

Los bags son **sintéticos**: modelan cola, bloqueo, reloj, huecos y ritmo del sistema de la S7, pero no son capturas de un robot real.

## Integración continua

El workflow [`ci.yml`](.github/workflows/ci.yml) se ejecuta en cada *push* a `main` y en cada *pull request*:

1. `python -m unittest discover -v`: pruebas del kit y pruebas propias;
2. `python regresion_bags.py`: cada bag de referencia debe dar **exactamente** el diagnóstico de `esperado.json`;
3. `python analiza_bag.py bags/caso_0_linea_base`: el sistema sano debe dar `TODO_OK`.

Ejecuciones destacadas: [rojo provocado a propósito](https://github.com/fabriirguez/p2-autopsia-bags-ci/actions/runs/40731881059) (umbral de latencia subido a 2 s → falla `test_caso1_callback_bloqueante`) y [verde tras el arreglo](https://github.com/fabriirguez/p2-autopsia-bags-ci/actions/runs/40732047349) con un commit nuevo, sin reescribir la historia.

> Una CI en verde garantiza que la herramienta se comporta **como especifica el contrato**, no que no haya fallos. `mi_fallo` está en el contrato con `TODO_OK` aunque contiene un fallo real (memoria, M4).

## Autoría y uso de IA

Trabajo individual. He usado un asistente de IA (Claude, de Anthropic) como apoyo, y el detalle de para qué está en la declaración del [`informe.md`](informe.md). Los commits de los ejercicios 1-5 llevan la línea `Co-Authored-By`; los del ejercicio 6 y de la parte de GitHub del 7 también los hizo el asistente siguiendo mis guiones, aunque no la llevan. Las medidas, capturas y ejecuciones en ROS 2 son mías, y puedo explicar cada decisión y cada resultado.
