"""Frontera interna de identidad; sin login, credenciales, endpoints o sesiones UI.

El verificador y el consumo de nonce son dependencias exclusivas del servidor.
Nunca construirlos a partir de parámetros del navegador. El store sigue aplicando
la política por agencia/proyecto en cada operación, después de autenticar.
"""
import hmac
import math
import time
from decision_store import Actor


class AuthenticationDenied(ValueError):
    pass


class GoogleIdentityBoundary:
    def __init__(self, client_id, verifier, consume_nonce, clock=time.time):
        if not isinstance(client_id,str) or not client_id.strip():
            raise ValueError('Falta la audiencia OAuth del servidor.')
        if not callable(verifier) or not callable(consume_nonce):
            raise ValueError('Verificador y nonce del servidor obligatorios.')
        self.client_id=client_id
        self.verifier=verifier
        self.consume_nonce=consume_nonce
        self.clock=clock

    def authenticate(self, token, expected_nonce):
        # Errores públicos uniformes: no filtrar token, claims o detalles de red.
        try:
            if not isinstance(token,str) or not 1<=len(token)<=16384:
                raise AuthenticationDenied()
            if not isinstance(expected_nonce,str) or not 16<=len(expected_nonce)<=256:
                raise AuthenticationDenied()
            # Debe verificar firma, claves Google, audiencia y vigencia; nunca decode-only.
            claims=self.verifier(token,self.client_id)
            if not isinstance(claims,dict):
                raise AuthenticationDenied()
            issuer=claims.get('iss')
            if issuer not in ('https://accounts.google.com','accounts.google.com'):
                raise AuthenticationDenied()
            if claims.get('aud')!=self.client_id:
                raise AuthenticationDenied()
            if 'azp' in claims and claims['azp']!=self.client_id:
                raise AuthenticationDenied()
            sub=claims.get('sub')
            if not isinstance(sub,str) or not 1<=len(sub)<=200 or not sub.isascii() or not sub.isdigit():
                raise AuthenticationDenied()
            now=self.clock()
            if type(claims.get('exp')) not in (int,float) or type(claims.get('iat')) not in (int,float):
                raise AuthenticationDenied()
            if not all(math.isfinite(v) for v in (claims['iat'],claims['exp'],now)):
                raise AuthenticationDenied()
            if not (claims['iat']<=now<claims['exp']) or claims['iat']>=claims['exp']:
                raise AuthenticationDenied()
            nonce=claims.get('nonce')
            if not isinstance(nonce,str) or not hmac.compare_digest(nonce,expected_nonce):
                raise AuthenticationDenied()
            # Debe consumir una vez el nonce de ESTA sesión, con expiración y operación atómica.
            if self.consume_nonce(expected_nonce) is not True:
                raise AuthenticationDenied()
            # Google admite ambos issuer; canonicalizar evita duplicar identidades.
            return Actor('https://accounts.google.com',sub)
        except Exception:
            raise AuthenticationDenied('No se pudo verificar la identidad.') from None


def google_library_verifier(token, audience):
    """Adaptador opcional futuro a biblioteca oficial. No se llama al importar.

    Esta función puede consultar certificados públicos de Google. No se ejecuta
    en pruebas aisladas. Requiere requirements-oidc.txt y configuración aprobada.
    """
    from functools import partial
    from google.oauth2 import id_token
    from google.auth.transport.requests import Request
    request=partial(Request(),timeout=5)
    return dict(id_token.verify_oauth2_token(token,request,audience=audience,clock_skew_in_seconds=0))
