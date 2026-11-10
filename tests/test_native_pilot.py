"""Pruebas LOCALES con st.user simulado. Ningún login/certificado Google real."""
import importlib.util
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from decision_store import DecisionStore, Scope
from native_pilot_access import NativePilotAccess, ISSUER
from review_workflow import new_review
from store_backup import backup_database, restore_database

ROOT = Path(__file__).resolve().parents[1]


class User(dict):
    @property
    def is_logged_in(self):
        return self['is_logged_in']


class NativePilotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'pilot.sqlite'
        self.now = 1000
        self.access = NativePilotAccess(self.path, 'client-ficticio', lambda: self.now)
        self.user = User(is_logged_in=True, iss=ISSUER, aud='client-ficticio',
                         sub='10001', iat=900, exp=2000)
        self.fixture = json.loads((ROOT/'examples/taller_rio_synthetic.json').read_text())
        self.project = self.fixture['record']['submission_id']
        self.scope = Scope('AGENCIA-FICTICIA', self.project)
        self.access.set_user('10001', self.project, 'direccion')
        self.actor = self.access.actor(self.user)
        self.store = DecisionStore(self.path, self.access.policy(self.user))

    def save(self, store=None, actor=None, version=0):
        f = self.fixture
        return (store or self.store).save_revision(actor or self.actor, self.scope, f['record'],
            f['audit'], new_review(f['record'], f['audit']), f['dossier'], version)

    def test_canonical_identity(self):
        self.user['iss'] = 'accounts.google.com'
        self.assertEqual(self.access.actor(self.user), self.actor)

    def test_invalid_claims_are_denied(self):
        for key, value in [('is_logged_in', False), ('iss', 'otro'), ('aud', 'otro'),
                           ('azp', 'otro'), ('sub', '１'), ('sub', 'nombre'),
                           ('iat', True), ('iat', float('nan')), ('iat', 1100),
                           ('exp', float('inf')), ('exp', 1000)]:
            with self.subTest(key=key, value=value):
                user = {**self.user, key: value}
                with self.assertRaises(PermissionError): self.access.actor(user)

    def test_email_and_claimed_role_do_not_grant_access(self):
        self.user.update(sub='20002', email='direccion@example.invalid', role='direccion')
        with self.assertRaises(PermissionError): self.access.projects(self.user)

    def test_unknown_user_logged_without_raw_claims(self):
        self.user['sub'] = '20002'
        with self.assertRaises(PermissionError): self.access.projects(self.user)
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT actor_hash,result FROM pilot_security_events WHERE action='access'").fetchone()
        self.assertEqual(row[1], 'denied')
        self.assertEqual(len(row[0]), 64)
        self.assertNotIn('20002', row[0])

    def test_registry_not_cached_for_existing_policy(self):
        self.save()
        self.access.set_user('10001', self.project, 'direccion', active=False)
        with self.assertRaises(PermissionError): self.store.load_latest(self.actor, self.scope)
        with self.assertRaises(PermissionError): self.store.history(self.actor, self.scope)

    def test_cross_project_denied_and_durable_event(self):
        with self.assertRaises(PermissionError):
            self.store.load_latest(self.actor, Scope('AGENCIA-FICTICIA', 'SYNTH-NO-ASIGNADO'))
        with sqlite3.connect(self.path) as db:
            payload = json.loads(db.execute('SELECT payload FROM events').fetchone()[0])
        self.assertEqual(payload['result'], 'denied')
        self.assertEqual(payload['action'], 'read')

    def test_operator_cannot_approve(self):
        self.save()
        self.access.set_user('10001', self.project, 'operacion')
        with self.assertRaises(PermissionError):
            self.store.decide(self.actor, self.scope, 1, 'irrelevante', 'fundamento', 'request-ficticio-0001')
        self.assertEqual(self.store.load_latest(self.actor, self.scope)['version'], 1)

    def test_expiry_rechecked_on_each_operation(self):
        self.save()
        self.now = 1800  # límite iat+900 aun si exp sigue vigente
        with self.assertRaises(PermissionError): self.store.load_latest(self.actor, self.scope)
        with self.assertRaises(PermissionError): self.save(version=1)

    def test_missing_epoch_fails_closed(self):
        with sqlite3.connect(self.path) as db: db.execute('DELETE FROM pilot_access_meta')
        with self.assertRaises(PermissionError): self.access.actor(self.user)
        fresh = NativePilotAccess(self.path, 'client-ficticio', lambda: 1000)
        with self.assertRaises(PermissionError): fresh.actor(self.user)

    def test_invalid_registration_rejected(self):
        for args in [('10001', 'REAL-1', 'direccion'), ('10001', self.project, 'admin'),
                     ('email@example.invalid', self.project, 'direccion')]:
            with self.subTest(args=args):
                with self.assertRaises(ValueError): self.access.set_user(*args)

    def test_unknown_role_in_database_denied(self):
        with sqlite3.connect(self.path) as db: db.execute("UPDATE pilot_users SET role='admin'")
        with self.assertRaises(PermissionError): self.access.projects(self.user)
        self.assertFalse(self.access.policy(self.user)(self.actor, self.scope, 'read'))

    def test_project_list_excludes_other_users(self):
        self.access.set_user('20002', 'SYNTH-OTRO', 'direccion')
        self.assertEqual(self.access.projects(self.user), [self.project])

    def test_existing_gate_after_restore_requires_new_identity(self):
        self.save()
        backup = Path(self.tmp.name)/'backup.sqlite'
        restored = Path(self.tmp.name)/'restored.sqlite'
        backup_database(self.path, backup)
        with patch('store_backup.time.time', return_value=1001):
            restore_database(backup, restored)
        access = NativePilotAccess(restored, 'client-ficticio', lambda: 1010)
        store = DecisionStore(restored, access.policy(self.user))
        with self.assertRaises(PermissionError): store.load_latest(self.actor, self.scope)
        self.user.update(iat=1002, exp=2000)
        self.assertEqual(store.load_latest(access.actor(self.user), self.scope)['version'], 1)

    def test_policy_rechecks_epoch_even_if_created_before_restore(self):
        policy = self.access.policy(self.user)
        self.assertTrue(policy(self.actor, self.scope, 'read'))
        with sqlite3.connect(self.path) as db: db.execute('UPDATE pilot_access_meta SET not_before=1001')
        self.assertFalse(policy(self.actor, self.scope, 'read'))

    def test_registry_survives_new_access_instance(self):
        fresh = NativePilotAccess(self.path, 'client-ficticio', lambda: 1000)
        self.assertEqual(fresh.projects(self.user), [self.project])

    def test_two_operator_limit_preserved_from_previous_lab(self):
        self.access.set_user('20002', self.project, 'operacion')
        with self.assertRaises(ValueError): self.access.set_user('30003', self.project, 'operacion')

    def test_revoked_slot_is_not_reused_by_an_implicit_new_identity(self):
        self.access.set_user('20002', self.project, 'operacion')
        self.access.set_user('20002', self.project, 'operacion', active=False)
        with self.assertRaises(ValueError): self.access.set_user('30003', self.project, 'operacion')

    def test_provisioning_does_not_reactivate_revoked_user(self):
        self.access.set_user('10001', self.project, 'direccion', active=False)
        for project in (self.project, 'SYNTH-OTRO'):
            with self.subTest(project=project):
                with self.assertRaises(ValueError): self.access.set_user('10001', project, 'direccion')
        with self.assertRaises(PermissionError): self.access.projects(self.user)

    def test_revocation_covers_all_projects_for_the_identity(self):
        other = Scope('AGENCIA-FICTICIA', 'SYNTH-OTRO')
        self.access.set_user('10001', other.project, 'direccion')
        self.access.set_user('10001', self.project, 'direccion', active=False)
        self.assertFalse(self.access.policy(self.user)(self.actor, other, 'read'))

    def test_legacy_partial_revocation_is_conservatively_denied(self):
        self.access.set_user('10001', 'SYNTH-OTRO', 'direccion')
        with sqlite3.connect(self.path) as db:
            db.execute('UPDATE pilot_users SET active=0 WHERE project=?', (self.project,))
        self.assertFalse(self.access.policy(self.user)(self.actor, Scope('AGENCIA-FICTICIA', 'SYNTH-OTRO'), 'read'))

    def test_existing_overfull_registry_fails_closed_without_deleting_data(self):
        with sqlite3.connect(self.path) as db:
            for subject in ('20002', '30003'):
                db.execute('INSERT INTO pilot_users VALUES(?,?,?,?,?)',
                           (subject, self.scope.agency, self.project, 'operacion', 1))
        with self.assertRaises(PermissionError): self.access.projects(self.user)
        self.assertFalse(self.access.policy(self.user)(self.actor, self.scope, 'read'))
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT COUNT(DISTINCT subject) FROM pilot_users').fetchone()[0], 3)

    def test_concurrent_grants_respect_the_same_two_operator_limit(self):
        from concurrent.futures import ThreadPoolExecutor
        def provision(subject):
            try:
                self.access.set_user(subject, self.project, 'operacion')
                return 'allowed'
            except ValueError:
                return 'denied'
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(provision, ['20002', '30003'])), ['allowed', 'denied'])

    def test_disabled_app_does_not_create_database(self):
        missing = Path(self.tmp.name)/'must-not-exist.sqlite'
        with patch.dict(os.environ, {'PUENTE_OIDC_PILOT_ENABLED': '0', 'PUENTE_OIDC_PILOT_DB': str(missing)}):
            app = AppTest.from_file(str(ROOT/'pilot_oidc_app.py')).run()
        self.assertFalse(app.exception)
        self.assertFalse(missing.exists())
        self.assertEqual(len(app.selectbox), 0)

    def run_ui(self, app, user):
        # Proveedor y dependencia simulados: no se invoca st.login ni Google.
        real_find = importlib.util.find_spec
        find = lambda name, *args: object() if name == 'authlib' else real_find(name, *args)
        # iat/exp solo ficticios, adecuados al reloj real de la UI.
        import time
        self.now = time.time()
        user.update(iat=time.time()-1, exp=time.time()+600)
        env = {'PUENTE_OIDC_PILOT_ENABLED': '1', 'PUENTE_OIDC_PILOT_DB': str(self.path)}
        get_option = __import__('streamlit').get_option
        option = lambda name: 'localhost' if name == 'server.address' else get_option(name)
        user_attribute = 'user' if hasattr(__import__('streamlit'), 'user') else 'experimental_user'
        with patch.dict(os.environ, env), patch('streamlit.'+user_attribute, user), patch('importlib.util.find_spec', side_effect=find), patch('streamlit.get_option', side_effect=option):
            app.run()
        self.assertFalse(app.exception)
        return app

    def ui(self, user):
        app = AppTest.from_file(str(ROOT/'pilot_oidc_app.py'), default_timeout=15)
        app.secrets = {'auth': {'redirect_uri': 'http://localhost:8501/oauth2callback',
            'server_metadata_url': 'https://accounts.google.com/.well-known/openid-configuration',
            'client_id': 'client-ficticio', 'client_secret': 'FICTICIO', 'cookie_secret': 'FICTICIO'*8}}
        return self.run_ui(app, user)

    def test_ui_known_identity_loads_only_assigned_project(self):
        app = self.ui(self.user)
        self.assertFalse(app.error)
        self.assertEqual(app.selectbox[0].options, [self.project])
        self.assertFalse(any('simulada' in str(s.label).lower() for s in app.selectbox))

    def test_ui_unknown_identity_stops_before_project_controls(self):
        self.user['sub'] = '20002'
        app = self.ui(self.user)
        self.assertTrue(app.error)
        self.assertEqual(len(app.selectbox), 0)

    def test_self_enrollment_display_does_not_grant_access(self):
        self.user['sub'] = '20002'
        app = self.ui(self.user)
        app.checkbox[0].check()
        self.run_ui(app, self.user)
        self.assertEqual(app.code[0].value, '20002')
        self.assertEqual(len(app.selectbox), 0)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM pilot_users WHERE subject='20002'").fetchone()[0], 0)

    def test_ui_save_and_human_decision_persist(self):
        app = self.ui(self.user)
        app.button[1].click()
        self.run_ui(app, self.user)
        self.assertEqual(app.metric[0].value, '1')
        app.text_area[0].set_value('La alternativa presenta una dirección coherente con el briefing ficticio revisado.')
        app.checkbox[0].check()
        self.run_ui(app, self.user)
        app.button[2].click()
        self.run_ui(app, self.user)
        self.assertFalse(app.error)
        self.assertEqual(self.store.latest_decision(self.actor, self.scope)['package']['status'], 'creative_approved')

    def test_ui_revocation_removes_project_controls(self):
        app = self.ui(self.user)
        self.access.set_user('10001', self.project, 'direccion', active=False)
        self.run_ui(app, self.user)
        self.assertTrue(app.error)
        self.assertEqual(len(app.selectbox), 0)

    def test_ui_operator_approval_denied(self):
        self.save()
        self.access.set_user('10001', self.project, 'operacion')
        app = self.ui(self.user)
        app.text_area[0].set_value('Fundamento ficticio para comprobar una denegación efectiva en el servidor.')
        app.checkbox[0].check()
        self.run_ui(app, self.user)
        app.button[2].click()
        self.run_ui(app, self.user)
        self.assertTrue(app.error)
        self.assertIsNone(self.store.latest_decision(self.actor, self.scope))


if __name__ == '__main__': unittest.main()
