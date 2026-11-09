# Evidencias del ejercicio 6 (Guía de autoformación de la S8)

Capturas y salidas de la Guía de autoformación de la S8, hechas en **ROS 2 Jazzy** dentro de una VM (UTM, Ubuntu) el 9-10/11/2026. Los bags grabados (`etapa1_turtle`, `etapa2_*`) se quedaron en la VM: no se versionan (ver `.gitignore` y enunciado).

| Etapa | Fichero | Qué muestra |
|---|---|---|
| 0 | `etapa0_ros2_bag_help.jpg` | `echo $ROS_DISTRO` → `jazzy` y subcomandos de `ros2 bag` |
| 1 | `etapa1_turtlesim_teleop.jpg` | turtlesim + `turtle_teleop_key` |
| 1 | `etapa1_record_dibujo.jpg` | la tortuga dibujando mientras se graba |
| 1 | `etapa1_record_y_bag_info.jpg` | `ros2 bag record` (aviso de argumento posicional obsoleto) y `ros2 bag info`: 214,3 s, 86 `cmd_vel`, 13 375 `pose` |
| 1 | `etapa1_play_bag_completo_sin_movimiento.jpg` | `ros2 bag play` del bag completo: la tortuga no se mueve al principio |
| 1 | `etapa1_play_cmd_vel.jpg`, `etapa1_play_cmd_vel_choque_pared.jpg` | `ros2 bag play --topics /turtle1/cmd_vel --rate 5`: repite el dibujo (bucle abierto) y avisos «I hit the wall» |
| 2 | `etapa2_grabacion_automatica.jpg` | grabaciones de 20 s con `timeout -s INT` y la tortuga moviéndose sola (`ros2 topic pub`) |
| 2 | `etapa2_tamanos.jpg` | `du -sh` / `ls -l`: normal 92 K, zstd 44 K, partido 116 K (4 ficheros), qos 56 K |
| 2 | `etapa2_qos_overrides.jpg`, `overrides.yaml` | override *best_effort* y `ros2 bag info`: 596 mensajes en 9,58 s |
| 3 | `etapa3_difusor_tf.jpg`, `tf_tortuga.py` | difusor tf2 propio `world → turtle1` y `static_transform_publisher turtle1 → sensor_link` |
| 3 | `etapa3_tf2_echo.jpg` | `tf2_echo world sensor_link`: aviso inicial «frame does not exist» y transformaciones que cambian |
| 3 | `etapa3_view_frames.jpg`, `etapa3_frames_arbol.jpg` | `view_frames`: árbol `world → turtle1 → sensor_link` (62,7 Hz dinámica; estática) |
| 3 | `etapa3_rviz2_error_fixed_frame_map.png` | RViz2 con Fixed Frame `map` inexistente: error y marcos amontonados en el origen |
| 3 | `etapa3_rviz2_tf.jpg`, `etapa3_rviz2_tf_vista_lejana.jpg`, `etapa3_rviz2_y_turtlesim.jpg` | RViz2 con Fixed Frame `world` y display TF |
