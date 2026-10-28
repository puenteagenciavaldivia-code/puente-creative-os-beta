import unittest
from briefing_quality import diagnose, field_quality
from creative_handoff import build_handoff

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

class HandoffTests(unittest.TestCase):
    def test_handoff_preserves_original_and_never_approves(self):
        record={"submission_id":"example-id","answers":{
            "nombre":"Volterra","negocio":"Taller de bicicletas",
            "publico":"Personas que se mueven en bicicleta",
            "objetivo":"Conseguir consultas"},"diagnostic":{"flags":[]}}
        handoff=build_handoff(record)
        self.assertEqual(handoff["submission_id"],"example-id")
        self.assertEqual(handoff["respuestas_originales"],record["answers"])
        self.assertFalse(handoff["decisiones_creativas"]["aprobacion_humana"])
        self.assertIsNone(handoff["decisiones_creativas"]["corriente_madre"])
        self.assertIn("exploracion_de_corrientes_madre",handoff["preparacion"])

    def test_optional_missing_does_not_raise_flags(self):
        answers={"nombre":"Volterra","negocio":"Somos un taller de bicicletas en Valdivia y arreglamos bicicletas de todos los tamaños.",
                 "productos":"Realizamos servicios de frenos, cambios y mantencion general de bicicletas urbanas.",
                 "diferencia":"Entregamos un presupuesto claro y explicamos cada reparación antes de comenzar el trabajo.",
                 "publico":"Personas que usan sus bicicletas para moverse al trabajo y pasear en familia.",
                 "objetivo":"Conseguir consultas","canales":["Instagram"],
                 "identidad_visual":"Tenemos logo, pero no manual"}
        result=diagnose(answers)
        self.assertFalse(any(x["field"]=="referentes" for x in result["flags"]))
        self.assertEqual(result["optional_answered"],0)

if __name__=="__main__":
    unittest.main()
