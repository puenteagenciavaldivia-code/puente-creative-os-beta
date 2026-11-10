"""Firmas reales sobre datos ficticios; certificados locales y red prohibida.
No prueba confianza en certificados Google reales. No instala dependencias.
"""
import base64
import json
import time
import unittest
from datetime import datetime,timedelta,timezone
from unittest.mock import patch
from identity_boundary import GoogleIdentityBoundary,google_library_verifier,AuthenticationDenied
try:
    from google.auth import jwt,crypt
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes,serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    AVAILABLE=True
except ImportError:
    AVAILABLE=False


@unittest.skipUnless(AVAILABLE,'Faltan dependencias opcionales; no constituye aprobación criptográfica')
class GoogleTokenCryptoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        other=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'lab.example.invalid')])
        now=datetime.now(timezone.utc)
        cert=(x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
              .serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(minutes=1))
              .not_valid_after(now+timedelta(hours=1)).sign(key,hashes.SHA256()))
        cls.cert=cert.public_bytes(serialization.Encoding.PEM).decode()
        def signer(k):
            pem=k.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())
            return crypt.RSASigner.from_string(pem,key_id='fixture-key')
        cls.signer=signer(key);cls.wrong=signer(other)
    def setUp(self):
        now=int(time.time());self.used=set();self.urls=[]
        self.claims={'iss':'https://accounts.google.com','aud':'client-ficticio','sub':'123456789012345678901',
                     'iat':now-5,'exp':now+300,'nonce':'nonce-ficticio-crypto'}
        def consume(n):
            if n in self.used:return False
            self.used.add(n);return True
        self.boundary=GoogleIdentityBoundary('client-ficticio',google_library_verifier,consume)
        def transport(url,**kwargs):
            self.urls.append(url);self.assertEqual(url,'https://www.googleapis.com/oauth2/v1/certs')
            self.assertEqual(kwargs.get('timeout'),5)
            return type('Response',(),{'status':200,'data':json.dumps({'fixture-key':self.cert}).encode()})()
        self.transport=transport
    def token(self,claims=None,signer=None):return jwt.encode(signer or self.signer,claims or self.claims).decode()
    def verify(self,token):
        with patch('google.auth.transport.requests.Request',return_value=self.transport),\
             patch('requests.sessions.Session.request',side_effect=AssertionError('NETWORK FORBIDDEN')):
            return self.boundary.authenticate(token,'nonce-ficticio-crypto')
    def denied(self,token):
        with self.assertRaises(AuthenticationDenied):self.verify(token)
    def test_valid_signature(self):self.assertEqual(self.verify(self.token()).subject,self.claims['sub'])
    def test_wrong_key(self):self.denied(self.token(signer=self.wrong))
    def test_modified_payload(self):
        parts=self.token().split('.');parts[1]=base64.urlsafe_b64encode(json.dumps(dict(self.claims,sub='999999')).encode()).decode().rstrip('=')
        self.denied('.'.join(parts))
    def test_unsigned(self):self.denied('.'.join(self.token().split('.')[:2])+'.')
    def test_wrong_audience(self):self.denied(self.token(dict(self.claims,aud='otro')))
    def test_wrong_issuer(self):self.denied(self.token(dict(self.claims,iss='https://example.invalid')))
    def test_expired(self):self.denied(self.token(dict(self.claims,iat=int(time.time())-200,exp=int(time.time())-10)))
    def test_replay_nonce(self):
        token=self.token();self.verify(token);self.denied(token)
    def test_certificate_error(self):
        def broken(*args,**kwargs):raise RuntimeError('offline')
        self.transport=broken;self.denied(self.token());self.assertEqual(self.used,set())


if __name__=='__main__':unittest.main()
