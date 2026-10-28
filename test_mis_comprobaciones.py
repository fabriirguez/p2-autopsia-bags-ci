"""Pruebas del ejercicio 3. Al principio FALLAN (NotImplementedError): tu trabajo es hacer que pasen.
Despues, anade tus propias pruebas en la clase PruebasPropias (minimo dos)."""
import tempfile
import unittest

import mis_comprobaciones as mc
import simulador_bags as sim


def m(t, rango, mn=0.02, mx=4.0, frame='sensor_link'):
    return {'t': t, 'range': rango, 'min_range': mn, 'max_range': mx, 'frame_id': frame}


class PruebasRangos(unittest.TestCase):
    def test_todo_en_rango(self):
        self.assertEqual(mc.comprobar_rangos([m(0, 1.0), m(0.1, 3.9), m(0.2, 0.02)], '/d'), [])

    def test_sin_muestras(self):
        self.assertEqual(mc.comprobar_rangos([], '/d'), [])

    def test_por_encima_del_maximo(self):
        h = mc.comprobar_rangos([m(0, 1.0), m(1, 9.9), m(2, 9.9), m(3, 1.0)], '/d')
        self.assertEqual(len(h), 1)
        self.assertEqual((h[0].severidad, h[0].codigo, h[0].topic), ('ERROR', 'RANGO_FUERA', '/d'))
        self.assertIn('2', h[0].detalle)          # 2 muestras fallan

    def test_por_debajo_del_minimo(self):
        h = mc.comprobar_rangos([m(0, 0.001), m(1, 1.0)], '/d')
        self.assertEqual([x.codigo for x in h], ['RANGO_FUERA'])

    def test_margen_de_tolerancia(self):
        muestras = [m(0, 4.05)]
        self.assertEqual(len(mc.comprobar_rangos(muestras, '/d')), 1)
        self.assertEqual(mc.comprobar_rangos(muestras, '/d', margen=0.1), [])

    def test_con_bag_real_sano(self):
        with tempfile.TemporaryDirectory() as d:
            sim.generar('sano', d, duracion=5)
            self.assertEqual(mc.main([f'{d}/sano', '/distancia']), 0)

    def test_con_bag_real_fuera_de_rango(self):
        with tempfile.TemporaryDirectory() as d:
            sim.generar('malo', d, duracion=5, fuera_de_rango=(1, 2, 9.9))
            self.assertEqual(mc.main([f'{d}/malo', '/distancia']), 1)


class PruebasFrames(unittest.TestCase):
    """Ampliacion: se omiten mientras comprobar_frames no este implementada."""
    def setUp(self):
        try:
            mc.comprobar_frames([], '/d')
        except NotImplementedError:
            self.skipTest('comprobar_frames sin implementar (ampliacion)')

    def test_un_solo_frame(self):
        self.assertEqual(mc.comprobar_frames([m(0, 1, frame='a'), m(1, 1, frame='a')], '/d'), [])

    def test_dos_frames(self):
        h = mc.comprobar_frames([m(0, 1, frame='a'), m(1, 1, frame='b')], '/d')
        self.assertEqual(len(h), 1)
        self.assertEqual((h[0].severidad, h[0].codigo), ('WARN', 'FRAME_MIXTO'))
        self.assertIn('a', h[0].detalle)
        self.assertIn('b', h[0].detalle)


class PruebasPropias(unittest.TestCase):
    """TU TRABAJO: anade aqui al menos dos pruebas nuevas (casos limite, otro topic, tu propio fallo...)."""
    pass


if __name__ == '__main__':
    unittest.main()
