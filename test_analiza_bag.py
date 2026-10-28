"""Pruebas de analiza_bag.py (no necesitan ROS2; si `rosbags`: pip install rosbags).
Ejecutar:  python3 -m unittest -v test_analiza_bag
"""
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import analiza_bag as ab            # noqa: E402

CADENA = ab.CADENA_POR_DEFECTO
BAGS = AQUI / 'bags'
CASOS = ['caso_0_linea_base', 'caso_1', 'caso_2', 'caso_3', 'caso_4', 'caso_5_casa']


def codigos(hs, sev=None):
    return {(h.codigo, h.topic) for h in hs if sev is None or h.severidad == sev}


class PruebasFunciones(unittest.TestCase):
    def test_estadisticas_ritmo_y_huecos(self):
        s = ab.Serie('/x', 'std_msgs/msg/Float32', recv=[i * 0.1 for i in range(50)] + [10.0 + i * 0.1 for i in range(10)])
        st = ab.estadisticas(s, 0.0)
        self.assertEqual(st.n, 60)
        self.assertEqual(len(st.huecos), 1)
        self.assertAlmostEqual(st.huecos[0][0], 4.9, places=3)

    def test_reloj_sellos_constantes(self):
        s = ab.Serie('/y', 'sensor_msgs/msg/Range', recv=[100 + i * 0.1 for i in range(20)], stamps=[0.0] * 20)
        st = ab.estadisticas(s, 100.0)
        self.assertFalse(st.reloj_ok)

    def test_latencia_normal(self):
        s = ab.Serie('/y', 'sensor_msgs/msg/Range', recv=[100 + i * 0.1 for i in range(20)],
                     stamps=[100 + i * 0.1 - 0.005 for i in range(20)])
        st = ab.estadisticas(s, 100.0)
        self.assertTrue(st.reloj_ok)
        self.assertAlmostEqual(st.lat_med, 0.005, places=4)

    def test_sin_cadena_sin_hallazgos_y_ok(self):
        self.assertEqual({h.codigo for h in ab.diagnosticar({}, None, None)}, {'TODO_OK'})


class PruebasBags(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.res = {}
        for n in CASOS:
            _, st, _, hs = ab.analizar_ruta(BAGS / n, CADENA, {'/distancia': 10.0})
            cls.res[n] = (st, hs)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_linea_base_sin_errores(self):
        st, hs = self.res['caso_0_linea_base']
        self.assertEqual(codigos(hs, 'ERROR'), set())
        self.assertIn(('TODO_OK', '-'), codigos(hs))
        self.assertAlmostEqual(st['/distancia'].ritmo, 10.0, delta=0.2)

    def test_caso1_callback_bloqueante(self):
        st, hs = self.res['caso_1']
        self.assertIn(('CAIDA_EN_CADENA', '/distancia_filtrada'), codigos(hs, 'ERROR'))
        self.assertIn(('LATENCIA_ALTA', '/distancia_filtrada'), codigos(hs, 'ERROR'))
        self.assertAlmostEqual(st['/distancia_filtrada'].ritmo, 2.5, delta=0.2)
        self.assertGreater(st['/distancia_filtrada'].lat_med, 1.0)

    def test_caso2_reloj(self):
        _, hs = self.res['caso_2']
        self.assertEqual(codigos(hs, 'ERROR'), {('RELOJ_DESFASADO', '/distancia_filtrada')})

    def test_caso3_hueco_nace_en_sensor(self):
        _, hs = self.res['caso_3']
        self.assertIn(('HUECO_ORIGEN', '/distancia'), codigos(hs))
        self.assertIn(('HUECOS', '/distancia_filtrada'), codigos(hs, 'ERROR'))

    def test_caso4_nombre_mal_escrito(self):
        _, hs = self.res['caso_4']
        self.assertIn(('SIN_DATOS', '/cmd_vel_demo'), codigos(hs, 'ERROR'))
        det = [h for h in hs if h.codigo == 'TOPIC_INESPERADO' and h.topic == '/cmd_vel']
        self.assertTrue(det and '/cmd_vel_demo' in det[0].detalle)

    def test_caso5_ritmo_bajo(self):
        _, hs = self.res['caso_5_casa']
        self.assertIn(('RITMO_BAJO', '/distancia'), codigos(hs, 'ERROR'))

    def test_codigo_de_salida(self):
        d = BAGS
        self.assertEqual(ab.main([str(d / 'caso_0_linea_base')]), 0)
        self.assertEqual(ab.main([str(d / 'caso_1')]), 1)

    def test_info(self):
        d = BAGS
        txt = ab.info_bag(d / 'caso_1')
        self.assertIn('Storage id:        mcap', txt)
        self.assertIn('/distancia | Type: sensor_msgs/msg/Range | Count: 400', txt)
        self.assertEqual(ab.main([str(d / 'caso_1'), '--info']), 0)

    def test_png(self):
        out = Path(self.tmp.name) / 'i.png'
        ab.main([str(BAGS / 'caso_1'), '--png', str(out)])
        self.assertGreater(out.stat().st_size, 5000)


if __name__ == '__main__':
    unittest.main()
