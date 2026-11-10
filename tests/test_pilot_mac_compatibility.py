"""Compatibilidad de proxies nativos; no son tokens ni logins Google reales."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pilot_oidc_app import identity_user
from pilot_control import initialize, check


class MacCompatibilityTests(unittest.TestCase):
    def test_142_uses_experimental_server_proxy(self):
        proxy = object()
        self.assertIs(identity_user(SimpleNamespace(experimental_user=proxy)), proxy)

    def test_current_prefers_stable_proxy_without_reading_legacy(self):
        current = object()
        class API:
            user = current
            @property
            def experimental_user(self):
                raise AssertionError('No consultar alias antiguo cuando existe user')
        self.assertIs(identity_user(API()), current)

    def test_absent_user_does_not_create_a_fake_identity(self):
        self.assertIsNone(identity_user(SimpleNamespace()))

    def test_preflight_accepts_observed_mac_dependency_pair(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'pilot'
            initialize(root, 'client-ficticio')
            versions = {'streamlit': '1.42.2', 'Authlib': '1.3.2', 'google-auth': '2.62.1'}
            with patch('pilot_control.importlib.metadata.version', side_effect=versions.__getitem__):
                result = check(root)
        self.assertNotIn('VERSION_STREAMLIT_NO_VALIDADA', result['blockers'])
        self.assertNotIn('VERSION_AUTHLIB_NO_VALIDADA_PARA_MAC', result['blockers'])
        self.assertEqual(result['google_login'], 'NO_VERIFICADO')

    def test_preflight_refuses_unverified_authlib_change_for_142(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'pilot'
            initialize(root, 'client-ficticio')
            versions = {'streamlit': '1.42.2', 'Authlib': '1.6.12', 'google-auth': '2.62.1'}
            with patch('pilot_control.importlib.metadata.version', side_effect=versions.__getitem__):
                result = check(root)
        self.assertIn('VERSION_AUTHLIB_NO_VALIDADA_PARA_MAC', result['blockers'])


if __name__ == '__main__': unittest.main()
