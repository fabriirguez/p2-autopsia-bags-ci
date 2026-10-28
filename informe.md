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

Comprobación(es) implementada(s): las dos, en `mis_comprobaciones.py` y sin cambiar nombres ni firmas.
- **`comprobar_rangos` → `ERROR RANGO_FUERA`**: devuelve un único hallazgo con cuántas muestras fallan y de cuántas, el intervalo (primera y última), en cuántos tramos y entre qué valores. Usa los `min_range` y `max_range` **de cada mensaje** (intervalo cerrado). `±Inf` → `INFO RANGO_INFINITO` (no es error); `NaN` → error; margen negativo → `ValueError`.
- **`comprobar_frames` → `WARN FRAME_MIXTO`** (ampliación): lista los `frame_id` en orden de aparición con su cuenta; el frame vacío cuenta como uno más.
- **Integración**: `analiza_bag.analizar_ruta` aplica ambas a todos los topics `sensor_msgs/msg/Range` mediante `comprobar_bag()`, con un import tardío para evitar la importación circular. Así, la regresión con bags y la CI vigilan los rangos sin que nadie tenga que acordarse de ejecutar otro script.
- **Proceso (TDD) en la rama `ej3-rango`**: primero las pruebas en rojo (commit «Añade pruebas propias…»), después la implementación y por último la integración y el contrato.
Decisiones de diseño (¿ERROR o WARN? ¿margen?, ¿qué falsos positivos hay?):
- **¿Por qué `RANGO_FUERA` es ERROR?** El valor es **físicamente imposible** para ese sensor según sus propios límites, y `sensor_msgs/Range` dice que esos valores deben descartarse. Además **se propaga**: en `mi_rango` el filtro mete el 9,9 en su media y `/distancia_filtrada` también se sale (22 muestras, 4,17-9,90 m). El controlador acabaría actuando como si tuviera 9,9 m libres delante, que es un riesgo de seguridad. El origen se ve porque `/distancia` empieza antes (10,1 s frente a 10,2 s).
- **¿Por qué `FRAME_MIXTO` es WARN?** Cada valor puede ser correcto y el cambio de frame puede ser legítimo: varios sensores publicando en un mismo topic, o un frame renombrado tras cambiar la configuración. Es un síntoma que pide revisión humana (tf2 colocaría el dato en otro sitio), pero por sí solo no demuestra que el dato sea falso, así que no rompe la CI.
- **Margen = 0** (integración y por defecto). Los límites los declara el propio sensor en cada mensaje, así que un valor fuera de ellos es inválido por definición, y los extremos se aceptan (prueba `test_valor_exactamente_en_los_limites_es_valido`). Solo usaría un margen pequeño, del orden de la resolución del sensor (≈ 1 cm), si un sensor real satura en `max_range + ruido`. Es configurable en `comprobar_bag(..., margen=)`.
- **Falsos positivos posibles y qué hago con ellos:** (1) **`±Inf` como «sin detección» o «demasiado cerca»** (convenio de `Range.msg`): tratarlos como error dispararía la CI con cualquier sensor que mira al vacío, así que los cuento como INFO (prueba `test_inf_es_convenio_sin_deteccion_no_error`). (2) **Saturación con ruido** (`max_range + ε`): se resuelve con el margen. (3) **Límites mal configurados en el driver** (p. ej. `max_range = 0`): todas las muestras saldrían como `RANGO_FUERA`. No es un falso positivo del dato sino de los metadatos, pero el hallazgo lo deja ver (detalle «p. ej. [min, max]»). (4) **Sensores de distancia fija** (`min_range == max_range`, con ±Inf): cubiertos por la regla de Inf. (5) **Topics derivados** (filtro): heredan el error del origen, así que en un sistema con muchos derivados conviene informar solo del primero, como hace `HUECO_ORIGEN`. Lo dejo como mejora.
Pruebas propias añadidas (nombre y qué comprueban), 10 en `PruebasPropias`:

