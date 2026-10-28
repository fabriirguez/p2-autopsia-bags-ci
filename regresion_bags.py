#!/usr/bin/env python3
"""regresion_bags.py - prueba de regresion con bags de referencia (Sesion 9).

Idea: un bag grabado de un sistema sano (y varios con fallos conocidos) es un CONTRATO de comportamiento.
Este script analiza cada bag con analiza_bag.py y comprueba que el diagnostico coincide con el esperado en
esperado.json. Si alguien cambia un umbral o la logica y el diagnostico cambia, la prueba falla y la integracion
continua se pone en rojo.

Uso:   python3 regresion_bags.py [--contrato esperado.json] [--bags bags]
Salida: 0 si todos los bags dan el diagnostico esperado; 1 si alguno difiere.
"""
import argparse
import json
import sys
from pathlib import Path

# Evita .pyc obsoletos al cambiar de commit (git bisect/revert en el mismo segundo y con el mismo tamano)
sys.dont_write_bytecode = True

import analiza_bag as ab  # noqa: E402


def evaluar(contrato, carpeta_bags):
    cadena = contrato.get('cadena', ab.CADENA_POR_DEFECTO)
    esperado_hz = contrato.get('esperado_hz', {})
    filas, fallos = [], 0
    for nombre, exp in contrato['bags'].items():
        ruta = Path(carpeta_bags) / nombre
        if not ruta.exists():
            filas.append((nombre, 'FALLO', f'no existe {ruta}'))
            fallos += 1
            continue
        _, _, _, hallazgos = ab.analizar_ruta(ruta, cadena, esperado_hz)
        errores = sorted({h.codigo for h in hallazgos if h.severidad == 'ERROR'})
        salida = 1 if errores else 0
        esperados = sorted(exp['errores'])
        if salida == exp['salida'] and errores == esperados:
            filas.append((nombre, 'OK', f'errores = {errores or "ninguno"}'))
        else:
            fallos += 1
            filas.append((nombre, 'FALLO', f'esperado {esperados or "ninguno"} (salida {exp["salida"]}), '
                                            f'obtenido {errores or "ninguno"} (salida {salida})'))
    return filas, fallos


def main(argv=None):
    ap = argparse.ArgumentParser(description='Regresion con bags de referencia')
    ap.add_argument('--contrato', default=str(Path(__file__).with_name('esperado.json')))
    ap.add_argument('--bags', default=str(Path(__file__).with_name('bags')))
    a = ap.parse_args(argv)
    contrato = json.loads(Path(a.contrato).read_text(encoding='utf-8'))
    filas, fallos = evaluar(contrato, a.bags)
    for nombre, estado, detalle in filas:
        print(f'[{estado:5s}] {nombre:20s} {detalle}')
    print(f'\n{len(filas) - fallos}/{len(filas)} bags con el diagnostico esperado')
    return 1 if fallos else 0


if __name__ == '__main__':
    sys.exit(main())
