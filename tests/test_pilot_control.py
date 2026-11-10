"""Operación del paquete con bases/identidades FICTICIAS; sin red ni OAuth."""
import importlib.metadata
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pilot_control import initialize, workspace, check, change_user


class PilotControlTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)/'pilot'
        self.project = json.loads((Path(__file__).resolve().parents[1]/'examples/taller_rio_synthetic.json').read_text())['record']['submission_id']

    def init(self):
        return initialize(self.root, 'audiencia-ficticia')

    def test_initialization_never_creates_real_config_or_users(self):
        self.init()
        _, path, _ = workspace(self.root)
        self.assertFalse((self.root/'.streamlit/secrets.toml').exists())
        with sqlite3.connect(path) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM pilot_users').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM revisions').fetchone()[0], 0)
        result = json.loads((self.root/'resultados_piloto.json').read_text())
        self.assertEqual(result['status'], 'NO_INICIADO')
        self.assertTrue(all(case['status'] == 'NO_EJECUTADO' for case in result['cases']))

    def test_existing_directory_refused_without_changes(self):
        self.root.mkdir()
        (self.root/'original').write_text('conservar')
        with self.assertRaises(FileExistsError): self.init()
        self.assertEqual(list(self.root.iterdir()), [self.root/'original'])

    def test_invalid_audience_does_not_create_directory(self):
        with self.assertRaises(ValueError): initialize(self.root, 'audiencia\n[auth]')
        self.assertFalse(self.root.exists())

    def test_check_is_read_only_and_does_not_read_secrets(self):
        self.init()
        secret = self.root/'.streamlit/secrets.toml'
        secret.write_text('NO_LEER_VALOR_FICTICIO')
        secret.chmod(0o600)
        before = (self.root/'pilot.sqlite').read_bytes()
        original = Path.read_text
        def read(path, *args, **kwargs):
            if path == secret: raise AssertionError('No abrir secretos')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', read): result = check(self.root)
        self.assertEqual(result['oauth_values'], 'NO_LEIDOS')
        self.assertEqual(before, (self.root/'pilot.sqlite').read_bytes())
        self.assertFalse(result['production_ready'])

    def test_missing_dependencies_are_blockers(self):
        self.init()
        def version(name):
            if name == 'Authlib': raise importlib.metadata.PackageNotFoundError()
            return '1.67.0' if name == 'streamlit' else '2.62.1'
        with patch('pilot_control.importlib.metadata.version', side_effect=version):
            result = check(self.root)
        self.assertIn('DEPENDENCIA_Authlib', result['blockers'])
        self.assertEqual(result['google_login'], 'NO_VERIFICADO')

    def test_foreign_database_or_marker_refused(self):
        self.init()
        (self.root/'pilot.json').write_text(json.dumps({'format': 'beta', 'database': 'pilot.sqlite'}))
        with self.assertRaises(ValueError): workspace(self.root)

    def test_database_symlink_refused(self):
        self.init()
        target = Path(self.tmp.name)/'outside.sqlite'
        (self.root/'pilot.sqlite').rename(target)
        (self.root/'pilot.sqlite').symlink_to(target)
        with self.assertRaises(ValueError): workspace(self.root)

    def test_fictional_grant_and_revocation_recorded(self):
        self.init()
        change_user(self.root, '10001', self.project, 'direccion', True)
        change_user(self.root, '10001', self.project, 'direccion', False)
        with sqlite3.connect(self.root/'pilot.sqlite') as db:
            self.assertEqual(db.execute('SELECT active FROM pilot_users').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM pilot_security_events').fetchone()[0], 2)

    def test_real_project_refused(self):
        self.init()
        with self.assertRaises(ValueError): change_user(self.root, '10001', 'REAL-CLIENTE', 'direccion', True)

    def test_preconditions_never_equal_real_login_success(self):
        self.init()
        change_user(self.root, '10001', self.project, 'direccion', True)
        change_user(self.root, '20002', self.project, 'operacion', True)
        secret = self.root/'.streamlit/secrets.toml'
        secret.write_text('FICTICIO')
        secret.chmod(0o600)
        with patch('pilot_control.importlib.metadata.version', return_value='1.67.0'):
            result = check(self.root)
        self.assertEqual(result['status'], 'PRECONDICIONES_LOCALES_PRESENTES')
        self.assertEqual(result['google_login'], 'NO_VERIFICADO')
        self.assertFalse(result['production_ready'])

    def test_preflight_matches_gate_for_old_overfull_registry(self):
        self.init()
        with sqlite3.connect(self.root/'pilot.sqlite') as db:
            for subject, active in [('10001', 1), ('20002', 1), ('30003', 0)]:
                db.execute('INSERT INTO pilot_users VALUES(?,?,?,?,?)',
                           (subject, 'AGENCIA-FICTICIA', self.project, 'direccion', active))
        result = check(self.root)
        self.assertIn('REGISTRO_SUPERA_DOS_IDENTIDADES', result['blockers'])

    def test_preflight_counts_partial_revocation_as_revoked_identity(self):
        self.init()
        with sqlite3.connect(self.root/'pilot.sqlite') as db:
            for subject, project, active in [('10001', self.project, 1),
                                             ('10001', 'SYNTH-OTRO', 0),
                                             ('20002', self.project, 1)]:
                db.execute('INSERT INTO pilot_users VALUES(?,?,?,?,?)',
                           (subject, 'AGENCIA-FICTICIA', project, 'direccion', active))
        self.assertIn('DOS_OPERADORES_PENDIENTES', check(self.root)['blockers'])


if __name__ == '__main__': unittest.main()
