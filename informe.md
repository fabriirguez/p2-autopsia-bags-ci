# Práctica P2 (Tema 2) — Informe

**Nombre:** <<RELLENAR>>
**Fecha:** <<RELLENAR>>
**Entorno usado:** (Colab / local; versión de Python; ¿ROS2? ¿cuál?) <<RELLENAR>>

> Regla de oro: **hipótesis escrita ANTES de medir**. Cada afirmación lleva su evidencia (comando + salida o gráfica).

---

## Declaración de autoría y uso de IA

Trabajo individual. Fuentes consultadas: <<RELLENAR>>
Uso de asistentes de IA (para qué, o «ninguno»): <<RELLENAR>>

## Ejercicio 1 — Caso 5 (`bags/caso_5_casa`)

| Campo | Contenido |
|---|---|
| Síntoma (lo que se observa) | El sistema está «vivo»: los tres topics existen y publican. Pero `/cmd_vel_demo` solo recibe **1 orden por segundo** en lugar de 10, y lo que debería ocurrir es que el controlador actúe a 10 Hz como en la línea base (400 mensajes por topic en 40 s). Consecuencia: el robot reacciona tarde y a saltos. |
| Hipótesis (escrita antes de ejecutar nada) | Escrita solo con `--info` (`evidencias/ej1/caso5_info.txt`) y comparada con la línea base (`evidencias/ej1/caso0_info.txt`), **antes** del análisis completo; queda en el commit «Escribe la hipótesis del caso 5 antes de medir», anterior al del análisis. **Lo que veo:** los tres topics tienen 40 mensajes en 39 s (≈ 1 Hz), frente a 400 en la línea base (10 Hz); los tres topics existen, con el tipo correcto, y la cuenta **no cae a lo largo de la cadena** (40 → 40 → 40). **H1 (principal):** el sensor publica a ≈ 1 Hz en origen; el filtro y el controlador hacen bien su trabajo y se limitan a propagar ese ritmo (como el caso D de la S7). *Predicción:* `RITMO_BAJO` en `/distancia` (≈ 1 Hz frente a 10 Hz), **sin** `CAIDA_EN_CADENA`, latencia baja (el filtro no hace cola) y sin `HUECOS` si los mensajes llegan espaciados de forma regular (dt ≈ 1 s en todo el bag). **H2 (alternativa):** el sensor va a 10 Hz pero solo durante ≈ 4 s y después se calla. Daría la misma cuenta en `--info`, pero la herramienta marcaría `HUECOS`/`HUECO_ORIGEN` en `/distancia` con un `max dt` de decenas de segundos. Para distinguirlas miraré `max dt` y la gráfica de ritmo. **H3 (descartada de antemano):** fallo en el filtro o en el controlador. Si fuera así, la cuenta caería en algún eslabón y no cae. **Fallo estructural:** descartado, porque los tres topics existen con nombre y tipo correctos. **Reloj:** `--info` no lo muestra; espero que no haya `RELOJ_DESFASADO`. |
| Comando(s) | `python3 analiza_bag.py bags/caso_5_casa --esperado /distancia=10 --png informe_caso5.png` |
| Evidencia (salida / gráfica) | `evidencias/ej1/caso5_analisis.txt` y `informe_caso5.png`: `/distancia`, `/distancia_filtrada` y `/cmd_vel_demo` van todos a **1,00 Hz**, con `max dt` = 1,00 s. **Único hallazgo:** `[ERROR] RITMO_BAJO /distancia 1.00 Hz medidos frente a 10 Hz esperados` (salida 1). **Confirma la H1:** no hay `CAIDA_EN_CADENA`, la latencia mediana es de 0,002 s en el sensor y 0,007 s en el filtro (igual que en la línea base) y no hay `HUECOS` ni `RELOJ_DESFASADO`. **Descarta la H2:** con `max dt` = 1,00 s los mensajes están espaciados de forma regular; no hay ninguna ráfaga seguida de silencio. **Lectura de la gráfica:** en el panel de ritmo, el zigzag 0/2 de `/distancia` es un artefacto del histograma. Los mensajes llegan en 0,000, 1,000, 2,000 s… justo en el borde de las cajas de 1 s, y el redondeo los manda a la caja de al lado (los instantes están en `evidencias/ej1/retraso_senal.txt`). **Medida extra (`herramientas_extra/retraso_senal.py`, correlación cruzada de `range`):** la señal filtrada va **2,0 s** por detrás de la cruda, frente a 0,30 s en la línea base. Cada mensaje llega fresco (7 ms), pero su contenido es viejo, porque el filtro trabaja en número de muestras y su retraso crece con el periodo del sensor. **Contraste causal (`evidencias/ej1/reproduccion_causa.txt`):** el simulador con `frecuencia=1` reproduce la misma huella (40 mensajes, 1,00 Hz, 2 y 7 ms, 2,0 s) y con `frecuencia=10` da `TODO_OK` (0,30 s). |
| Eslabón donde se rompe | **Aguas arriba de `/distancia`: el propio nodo sensor (o su driver).** Los eslabones siguientes conservan el 100 % del ritmo que reciben: filtro (`/distancia` → `/distancia_filtrada`, 40 → 40) y controlador (`/distancia_filtrada` → `/cmd_vel_demo`, 40 → 40). Solo propagan el ritmo bajo, como muestra la evidencia. |
| Familia (estructural / dinámico / tiempo / origen) | **Dinámico, con origen aguas arriba:** es el «ritmo bajo en origen» del caso D de la S7. Lo que falla es el ritmo, no la conexión, y el fallo nace en el primer eslabón. **No es estructural:** el grafo conecta y los nombres, tipos y QoS son correctos. **No es de tiempo:** los sellos son coherentes. **No es un hueco de origen (familia «origen» de la S8):** no hay silencios, sino un ritmo constante pero bajo. |
| Causa raíz probable | El nodo sensor está configurado para publicar a 1 Hz y no a 10 Hz. Lo más probable es un parámetro de frecuencia mal puesto (`frecuencia: 1.0` en el YAML o el launch). Otra posibilidad típica es un error de unidades, al crear el temporizador con `create_timer(1.0, …)` (periodo en s) en lugar de `create_timer(1.0 / frecuencia, …)`. **Lo que no sé:** el bag no guarda parámetros, código ni logs, así que no puedo distinguir entre un parámetro, el código o un driver de hardware configurado a 1 Hz. Tampoco puedo descartar desde el bag que el sensor estuviera **diseñado** a 1 Hz (ver la pregunta de control). |
| Arreglo concreto y cómo comprobarlo | **1) Confirmar en vivo:** `ros2 param get /<nodo_sensor> frecuencia` y `ros2 topic hz /distancia` (espero ≈ 1 Hz). **2) Arreglar:** en el fichero de parámetros del sensor, poner `frecuencia: 10.0` (y, si es un error de unidades, el temporizador con `1.0 / frecuencia`). **3) Comprobar:** `ros2 topic hz` en los tres topics ≈ 10 Hz, volver a grabar con `ros2 bag record -o caso5_arreglado /distancia /distancia_filtrada /cmd_vel_demo` y pasar `python3 analiza_bag.py caso5_arreglado --esperado /distancia=10` → `TODO_OK` (salida 0), con un retraso de la señal ≈ 0,3 s en `retraso_senal.py`. **4) Que no vuelva a pasar:** que el ritmo esperado viva en el contrato (`esperado.json → esperado_hz`) y se compruebe en la CI. Como mejora de arquitectura, definir la ventana del filtro en **segundos**, no en muestras, para que su retraso no dependa del ritmo del sensor. |

