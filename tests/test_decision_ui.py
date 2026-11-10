import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

APP=Path(__file__).resolve().parents[1]/'decision_demo.py'
RATIONALE='La opción desarrolla un concepto pertinente y un sistema visual claro para este caso ficticio.'


class DecisionUITests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.env=patch.dict(os.environ,{'PUENTE_DECISION_LAB_PATH':str(Path(self.tmp.name)/'lab.sqlite')})
        self.env.start();self.addCleanup(self.env.stop)
    def app(self):
        app=AppTest.from_file(str(APP),default_timeout=15).run()
        self.assertEqual(list(app.exception),[])
        return app
    def save(self,app):app.button[0].click().run();self.assertFalse(app.exception)
    def decide(self,app):
        app.text_area[0].set_value(RATIONALE).run()
        app.checkbox[0].check().run();app.button[1].click().run()
        self.assertFalse(app.exception)
    def test_decision_survives_new_session(self):
        app=self.app();self.save(app);self.decide(app)
        self.assertFalse(app.error)
        fresh=self.app()
        self.assertEqual(fresh.metric[0].value,'1')
        self.assertTrue(any('creative_approved' in m.value for m in fresh.markdown))
    def test_operation_identity_cannot_approve(self):
        app=self.app();self.save(app)
        app.selectbox[1].select('operacion-ficticia').run();self.decide(app)
        self.assertTrue(any('denegado' in e.value for e in app.error))
    def test_new_revision_removes_current_approval(self):
        app=self.app();self.save(app);self.decide(app);self.save(app)
        self.assertTrue(any('todavía no tiene' in i.value for i in app.info))
    def test_project_history_not_shared(self):
        app=self.app();self.save(app);app.selectbox[0].select_index(1).run()
        self.assertEqual(app.metric[0].value,'0');self.assertFalse(app.exception)


if __name__=='__main__':unittest.main()
