import copy
import json
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from client_delivery import client_delivery,client_html
from dossier_adapter import bind_dossier,approve_bound
from review_workflow import new_review
from session_store import SessionStore
from identity_boundary import AuthenticationDenied
from store_backup import backup_database,restore_database
from pilot_rehearsal import rehearse


class PilotRehearsalTests(unittest.TestCase):
    def test_full_local_workflow(self):
        report,html=rehearse()
        self.assertEqual(report['status'],'LOCAL_APROBADO');self.assertTrue(report['restore_matches'])
        self.assertEqual(report['client_sections'],['strategy','direction'])
        self.assertFalse(report['production_approved']);self.assertIn('Contrato',html)
    def test_rehearsal_does_not_export_handles_or_internal_notes(self):
        report,html=rehearse()
        text=json.dumps(report)+html
        self.assertNotIn('TOKEN-FICTICIO',text);self.assertNotIn('nonce',text)
        self.assertNotIn('request-ficticio-endtoend',text);self.assertNotIn('rejected_reasons',text)


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.now=1000;self.path=Path(self.tmp.name)/'s.sqlite';self.store=SessionStore(self.path,clock=lambda:self.now)
        self.binding='browser-ficticio-'+'a'*32;self.challenge=self.store.begin(self.binding)
        self.claims={'iss':'https://accounts.google.com','aud':'client','sub':'123456789012345678901','iat':990,'exp':1100,'nonce':self.challenge['nonce']}
    def finish(self,state=None,binding=None,verifier=None):
        return self.store.finish(state or self.challenge['state'],binding or self.binding,'ficticio','client',verifier or (lambda *args:self.claims))
    def test_roundtrip_new_store(self):
        handle=self.finish();other=SessionStore(self.path,clock=lambda:self.now)
        self.assertEqual(other.resolve(handle).subject,self.claims['sub'])
    def test_expired_login(self):
        self.now=1300
        with self.assertRaises(AuthenticationDenied):self.finish()
    def test_wrong_browser_binding(self):
        with self.assertRaises(AuthenticationDenied):self.finish(binding='otro-browser-'+('b'*32))
    def test_unknown_state(self):
        with self.assertRaises(AuthenticationDenied):self.finish(state='otro-state-'+('c'*32))
    def test_callback_cannot_repeat(self):
        self.finish()
        with self.assertRaises(AuthenticationDenied):self.finish()
    def test_failed_verification_consumes_challenge(self):
        def broken(*args):raise ValueError('fixture failure')
        with self.assertRaises(AuthenticationDenied):self.finish(verifier=broken)
        with self.assertRaises(AuthenticationDenied):self.finish()
    def test_concurrent_callbacks_one_winner(self):
        def attempt(_):
            try:self.finish();return 'ok'
            except AuthenticationDenied:return 'denied'
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(attempt,range(2)))
        self.assertEqual(sorted(results),['denied','ok'])
    def test_absolute_expiry(self):
        handle=self.finish()
        for now in (1200,1400,1600,1800):self.now=now;self.store.resolve(handle)
        self.now=1900
        with self.assertRaises(AuthenticationDenied):self.store.resolve(handle)
    def test_idle_expiry(self):
        handle=self.finish();self.now=1300
        with self.assertRaises(AuthenticationDenied):self.store.resolve(handle)
    def test_logout(self):
        handle=self.finish();self.store.revoke(handle)
        with self.assertRaises(AuthenticationDenied):self.store.resolve(handle)
    def test_revoke_all_local_actor_sessions(self):
        handle=self.finish();actor=self.store.resolve(handle);self.store.revoke_actor(actor)
        with self.assertRaises(AuthenticationDenied):self.store.resolve(handle)
    def test_handles_not_stored_in_clear(self):
        handle=self.finish()
        with sqlite3.connect(self.path) as db:
            content=str(db.execute('SELECT * FROM identity_sessions').fetchall())+str(db.execute('SELECT * FROM login_challenges').fetchall())
        self.assertNotIn(handle,content);self.assertNotIn(self.challenge['state'],content)
    def test_restore_invalidates_sessions_and_pending_callbacks(self):
        handle=self.finish();pending=self.store.begin(self.binding)
        backup=Path(self.tmp.name)/'backup.sqlite';target=Path(self.tmp.name)/'restore.sqlite'
        backup_database(self.path,backup);restore_database(backup,target)
        restored=SessionStore(target,clock=lambda:self.now)
        with self.assertRaises(AuthenticationDenied):restored.resolve(handle)
        with self.assertRaises(AuthenticationDenied):restored.finish(pending['state'],self.binding,'fake','client',lambda *a:self.claims)


