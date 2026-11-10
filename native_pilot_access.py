"""Autorización del piloto para claims ya verificados por Streamlit OIDC.

NO verifica firmas ni acepta claims desde formularios/JSON del navegador.
La única entrada de la UI es st.user; las pruebas usan un proveedor simulado.
El registro se administra exclusivamente fuera de la UI, por el responsable.
"""
import hashlib
import math
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

from decision_store import Actor

ISSUER = 'https://accounts.google.com'
ROLES = {
    'direccion': frozenset({'read', 'write', 'decide', 'history'}),
    'operacion': frozenset({'read', 'write', 'history'}),
}


class NativePilotAccess:
    def __init__(self, path, audience, clock=time.time):
        if not isinstance(audience, str) or not audience.strip():
            raise ValueError('Falta la audiencia del piloto.')
        self.path, self.audience, self.clock = str(path), audience, clock
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            pass
        else:
            os.close(fd)
        with self.connect() as db:
            fresh = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='pilot_access_meta'").fetchone() is None
            db.executescript('''
                CREATE TABLE IF NOT EXISTS pilot_users (
                    subject TEXT NOT NULL, agency TEXT NOT NULL, project TEXT NOT NULL,
                    role TEXT NOT NULL, active INTEGER NOT NULL,
                    PRIMARY KEY(subject,agency,project));
                CREATE TABLE IF NOT EXISTS pilot_access_meta (
                    id INTEGER PRIMARY KEY CHECK(id=1), not_before REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS pilot_security_events (
                    id INTEGER PRIMARY KEY, at TEXT NOT NULL, actor_hash TEXT NOT NULL,
                    action TEXT NOT NULL, result TEXT NOT NULL);
            ''')
            if fresh:
                db.execute('INSERT INTO pilot_access_meta VALUES(1,0)')

    def connect(self):
        # Los context managers de sqlite3 hacen commit/rollback, pero no close.
        from contextlib import closing
        return closing(sqlite3.connect(self.path, timeout=5, isolation_level=None))

    def record(self, actor, action, result):
        key = hashlib.sha256((actor.issuer+'|'+actor.subject).encode()).hexdigest() if actor else 'unverified'
        with self.connect() as db:
            db.execute('INSERT INTO pilot_security_events(at,actor_hash,action,result) VALUES(?,?,?,?)',
                       (datetime.now(timezone.utc).isoformat(), key, action, result))

    def set_user(self, subject, project, role, active=True):
        """Operación administrativa LOCAL; nunca exponer como control de la app."""
        if (not isinstance(subject, str) or not subject.isascii() or not subject.isdigit()
                or not 1 <= len(subject) <= 200 or role not in ROLES
                or type(active) is not bool or not isinstance(project, str)
                or not project.startswith('SYNTH-') or len(project) > 200):
            raise ValueError('Alta del piloto no válida.')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            try:
                # Garantías de Puerta A V1: dos identidades, sin auto-reactivación.
                prior = db.execute('SELECT MIN(active) FROM pilot_users WHERE subject=?', (subject,)).fetchone()[0]
                total = db.execute('SELECT COUNT(DISTINCT subject) FROM pilot_users').fetchone()[0]
                if total > 2 or (prior is None and (total >= 2 or not active)):
                    raise ValueError('Límite de dos operadores o identidad no registrada.')
                if prior == 0 and active:
                    raise ValueError('No se reactiva una identidad revocada mediante un alta.')
                if not active:
                    db.execute('UPDATE pilot_users SET active=0 WHERE subject=?', (subject,))
                db.execute('INSERT OR REPLACE INTO pilot_users VALUES(?,?,?,?,?)',
                           (subject, 'AGENCIA-FICTICIA', project, role, int(active)))
                key = hashlib.sha256((ISSUER+'|'+subject).encode()).hexdigest()
                db.execute('INSERT INTO pilot_security_events(at,actor_hash,action,result) VALUES(?,?,?,?)',
                           (datetime.now(timezone.utc).isoformat(), key, 'registry.changed',
                            'active' if active else 'disabled'))
                db.commit()
            except Exception:
                db.rollback()
                raise

    def actor(self, user):
        """Solo llamar con el st.user del servidor; no es verificación criptográfica."""
        try:
            if user.get('is_logged_in') is not True:
                raise ValueError()
            if user.get('iss') not in (ISSUER, 'accounts.google.com') or user.get('aud') != self.audience:
                raise ValueError()
            if 'azp' in user and user['azp'] != self.audience:
                raise ValueError()
            sub = user.get('sub')
            if (not isinstance(sub, str) or not sub.isascii() or not sub.isdigit()
                    or not 1 <= len(sub) <= 200):
                raise ValueError()
            now, issued, expires = self.clock(), user.get('iat'), user.get('exp')
            if any(type(v) not in (int, float) or not math.isfinite(v) for v in (now, issued, expires)):
                raise ValueError()
            # Máximo operativo 15 minutos desde emisión del ID token, no desde abrir pestaña.
            if not issued <= now < min(expires, issued+900):
                raise ValueError()
            with self.connect() as db:
                epoch = db.execute('SELECT not_before FROM pilot_access_meta WHERE id=1').fetchone()
            if epoch is None or issued < epoch[0]:
                raise ValueError()
            return Actor(ISSUER, sub)
        except Exception:
            raise PermissionError('Acceso del piloto no válido o vencido. Vuelve a identificarte.') from None

    def policy(self, user):
        """Cada llamada vuelve a comprobar vigencia, recuperación y registro sin caché."""
        def allowed(actor, scope, action):
            try:
                if self.actor(user) != actor or scope.agency != 'AGENCIA-FICTICIA':
                    return False
                with self.connect() as db:
                    row = db.execute('''SELECT role,active,
                        (SELECT MIN(active) FROM pilot_users WHERE subject=?),
                        (SELECT COUNT(DISTINCT subject) FROM pilot_users)
                        FROM pilot_users WHERE subject=? AND agency=? AND project=?''',
                                     (actor.subject, actor.subject, scope.agency, scope.project)).fetchone()
                return bool(row and row[1] == 1 and row[2] == 1 and row[3] <= 2
                            and action in ROLES.get(row[0], ()))
            except Exception:
                return False
        return allowed

    def projects(self, user):
        try:
            actor = self.actor(user)
        except PermissionError:
            self.record(None, 'access', 'denied')
            raise
        with self.connect() as db:
            active = db.execute('SELECT MIN(active) FROM pilot_users WHERE subject=?', (actor.subject,)).fetchone()[0]
            total = db.execute('SELECT COUNT(DISTINCT subject) FROM pilot_users').fetchone()[0]
            projects = [row[0] for row in db.execute(
                'SELECT project FROM pilot_users WHERE subject=? AND agency=? AND active=1 AND role IN (?,?) ORDER BY project',
                (actor.subject, 'AGENCIA-FICTICIA', 'direccion', 'operacion'))]
        if not projects or active != 1 or total > 2:
            self.record(actor, 'access', 'denied')
            raise PermissionError('Sin proyectos autorizados en el piloto.')
        self.record(actor, 'access', 'allowed')
        return projects