| Prueba | Qué comprueba |
|---|---|
| `test_valor_exactamente_en_los_limites_es_valido` | `range == min_range` y `range == max_range` son válidos (intervalo cerrado) |
| `test_margen_exacto_y_justo_por_encima` | `max + margen` pasa; `max + margen + 1e-6` falla |
| `test_margen_negativo_no_se_admite` | un margen negativo lanza `ValueError` |
| `test_un_solo_hallazgo_con_cuenta_e_intervalo` | un único hallazgo, con «3 de 5» y el intervalo 10.0 s-11.9 s |
| `test_limites_por_muestra_no_globales` | se usan los límites de cada mensaje |
| `test_inf_es_convenio_sin_deteccion_no_error` | `±Inf` → solo `INFO RANGO_INFINITO`, sin ERROR (falso positivo evitado) |
| `test_nan_es_medida_invalida` | `NaN` → `ERROR RANGO_FUERA` con «NaN» en el detalle |
| `test_frame_vacio_cuenta_como_frame_distinto` | `''` cuenta como frame y aparece como «(vacío)» |
| `test_mi_fallo_de_rango_cuenta_muestras_e_intervalo` | mi bag: 20 de 150 muestras, intervalo ≈ 10-12 s |
| `test_integrado_en_analiza_bag` | `analizar_ruta` da `RANGO_FUERA` (y no `TODO_OK`) en el bag malo y `TODO_OK` en el sano |

Lección: mi primera versión de `test_mi_fallo_de_rango…` esperaba exactamente «10.0 s - 11.9 s» y falló. **La herramienta tenía razón**: el simulador añade ±1 ms de jitter, la muestra de 10,0 s puede caer justo antes de la ventana y la de 12,0 s justo dentro (sale 10.1 s-12.0 s). Corregí **la prueba** (tolerancia) y no el código: una prueba también puede tener una especificación equivocada.
Salida de `python3 -m unittest -v test_mis_comprobaciones`: completa en `evidencias/ej3/unittest_mis_comprobaciones.txt` → **`Ran 19 tests … OK`**: 7 dadas de rangos, 2 de frames (ya no se omiten) y 10 propias. Las 13 originales de `test_analiza_bag` siguen pasando (`bash ci_local.sh` → «VERDE: todo pasa»).
Resultado sobre `bags/mi_rango` (antes: TODO_OK; ahora: ...):
- **Antes** (`evidencias/ej3/mi_rango_antes.txt`): `[INFO] TODO_OK`, salida 0.
- **Ahora** (`evidencias/ej3/mi_rango_despues.txt`): `python3 mis_comprobaciones.py bags/mi_rango /distancia` → `[ERROR] RANGO_FUERA /distancia 20 de 400 muestras fuera de [...] (p. ej. [0.02, 4.00] m) entre 10.1 s y 12.0 s, en 1 tramo(s); valores de 9.90 a 9.90 m`, **salida 1**. Con el bag sano `caso_0_linea_base`, salida 0. Integrado en `analiza_bag.py`, aparece además `RANGO_FUERA` en `/distancia_filtrada` (propagación).
- Al integrarla, la regresión **se puso en rojo sola** (`evidencias/ej3/regresion_detecta_cambio.txt`: `mi_rango esperado ninguno (salida 0), obtenido ['RANGO_FUERA'] (salida 1)`). El contrato hizo su trabajo: obliga a actualizar `esperado.json` a propósito, en la misma rama y con explicación (ejercicio 7).

## Ejercicio 4 — Un quinto fallo

Ficha del fallo (SIN la solución; es lo que recibirá tu compañero):
- Nombre del bag: `reto/reto_1`. Generado como `bags/mi_fallo` y empaquetado con `python3 empaquetar_reto.py bags/mi_fallo reto/`. La ficha completa está en `reto/reto_1_ficha.md`.
- Síntoma observable: «A mitad de la prueba el robot se detuvo y se quedó parado más de diez segundos, aunque delante no había nada que le impidiera avanzar. Después volvió a moverse él solo. No apareció ningún error en pantalla y nadie tocó el robot.»
- Qué debe averiguar quien lo resuelva: (1) si es un fallo o un comportamiento correcto del controlador, con datos; (2) el eslabón; (3) la familia; (4) la causa probable y qué no se puede saber solo con el bag; (5) un arreglo concreto y cómo comprobarlo; (6) los comandos usados y qué dijo cada uno. Se pide hipótesis antes de medir.
- **Cuidado al empaquetar (fallo encontrado en el kit):** mi primer bag tenía un nombre descriptivo y, tras empaquetarlo, `grep` encontró ese nombre **dentro del `.mcap`**. rosbag2 guarda una copia de los metadatos dentro del propio MCAP, y `empaquetar_reto.py` solo limpia `metadata.yaml`. Lo resolví generando el bag con el nombre neutro `mi_fallo`, sin modificar el script del kit, y comprobé que en `reto/` no queda ninguna pista textual.