¿Qué os dice el grafo del sistema y qué os dice el bag? (pista: comparad con el caso D de la S7)

**El grafo** (`rqt_graph`, `ros2 topic info -v`) diría que todo está bien: sensor → filtro → controlador conectados, con tipos y QoS compatibles. Pero el grafo es una foto **estructural** y no tiene dimensión de tiempo: no sabe a qué ritmo fluyen los datos. Igual que en el caso D de la S7, «el grafo es correcto, pero el ritmo cae», así que con el grafo solo se descarta la familia estructural. **El bag** añade la dimensión temporal. Da el ritmo de **todos los eslabones a la vez**, donde en la S7 había que ir topic a topic con `ros2 topic hz`. Da también la latencia de cada mensaje y los valores, y por eso señala el origen y no un eslabón intermedio. Además, con los valores se puede medir un efecto que ni el grafo ni la latencia ven: la señal que usa el controlador va 2 s retrasada.

**Pregunta de control (sensor diseñado a 1 Hz).** Sin `--esperado`, `main()` hace `esperado = {cadena[0]: 10.0}`. Con un sensor que de verdad está diseñado a 1 Hz, la herramienta daría un **falso positivo** `RITMO_BAJO` y saldría con 1, rompiendo la CI sin motivo. Lo he comprobado: `python3 analiza_bag.py bags/caso_5_casa --esperado /distancia=1` → `TODO_OK`, salida 0. Por tanto **el bag no puede decir por sí solo si 1 Hz es un fallo**: depende del requisito. Ese requisito no debe estar escrito en el código de la herramienta. Debe vivir **junto al sistema que lo define y versionado con él**: en la especificación o interfaz del nodo sensor (parámetro declarado con su rango) y en el contrato de pruebas que lee la herramienta (`esperado.json → esperado_hz`, que ya existe en este repositorio). Así, si el diseño cambia a 1 Hz, se cambia el contrato en un commit revisado y no un número escondido en la herramienta.

