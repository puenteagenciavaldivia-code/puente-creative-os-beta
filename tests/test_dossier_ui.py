"""Pruebas Streamlit en memoria, sin backend ni secretos."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP=Path(__file__).resolve().parents[1]/'dossier_demo.py'


class DossierUITests(unittest.TestCase):
    def app(self):
        app=AppTest.from_file(str(APP),default_timeout=15).run()
        self.assertEqual(list(app.exception),[])
        return app
    def test_three_cases_render_and_validate(self):
        app=self.app()
        for i in range(3):
            app.selectbox[0].select_index(i).run()
            app.button[0].click().run()
            self.assertEqual(list(app.exception),[])
            self.assertEqual(list(app.error),[])
            self.assertTrue(app.dataframe)
    def test_invalid_import_shows_error(self):
        app=self.app();next(x for x in app.text_area if x.label=='Dossier JSON').set_value('{bad').run();app.button[0].click().run()
        self.assertTrue(app.error);self.assertEqual(list(app.exception),[])
    def test_creative_only_approval_flow(self):
        app=self.app();app.button[0].click().run()
        app.text_input[0].set_value('Dirección ficticia').run()
        next(x for x in app.text_area if x.label=='Fundamento de la decisión').set_value('Esta alternativa ofrece un concepto pertinente y un sistema visual claro para el caso ficticio.').run()
        app.checkbox[0].check().run();app.button[1].click().run()
        self.assertTrue(app.success);self.assertEqual(list(app.exception),[])
        self.assertEqual(app.selectbox[-1].value,'undecided')
    def test_editing_invalidates_visible_approval(self):
        app=self.app();app.button[0].click().run()
        next(x for x in app.text_area if x.label=='Dossier JSON').set_value(next(x for x in app.text_area if x.label=='Dossier JSON').value.replace('project_never_found','unused')+' ').run()
        # Semantic whitespace does not change content; changing objective does.
        import json
        d=json.loads(next(x for x in app.text_area if x.label=='Dossier JSON').value);d['objective']='Objetivo modificado para revisión'
        next(x for x in app.text_area if x.label=='Dossier JSON').set_value(json.dumps(d)).run()
        self.assertTrue(any('cambió' in w.value for w in app.warning))
        self.assertEqual(len(app.checkbox),0)


if __name__=='__main__':unittest.main()
