import copy
import json
import tempfile
import unittest
from pathlib import Path
from identity_boundary import GoogleIdentityBoundary, AuthenticationDenied
from decision_store import DecisionStore,Scope
from review_workflow import new_review


class IdentityBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.claims={'iss':'https://accounts.google.com','sub':'123456789012345678901',
                     'aud':'client-ficticio','iat':900,'exp':1100,'nonce':'nonce-ficticio-0001'}
        self.used=set();self.calls=[]
        def verify(token,aud):
            self.calls.append((token,aud));return copy.deepcopy(self.claims)
        def consume(n):
            if n in self.used:return False
            self.used.add(n);return True
        self.boundary=GoogleIdentityBoundary('client-ficticio',verify,consume,lambda:1000)
    def auth(self):return self.boundary.authenticate('TOKEN-FICTICIO-NO-JWT','nonce-ficticio-0001')
    def denied(self):
        with self.assertRaisesRegex(AuthenticationDenied,'No se pudo verificar'):self.auth()
    def test_actor_uses_sub_not_email(self):
        self.claims['email']='cambiante@example.invalid';self.claims['role']='admin'
        self.assertEqual(self.auth().subject,self.claims['sub'])
    def test_alternate_issuer_canonicalized(self):
        self.claims['iss']='accounts.google.com';self.assertEqual(self.auth().issuer,'https://accounts.google.com')
    def test_unknown_issuer(self):self.claims['iss']='https://otro.invalid';self.denied()
    def test_wrong_audience(self):self.claims['aud']='otro';self.denied()
    def test_audience_array_rejected(self):self.claims['aud']=['client-ficticio','otro'];self.denied()
    def test_wrong_authorized_party(self):self.claims['azp']='otro';self.denied()
    def test_expired(self):self.claims['exp']=999;self.denied()
    def test_future_issue(self):self.claims['iat']=1001;self.denied()
    def test_missing_expiry(self):del self.claims['exp'];self.denied()
    def test_nonfinite_expiry(self):self.claims['exp']=float('nan');self.denied()
    def test_bool_expiry(self):self.claims['exp']=True;self.denied()
    def test_infinite_expiry(self):self.claims['exp']=float('inf');self.denied()
    def test_missing_subject(self):del self.claims['sub'];self.denied()
    def test_email_as_subject_rejected(self):self.claims['sub']='admin@example.invalid';self.denied()
    def test_wrong_nonce_not_consumed(self):
        self.claims['nonce']='otro-nonce-ficticio';self.denied();self.assertEqual(self.used,set())
    def test_reused_nonce(self):self.auth();self.denied()
    def test_missing_nonce(self):del self.claims['nonce'];self.denied()
    def test_verifier_failure_redacted(self):
        def bad(*args):raise RuntimeError('TOKEN-SECRET-MARKER')
        self.boundary.verifier=bad
        try:self.auth()
        except AuthenticationDenied as e:self.assertNotIn('SECRET',str(e))
        else:self.fail('accepted')
    def test_verifier_gets_server_audience(self):self.auth();self.assertEqual(self.calls[0][1],'client-ficticio')
    def test_missing_server_dependencies(self):
        with self.assertRaises(ValueError):GoogleIdentityBoundary('',lambda *a:{},lambda *a:True)
    def test_unconfigured_verifier_denies(self):
        with self.assertRaises(ValueError):GoogleIdentityBoundary('client',None,lambda *a:True)
    def test_oversize_token_never_verified(self):
        with self.assertRaises(AuthenticationDenied):self.boundary.authenticate('x'*16385,'nonce-ficticio-0001')
        self.assertEqual(self.calls,[])
    def test_failing_nonce_store_denies(self):
        def broken(*a):raise RuntimeError('offline')
        self.boundary.consume_nonce=broken;self.denied()
    def test_truthy_nonce_does_not_allow(self):self.boundary.consume_nonce=lambda n:'yes';self.denied()
    def test_identity_does_not_grant_permission(self):
        actor=self.auth()
        with tempfile.TemporaryDirectory() as d:
            store=DecisionStore(Path(d)/'test.sqlite')
            with self.assertRaises(PermissionError):store.load_latest(actor,Scope('ficticia','proyecto'))
    def test_boundary_and_policy_and_store(self):
        actor=self.auth()
        fixture=json.loads((Path(__file__).resolve().parents[1]/'examples/taller_rio_synthetic.json').read_text())
        scope=Scope('AGENCIA-FICTICIA',fixture['record']['submission_id'])
        with tempfile.TemporaryDirectory() as d:
            store=DecisionStore(Path(d)/'test.sqlite',lambda who,target,action:who==actor and target==scope)
            version=store.save_revision(actor,scope,fixture['record'],fixture['audit'],new_review(fixture['record'],fixture['audit']),fixture['dossier'],0)
            result=store.decide(actor,scope,version,'A','Concepto pertinente para el público y aplicaciones fundamentadas en el briefing ficticio.','request-ficticio-0001')
            self.assertEqual(result['actor']['subject'],self.claims['sub'])
            self.assertFalse(result['production_approved'])


if __name__=='__main__':unittest.main()
