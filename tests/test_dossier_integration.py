"""Pruebas de regresión del flujo de dossier independiente de producción."""
import copy
import unittest
from dossier_engine import validate_dossier,prepare,approve_creative,handoff,dossier_html
from creative_dossier_bridge import prepare_for_brief,finalize_from_review,deliver_creative
from review_workflow import new_review

def case():
    record={"submission_id":"test-001","answers":{"nombre":"Marca prueba"}}
    audit={"preguntas_priorizadas":[{"id":"a1"}]}
    dirs=[]
    for i in "AB":
        dirs.append({"id":i,"name":"Concepto "+i,"insight":"Insight verificable y contextual",
          "big_idea":"Idea estratégica de comunicación",
          "promise":"Promesa para el público indicado",
          "visual_system":"Sistema editorial estructurado",
          "typography":"Jerarquía tipográfica definida",
          "photography":"Fotografía documental contextual",
          "composition":"Retícula adaptable y original",
          "differentiation":"Diferenciación respecto de competidores",
          "visual_signature":"signature_"+i,
          "risks":["Limitaciones pendientes de revisión"],
          "applications":{k:"Aplicación editorial propuesta "+k for k in ("feed","carousel","story","reel")},
          "references":["s1"]})
    dossier={"schema_version":"puente.dossier.v0.2","brand":"Marca prueba",
        "brief":"Briefing estratégico completo",
        "audience":"Audiencia correctamente delimitada",
        "communication_problem":"Comunicación sin diferenciación",
        "objective":"Generar posicionamiento con identidad",
        "constraints":["No inventar cifras"],
        "directions":dirs,
        "source_register":[{"id":"s1","type":"client","origin":"Briefing original del cliente","usage":"Objetivo e identidad"}],
        "comparison":{"criteria":["Pertinencia","Originalidad"],"tradeoffs":"Evaluación contextual de opciones",
        "recommendation":"A","rejected_reasons":{"B":"Menos pertinente para el objetivo original"}},
        "production_approved":False,"requested_route":"undecided"}
    review=new_review(record,audit)
    review.update({"revision":{"a1":{"estado":"confirmado","nota":"Confirmado por dirección"}},
       "corrientes":[{"nombre":d["name"],"fundamento":"Criterio creativo respaldado por briefing",
         "riesgos":"Riesgos de producción documentados",
         "diferenciacion":"Contraste comprobable con otras corrientes"} for d in dirs],
       "direccion_seleccionada":"Concepto A",
       "observaciones":"Alinea el objetivo y permite una solución original y escalable.",
       "responsable":"Directora creativa de pruebas",
       "autorizacion_produccion":False})
    return record,audit,review,dossier

class CreativeDirectionIntegration(unittest.TestCase):
    def setUp(self):
        self.record,self.audit,self.review,self.dossier=case()
        self.package=prepare_for_brief(self.record,self.dossier)
    def test_dossier_valid(self):
        self.assertEqual(validate_dossier(self.dossier)["errors"],[])
    def test_no_production_required(self):
        p=finalize_from_review(self.package,self.record,self.audit,self.review)
        self.assertEqual(deliver_creative(p)["status"],"creative_delivery_complete")
    def test_manual_handoff(self):
        p=finalize_from_review(self.package,self.record,self.audit,self.review)
        self.assertEqual(deliver_creative(p,"manual")["status"],"designer_handoff")
    def test_ai_requires_separate_scope(self):
        p=finalize_from_review(self.package,self.record,self.audit,self.review)
        out=deliver_creative(p,"ai")
        self.assertEqual(out["status"],"ai_scope_pending")
        self.assertFalse(out["production_approved"])
    def test_hybrid_requires_separate_scope(self):
        p=finalize_from_review(self.package,self.record,self.audit,self.review)
        self.assertEqual(deliver_creative(p,"hybrid")["status"],"hybrid_scope_pending")
    def test_unapproved_cannot_deliver(self):
        with self.assertRaises(ValueError):deliver_creative(self.package,"manual")
    def test_unresolved_audit_blocks(self):
        self.review["revision"]["a1"]={"estado":"aclarar"}
        with self.assertRaises(ValueError):finalize_from_review(self.package,self.record,self.audit,self.review)
    def test_brief_change_invalidates(self):
        self.record["answers"]["nombre"]="Otra marca"
        with self.assertRaises(ValueError):finalize_from_review(self.package,self.record,self.audit,self.review)
    def test_dossier_change_invalidates(self):
        p=finalize_from_review(self.package,self.record,self.audit,self.review)
        p["dossier"]["objective"]="Objetivo modificado"
        with self.assertRaises(ValueError):handoff(p,"manual")
    def test_prevent_production_approval_in_creative(self):
        self.dossier["production_approved"]=True
        self.assertTrue(validate_dossier(self.dossier)["errors"])
    def test_escape_html(self):
        self.dossier["brand"]="<script>alert(1)</script>"
        self.assertNotIn("<script>",dossier_html(self.dossier))
    def test_wrong_selection_blocks(self):
        self.review["direccion_seleccionada"]="Concepto inexistente"
        with self.assertRaises(ValueError):finalize_from_review(self.package,self.record,self.audit,self.review)

if __name__=="__main__":unittest.main()