## Ejercicio 2 — Mis propios bags

**Hipótesis (escrita antes de generar y medir; commit «Escribe la hipótesis del ejercicio 2»).** Fallo elegido: **callback del filtro de 0,15 s** (distinto del caso 1, que tenía 0,4 s). Con él, el filtro solo puede procesar 1 / 0,15 ≈ **6,7 Hz** frente a los 10 Hz que entran. Predicciones:
- `mi_lento` (Range, cola de 10): la cola se llena y la salida baja a ≈ 6,7 Hz, por debajo del 80 % de 10 Hz → `CAIDA_EN_CADENA` en `/distancia_filtrada`. Con la cola llena, cada mensaje avanza un puesto por cada mensaje que entra (cada 0,1 s), así que espera ≈ 10 × 0,1 s = 1,0 s; sumando el callback, la latencia será ≈ **1,1-1,2 s** → `LATENCIA_ALTA`.
- `mi_lento_cola1` (lo mismo con cola de 1): el ritmo cae igual (el filtro no es más rápido), pero la latencia baja a ≈ 0,1-0,25 s, porque siempre se procesa el dato más reciente y se descarta el resto. Es posible que aún supere el umbral de 0,1 s.
- `mi_float_sano` y `mi_float_lento` (Float32, sin cabecera): la herramienta solo puede contar mensajes y mirar los instantes de grabación. Se detectará la `CAIDA_EN_CADENA`, pero **desaparecerá `LATENCIA_ALTA`** (no hay `header.stamp`) y no se podrá comprobar el reloj (`RELOJ_DESFASADO`).

Bags entregados (en `bags/`, nombres que empiezan por `mi_`): `mi_sano` (sano, Range), `mi_lento` (callback del filtro de 0,15 s, cola de 10), `mi_lento_cola1` (el mismo fallo con cola de 1), `mi_float_sano` (sano, Float32 sin cabecera) y `mi_float_lento` (el mismo fallo, Float32). `mi_rango` es del ejercicio 3.
Cómo los generé (comandos): sin ROS2, con `simulador_bags.py` (semilla fija → bags idénticos en cada ejecución). **Se regeneran todos con un solo comando: `bash generar_mis_bags.sh`**, que contiene exactamente estas llamadas:
```python
sim.generar('mi_sano',        'bags')
sim.generar('mi_lento',       'bags', retardo_filtro=0.15)
sim.generar('mi_lento_cola1', 'bags', retardo_filtro=0.15, profundidad=1)
sim.generar('mi_float_sano',  'bags', tipo_mensaje='Float32')
sim.generar('mi_float_lento', 'bags', tipo_mensaje='Float32', retardo_filtro=0.15)
```
Análisis: `for b in mi_sano mi_lento mi_lento_cola1 mi_float_sano mi_float_lento; do python3 analiza_bag.py bags/$b --esperado /distancia=10; done` → `evidencias/ej2/analisis_mis_bags.txt` (gráficas: `evidencias/ej2/grafica_mi_lento.png` y `grafica_mi_float_lento.png`). La vía con ROS2 (`ros2 bag record`) no la he hecho: no tengo ROS2 instalado en el entorno de trabajo.

Tabla comparativa sano / con fallo (ritmos, latencia, hallazgos):

