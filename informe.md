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

Bags entregados (en `bags/`, nombres que empiezan por `mi_`): <<RELLENAR>>
Cómo los generé (comandos): <<RELLENAR>>

Tabla comparativa sano / con fallo (ritmos, latencia, hallazgos): <<RELLENAR>>

**¿Qué no puede medir la herramienta con mensajes sin cabecera (`Float32`)? ¿Por qué?** <<RELLENAR>>

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