**Solución (aparte, en sobre cerrado hasta que el compañero entregue):**
- Cómo se genera (parámetros o función `post`): `bash generar_mis_bags.sh` (contiene `mi_fallo`) → `sim.generar('mi_fallo', 'bags', post=mi_fallo)`. Entre **15 s y 30 s**, `mi_fallo(msgs)` sustituye cada mensaje de `/distancia_filtrada` y de `/cmd_vel_demo` por **el último publicado antes de los 15 s** (el mismo objeto: mismo valor y mismo `header.stamp`) y mantiene sus instantes, es decir, sigue a 10 Hz. El sensor no se toca. Modela un **filtro «zombi»**: deja de recibir `/distancia`, pero un temporizador sigue republicando su último mensaje guardado.
- Hallazgo(s) de `analiza_bag.py` que lo detectan, o por qué la herramienta no lo detecta: **ninguno. Da `TODO_OK` y salida 0** (`evidencias/ej4/analisis_mi_fallo.txt`), incluso con mis comprobaciones del ejercicio 3. Es **ciega** por cuatro razones: (1) los ritmos son de 10 Hz en todos los eslabones, sin huecos ni caída; (2) `LATENCIA_ALTA` usa la **mediana**, y el fallo afecta a 150 de 400 mensajes (37,5 %), así que la mediana sigue en 0,007 s **aunque la latencia máxima es de 15,01 s**: la herramienta la calcula y no la usa; (3) `RELOJ_DESFASADO` solo salta si *todos* los sellos son iguales, y aquí son 250 distintos; (4) los valores están dentro de rango. **Lo que sí lo delata** (`evidencias/ej4/grafica_mi_fallo.png` y `herramientas_extra/por_tramos.py`): la latencia sube en **rampa de 0 a 15 s** entre los 15 y los 30 s; `/distancia_filtrada` se queda **plana en 0,20 m (desviación 0,000)** mientras `/distancia` varía entre 0,18 y 1,84 m; hay **150 mensajes con sello repetido**; y `/cmd_vel_demo` manda **0,000 m/s** todo ese tramo, cuando antes y después llega a 0,5 m/s. **Qué ve y qué no ve la herramienta:** ve el *transporte* (ritmo, huecos, latencia típica), pero no el *contenido* ni la *frescura* de cada dato. Es un fallo de «latido sano, dato muerto».
- Eslabón, familia, causa y arreglo:
  - **¿Fallo o comportamiento correcto?** Es un fallo. El controlador hace bien su trabajo **con lo que recibe** (cree tener un obstáculo a 0,20 m y se para), pero lo que recibe es falso: el sensor mide hasta 1,84 m en ese tramo.
  - **Eslabón:** el **filtro** (`/distancia` → `/distancia_filtrada`). La entrada está viva y varía; la salida está congelada. El controlador solo propaga el problema.
  - **Familia:** **dinámica, de frescura del dato** (pregunta 5 de la lista: «¿los datos llegan frescos?»). El ritmo es correcto pero el dato es viejo, de hasta 15 s. La causa raíz probable es **estructural en tiempo de ejecución** (el filtro pierde su suscripción), **enmascarada** por un diseño que publica por temporizador. Esa máscara es lo que la vuelve invisible al ritmo.
  - **Causa probable** (corregida tras la prueba a ciegas, ver abajo): el filtro publica con un temporizador un **mensaje guardado en caché**, y entre los 15 y los 30 s **esa caché dejó de actualizarse aunque el filtro siguió procesando su entrada**. La prueba está en el bag: a los 30,0 s la salida salta de 0,20 a **0,60 m**, que es exactamente la media de las 5 últimas muestras crudas (0,65, 0,55, 0,60, 0,62 y 0,58). Si el filtro hubiera perdido la entrada, su ventana guardaría valores viejos y la salida subiría poco a poco durante 0,5 s. Si se hubiera reiniciado, la primera salida sería una sola muestra (0,58). Candidatos: el callback calcula la media pero falla (una excepción, un lock) antes de actualizar el mensaje que publica el temporizador, o escribe en otra variable distinta de la que se publica. Mi primera hipótesis, «perdió la suscripción por QoS», **no encaja** con ese salto. **Lo que no sé con el bag:** qué falló exactamente en el nodo ni por qué se recuperó a los 30 s. Para saberlo: grabar `/rosout` (excepciones o avisos del filtro), poner un contador o log en el callback y en el temporizador, y `ros2 topic info -v /distancia` para descartar del todo la QoS.
  - **Arreglo concreto:** (1) en el filtro, **publicar en el callback de entrada**; o, si se mantiene el temporizador, añadir un **watchdog** (`if now - ultimo.header.stamp > 3 × periodo: no republicar` y publicar un diagnóstico de ERROR en `/diagnostics`). (2) En el controlador, la **misma comprobación de frescura** sobre el `header.stamp` de entrada, con parada segura si el dato es viejo. Aquí el robot se quedó parado *por suerte*: si el filtro se hubiera congelado a 1,8 m, habría avanzado a ciegas a 0,5 m/s durante 15 s (≈ 7,5 m). (3) En el filtro, actualizar la media y el mensaje publicado **en el mismo paso** (o publicar directamente en el callback), y registrar cualquier excepción del callback en lugar de tragarla.
  - **Cómo comprobarlo:** reproducir el corte (parar y relanzar el nodo sensor), grabar un bag y verificar que `/distancia_filtrada` **deja de publicar** o que sale el diagnóstico de error, y que `cmd_vel` se pone a 0 por la regla de frescura. En la herramienta: alertar por **latencia máxima o p95** (no solo la mediana) y añadir una comprobación **`SELLO_REPETIDO`** (el mismo `header.stamp` publicado varias veces). Así este bag daría ERROR: el fallo no detectado se convierte en especificación.

