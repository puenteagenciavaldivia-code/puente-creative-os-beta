import json
import unittest
from pathlib import Path
from dossier_adapter import parse_dossier,quality_evidence
from dossier_engine import validate_dossier


class ImportBoundaryTests(unittest.TestCase):
    def fixture(self):return json.loads((Path(__file__).resolve().parents[1]/'examples/taller_rio_synthetic.json').read_text())
    def test_nested_json_rejected(self):
        with self.assertRaises(ValueError):parse_dossier('['*40+'0'+']'*40)
    def test_large_node_count_rejected(self):
        with self.assertRaises(ValueError):parse_dossier(json.dumps([0]*10001))
    def test_unhashable_citation_field_rejected(self):
        f=self.fixture();f['dossier']['brief_evidence'][0]['field']=['malformed']
        self.assertTrue(validate_dossier(f['dossier'])['errors']);quality_evidence(f['dossier'],f['record'])
    def test_wrong_citation_structures_rejected(self):
        for value in [None,{},[False],[{'direction_id':{},'field':{},'quote':[]}]]:
            f=self.fixture();f['dossier']['brief_evidence']=value
            self.assertTrue(validate_dossier(f['dossier'])['errors'])
    def test_unknown_direction_citation_rejected(self):
        f=self.fixture();f['dossier']['brief_evidence'][0]['direction_id']='UNKNOWN'
        self.assertTrue(validate_dossier(f['dossier'])['errors'])


if __name__=='__main__':unittest.main()
