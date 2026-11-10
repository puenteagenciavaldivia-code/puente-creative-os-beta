"""Regresión de los contratos reconciliados del PR DCP-02; datos ficticios."""
import copy
import json
import unittest
from pathlib import Path

from creative_dossier_bridge import prepare_for_brief, finalize_from_review, deliver_creative
from review_workflow import new_review


class ReconciledBridgeTests(unittest.TestCase):
    def setUp(self):
        f = json.loads((Path(__file__).resolve().parents[1]/'examples/taller_rio_synthetic.json').read_text())
        self.record, self.audit, self.dossier = f['record'], f['audit'], f['dossier']
        self.review = new_review(self.record, self.audit)
        self.review.update(direccion_seleccionada=self.dossier['directions'][0]['name'],
                           responsable='Dirección ficticia',
                           observaciones='La propuesta responde al briefing y desarrolla una dirección visual pertinente y diferenciada.')
        self.package = prepare_for_brief(self.record, self.dossier, self.audit)

    def approve(self):
        return finalize_from_review(self.package, self.record, self.audit, self.review)

    def test_legacy_routes_preserved_without_production(self):
        pkg = self.approve()
        for route, status in [('undecided', 'creative_delivery_complete'), ('manual', 'designer_handoff'),
                              ('hybrid', 'hybrid_scope_pending'), ('ai', 'ai_scope_pending')]:
            with self.subTest(route=route):
                out = deliver_creative(pkg, route)
                self.assertEqual(out['status'], status)
                self.assertFalse(out['production_approved'])

    def test_legacy_call_without_audit_fails_explicitly(self):
        with self.assertRaisesRegex(ValueError, 'auditoría'):
            prepare_for_brief(self.record, self.dossier)

    def test_audit_change_invalidates_binding(self):
        self.audit['reconciled_change'] = 'ficticio'
        with self.assertRaises(ValueError): self.approve()

    def test_substring_brand_from_old_bridge_is_not_accepted(self):
        dossier = copy.deepcopy(self.dossier)
        dossier['brand'] += ' - otra marca'
        with self.assertRaises(ValueError): prepare_for_brief(self.record, dossier, self.audit)

    def test_missing_quotes_do_not_get_fabricated_for_legacy_import(self):
        self.dossier.pop('brief_evidence', None)
        self.package = prepare_for_brief(self.record, self.dossier, self.audit)
        with self.assertRaisesRegex(ValueError, 'cita exacta'): self.approve()

    def test_legacy_selection_cannot_choose_unknown_direction(self):
        self.review['direccion_seleccionada'] = 'Inexistente'
        with self.assertRaises(ValueError): self.approve()

    def test_changed_dossier_cannot_be_delivered(self):
        pkg = self.approve()
        pkg['dossier']['objective'] = 'Otro objetivo ficticio'
        with self.assertRaises(ValueError): deliver_creative(pkg)

    def test_source_objects_not_marked_as_approved(self):
        original = copy.deepcopy(self.review)
        self.approve()
        self.assertEqual(original, self.review)
        self.assertFalse(self.review['autorizacion_produccion'])


if __name__ == '__main__': unittest.main()