Resultado de la resolución del compañero (¿acertó? ¿qué le faltó? Si no hubo intercambio, «sin intercambio» y por qué): **sin intercambio con un compañero**: la práctica la he hecho de forma individual y no tengo pareja asignada (el enunciado indica que no se pierden puntos). **Para comprobar igualmente que el reto se puede resolver y que la ficha no da pistas**, hice una **prueba a ciegas con un agente de IA** (declarado en «Uso de IA»). Lo lancé en una carpeta aislada que solo contenía `reto/` con la ficha, `analiza_bag.py`, `mis_comprobaciones.py` y la línea base, sin acceso a la solución. **Acertó en lo esencial:** el eslabón sensor → filtro, la familia dinámica (dato rancio), el temporizador que republica, que `TODO_OK` es un falso negativo porque la mediana diluye los 15 s, y el arreglo (publicar en el callback o un watchdog de frescura, también en el controlador). Lo destapó la gráfica `--png`, no los hallazgos, y valoró la dificultad como media-baja, con una ficha que «no daba la respuesta». Midió además que el robot está parado de 11,7 a 29,9 s, frente a 11,7-16,9 s en la línea base: **≈ 13 s de parada injustificada**. **Qué le faltó:** atribuyó el salto final de 0,195 a 0,60 m a un «reinicio del estado del filtro», cuando la media exacta de las 5 últimas muestras indica que el filtro siguió procesando. **Qué me aportó a mí:** ese salto, en el que yo no me había fijado, **refutó mi propia hipótesis de causa** (pérdida de la suscripción) y me obligó a corregirla: el bag contaba más de lo que yo creía haber puesto en él.

## Ejercicio 5 — Lista de comprobación ampliada

Las 7 preguntas de la clase + 3 mías (cada una con su herramienta, qué detecta y un caso que la justifique):

| # | Pregunta | Herramienta | Detecta | Caso que la justifica |
|---|---|---|---|---|
| 8 | ¿El **contenido** de cada dato es físicamente posible y está en el marco esperado? (valores dentro de `[min_range, max_range]`, sin `NaN`, `±Inf` solo como convenio; un único `frame_id`) | `mis_comprobaciones.py` (`RANGO_FUERA`, `FRAME_MIXTO`), integrado en `analiza_bag.py`; en vivo, `ros2 topic echo /distancia --field range` | Datos imposibles que el ritmo no ve y que **se propagan** aguas abajo; sensores mal configurados (límites a 0); frames mezclados que tf2 colocaría mal | `mi_rango`: 2 s publicando 9,9 m con `max_range` = 4 m, y la herramienta original decía `TODO_OK`. Con la pregunta 8 sale `RANGO_FUERA` en `/distancia` **y** en `/distancia_filtrada` (22 muestras contaminadas por la media del filtro) |
| 9 | ¿Cada dato es **nuevo** o se está republicando uno viejo? (sellos repetidos; latencia **máxima / p95** y no solo la mediana) | `herramientas_extra/por_tramos.py` (sellos repetidos, latencia máxima, desviación por tramo); `ros2 topic echo /x --field header.stamp`; gráfica de latencia de `--png` | Nodos «zombi» que publican por temporizador una caché antigua, fallos intermitentes que la mediana esconde, señales congeladas | `reto_1` (mi quinto fallo): ritmo perfecto y latencia **mediana** de 7 ms (`TODO_OK`), pero **latencia máxima de 15 s**, 150 sellos repetidos y una señal plana durante 15 s mientras el robot está parado sin motivo |
| 10 | ¿La **señal** de salida de cada eslabón sigue a la de entrada a tiempo? (retraso de la señal, no del mensaje) | `herramientas_extra/retraso_senal.py` (correlación cruzada de `range`); panel de valores de `--png` | Filtros cuyo retraso efectivo crece al bajar el ritmo (ventana definida en muestras), salidas desacopladas de la entrada | Caso 5: cada mensaje llega en 7 ms, pero la señal filtrada va **2,0 s** detrás de la real (0,3 s en la línea base), porque la media móvil de 5 muestras a 1 Hz abarca 5 s. La latencia por mensaje no lo puede ver |

