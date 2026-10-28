import unittest
from briefing_quality import diagnose, field_quality
from creative_handoff import build_handoff
from strategic_audit import audit_briefing
from review_workflow import new_review, validate_review, prepare_reviewed_package
from design_catalog import read_catalog, search_catalog
from design_methodology import CRITERIA, BIBLIOGRAPHY
from ai_art_direction import validate_suggestions
from clarifications import build_request,validate_request,build_reply,validate_reply,attach_reply
from creative_preselection import preselect
from dashboard_helpers import public_clarification_url,invitation_copy,whatsapp_share_url,mailto_url

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

class StrategicAuditTests(unittest.TestCase):
    def test_tourism_gaps_even_with_fully_written_brief(self):
        a={"negocio":"Somos una empresa de turismo de naturaleza en la Región de Los Ríos",
           "productos":"Ofrecemos caminatas guiadas de medio día en grupos pequeños",
           "objetivo":"Conseguir consultas", "publico":"Parejas y familias que visitan Valdivia",
           "materiales":"Tenemos muchas fotografías y testimonios",
           "condiciones":"Queremos lanzar una campaña de verano"}
        result=audit_briefing(a)
        ids={q["id"] for q in result["preguntas_priorizadas"]}
        self.assertIn("precios",ids)
        self.assertIn("seguridad",ids)
        self.assertIn("indicador",ids)
        self.assertTrue(result["apto_para_producir"] is False)

    def test_bosque_adentro_vague_mentions_still_need_details(self):
        a={
            "negocio":"Somos una empresa de turismo de naturaleza. Organizamos caminatas guiadas.",
            "productos":"Ofrecemos caminatas guiadas de medio día, para grupos pequeños y excursiones.",
            "diferencia":"Los clientes valoran la tranquilidad y los grupos pequeños.",
            "publico":"Parejas y familias que visitan Valdivia.",
            "objetivo":"Conseguir consultas",
            "accion":"Reservar",
            "materiales":"Tenemos fotos y testimonios de las excursiones.",
            "condiciones":"Queremos explicar cómo reservar y qué hacer cuando llueve."
        }
        ids={q["id"] for q in audit_briefing(a)["preguntas_priorizadas"]}
        self.assertIn("conversion",ids)
        self.assertIn("clima",ids)
        self.assertIn("cupos",ids)
        self.assertNotIn("duracion",ids)

    def test_avoid_duplicate_questions_when_info_explicit(self):
        a={"negocio":"Cafetería de barrio", "productos":"Tenemos una carta disponible con precios actualizados",
           "condiciones":"Atendemos de lunes a viernes, presupuesto mensual para pauta y pedidos por WhatsApp",
           "materiales":"Tenemos fotos con permiso para publicar"}
        ids={q["id"] for q in audit_briefing(a)["preguntas_priorizadas"]}
        self.assertNotIn("horarios",ids)
        self.assertNotIn("carta",ids)
        self.assertNotIn("permisos",ids)
        self.assertNotIn("conversion",ids)

class HumanReviewWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.record={"submission_id":"id-123","answers":{"nombre":"Bosque Adentro","objetivo":"Conseguir consultas"}}
        self.audit={"preguntas_priorizadas":[
            {"id":"precios","pregunta":"¿Qué precios tienen?"},
            {"id":"reservas","pregunta":"¿Cómo se reserva?"}
        ]}
        self.review=new_review(self.record,self.audit)

    def test_default_cannot_approve_or_produce(self):
        self.assertTrue(validate_review(self.review,self.record,self.audit))
        handoff=build_handoff(self.record)
        package=prepare_reviewed_package(handoff,self.review,self.audit)
        self.assertFalse(package["aprobado_para_produccion"])

    def test_requires_two_distinct_evidenced_directions(self):
        self.review["responsable"]="Equipo Puente"
        self.review["revision"]={
            "precios":{"estado":"confirmado","nota":"Precios validados por el cliente"},
            "reservas":{"estado":"descartado","nota":"Se excluye porque la campaña es informativa"}
        }
        self.review["corrientes"]=[{
            "nombre":"Naturalismo editorial",
            "fundamento":"El cliente declaró que busca fotografías reales del bosque.",
            "diferenciacion":"Se fundamenta en ilustración botánica y narrativa pausada.",
            "riesgos":"Puede generar problemas de legibilidad y poca diferenciación."
        }]
        self.review["direccion_seleccionada"]="Naturalismo editorial"
        self.review["observaciones"]="La propuesta se alinea con referencias del cliente."
        self.assertTrue(any("dos o tres" in e for e in validate_review(self.review,self.record,self.audit)))
        self.review["corrientes"].append({
            "nombre":"Documental fotográfico",
            "fundamento":"El cliente tiene fotografías originales de sus excursiones.",
            "diferenciacion":"Prioriza escenas reales y retratos en contexto.",
            "riesgos":"Las fotos podrían no tener una calidad consistente."
        })
        self.assertEqual(validate_review(self.review,self.record,self.audit),[])
        handoff=build_handoff(self.record)
        package=prepare_reviewed_package(handoff,self.review,self.audit)
        self.assertFalse(package["aprobado_para_produccion"])
        self.review["autorizacion_produccion"]=True
        package=prepare_reviewed_package(handoff,self.review,self.audit)
        self.assertTrue(package["aprobado_para_produccion"])
        self.assertEqual(package["decisiones_creativas"]["corriente_madre"],"Naturalismo editorial")

    def test_rejects_cross_brand_review(self):
        self.review["submission_id"]="different-id"
        self.assertTrue(any("no corresponde" in e for e in validate_review(self.review,self.record,self.audit)))

