#!/usr/bin/env python3
"""Copia un bag a reto/ con el nombre 'reto_<n>' (para no dar pistas con el nombre original).
Uso: python3 empaquetar_reto.py bags/mi_fallo reto/"""
import shutil
import sys
from pathlib import Path

if len(sys.argv) != 3:
    sys.exit('uso: empaquetar_reto.py <carpeta_bag> <carpeta_reto>')
origen, destino = Path(sys.argv[1]), Path(sys.argv[2])
n = len([p for p in destino.glob('reto_*') if p.is_dir()]) + 1
final = destino / f'reto_{n}'
shutil.copytree(origen, final)
# el nombre del bag tambien aparece en el fichero .mcap y en metadata.yaml: se cambia para no dar pistas
for f in final.glob('*.mcap'):
    f.rename(final / f'reto_{n}.mcap')
meta = final / 'metadata.yaml'
meta.write_text(meta.read_text(encoding='utf-8').replace(origen.name, f'reto_{n}'), encoding='utf-8')
(destino / f'reto_{n}_ficha.md').write_text('# Ficha del reto\n\nSintoma observable: <<RELLENAR>>\n\nQue debes averiguar: <<RELLENAR>>\n', encoding='utf-8')
print(f'Bag copiado en {final}; rellena {final.name}_ficha.md (sin la solucion)')