Orden de coste: la 8 es barata (una pasada por los valores); la 9 necesita sellos y mirar por tramos; la 10, valores de dos topics y una correlación. Encajan detrás de la 5 («¿llegan frescos?»), que solo mira el transporte. Estas tres miran **qué** se transporta.

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

**M1.** Familias de fallo de arquitectura (estructural, dinámico, de tiempo, de origen aguas arriba): un ejemplo de cada una y la herramienta más barata que la detectaría.
**Estructural:** el sensor publica en *best effort* y el filtro se suscribe en *reliable*. No pasa ningún dato → `ros2 topic info -v`. **Dinámico:** mi `mi_lento`, con un callback de 0,15 s que baja el filtro a 6,7 Hz y envejece el dato 1,1 s → `ros2 topic hz` en cada eslabón. **Tiempo:** un nodo con `use_sim_time` sin `/clock` estampa a 0 → `ros2 param get <nodo> use_sim_time`. **Origen aguas arriba:** un cable flojo hace callar al sensor 4 s y el hueco recorre toda la cadena → mirar dónde empieza **primero** el hueco (`HUECO_ORIGEN`); lo de abajo es consecuencia.

**M2.** ¿Por qué una herramienta de análisis necesita pruebas unitarias, y qué significa que «un fallo no detectado es una especificación pendiente»?
La herramienta también es código que decide. Un `TODO_OK` falso da confianza falsa, y una falsa alarma rompe la CI y enseña a ignorarla. Las pruebas fijan qué debe decir en casos conocidos. También pueden estar mal: mi prueba de `mi_rango` esperaba un intervalo exacto y era ella la que fallaba (por el jitter). «Fallo no detectado = especificación pendiente» significa que un `TODO_OK` sobre un bag malo no prueba que no haya fallo, sino que **nadie ha dicho aún que eso lo es**. Se arregla escribiéndolo: prueba, comprobación y contrato. Así `mi_rango` pasó de salida 0 a 1, y `mi_fallo` queda como punto ciego declarado.

**M3.** ¿Qué ocurre exactamente en un conflicto de fusión en Git, cómo se ve en el fichero y cómo se resuelve? ¿Por qué no se debe «aceptar el mío» sin leer?
Git compara cada rama con el **ancestro común**. Si las dos cambiaron las mismas líneas, no puede saber la intención: para la fusión y deja ambas versiones entre `<<<<<<< HEAD`, `=======` y `>>>>>>> rama`. Para resolverlo: leer las dos, escribir la versión correcta (que puede combinar ambas), quitar los marcadores, pasar las pruebas, `git add` y `git commit`. «Aceptar el mío» **borra en silencio el trabajo del otro** y suele compilar. Por ejemplo: si mi rama cambia `mi_rango` en `esperado.json` y otra añade `mi_fallo`, quedarme con lo mío saca `mi_fallo` del contrato, y la CI sigue en verde sin vigilarlo.

**M4.** ¿Qué garantiza y qué NO garantiza una CI en verde? Usa como ejemplo el contrato de regresión con bags.
**Garantiza** que, en ese commit y en un entorno limpio, todas las pruebas pasan y cada bag de referencia da **exactamente** el diagnóstico del contrato: nadie ha cambiado el comportamiento sin querer. **No garantiza** que ese comportamiento sea correcto. `mi_fallo` figura en el contrato con salida 0 y la CI está en verde, **aunque ese bag deja el robot parado 13 s sin motivo**. Tampoco cubre bags fuera del contrato, el robot real con ROS2, ni el futuro (`rosbags>=0.10` no está fijado). Verde significa «se comporta como se especificó», no «no hay fallos».

## Opcional — `ros2 bag play` y RViz2

<<RELLENAR o "No realizado">>

## Reflexión final (5 líneas)

¿Qué fue lo más difícil? ¿Qué cambiarías en la herramienta? ¿Qué le faltó al bag para estar seguro de la causa? <<RELLENAR>>
