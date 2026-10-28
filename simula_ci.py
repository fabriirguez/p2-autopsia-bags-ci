#!/usr/bin/env python3
"""simula_ci.py - ejecuta en local los pasos `run:` de un workflow de GitHub Actions (Sesion 9).

NO es un runner real de GitHub: sirve para ENTENDER la mecanica y comprobar tu YAML sin subirlo.
  - Lee el YAML con PyYAML y recorre jobs -> steps en orden.
  - Los pasos `run:` se ejecutan con bash en la carpeta actual (con `python` -> python3 si hace falta).
  - Los pasos `uses:` (checkout, setup-python, upload-artifact...) los hace GitHub: aqui se SALTAN y se avisa.
  - Un paso que falla (codigo != 0) detiene el job, salvo los marcados con `if: always()` o `if: failure()`.
  - Un paso con `continue-on-error: true` no detiene el job.
Ademas valida la estructura: debe haber `on`, `jobs`, y cada job `runs-on` y `steps`.

Uso: python3 simula_ci.py [-v] [.github/workflows/ci.yml]
Salida: 0 si el job queda en verde; 1 si queda en rojo o el YAML es invalido.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


def validar(wf):
    """Devuelve la lista de problemas de estructura del workflow."""
    prob = []
    if not isinstance(wf, dict):
        return ['el YAML no es un diccionario']
    # OJO: en YAML 1.1 la clave `on` se lee como el booleano True
    if 'on' not in wf and True not in wf:
        prob.append("falta la clave 'on' (cuando se ejecuta)")
    jobs = wf.get('jobs')
    if not isinstance(jobs, dict) or not jobs:
        prob.append("falta 'jobs' o esta vacio")
        return prob
    for nombre, job in jobs.items():
        if not isinstance(job, dict):
            prob.append(f"job '{nombre}': no es un diccionario")
            continue
        if 'runs-on' not in job:
            prob.append(f"job '{nombre}': falta 'runs-on'")
        steps = job.get('steps')
        if not isinstance(steps, list) or not steps:
            prob.append(f"job '{nombre}': falta 'steps' o no es una lista")
            continue
        for i, st in enumerate(steps, 1):
            if not isinstance(st, dict):
                prob.append(f"job '{nombre}' paso {i}: no es un diccionario")
            elif ('run' in st) == ('uses' in st):
                prob.append(f"job '{nombre}' paso {i}: debe tener exactamente uno de 'run' o 'uses'")
    return prob


VERBOSO = False


def ejecutar(wf, cwd):
    # shim para que `python` exista aunque solo haya python3
    shim = tempfile.mkdtemp(prefix='shim_')
    if not shutil.which('python'):
        os.symlink(sys.executable, os.path.join(shim, 'python'))
    env = dict(os.environ, PATH=shim + os.pathsep + os.environ.get('PATH', ''),
               PYTHONDONTWRITEBYTECODE='1')   # evita .pyc obsoletos entre commits
    rojo_global = False
    for nombre, job in wf['jobs'].items():
        print(f"\n=== job: {nombre}  (runs-on: {job.get('runs-on')}) ===")
        fallo = False
        for i, st in enumerate(job['steps'], 1):
            etiqueta = st.get('name') or st.get('run') or st.get('uses')
            cond = str(st.get('if', '')).strip()
            if fallo and cond not in ('always()', 'failure()'):
                print(f"[{i}] SALTADO (un paso anterior fallo): {etiqueta}")
                continue
            if not fallo and cond == 'failure()':
                print(f"[{i}] SALTADO (if: failure() y no hay fallo): {etiqueta}")
                continue
            if 'uses' in st:
                print(f"[{i}] (lo hace GitHub, aqui se salta) uses: {st['uses']}  <- {etiqueta}")
                continue
            print(f"[{i}] {etiqueta}")
            r = subprocess.run(['bash', '-eo', 'pipefail', '-c', st['run']], cwd=cwd, env=env,
                               capture_output=True, text=True)
            lineas = (r.stdout + r.stderr).rstrip().splitlines()
            if not VERBOSO and len(lineas) > 14:
                lineas = [f'... ({len(lineas) - 14} lineas omitidas; usa -v para verlas todas)'] + lineas[-14:]
            if lineas:
                print('    ' + '\n    '.join(lineas))
            if r.returncode != 0 and not st.get('continue-on-error'):
                print(f"    -> FALLO (codigo {r.returncode})")
                fallo = True
            else:
                print(f"    -> ok{' (fallo ignorado)' if r.returncode else ''}")
        print(f"=== job {nombre}: {'ROJO' if fallo else 'VERDE'} ===")
        rojo_global = rojo_global or fallo
    return rojo_global


def main(argv=None):
    global VERBOSO
    argv = sys.argv[1:] if argv is None else argv
    VERBOSO = '-v' in argv
    argv = [a for a in argv if a != '-v']
    ruta = Path(argv[0] if argv else '.github/workflows/ci.yml')
    try:
        wf = yaml.safe_load(ruta.read_text(encoding='utf-8'))
    except (OSError, yaml.YAMLError) as e:
        print(f"YAML invalido o ilegible: {e}")
        return 1
    prob = validar(wf)
    if prob:
        print('El workflow tiene problemas de estructura:')
        for p in prob:
            print('  -', p)
        return 1
    rojo = ejecutar(wf, ruta.resolve().parents[2] if ruta.parent.name == 'workflows' else Path.cwd())
    print('\nRESULTADO:', 'ROJO (la integracion continua fallaria)' if rojo else 'VERDE (todo pasa)')
    return 1 if rojo else 0


if __name__ == '__main__':
    sys.exit(main())
