import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP_FILE = Path(__file__).resolve().parents[1] / 'app.py'

class StreamlitLabSmoke(unittest.TestCase):
    def test_initial_screen_offline(self):
        at = AppTest.from_file(str(APP_FILE), default_timeout=30).run()
        self.assertFalse(at.exception, [str(x.message) for x in at.exception])
        self.assertTrue(at.title)
        self.assertTrue(any('Descubramos tu marca' in t.value for t in at.title))
        self.assertTrue(any('Identidad' in x.value for x in at.subheader))
        self.assertTrue(any('recepción automática' in x.value for x in at.warning))

    def test_first_step_requires_fields(self):
        at = AppTest.from_file(str(APP_FILE), default_timeout=30).run()
        self.assertFalse(at.exception)
        forward = [x for x in at.button if x.label == 'Continuar →']
        self.assertEqual(len(forward), 1)
        self.assertTrue(forward[0].disabled)
        at.text_input[0].set_value('Taller de prueba').run()
        at.text_area[0].set_value('Venta de productos artesanales de prueba').run()
        self.assertFalse(at.exception)
        forward = [x for x in at.button if x.label == 'Continuar →']
        self.assertFalse(forward[0].disabled)
        forward[0].click().run()
        self.assertFalse(at.exception)
        self.assertTrue(any('Negocio' in x.value for x in at.subheader))

    def test_five_step_offline_flow(self):
        at = AppTest.from_file(str(APP_FILE), default_timeout=30).run()
        def fill(collection, key, value):
            matches = [widget for widget in collection if widget.key == key]
            self.assertEqual(len(matches), 1, (key, [x.key for x in collection]))
            matches[0].set_value(value).run()
            self.assertFalse(at.exception, [str(x.message) for x in at.exception])
        def forward():
            matches = [x for x in at.button if x.label == "Continuar →"]
            self.assertEqual(len(matches), 1)
            self.assertFalse(matches[0].disabled)
            matches[0].click().run()
            self.assertFalse(at.exception, [str(x.message) for x in at.exception])
        fill(at.text_input, "nombre", "Marca ficticia")
        fill(at.text_area, "negocio", "Servicios ficticios de prueba")
        forward()
        fill(at.text_area, "productos", "Producto ficticio")
        fill(at.text_area, "diferencia", "Atencion ficticia y personalizada")
        forward()
        fill(at.text_area, "publico", "Personas adultas ficticias")
        forward()
        fill(at.selectbox, "identidad_visual", "No tenemos identidad visual")
        forward()
        fill(at.selectbox, "objetivo", "Conseguir consultas")
        fill(at.multiselect, "canales", ["Instagram"])
        fill(at.checkbox, "consent", True)
        ready = [x for x in at.button if x.label == "Revisar respuestas →"]
        self.assertEqual(len(ready), 1)
        self.assertFalse(ready[0].disabled)
        ready[0].click().run()
        self.assertFalse(at.exception)
        confirm = [x for x in at.button if x.label == "Confirmar y enviar"]
        self.assertEqual(len(confirm), 1)
        confirm[0].click().run()
        self.assertFalse(at.exception, [str(x.message) for x in at.exception])
        self.assertTrue(at.session_state["finished"])
        self.assertFalse(at.session_state["saved"])
        self.assertEqual(at.session_state["export"]["answers"]["nombre"], "Marca ficticia")
        self.assertIs(at.session_state["export"]["files_consent"], False)
