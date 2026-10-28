import unittest
from briefing_quality import diagnose, field_quality

class BriefingQualityTests(unittest.TestCase):
    def test_gibberish_is_flagged(self):
        for text in ("sdfsdfgdsfhg", "asdfasdf", "dfghdfgh", "1234"):
            self.assertEqual(field_quality("negocio", text)[0], 0.0)

    def test_clear_answer_receives_full_credit(self):
        text = "Somos un taller de bicicletas en Valdivia y hacemos mantenciones y reparaciones de componentes."
        self.assertEqual(field_quality("negocio", text)[0], 1.0)

    def test_missing_core_information_blocks_approval(self):
        answers = dict.fromkeys((
            "nombre negocio personalidad recuerdo productos diferencia destacar competencia "
            "publico publico_nuevo dudas tono identidad_visual elementos referentes evitar "
            "objetivo canales materiales condiciones"
        ).split(), "sdfsdfgdsfhg")
        answers["nombre"] = "VOLTERRA"
        answers["tono"] = "Cercano"
        answers["objetivo"] = "Conseguir consultas"
        answers["canales"] = ["Instagram", "WhatsApp"]
        answers["identidad_visual"] = "Tenemos logo, pero no manual"
        result = diagnose(answers)
        self.assertLess(result["score"], 60)
        self.assertEqual(result["status"], "insuficiente")
        self.assertTrue(result["follow_up_questions"])

    def test_realistic_briefing_is_distinct_from_placeholder(self):
        answers = {
            "nombre":"VOLTERRA",
            "negocio":"Somos un taller de bicicletas urbanas de Valdivia y realizamos ajustes, reparaciones y ventas de accesorios.",
            "productos":"Ofrecemos mantención general, ajuste de frenos y cambios, reparación de ruedas y accesorios para ciclistas.",
            "diferencia":"Entregamos diagnóstico antes de reparar, explicamos precios y mantenemos historial de cada bicicleta.",
            "publico":"Atendemos personas que usan la bicicleta para trabajar, desplazarse y salir a rutas de fin de semana.",
            "objetivo":"Conseguir consultas",
            "canales":["Instagram","WhatsApp"],
            "tono":"Cercano",
            "identidad_visual":"Tenemos logo, pero no manual",
        }
        result=diagnose(answers)
        self.assertGreater(result["score"], 25)
        self.assertTrue(result["human_review_required"])
        self.assertFalse(result["approved"])

if __name__=="__main__":
    unittest.main()
