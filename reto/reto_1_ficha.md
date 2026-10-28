# Ficha del reto 1 (sin solución)

**Bag:** `reto/reto_1` (rosbag2, MCAP, ROS2 Jazzy, ≈ 40 s). Sistema de la S7: sensor → filtro → controlador, con los topics `/distancia` (`sensor_msgs/Range`, diseñado a 10 Hz), `/distancia_filtrada` (`sensor_msgs/Range`) y `/cmd_vel_demo` (`geometry_msgs/Twist`).

**Síntoma observable** (lo que contó el operador): «A mitad de la prueba el robot se detuvo y se quedó parado bastante tiempo, más de diez segundos, aunque delante no había nada que le impidiera avanzar. Después volvió a moverse él solo. No apareció ningún error en pantalla y nadie tocó el robot.»

**Qué debes averiguar** (con método: hipótesis escrita antes de medir y evidencia reproducible):
1. ¿Es un fallo o un comportamiento correcto del controlador? Justifícalo con datos del bag.
2. ¿En qué eslabón (entre qué dos componentes) se rompe el sistema?
3. ¿De qué familia es el fallo?
4. ¿Cuál es la causa probable? ¿Qué **no** puedes saber solo con el bag y qué prueba harías con el sistema vivo?
5. Un arreglo concreto y cómo comprobarías que funciona.
6. Los comandos que has usado y qué te ha dicho cada uno.
