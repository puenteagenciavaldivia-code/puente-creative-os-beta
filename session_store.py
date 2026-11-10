"""Sesión LOCAL del servidor; no implementa cookies, rutas OAuth ni PKCE."""
import hashlib
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from decision_store import Actor
from identity_boundary import GoogleIdentityBoundary, AuthenticationDenied


def _hash(value):
    if not isinstance(value,str) or not 32<=len(value)<=512:
        raise AuthenticationDenied('Sesión no válida.')
    return hashlib.sha256(value.encode()).hexdigest()


class SessionStore:
    def __init__(self,path,clock=time.time,login_ttl=300,lifetime=900,idle=300):
        if not all(type(v) is int and 0<v<=3600 for v in (login_ttl,lifetime,idle)):
            raise ValueError('Duraciones de laboratorio no válidas.')
        self.path=str(path);self.clock=clock;self.login_ttl=login_ttl;self.lifetime=lifetime;self.idle=idle
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        with self.db() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS login_challenges(
                state_hash TEXT PRIMARY KEY,binding_hash TEXT NOT NULL,nonce TEXT NOT NULL,
                expires REAL NOT NULL,used INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS identity_sessions(
                token_hash TEXT PRIMARY KEY,issuer TEXT NOT NULL,subject TEXT NOT NULL,
                expires REAL NOT NULL,last_seen REAL NOT NULL,revoked INTEGER NOT NULL DEFAULT 0);''')
    @contextmanager
    def db(self):
        db=sqlite3.connect(self.path,timeout=5,isolation_level=None);db.row_factory=sqlite3.Row
        try:
            db.execute('PRAGMA synchronous=FULL');yield db
        finally:db.close()
    def begin(self,browser_binding):
        binding=_hash(browser_binding);state=secrets.token_urlsafe(32);nonce=secrets.token_urlsafe(32)
        with self.db() as db:
            db.execute('INSERT INTO login_challenges(state_hash,binding_hash,nonce,expires) VALUES(?,?,?,?)',
                       (_hash(state),binding,nonce,self.clock()+self.login_ttl))
        return {'state':state,'nonce':nonce}
    def finish(self,state,browser_binding,token,client_id,verifier):
        """state y binding deben provenir del flujo/cookie del servidor, no de un Actor cliente."""
        with self.db() as db:
            try:
                db.execute('BEGIN IMMEDIATE')
                row=db.execute('SELECT * FROM login_challenges WHERE state_hash=?',(_hash(state),)).fetchone()
                if row is None or row['used'] or row['expires']<=self.clock() or row['binding_hash']!=_hash(browser_binding):
                    raise AuthenticationDenied('Solicitud de acceso no válida.')
                # Consumir antes de verificar: un fallo no permite repetir el callback.
                db.execute('UPDATE login_challenges SET used=1 WHERE state_hash=?',(_hash(state),));db.commit()
            except Exception:
                db.rollback();raise
        actor=GoogleIdentityBoundary(client_id,verifier,lambda n:n==row['nonce'],self.clock).authenticate(token,row['nonce'])
        handle=secrets.token_urlsafe(32);now=self.clock()
        with self.db() as db:
            db.execute('INSERT INTO identity_sessions VALUES(?,?,?,?,?,0)',
                       (_hash(handle),actor.issuer,actor.subject,now+self.lifetime,now))
        return handle
    def resolve(self,handle):
        with self.db() as db:
            try:
                db.execute('BEGIN IMMEDIATE')
                row=db.execute('SELECT * FROM identity_sessions WHERE token_hash=?',(_hash(handle),)).fetchone()
                now=self.clock()
                if row is None or row['revoked'] or row['expires']<=now or row['last_seen']+self.idle<=now:
                    raise AuthenticationDenied('Sesión no válida.')
                db.execute('UPDATE identity_sessions SET last_seen=? WHERE token_hash=?',(now,_hash(handle)));db.commit()
                return Actor(row['issuer'],row['subject'])
            except Exception:
                db.rollback();raise
    def revoke(self,handle):
        with self.db() as db:db.execute('UPDATE identity_sessions SET revoked=1 WHERE token_hash=?',(_hash(handle),))
    def revoke_actor(self,actor):
        """Operación interna; su autorización administrativa corresponde al servidor llamador."""
        with self.db() as db:db.execute('UPDATE identity_sessions SET revoked=1 WHERE issuer=? AND subject=?',(actor.issuer,actor.subject))
