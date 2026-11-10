"""Herramientas LOCALES del piloto. Nunca llaman Google ni despliegan.

init crea un directorio nuevo. check es de lectura y no abre secretos.
user requiere autorización nominal previa; recibe sub por entrada oculta local.
"""
import argparse
import getpass
import importlib.metadata
import json
import os
import re
import sqlite3
from pathlib import Path

from decision_store import DecisionStore
from native_pilot_access import NativePilotAccess, ROLES

FORMAT = 'puente.0401.oidc.local.v1'
CASES = [f'P{n:02d}' for n in range(10)]


def write_private(path, text):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as out:
        out.write(text)


def workspace(directory):
    root = Path(directory).absolute()
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Directorio del piloto no válido.')
    marker = root/'pilot.json'
    if marker.is_symlink() or not marker.is_file():
        raise ValueError('Falta el marcador de aislamiento.')
    data = json.loads(marker.read_text(encoding='utf-8'))
    if (data.get('format') != FORMAT or data.get('database') != 'pilot.sqlite'
            or not re.fullmatch(r'[A-Za-z0-9._-]{1,200}', data.get('audience', ''))):
        raise ValueError('Marcador de aislamiento no válido.')
    path = root/'pilot.sqlite'
    if path.is_symlink() or not path.is_file():
        raise ValueError('Base aislada no válida.')
    with sqlite3.connect(path.as_uri()+'?mode=ro', uri=True) as db:
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'pilot_users', 'pilot_access_meta', 'pilot_security_events', 'revisions', 'decisions', 'events'} <= tables:
            raise ValueError('Base ajena o incompleta.')
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('Integridad de base no válida.')
    return root, path, data


def initialize(directory, audience):
    if not isinstance(audience, str) or not re.fullmatch(r'[A-Za-z0-9._-]{1,200}', audience):
        raise ValueError('Audiencia del piloto no válida.')
    root = Path(directory).absolute()
    # No reutilizar ni vaciar directorios existentes, aunque parezcan vacíos.
    root.mkdir(mode=0o700, parents=False, exist_ok=False)
    path = root/'pilot.sqlite'
    NativePilotAccess(path, audience)
    DecisionStore(path)  # Denegación por defecto; ninguna cuenta ni expediente.
    write_private(root/'pilot.json', json.dumps({
        'format': FORMAT, 'database': 'pilot.sqlite', 'audience': audience}, indent=2)+'\n')
    config_dir = root/'.streamlit'
    config_dir.mkdir(mode=0o700)
    write_private(config_dir/'config.toml', '''[server]
address = "localhost"
port = 8501
enableCORS = true
enableXsrfProtection = true

[browser]
gatherUsageStats = false
''')
    # Ejemplo inerte: no genera claves y no se llama secrets.toml.
    write_private(root/'secrets.example.toml', '''# Completar solo en el equipo autorizado; nunca subir a Git o Chat.
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
client_id = '''+json.dumps(audience)+'''
client_secret = "PENDIENTE_DE_AUTORIZACION"
cookie_secret = "PENDIENTE_DE_AUTORIZACION"
''')
    write_private(root/'resultados_piloto.json', json.dumps({
        'format': 'puente.0401.real-results.v1', 'status': 'NO_INICIADO',
        'cases': [{'id': case, 'status': 'NO_EJECUTADO', 'observed': '', 'evidence': ''} for case in CASES]
    }, ensure_ascii=False, indent=2)+'\n')
    return root


def check(directory):
    root, path, data = workspace(directory)
    missing = []
    versions = {}
    for distribution in ('streamlit', 'Authlib', 'google-auth'):
        try:
            versions[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            versions[distribution] = 'NO_INSTALADO'
            missing.append('DEPENDENCIA_'+distribution)
    if versions['streamlit'] not in ('1.67.0', '1.42.2'):
        missing.append('VERSION_STREAMLIT_NO_VALIDADA')
    if versions['streamlit'] == '1.42.2' and versions['Authlib'] != '1.3.2':
        missing.append('VERSION_AUTHLIB_NO_VALIDADA_PARA_MAC')
    # No leer, copiar, imprimir ni validar valores secretos en esta comprobación.
    secrets = root/'.streamlit/secrets.toml'
    if secrets.is_symlink() or not secrets.is_file():
        missing.append('CONFIGURACION_OIDC_LOCAL_PENDIENTE')
    if os.name == 'posix':
        for candidate in (root, path, secrets):
            if candidate.exists() and candidate.stat().st_mode & 0o077:
                missing.append('PERMISOS_LOCALES_AMPLIOS')
                break
    with sqlite3.connect(path.as_uri()+'?mode=ro', uri=True) as db:
        total = db.execute('SELECT COUNT(DISTINCT subject) FROM pilot_users').fetchone()[0]
        operators = db.execute('''SELECT COUNT(*) FROM
            (SELECT subject FROM pilot_users GROUP BY subject HAVING MIN(active)=1)''').fetchone()[0]
        if total > 2:
            missing.append('REGISTRO_SUPERA_DOS_IDENTIDADES')
        if operators != 2:
            missing.append('DOS_OPERADORES_PENDIENTES')
        # Nunca imprimir sub ni correos en la salida.
    return {'status': 'BLOQUEADO' if missing else 'PRECONDICIONES_LOCALES_PRESENTES',
            'versions': versions, 'blockers': missing,
            'google_login': 'NO_VERIFICADO', 'permissions_and_cookie_flow': 'NO_VERIFICADO',
            'oauth_values': 'NO_LEIDOS', 'production_ready': False}


def change_user(directory, subject, project, role, active):
    _, path, data = workspace(directory)
    # Esta herramienta solo usa IDs de fixtures del paquete revisado.
    projects = {json.loads(p.read_text(encoding='utf-8'))['record']['submission_id']
                for p in (Path(__file__).parent/'examples').glob('*_synthetic.json')}
    if project not in projects:
        raise ValueError('Proyecto ajeno a los fixtures del piloto.')
    access = NativePilotAccess(path, data['audience'])
    access.set_user(subject, project, role, active)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    init = commands.add_parser('init', help='Crear únicamente un directorio NUEVO de laboratorio')
    init.add_argument('--directory', required=True)
    init.add_argument('--audience', required=True, help='Client ID no secreto, o ficticio para ensayo local')
    verify = commands.add_parser('check', help='Comprobar sin red ni lectura de secretos')
    verify.add_argument('--directory', required=True)
    user = commands.add_parser('user', help='Administración LOCAL, solo con autorización nominal previa')
    user.add_argument('--directory', required=True)
    user.add_argument('--project', required=True)
    user.add_argument('--role', choices=sorted(ROLES), required=True)
    user.add_argument('--disable', action='store_true')
    user.add_argument('--authorized-change', action='store_true')
    args = parser.parse_args()
    try:
        if args.command == 'init':
            initialize(args.directory, args.audience)
            print('Laboratorio local vacío creado. Google NO configurado; prueba real NO iniciada.')
        elif args.command == 'check':
            result = check(args.directory)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 2 if result['blockers'] else 0
        else:
            if not args.authorized_change:
                raise ValueError('Falta confirmar autorización nominal previa; no se cambia el registro.')
            subject = getpass.getpass('sub verificado, solo en este equipo (entrada oculta): ')
            change_user(args.directory, subject, args.project, args.role, not args.disable)
            print('Cambio local registrado. No se muestran identidades ni se configura Google.')
        return 0
    except (OSError, ValueError, sqlite3.Error):
        print('Operación detenida: revisar directorio, aislamiento y autorización. No se muestran datos privados.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
