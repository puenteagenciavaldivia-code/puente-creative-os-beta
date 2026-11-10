import copy
import json
from pathlib import Path
import unittest

from dossier_adapter import (parse_dossier, bind_dossier, approve_bound, legacy_review,
                             quality_evidence, verify_context)
from dossier_engine import validate_dossier, prepare, dossier_html, handoff, approve_creative
from review_workflow import new_review, prepare_reviewed_package
from graphic_production import build_production_plan, build_piece, production_prompt
from dossier_pdf import dossier_pdf
from dossier_adapter import research_request

ROOT=Path(__file__).resolve().parents[1]


class DossierIntegrationTests(unittest.TestCase):
    def setUp(self):
        f=json.loads((ROOT/'examples/taller_rio_synthetic.json').read_text())
        self.d=f['dossier']; self.r=f['record']; self.a=f['audit']; self.review=new_review(self.r,self.a)

    def bound(self):return bind_dossier(self.d,self.r,self.a)
    def approved(self):return approve_bound(self.bound(),self.r,self.a,self.review,'Dirección ficticia','A','La ruta conecta el cuidado de la bicicleta con autonomía urbana y ofrece aplicaciones claras.')

    def test_three_synthetic_cases_valid(self):
        for p in (ROOT/'examples').glob('*_synthetic.json'):
            with self.subTest(p=p.name):
                f=json.loads(p.read_text());self.assertEqual(validate_dossier(f['dossier'])['errors'],[])
                self.assertTrue(all(x['brief_quotes_verified'] for x in quality_evidence(f['dossier'],f['record'])))
                self.assertIn('Restricciones del encargo',dossier_html(f['dossier']))

    def test_json_duplicate_rejected(self):
        with self.assertRaises(ValueError):parse_dossier('{"brand":"a","brand":"b"}')
    def test_json_size_limit(self):
        with self.assertRaises(ValueError):parse_dossier('á'*100001)
    def test_nonfinite_json_rejected(self):
        with self.assertRaises(ValueError):parse_dossier('{"value": NaN}')
    def test_wrong_root_rejected(self):
        with self.assertRaises(ValueError):bind_dossier([],self.r,self.a)
    def test_cross_brand_rejected(self):
        self.d['brand']='Otra marca ficticia'
        with self.assertRaises(ValueError):self.bound()
    def test_changed_answers_invalidate(self):
        p=self.bound();self.r['answers']['objetivo']='Objetivo cambiado'
        with self.assertRaises(ValueError):verify_context(p,self.r,self.a)
    def test_changed_audit_invalidate(self):
        p=self.bound();self.a['preguntas_priorizadas']=[{'id':'nuevo'}]
        with self.assertRaises(ValueError):verify_context(p,self.r,self.a)
    def test_changed_submission_invalidate(self):
        p=self.bound();self.r['submission_id']='OTRO'
        with self.assertRaises(ValueError):verify_context(p,self.r,self.a)
    def test_content_change_invalidates_approval(self):
        p=self.approved();p['dossier']['objective']='Otro objetivo';
        with self.assertRaises(ValueError):handoff(p,'manual')
    def test_approval_never_imported(self):
        p=self.bound();self.assertIsNone(p['creative_approval']);self.assertEqual(p['production_route'],'undecided')
    def test_manual_handoff_not_production(self):
        self.assertFalse(handoff(self.approved(),'manual')['production_approved'])
    def test_creative_delivery_without_production(self):
        h=handoff(self.approved(),'undecided');self.assertEqual(h['status'],'creative_delivery_complete');self.assertFalse(h['production_required'])
    def test_routes_do_not_generate_images(self):
        for route in ['hybrid','ai']:
            self.assertFalse(handoff(self.approved(),route)['production_approved'])
    def test_missing_reviewer_blocks(self):
        with self.assertRaises(ValueError):approve_bound(self.bound(),self.r,self.a,self.review,'','A','Fundamento suficientemente extenso para revisión humana.')
    def test_questions_pending_block_signoff(self):
        self.a['preguntas_priorizadas']=[{'id':'Q1'}]
        with self.assertRaises(ValueError):self.approved()
    def test_unknown_selection_blocks(self):
        with self.assertRaises(ValueError):approve_bound(self.bound(),self.r,self.a,self.review,'Dirección','X','Fundamento suficientemente extenso para revisión humana.')
    def test_missing_brief_quote_blocks(self):
        self.d['brief_evidence']=[]
        with self.assertRaises(ValueError):self.approved()
    def test_fabricated_quote_blocks(self):
        self.d['brief_evidence'][0]['quote']='Esta frase no existe en el briefing.'
        with self.assertRaises(ValueError):self.approved()
    def test_legacy_mapping_does_not_mutate(self):
        original=copy.deepcopy(self.review);v=legacy_review(self.bound(),self.review)
        self.assertEqual(original,self.review);self.assertFalse(v['autorizacion_produccion'])
        plan=build_production_plan(self.r,v,self.a,[])
        self.assertEqual(plan['estado'],'borrador_bloqueado')
    def test_html_escapes_user_content(self):
        self.d['brand']='<script>alert(1)</script>'
        h=dossier_html(self.d);self.assertNotIn('<script>',h);self.assertIn('&lt;script&gt;',h)
    def test_html_has_no_external_resources(self):
        h=dossier_html(self.d);self.assertNotIn('<img',h);self.assertNotIn('<script',h);self.assertNotIn('src=',h)
    def test_invalid_html_export_blocks(self):
        self.d['directions']=[]
        with self.assertRaises(ValueError):dossier_html(self.d)
    def test_malformed_structures_fail_without_crash(self):
        mutations=[('directions',{}),('source_register',{}),('directions',[None])]
        for k,v in mutations:
            d=copy.deepcopy(self.d);d[k]=v;self.assertTrue(validate_dossier(d)['errors'])
        for k in ['id','visual_signature','references','risks']:
            d=copy.deepcopy(self.d);d['directions'][0][k]={};self.assertTrue(validate_dossier(d)['errors'])
    def test_no_duplicate_visual_signature(self):
        self.d['directions'][1]['visual_signature']=self.d['directions'][0]['visual_signature']
        self.assertTrue(validate_dossier(self.d)['errors'])
    def test_unknown_source_rejected(self):
        self.d['directions'][0]['references']=['MISSING'];self.assertTrue(validate_dossier(self.d)['errors'])
    def test_research_limit_visible(self):
        self.assertTrue(self.bound()['validation']['warnings'])
    def test_cached_validation_cannot_bypass(self):
        p=self.bound();p['dossier']['directions']=[];p['validation']['errors']=[]
        with self.assertRaises(ValueError):approve_creative(p,'Director','A','Fundamento suficientemente extenso para revisión humana.')
    def test_boolean_approval_required(self):
        with self.assertRaises(ValueError):approve_creative(self.bound(),'Director','A','Fundamento suficientemente extenso para revisión humana.','yes')
    def test_unknown_handoff_selection_rejected(self):
        p=self.approved();p['creative_approval']['selected_direction']='UNKNOWN'
        with self.assertRaises(ValueError):handoff(p,'manual')
    def test_truthy_legacy_approval_cannot_enable_production(self):
        p=self.approved();v=legacy_review(p,self.review);v.update(responsable='Dirección ficticia',direccion_seleccionada=self.d['directions'][0]['name'],observaciones='Fundamento suficientemente extenso para revisión humana.',autorizacion_produccion='false')
        result=prepare_reviewed_package({'submission_id':self.r['submission_id'],'respuestas_originales':self.r['answers'],'decisiones_creativas':{}},v,self.a)
        self.assertFalse(result['aprobado_para_produccion'])
    def test_piece_substitution_rejected(self):
        piece=build_piece(self.r['submission_id'],1,'instagram_post_4_5','Título ficticio','Objetivo ficticio','Mensaje ficticio','Consultar')
        plan={'estado':'habilitado_para_produccion','piezas':[piece]}
        substituted=copy.deepcopy(piece);substituted['mensaje_principal']='Contenido no revisado'
        with self.assertRaises(ValueError):production_prompt(plan,substituted)
    def test_pdf_generated_for_all_cases(self):
        for p in (ROOT/'examples').glob('*_synthetic.json'):
            self.assertTrue(dossier_pdf(json.loads(p.read_text())['dossier']).startswith(b'%PDF-'))
    def test_pdf_invalid_input_rejected(self):
        self.d['directions']=[]
        with self.assertRaises(ValueError):dossier_pdf(self.d)
    def test_request_excludes_unknown_private_fields(self):
        self.r['answers']['admin_token']='SYNTHETIC_PRIVATE_MARKER'
        self.assertNotIn('SYNTHETIC_PRIVATE_MARKER',research_request(self.r,self.a))
    def test_comparison_types_rejected(self):
        self.d['comparison']['criteria']='No es una lista'
        self.assertTrue(validate_dossier(self.d)['errors'])
    def test_duplicate_names_rejected(self):
        self.d['directions'][1]['name']=self.d['directions'][0]['name'].upper()
        self.assertTrue(validate_dossier(self.d)['errors'])


if __name__=='__main__':unittest.main()