class ClientDeliveryTests(unittest.TestCase):
    def setUp(self):
        f=json.loads((Path(__file__).resolve().parents[1]/'examples/taller_rio_synthetic.json').read_text())
        self.record=f['record'];self.audit=f['audit'];self.dossier=f['dossier'];self.review=new_review(self.record,self.audit)
        self.pkg=approve_bound(bind_dossier(self.dossier,self.record,self.audit),self.record,self.audit,self.review,'Director ficticio','A','La ruta elegida aporta una solución coherente y pertinente al briefing ficticio.')
        self.contract={'submission_id':self.record['submission_id'],'version':'ficticia-v1','included_deliverables':['direction']}
    def deliver(self):return client_delivery(self.pkg,self.record,self.audit,self.contract)
    def test_only_contracted_direction(self):
        out=self.deliver();self.assertEqual(set(out['sections']),{'direction'});self.assertFalse(out['production_approved'])
    def test_internal_metadata_absent(self):
        text=json.dumps(self.deliver());self.assertNotIn('reviewer',text);self.assertNotIn('rejected_reasons',text);self.assertNotIn('source_register',text)
    def test_only_selected_alternative(self):
        text=json.dumps(self.deliver());self.assertIn(self.dossier['directions'][0]['name'],text);self.assertNotIn(self.dossier['directions'][1]['name'],text)
    def test_unknown_deliverable_rejected(self):
        self.contract['included_deliverables']=['brand_manual']
        with self.assertRaises(ValueError):self.deliver()
    def test_cross_project_contract_rejected(self):
        self.contract['submission_id']='OTHER'
        with self.assertRaises(ValueError):self.deliver()
    def test_unapproved_dossier_rejected(self):
        self.pkg=bind_dossier(self.dossier,self.record,self.audit)
        with self.assertRaises(ValueError):self.deliver()
    def test_stale_approval_rejected(self):
        self.record['answers']['objetivo']='Otro objetivo'
        with self.assertRaises(ValueError):self.deliver()
    def test_comparison_cannot_leak_internal_tradeoffs(self):
        self.contract['included_deliverables']=['comparison']
        with self.assertRaises(ValueError):self.deliver()
    def test_internal_sources_excluded(self):
        self.contract['included_deliverables']=['sources'];self.assertEqual(self.deliver()['sections']['sources'],[])
    def test_projection_cannot_mutate_original(self):
        out=self.deliver();out['sections']['direction']['applications']['feed']='changed'
        self.assertNotEqual(self.pkg['dossier']['directions'][0]['applications']['feed'],'changed')
    def test_html_escapes_content(self):
        out=self.deliver();out['brand']='<script>bad</script>';text=client_html(out)
        self.assertNotIn('<script>',text);self.assertIn('&lt;script&gt;',text)


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);p=Path(self.tmp.name)
        self.source=p/'source.sqlite';self.backup=p/'copy.sqlite';self.restored=p/'restored.sqlite'
        with sqlite3.connect(self.source) as db:db.execute('CREATE TABLE fixture(value TEXT)');db.execute("INSERT INTO fixture VALUES('SOLO FICTICIO')")
    def test_restore_verified_copy(self):
        backup_database(self.source,self.backup);restore_database(self.backup,self.restored)
        with sqlite3.connect(self.restored) as db:self.assertEqual(db.execute('SELECT value FROM fixture').fetchone()[0],'SOLO FICTICIO')
    def test_existing_backup_not_overwritten(self):
        backup_database(self.source,self.backup)
        with self.assertRaises(FileExistsError):backup_database(self.source,self.backup)
    def test_existing_restore_not_overwritten(self):
        backup_database(self.source,self.backup);restore_database(self.backup,self.restored)
        with self.assertRaises(FileExistsError):restore_database(self.backup,self.restored)
    def test_changed_copy_rejected(self):
        backup_database(self.source,self.backup)
        with self.backup.open('ab') as f:f.write(b'alterado')
        with self.assertRaises(ValueError):restore_database(self.backup,self.restored)
    def test_original_not_changed(self):
        original=self.source.read_bytes();backup_database(self.source,self.backup);self.assertEqual(self.source.read_bytes(),original)
    def test_missing_source_rejected(self):
        with self.assertRaises(ValueError):backup_database(self.restored,self.backup)
    def test_same_file_rejected(self):
        with self.assertRaises(ValueError):backup_database(self.source,self.source)


if __name__=='__main__':unittest.main()