class DesignCatalogTests(unittest.TestCase):
    def test_catalog_has_diverse_categories_and_unique_ids(self):
        items=read_catalog()
        self.assertGreaterEqual(len(items),35)
        self.assertEqual(len({x["id"] for x in items}),len(items))
        self.assertIn("histórica",{x["categoria"] for x in items})
        self.assertIn("lenguaje fotográfico",{x["categoria"] for x in items})
        self.assertIn("técnica",{x["categoria"] for x in items})

    def test_search_finds_both_history_and_photo(self):
        self.assertTrue(any("Swiss" in x["nombre"] or "Tipográfico Internacional" in x["nombre"]
                 for x in search_catalog("tipográfico")))
        self.assertTrue(any(x["nombre"]=="Fotografía documental" for x in search_catalog("documental")))

class MethodologyTests(unittest.TestCase):
    def test_references_have_verifiable_sources(self):
        self.assertGreaterEqual(len(BIBLIOGRAPHY),4)
        self.assertTrue(all(x["url"].startswith("https://") for x in BIBLIOGRAPHY))
        self.assertIn("audiencia",CRITERIA)
        self.assertIn("accesibilidad",CRITERIA)

    def test_ai_output_requires_exact_source_evidence(self):
        answers={"referentes":"Nos gustan los libros antiguos de exploración.","negocio":"Somos guías de naturaleza."}
        names=[x for x in read_catalog() if x["categoria"] in ("histórica","enfoque")][:3]
        def proposal(x):
            return {"nombre":x["nombre"],"movimiento_catalogo_id":x["id"],
                    "categoria":x["categoria"],"argumento":"Una investigación razonada para la propuesta editorial.",
                    "evidencias":[{"campo":"referentes","cita_respuesta":"libros antiguos de exploración"}],
                    "sistema_visual":"Un sistema visual coherente y de composición editorial.",
                    "tipografia":"Jerarquía tipográfica legible y con fuerte contraste.",
                    "tratamiento_fotografico":"Fotografía real y documental.",
                    "aplicaciones":"Aplicaciones en piezas de redes sociales y documentos.",
                    "contraste":"Alternativa diferenciable mediante su estructura y ritmo.",
                    "riesgos":"Puede resultar genérica si no se incorpora contexto local.",
                    "criterios_verificar":"Validación editorial del director de arte."}
        result={"diagnostico":"Prueba","preguntas_criticas":[],"propuestas":[proposal(x) for x in names]}
        self.assertEqual(len(validate_suggestions(result,answers)["propuestas"]),3)
        result["propuestas"][1]["evidencias"][0]["cita_respuesta"]="cita inventada"
        with self.assertRaises(ValueError):
            validate_suggestions(result,answers)

class ClarificationsTests(unittest.TestCase):
    def setUp(self):
        self.record={"submission_id":"brief-001","answers":{"nombre":"Bosque Adentro"}}
        self.audit={"preguntas_priorizadas":[
            {"id":"precios","pregunta":"¿Cuáles son los precios?","prioridad":"alta"},
            {"id":"clima","pregunta":"¿Qué ocurre si llueve?","prioridad":"alta"}]}

    def test_targeted_questions_roundtrip(self):
        req=build_request(self.record,self.audit,["precios"])
        validate_request(req)
        self.assertEqual(len(req["preguntas"]),1)
        reply=build_reply(req,{"precios":"Las tarifas se confirman cada temporada."})
        validate_reply(reply,self.record,self.audit)
        review={"revision":{}}
        updated=attach_reply(review,reply,self.record,self.audit)
        self.assertEqual(updated["aclaraciones_cliente"]["estado"],"recibido_sin_verificar")
        self.assertNotIn("precios",updated["revision"])

    def test_cannot_import_to_another_brand(self):
        req=build_request(self.record,self.audit,["clima"])
        reply=build_reply(req,{"clima":"Necesito ayuda"})
        with self.assertRaises(ValueError):
            validate_reply(reply,{"submission_id":"another-brief"},self.audit)

class NoApiFallbackTests(unittest.TestCase):
    def test_prefill_three_options_without_claiming_ai(self):
        a={"negocio":"Ofrecemos caminatas por el bosque valdiviano.",
           "referentes":"Nos gustan fotografías documentales y libros de botánica.",
           "personalidad":"Somos tranquilos, cercanos y nos interesa la naturaleza."}
        proposals=preselect(a)
        self.assertEqual(len(proposals),3)
        self.assertEqual(len({p["nombre"] for p in proposals}),3)
        self.assertTrue(all(p["tipo"]=="preseleccion_por_reglas" for p in proposals))
        self.assertTrue(all(len(p["fundamento"])>20 for p in proposals))

    def test_empty_brief_produces_no_prefill(self):
        self.assertEqual(preselect({}),[])

class InvitationLinkTests(unittest.TestCase):
    def test_secure_link_never_contains_briefing_data(self):
        token="a"*64
        url=public_clarification_url("https://puente-test.streamlit.app",token)
        self.assertIn("/Aclaraciones?t=",url)
        self.assertNotIn("BOSQUE ADENTRO",url)
        self.assertIn(token,url)

    def test_link_rejects_other_hosts(self):
        for host in ("https://evil.test","http://puente.streamlit.app",
                     "https://puente.streamlit.app.evil.org"):
            with self.assertRaises(ValueError):
                public_clarification_url(host,"b"*64)

    def test_invites_use_same_link(self):
        link=public_clarification_url("https://puente-test.streamlit.app","a"*64)
        msg=invitation_copy("Bosque Adentro",link)
        self.assertIn(link,msg)
        self.assertIn("https://wa.me/?text=",whatsapp_share_url(msg))
        self.assertIn("mailto:cliente@example.com",mailto_url("cliente@example.com","Bosque Adentro",msg))

if __name__=="__main__":
    unittest.main()
