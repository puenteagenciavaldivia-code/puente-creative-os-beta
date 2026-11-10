#!/bin/bash
# Preparación local separada. No abre Google ni accede a configuraciones privadas.
set -euo pipefail
cd "$(dirname "$0")"
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Este preparador es exclusivamente para el Mac del piloto."
  exit 1
fi
python3 - <<'PY'
import sys
if sys.version_info[:2] != (3, 9):
    raise SystemExit('Este perfil corresponde al Python 3.9 observado. No se cambia Python automáticamente.')
PY
pilot_venv=".venv-piloto-mac-142"
if [[ -e "$pilot_venv" || -L "$pilot_venv" ]]; then
  echo "Ya existe el entorno de esta carpeta. Se conserva intacto; no se reinstala automáticamente."
  exit 1
fi
python3 -m venv "$pilot_venv"
"$pilot_venv/bin/python" -m pip install -r requirements-pilot-mac.txt
"$pilot_venv/bin/python" -m pip check
"$pilot_venv/bin/python" - <<'PY'
import sys
from importlib.metadata import version
print('\nPREPARACIÓN LOCAL COMPLETADA')
print('Python:', sys.version.split()[0])
print('Streamlit:', version('streamlit'))
print('Authlib:', version('Authlib'))
print('Google no iniciado; sin base, usuarios ni configuración privada nueva.')
PY
