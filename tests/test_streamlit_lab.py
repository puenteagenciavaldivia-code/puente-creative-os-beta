import unittest
from streamlit.testing.v1 import AppTest

class StreamlitLabSmoke(unittest.TestCase):
    def test_initial_screen_offline(self):
        at = AppTest.from_file("app.py", default_timeout=30).run()
        self.assertFalse(at.exception, [str(x.message) for x in at.exception])
        self.assertTrue(at.title)
        self.assertTrue(any('Descubramos tu marca' in t.value for t in at.title))
        self.assertTrue(any('Identidad' in x.value for x in at.subheader))
        self.assertTrue(any('recepción automática' in x.message for x in at.warning))

    def test_first_step_requires_fields(self):
        at = AppTest.from_file("app.py", default_timeout=30).run()
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