| Bag | Tipo | `/distancia` Hz | `/distancia_filtrada` Hz | `/cmd_vel_demo` Hz | Latencia mediana del filtro (máx.) | Hallazgos | Salida | ¿Se cumple la hipótesis? |
|---|---|---|---|---|---|---|---|---|
| `mi_sano` | Range | 10,00 | 10,00 | 10,00 | 0,007 s | `TODO_OK` | 0 | — (referencia) |
| `mi_lento` | Range | 10,00 | **6,67** | 6,67 | **1,104 s** (1,16) | `CAIDA_EN_CADENA`, `LATENCIA_ALTA` | 1 | Sí: predije ≈ 6,7 Hz y ≈ 1,1-1,2 s |
| `mi_lento_cola1` | Range | 10,00 | **6,67** | 6,67 | **0,204 s** (0,25) | `CAIDA_EN_CADENA`, `LATENCIA_ALTA` | 1 | Sí: el mismo ritmo, pero la latencia se divide por 5 y sigue por encima de 0,1 s |
| `mi_float_sano` | Float32 | 10,00 | 10,00 | 10,00 | — (no medible) | `TODO_OK` | 0 | — (referencia) |
| `mi_float_lento` | Float32 | 10,00 | **6,67** | 6,67 | — (no medible) | solo `CAIDA_EN_CADENA` | 1 | Sí: se pierde `LATENCIA_ALTA` |

Lectura: el eslabón es el filtro (`/distancia` → `/distancia_filtrada`) y la familia es **dinámica** (callback lento). `mi_lento` y `mi_lento_cola1` demuestran lo de la S8, «dimensionar una cola es dimensionar un retraso»: la cola no cambia cuánto procesa el filtro, solo **cuánto envejecen** los datos (1,10 s frente a 0,20 s). Para control, la cola de 1 es preferible: el dato es fresco aunque se pierdan muestras.

**¿Qué no puede medir la herramienta con mensajes sin cabecera (`Float32`)? ¿Por qué?** La latencia es `grabación − header.stamp`. Sin cabecera solo existe un instante, el de grabación, y falta el de **nacimiento del dato** en el sensor. Por eso no puede medir: (1) la **latencia** (`LATENCIA_ALTA`); (2) la **coherencia del reloj** (`RELOJ_DESFASADO`), porque no hay sellos que comparar; (3) tampoco puede emparejar cada salida del filtro con la entrada que la produjo, porque nada viaja con el dato. Además, sin `frame_id`, `min_range` y `max_range` tampoco servirían las comprobaciones del ejercicio 3, y la herramienta ni siquiera dibuja los valores (busca el campo `range`, y Float32 lo llama `data`). Lo único que queda es **contar mensajes y medir intervalos de grabación**: ritmo, huecos y caída en cadena.

**Mismo fallo, distinto tipo (`mi_lento` frente a `mi_float_lento`): ¿qué hallazgo se pierde?** Se pierde **`LATENCIA_ALTA` (1,10 s)**, que es precisamente el dato que más importa para el control: dice que el robot actúa con información de hace más de un segundo. La consecuencia la he comprobado (`evidencias/ej2/float_cola10_vs_cola1.txt`): con Float32, el fallo con cola de 10 y con cola de 1 dan **una salida idéntica**. La herramienta no puede distinguir «datos de hace 1,1 s» de «datos de hace 0,2 s», que llevan a arreglos distintos (reducir la cola frente a acelerar el callback).

**¿Qué haría en el sistema real para medir latencia sin cabecera?** (1) **Lo mejor: cambiar la interfaz** a un mensaje con sello de tiempo (`sensor_msgs/Range` o un tipo propio con `std_msgs/Header`), y que el filtro **copie el `header.stamp` de entrada** a su salida en lugar de poner `now()`, para que el sello represente el origen del dato. (2) Si la interfaz no se puede tocar: publicar **en paralelo** un topic de diagnóstico con sello (p. ej. un `Header` con el instante de recepción y el de salida en cada nodo). También se puede instrumentar el sistema con **`ros2_tracing`** (LTTng), que mide cuándo se publica cada mensaje y cuánto dura cada callback sin cambiar los mensajes. (3) Como mínimo, medir la **duración del callback** del filtro con logs o estadísticas (`ros2 topic hz` en cada eslabón y tiempos de callback). Con eso se obtiene la capacidad del nodo, aunque no la edad del dato.

