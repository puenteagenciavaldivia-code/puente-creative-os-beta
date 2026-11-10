import copy
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from decision_store import Actor, Scope, DecisionStore, Conflict, IntegrityFailure
from review_workflow import new_review

ROOT = Path(__file__).resolve().parents[1]
RATIONALE = 'La alternativa desarrolla un concepto pertinente y aplicaciones claras para esta marca ficticia.'


class DecisionStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'lab.sqlite'
        self.fixture = json.loads((ROOT/'examples/taller_rio_synthetic.json').read_text())
        self.record = self.fixture['record'];self.audit = self.fixture['audit'];self.dossier = self.fixture['dossier']
        self.review = new_review(self.record,self.audit)
        self.scope = Scope('AGENCIA-FICTICIA',self.record['submission_id'])
        self.admin = Actor('issuer-ficticio','admin-ficticio')
        self.viewer = Actor('issuer-ficticio','consulta-ficticia')
        self.active = True
        self.policy = lambda a,s,action: bool(self.active and s==self.scope and
            (a==self.admin or (a==self.viewer and action=='read')))
        self.store = DecisionStore(self.path,self.policy)

    def save(self,expected=0,dossier=None):
        return self.store.save_revision(self.admin,self.scope,self.record,self.audit,self.review,dossier or self.dossier,expected)
    def decide(self,request='request-ficticio-0001',version=1,approve=True):
        return self.store.decide(self.admin,self.scope,version,'A',RATIONALE,request,approve)
    def counts(self):
        with sqlite3.connect(self.path) as db:
            return tuple(db.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in ['revisions','decisions','events'])

    def test_persist_and_reload_new_instance(self):
        self.save();self.decide()
        other=DecisionStore(self.path,self.policy)
        self.assertEqual(other.load_latest(self.admin,self.scope)['version'],1)
        self.assertEqual(other.latest_decision(self.admin,self.scope)['actor']['subject'],'admin-ficticio')
    def test_real_process_restart_reads_saved_revision(self):
        self.save()
        script="from decision_store import *; import sys; s=DecisionStore(sys.argv[1],lambda *args:True); print(s.load_latest(Actor('fixture','fixture'),Scope('AGENCIA-FICTICIA','SYNTH-TALLER_RIO'))['version'])"
        r=subprocess.run([sys.executable,'-c',script,str(self.path)],cwd=ROOT,capture_output=True,text=True,check=True)
        self.assertEqual(r.stdout.strip(),'1')
    def test_default_deny(self):
        with self.assertRaises(PermissionError):DecisionStore(self.path).load_latest(self.admin,self.scope)
    def test_unknown_actor_denied(self):
        with self.assertRaises(PermissionError):self.store.load_latest(Actor('fixture','unknown'),self.scope)
        self.assertEqual(self.store.history(self.admin,self.scope)[0]['result'],'denied')
    def test_viewer_cannot_decide(self):
        self.save()
        with self.assertRaises(PermissionError):self.store.decide(self.viewer,self.scope,1,'A',RATIONALE,'request-ficticio-0001')
    def test_viewer_can_read(self):
        self.save();self.assertEqual(self.store.load_latest(self.viewer,self.scope)['version'],1)
    def test_cross_project_denied(self):
        self.save()
        with self.assertRaises(PermissionError):self.store.load_latest(self.admin,Scope(self.scope.agency,'OTRO'))
    def test_cross_agency_denied(self):
        self.save()
        with self.assertRaises(PermissionError):self.store.load_latest(self.admin,Scope('OTRA',self.scope.project))
    def test_disabled_actor_denied_even_idempotent_retry(self):
        self.save();self.decide();self.active=False
        with self.assertRaises(PermissionError):self.decide()
    def test_idempotent_decision_has_single_event(self):
        self.save();one=self.decide();two=self.decide()
        self.assertEqual(one,two);self.assertEqual(self.counts(),(1,1,2))
    def test_request_reuse_with_different_payload_rejected(self):
        self.save();self.decide()
        with self.assertRaises(Conflict):self.store.decide(self.admin,self.scope,1,'B',RATIONALE,'request-ficticio-0001')
    def test_stale_write_rejected(self):
        self.save()
        with self.assertRaises(Conflict):self.save()
        self.assertEqual(self.counts(),(1,0,1))
    def test_new_revision_invalidates_prior_decision(self):
        self.save();self.decide();d=copy.deepcopy(self.dossier);d['objective']='Objetivo revisado para este caso ficticio.';self.save(1,d)
        self.assertIsNone(self.store.latest_decision(self.admin,self.scope))
        with self.assertRaises(Conflict):self.decide(version=1)
        self.assertEqual(self.store.load_latest(self.admin,self.scope)['package']['creative_approval'],None)
    def test_rejection_supersedes_approval(self):
        self.save();self.decide();self.decide('request-ficticio-0002',approve=False)
        self.assertFalse(self.store.latest_decision(self.admin,self.scope)['package']['creative_approval']['approved'])
    def test_no_production_permission(self):
        self.save();self.assertFalse(self.decide()['production_approved'])
    def test_input_approval_ignored(self):
        self.review['autorizacion_produccion']=True;self.save()
        self.assertFalse(self.store.load_latest(self.admin,self.scope)['review']['autorizacion_produccion'])
    def test_failed_audit_rolls_back_revision(self):
        with sqlite3.connect(self.path) as db:db.execute("CREATE TRIGGER audit_fail BEFORE INSERT ON events BEGIN SELECT RAISE(ABORT,'lab audit failure'); END")
        with self.assertRaises(sqlite3.DatabaseError):self.save()
        self.assertEqual(self.counts(),(0,0,0))
    def test_failed_audit_rolls_back_decision(self):
        self.save()
        with sqlite3.connect(self.path) as db:db.execute("CREATE TRIGGER audit_fail BEFORE INSERT ON events BEGIN SELECT RAISE(ABORT,'lab audit failure'); END")
        with self.assertRaises(sqlite3.DatabaseError):self.decide()
        self.assertEqual(self.counts(),(1,0,1))
    def test_pending_questions_block_approval(self):
        self.audit['preguntas_priorizadas']=[{'id':'Q1'}];self.save()
        with self.assertRaises(ValueError):self.decide()
    def test_corrupted_revision_detected(self):
        self.save()
        with sqlite3.connect(self.path) as db:db.execute("UPDATE revisions SET payload_hash='broken'")
        with self.assertRaises(IntegrityFailure):self.store.load_latest(self.admin,self.scope)
    def test_corrupted_event_detected(self):
        self.save();self.decide()
        with sqlite3.connect(self.path) as db:db.execute("UPDATE events SET event_hash='broken' WHERE id=1")
        with self.assertRaises(IntegrityFailure):self.store.latest_decision(self.admin,self.scope)
    def test_corrupted_decision_detected_on_retry(self):
        self.save();self.decide()
        with sqlite3.connect(self.path) as db:db.execute("UPDATE decisions SET payload='{}'")
        with self.assertRaises(IntegrityFailure):self.decide()
    def test_backup_restore_local_roundtrip(self):
        self.save();self.decide();target=Path(self.tmp.name)/'restored.sqlite'
        with sqlite3.connect(self.path) as src,sqlite3.connect(target) as dst:src.backup(dst)
        restored=DecisionStore(target,self.policy)
        self.assertEqual(restored.latest_decision(self.admin,self.scope),self.store.latest_decision(self.admin,self.scope))
        self.assertEqual(restored.history(self.admin,self.scope),self.store.history(self.admin,self.scope))
    def test_competing_writes_only_one_wins(self):
        def attempt(_):
            try:return self.save()
            except Conflict:return 'conflict'
        with ThreadPoolExecutor(max_workers=2) as pool:out=list(pool.map(attempt,range(2)))
        self.assertEqual(out.count(1),1);self.assertEqual(out.count('conflict'),1)
        self.assertEqual(self.counts(),(1,0,1))
    def test_policy_exception_denies(self):
        def broken(*args):raise RuntimeError('offline')
        with self.assertRaises(PermissionError):DecisionStore(self.path,broken).load_latest(self.admin,self.scope)
    def test_truthy_policy_does_not_allow(self):
        with self.assertRaises(PermissionError):DecisionStore(self.path,lambda *args:'yes').load_latest(self.admin,self.scope)
    def test_invalid_actor_denied(self):
        with self.assertRaises(PermissionError):self.store.load_latest({'subject':'fake'},self.scope)
    def test_project_binding_required(self):
        self.record['submission_id']='OTRO'
        with self.assertRaises(ValueError):self.save()


if __name__=='__main__':unittest.main()
