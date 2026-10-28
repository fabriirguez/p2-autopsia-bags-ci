#!/usr/bin/env python3
"""entrega.py - autocomprobacion y empaquetado de la practica P2 (Tema 2).

    python3 entrega.py                      # revisa que no falte nada (no cambia ficheros)
    python3 entrega.py --zip "Apellido_Nombre"   # ademas crea entrega_Apellido_Nombre.zip
    python3 entrega.py --sin-ci             # omite ejecutar simula_ci.py (mas rapido)

Las comprobaciones son FORMALES (ficheros, secciones, pruebas, CI local en verde): no valoran si tu diagnostico
es correcto ni si tu repositorio de GitHub esta bien montado: eso lo corrige el profesor.
"""
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MARCA = '<<RELLENAR>>'
URL_GITHUB = re.compile(r'https://github\.com/[\w.-]+/[\w.-]+')
ENV = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}


def secciones(texto):
    """{titulo_de_seccion: cuerpo} para las secciones '## ...'."""
    partes = re.split(r'^## ', texto, flags=re.M)[1:]
    return {p.split('\n', 1)[0].strip(): p.split('\n', 1)[1] if '\n' in p else '' for p in partes}


def sin_rellenar(cuerpo):
    return cuerpo.count(MARCA)


def pruebas(modulo):
    r = subprocess.run([sys.executable, '-m', 'unittest', modulo], cwd=AQUI, capture_output=True, text=True, env=ENV)
    return r.returncode == 0, (r.stderr.strip().splitlines() or ['?'])[-1]


def commits_en(texto):
    """Cuenta lineas de `git log --oneline [--graph]` (hash de 7+ hex tras el dibujo del grafo)."""
    return len([l for l in texto.splitlines() if re.match(r'^[\s*|\\/_.-]*[0-9a-f]{7,40}\b', l)])


def revisar(con_ci=True):
    res = []                                   # (ok, texto)
    inf = AQUI / 'informe.md'
    secs = {}
    if not inf.exists():
        res.append((False, 'Falta informe.md (copia plantilla_informe.md a informe.md y rellenalo)'))
    else:
        secs = secciones(inf.read_text(encoding='utf-8'))
        for titulo, cuerpo in secs.items():
            if titulo.startswith('Opcional'):
                continue
            n = sin_rellenar(cuerpo)
            res.append((n == 0, f'Informe - {titulo}: ' + ('completo' if n == 0 else f'{n} campo(s) sin rellenar')))
    bags = sorted(p.name for p in (AQUI / 'bags').glob('mi_*') if p.is_dir())
    res.append((len(bags) >= 2, f'Ejercicio 2: bags propios en bags/mi_* ({len(bags)} encontrados, minimo 2): {", ".join(bags)}'))
    ok, ult = pruebas('test_mis_comprobaciones')
    res.append((ok, f'Ejercicio 3: pruebas de test_mis_comprobaciones -> {ult}'))
    propias = (AQUI / 'test_mis_comprobaciones.py').read_text(encoding='utf-8')
    n_prop = len(re.findall(r'^\s+def test_', propias.split('class PruebasPropias', 1)[-1], flags=re.M))
    res.append((n_prop >= 2, f'Ejercicio 3: pruebas propias en PruebasPropias: {n_prop} (minimo 2)'))
    ok, ult = pruebas('test_analiza_bag')
    res.append((ok, f'Pruebas originales de analiza_bag.py siguen pasando -> {ult}'))
    retos = sorted(p.name for p in (AQUI / 'reto').glob('*') if p.name != 'LEEME.md')
    res.append((len(retos) >= 1, f'Ejercicio 4: contenido en reto/ ({", ".join(retos) or "vacio"})'))

    # --- Ejercicio 7: repositorio + CI ---
    cuerpo7 = next((c for t, c in secs.items() if t.startswith('Ejercicio 7')), '')
    urls = URL_GITHUB.findall(cuerpo7)
    res.append((bool(urls), 'Ejercicio 7: el informe incluye al menos una URL de GitHub (' + (urls[0] if urls else 'ninguna') + ') - sin GitHub, ver enunciado'))
    wf = AQUI / '.github' / 'workflows' / 'ci.yml'
    res.append((wf.exists(), 'Ejercicio 7: existe .github/workflows/ci.yml'))
    try:
        contrato = json.loads((AQUI / 'esperado.json').read_text(encoding='utf-8'))
        propios = [b for b in contrato.get('bags', {}) if b.startswith('mi_')]
    except (OSError, ValueError) as e:
        propios = []
        res.append((False, f'Ejercicio 7: esperado.json no se puede leer ({e})'))
    res.append((len(propios) >= 1, f'Ejercicio 7: esperado.json incluye tus bags mi_* ({", ".join(propios) or "ninguno"})'))
    log = AQUI / 'evidencias' / 'git_log.txt'
    n_c = commits_en(log.read_text(encoding='utf-8', errors='replace')) if log.exists() else 0
    res.append((n_c >= 6, f'Ejercicio 7: evidencias/git_log.txt con {n_c} commits (minimo 6)'))
    for nombre in ('ci_rojo', 'ci_verde'):
        hay = [p.name for p in (AQUI / 'evidencias').glob(nombre + '.*') if p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.txt', '.pdf')]
        res.append((bool(hay), f'Ejercicio 7: evidencias/{nombre}.(png|jpg|txt|pdf) ({", ".join(hay) or "falta"})'))
    if con_ci and wf.exists():
        r = subprocess.run([sys.executable, 'simula_ci.py', '.github/workflows/ci.yml'], cwd=AQUI, capture_output=True, text=True, env=ENV, timeout=600)
        ult = (r.stdout.strip().splitlines() or r.stderr.strip().splitlines() or ['?'])[-1]
        res.append((r.returncode == 0, f'Ejercicio 7: simula_ci.py con tu ci.yml -> {"VERDE" if r.returncode == 0 else "ROJO"} ({ult})'))
    return res


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    res = revisar(con_ci='--sin-ci' not in argv)
    for ok, t in res:
        print(('[ OK ] ' if ok else '[FALTA] ') + t)
    falta = sum(1 for ok, _ in res if not ok)
    print(f'\n{len(res) - falta}/{len(res)} comprobaciones formales superadas')
    print('Recuerda: no se comprueba que el repositorio de GitHub exista ni que su CI este en verde; eso va con las URL del informe.')
    if '--zip' in argv:
        i = argv.index('--zip')
        nombre = argv[i + 1] if len(argv) > i + 1 and not argv[i + 1].startswith('--') else 'alumno'
        destino = AQUI / f'entrega_{nombre}.zip'
        incluir = ['informe.md', 'mis_comprobaciones.py', 'test_mis_comprobaciones.py', 'esperado.json', '.gitignore',
                   '.github/workflows/ci.yml']
        with zipfile.ZipFile(destino, 'w', zipfile.ZIP_DEFLATED) as z:
            for f in incluir:
                if (AQUI / f).exists():
                    z.write(AQUI / f, f)
            for pat in ('bags/mi_*', 'reto/*', 'evidencias/*', '*.png'):
                for p in AQUI.glob(pat):
                    if p.is_dir():
                        for q in p.rglob('*'):
                            if q.is_file() and '__pycache__' not in q.parts:
                                z.write(q, q.relative_to(AQUI))
                    elif p.is_file():
                        z.write(p, p.relative_to(AQUI))
        print(f'\nCreado {destino.name} ({destino.stat().st_size // 1024} KiB). Revisalo antes de subirlo al campus.')
    return 1 if falta else 0


if __name__ == '__main__':
    sys.exit(main())