## Ejercicio 3 — Extensión de la herramienta

Comprobación(es) implementada(s): <<RELLENAR>>
Decisiones de diseño (¿ERROR o WARN? ¿margen?, ¿qué falsos positivos hay?): <<RELLENAR>>
Pruebas propias añadidas (nombre y qué comprueban): <<RELLENAR>>
Salida de `python3 -m unittest -v test_mis_comprobaciones`: <<RELLENAR>>
Resultado sobre `bags/mi_rango` (antes: TODO_OK; ahora: ...): <<RELLENAR>>

## Ejercicio 4 — Un quinto fallo

Ficha del fallo (SIN la solución; es lo que recibirá tu compañero):
- Nombre del bag: <<RELLENAR>>
- Síntoma observable: <<RELLENAR>>
- Qué debe averiguar quien lo resuelva: <<RELLENAR>>

**Solución (aparte, en sobre cerrado hasta que el compañero entregue):**
- Cómo se genera (parámetros o función `post`): <<RELLENAR>>
- Hallazgo(s) de `analiza_bag.py` que lo detectan, o por qué la herramienta no lo detecta: <<RELLENAR>>
- Eslabón, familia, causa y arreglo: <<RELLENAR>>

Resultado de la resolución del compañero (¿acertó? ¿qué le faltó? Si no hubo intercambio, «sin intercambio» y por qué): <<RELLENAR>>

## Ejercicio 5 — Lista de comprobación ampliada

Las 7 preguntas de la clase + 3 mías (cada una con su herramienta, qué detecta y un caso que la justifique):

| # | Pregunta | Herramienta | Detecta | Caso que la justifica |
|---|---|---|---|---|
| 8 | <<RELLENAR>> | | | |
| 9 | <<RELLENAR>> | | | |
| 10 | <<RELLENAR>> | | | |

## Ejercicio 6 — Autoformación guiada

Puntos de control de la *Guía de autoformación de la S8* (resumen de lo aprendido y dudas): <<RELLENAR>>

## Ejercicio 7 — Repositorio Git con integración continua

| Campo | Contenido |
|---|---|
| URL del repositorio (público, o privado con acceso para el profesor) | <<RELLENAR>> |
| Nº de commits y rama(s) de trabajo | <<RELLENAR>> |
| Pull Request (o merge) que integra una rama en `main` (URL) | <<RELLENAR>> |
| Ejecución de CI en **verde** (URL de la ejecución en Actions) | <<RELLENAR>> |
| Ejecución de CI en **rojo** provocada a propósito (URL) y commit que la arregla | <<RELLENAR>> |
| Qué rompí a propósito y cómo lo diagnostiqué en el log | <<RELLENAR>> |
| Bag(s) que añadí a `esperado.json` y por qué | <<RELLENAR>> |

Si **no** has podido usar GitHub, escribe aquí por qué y adjunta en `evidencias/` el `git_log.txt`, la salida de `simula_ci.py` y las capturas `ci_rojo` / `ci_verde` de la simulación local: la nota máxima del ejercicio baja (ver enunciado).

## Memoria conceptual (con tus palabras; máximo 1 página en total)

**M1.** Familias de fallo de arquitectura (estructural, dinámico, de tiempo, de origen aguas arriba): un ejemplo de cada una y la herramienta más barata que la detectaría. <<RELLENAR>>

**M2.** ¿Por qué una herramienta de análisis necesita pruebas unitarias, y qué significa que «un fallo no detectado es una especificación pendiente»? <<RELLENAR>>

**M3.** ¿Qué ocurre exactamente en un conflicto de fusión en Git, cómo se ve en el fichero y cómo se resuelve? ¿Por qué no se debe «aceptar el mío» sin leer? <<RELLENAR>>

**M4.** ¿Qué garantiza y qué NO garantiza una CI en verde? Usa como ejemplo el contrato de regresión con bags. <<RELLENAR>>

## Opcional — `ros2 bag play` y RViz2

<<RELLENAR o "No realizado">>

## Reflexión final (5 líneas)

¿Qué fue lo más difícil? ¿Qué cambiarías en la herramienta? ¿Qué le faltó al bag para estar seguro de la causa? <<RELLENAR>>
