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
    """Pruebas propias (Fabricio Andree Rodriguez): casos límite, falsos positivos y mi propio bag."""

    # --- límites y margen ---------------------------------------------------------------------------
    def test_valor_exactamente_en_los_limites_es_valido(self):
        # Los extremos [min_range, max_range] forman parte del rango válido (intervalo cerrado).
        self.assertEqual(mc.comprobar_rangos([m(0, 0.02), m(1, 4.0)], '/d'), [])

    def test_margen_exacto_y_justo_por_encima(self):
        self.assertEqual(mc.comprobar_rangos([m(0, 4.1)], '/d', margen=0.1), [])
        self.assertEqual(len(mc.comprobar_rangos([m(0, 4.1 + 1e-6)], '/d', margen=0.1)), 1)

    def test_margen_negativo_no_se_admite(self):
        # Un margen negativo estrecharía el rango en silencio: mejor fallar pronto.
        with self.assertRaises(ValueError):
            mc.comprobar_rangos([m(0, 1.0)], '/d', margen=-0.1)

    # --- contenido del hallazgo ---------------------------------------------------------------------
    def test_un_solo_hallazgo_con_cuenta_e_intervalo(self):
        muestras = [m(9.9, 1.0), m(10.0, 9.9), m(10.5, 9.9), m(11.9, 9.9), m(12.0, 1.0)]
        h = mc.comprobar_rangos(muestras, '/d')
        self.assertEqual(len(h), 1)                       # uno solo, aunque fallen varias
        self.assertIn('3 de 5', h[0].detalle)             # cuántas fallan y de cuántas
        self.assertIn('10.0 s', h[0].detalle)             # primera...
        self.assertIn('11.9 s', h[0].detalle)             # ...y última

    def test_limites_por_muestra_no_globales(self):
        # Cada mensaje Range trae sus propios min/max: 3 m es válido con max 4 m pero no con max 2 m.
        h = mc.comprobar_rangos([m(0, 3.0, mx=4.0), m(1, 3.0, mx=2.0)], '/d')
        self.assertIn('1 de 2', h[0].detalle)

    # --- falsos positivos: convenios de sensor_msgs/Range ---------------------------------------------
    def test_inf_es_convenio_sin_deteccion_no_error(self):
        # Range.msg: +Inf = no hay detección dentro del alcance, -Inf = detección por debajo del mínimo.
        # Es un valor LEGÍTIMO: no debe dar ERROR (solo un INFO que lo cuente).
        h = mc.comprobar_rangos([m(0, float('inf')), m(1, float('-inf')), m(2, 1.0)], '/d')
        self.assertFalse([x for x in h if x.severidad == 'ERROR'])
        self.assertEqual([x.codigo for x in h], ['RANGO_INFINITO'])

    def test_nan_es_medida_invalida(self):
        h = mc.comprobar_rangos([m(0, float('nan')), m(1, 1.0)], '/d')
        self.assertEqual([(x.severidad, x.codigo) for x in h], [('ERROR', 'RANGO_FUERA')])
        self.assertIn('NaN', h[0].detalle)

    def test_frame_vacio_cuenta_como_frame_distinto(self):
        h = mc.comprobar_frames([m(0, 1, frame='sensor_link'), m(1, 1, frame='')], '/d')
        self.assertEqual([x.codigo for x in h], ['FRAME_MIXTO'])
        self.assertIn('(vacío)', h[0].detalle)

    # --- con bags reales -----------------------------------------------------------------------------
    def test_mi_fallo_de_rango_cuenta_muestras_e_intervalo(self):
        # Mi bag: 9,9 m entre 10 s y 12 s a 10 Hz -> 20 muestras fuera de rango, de 10.0 s a 11.9 s.
        with tempfile.TemporaryDirectory() as d:
            sim.generar('rango', d, duracion=15, fuera_de_rango=(10, 12, 9.9))
            h = mc.comprobar_rangos(mc.leer_muestras_range(f'{d}/rango', '/distancia'), '/distancia')
        self.assertEqual(len(h), 1)
        self.assertIn('20 de 150', h[0].detalle)
        self.assertIn('10.0 s', h[0].detalle)
        self.assertIn('11.9 s', h[0].detalle)

    def test_integrado_en_analiza_bag(self):
        # La comprobación debe llegar a analiza_bag (y por tanto a la regresión y a la CI).
        import analiza_bag as ab
        with tempfile.TemporaryDirectory() as d:
            sim.generar('malo', d, duracion=15, fuera_de_rango=(10, 12, 9.9))
            sim.generar('sano', d, duracion=15)
            _, _, _, h_malo = ab.analizar_ruta(f'{d}/malo', ab.CADENA_POR_DEFECTO, {'/distancia': 10})
            _, _, _, h_sano = ab.analizar_ruta(f'{d}/sano', ab.CADENA_POR_DEFECTO, {'/distancia': 10})
        self.assertIn(('ERROR', 'RANGO_FUERA', '/distancia'), {(x.severidad, x.codigo, x.topic) for x in h_malo})
        self.assertNotIn('TODO_OK', {x.codigo for x in h_malo})
        self.assertEqual([x.codigo for x in h_sano], ['TODO_OK'])


if __name__ == '__main__':
    unittest.main()
