"""Registro LOCAL transaccional. Actor/política deben provenir del servidor.

No autentica Google. No conectar a producción hasta disponer de OIDC verificado,
política autoritativa, disco durable y respaldo. No aceptar Actor desde JSON cliente.
"""
import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from dossier_adapter import bind_dossier, approve_bound, verify_context
from dossier_engine import approve_creative, digest


class Conflict(ValueError):
    pass


class IntegrityFailure(ValueError):
    pass


@dataclass(frozen=True)
class Actor:
    issuer: str
    subject: str


@dataclass(frozen=True)
class Scope:
    agency: str
    project: str


class DecisionStore:
    """Una base local; revisiones inmutables y decisiones append-only por API."""
    def __init__(self, path, policy=None):
        self.path = str(path)
        self.policy = policy or (lambda actor, scope, action: False)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS revisions (
                    agency TEXT NOT NULL, project TEXT NOT NULL, version INTEGER NOT NULL,
                    payload TEXT NOT NULL, payload_hash TEXT NOT NULL,
                    PRIMARY KEY(agency, project, version));
                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY, agency TEXT NOT NULL, project TEXT NOT NULL,
                    version INTEGER NOT NULL, issuer TEXT NOT NULL, subject TEXT NOT NULL,
                    request_id TEXT NOT NULL, request_hash TEXT NOT NULL, payload TEXT NOT NULL,
                    UNIQUE(agency, project, issuer, subject, request_id));
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY, agency TEXT NOT NULL, project TEXT NOT NULL,
                    payload TEXT NOT NULL, previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL);
            ''')

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('PRAGMA synchronous=FULL')
            yield db
        finally:
            db.close()

    @staticmethod
    def _json(value):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
        if len(text.encode('utf-8')) > 400_000:
            raise ValueError('Expediente demasiado grande.')
        return text

    def _event(self, db, actor, scope, action, result, detail):
        last = db.execute('SELECT event_hash FROM events WHERE agency=? AND project=? ORDER BY id DESC LIMIT 1',
                          (scope.agency, scope.project)).fetchone()
        previous = last['event_hash'] if last else ''
        payload = {'agency': scope.agency, 'project': scope.project,
                   'issuer': actor.issuer, 'subject': actor.subject,
                   'action': action, 'result': result, 'detail': detail,
                   'at': datetime.now(timezone.utc).isoformat()}
        text = self._json(payload)
        db.execute('INSERT INTO events(agency,project,payload,previous_hash,event_hash) VALUES(?,?,?,?,?)',
                   (scope.agency, scope.project, text, previous, digest([previous, payload])))

    def _authorize(self, actor, scope, action):
        if not isinstance(actor, Actor) or not isinstance(scope, Scope):
            raise PermissionError('Identidad o ámbito no válidos.')
        if not all(isinstance(v, str) and 0 < len(v) <= 200 for v in
                   (actor.issuer, actor.subject, scope.agency, scope.project)):
            raise PermissionError('Identidad o ámbito no válidos.')
        # Una excepción o un valor truthy no booleano no concede acceso.
        try:
            allowed = self.policy(actor, scope, action) is True
        except Exception:
            allowed = False
        if not allowed:
            with self._connect() as db:
                db.execute('BEGIN IMMEDIATE')
                self._event(db, actor, scope, action, 'denied', 'policy-denied')
                db.commit()
            raise PermissionError('Acceso denegado.')

    @staticmethod
    def _latest(db, scope):
        return db.execute('SELECT * FROM revisions WHERE agency=? AND project=? ORDER BY version DESC LIMIT 1',
                          (scope.agency, scope.project)).fetchone()

    @staticmethod
    def _decode(row):
        payload = json.loads(row['payload'])
        if digest(payload) != row['payload_hash']:
            raise IntegrityFailure('La revisión almacenada cambió.')
        verify_context(payload['package'], payload['record'], payload['audit'])
        return payload

    def save_revision(self, actor, scope, record, audit, review, dossier, expected_version):
        self._authorize(actor, scope, 'write')
        if record.get('submission_id') != scope.project:
            raise ValueError('El proyecto no corresponde al briefing.')
        package = bind_dossier(dossier, record, audit)
        if package['validation']['errors']:
            raise ValueError('; '.join(package['validation']['errors']))
        # Descartar todas las aprobaciones del objeto de entrada.
        safe_review = dict(review)
        safe_review['autorizacion_produccion'] = False
        payload = {'record': record, 'audit': audit, 'review': safe_review, 'package': package}
        text = self._json(payload)
        if type(expected_version) is not int or expected_version < 0:
            raise ValueError('Versión esperada no válida.')
        with self._connect() as db:
            try:
                db.execute('BEGIN IMMEDIATE')
                current = self._latest(db, scope)
                version = current['version'] if current else 0
                if version != expected_version:
                    raise Conflict('Otro cambio creó una versión: recarga antes de guardar.')
                if current:
                    self._decode(current)
                version += 1
                db.execute('INSERT INTO revisions VALUES(?,?,?,?,?)',
                           (scope.agency, scope.project, version, text, digest(payload)))
                self._event(db, actor, scope, 'revision.saved', 'ok', {'version': version, 'hash': package['hash']})
                db.commit()
                return version
            except Exception:
                db.rollback()
                raise

    def decide(self, actor, scope, version, selection, rationale, request_id, approve=True):
        self._authorize(actor, scope, 'decide')
        if type(approve) is not bool or type(version) is not int:
            raise ValueError('Decisión o versión no válida.')
        if not isinstance(request_id, str) or not 16 <= len(request_id) <= 128:
            raise ValueError('Identificador de solicitud no válido.')
        fingerprint = digest([version, selection, rationale, approve])
        with self._connect() as db:
            try:
                db.execute('BEGIN IMMEDIATE')
                current = self._latest(db, scope)
                if current is None or current['version'] != version:
                    raise Conflict('La decisión corresponde a una versión obsoleta o inexistente.')
                payload = self._decode(current)
                prior = db.execute('SELECT * FROM decisions WHERE agency=? AND project=? AND issuer=? AND subject=? AND request_id=?',
                                   (scope.agency, scope.project, actor.issuer, actor.subject, request_id)).fetchone()
                if prior:
                    if prior['request_hash'] != fingerprint:
                        raise Conflict('Identificador reutilizado con otra decisión.')
                    event = json.loads(prior['payload'])
                    self._verify_decision(db, scope, event)
                    db.commit()
                    return event
                if approve:
                    pkg = approve_bound(payload['package'], payload['record'], payload['audit'], payload['review'],
                                        actor.subject, selection, rationale)
                else:
                    pkg = approve_creative(payload['package'], actor.subject, selection, rationale, approved=False)
                event = {'version': version, 'package': pkg,
                         'actor': {'issuer': actor.issuer, 'subject': actor.subject},
                         'production_approved': False}
                db.execute('INSERT INTO decisions(agency,project,version,issuer,subject,request_id,request_hash,payload) VALUES(?,?,?,?,?,?,?,?)',
                           (scope.agency, scope.project, version, actor.issuer, actor.subject, request_id, fingerprint, self._json(event)))
                self._event(db, actor, scope, 'creative.approved' if approve else 'creative.rejected', 'ok',
                            {'version': version, 'hash': pkg['hash'], 'request_id': request_id, 'decision_hash': digest(event)})
                db.commit()
                return event
            except Exception:
                db.rollback()
                raise

    def load_latest(self, actor, scope):
        self._authorize(actor, scope, 'read')
        with self._connect() as db:
            row = self._latest(db, scope)
            if row is None:
                return None
            payload = self._decode(row)
            # Decisiones previas no habilitan una revisión posterior.
            return {'version': row['version'], **payload}

    def history(self, actor, scope):
        self._authorize(actor, scope, 'history')
        with self._connect() as db:
            return self._events(db, scope)

    @staticmethod
    def _events(db, scope):
        rows = db.execute('SELECT * FROM events WHERE agency=? AND project=? ORDER BY id',
                          (scope.agency, scope.project)).fetchall()
        previous = ''
        result = []
        for row in rows:
            payload = json.loads(row['payload'])
            if (row['previous_hash'] != previous or row['event_hash'] != digest([previous, payload])
                    or payload['agency'] != scope.agency or payload['project'] != scope.project):
                raise IntegrityFailure('El historial no supera la comprobación de integridad.')
            previous = row['event_hash']
            result.append(payload)
        return result


    def _verify_decision(self, db, scope, event):
        events = self._events(db, scope)
        if not any(e.get('detail', {}).get('decision_hash') == digest(event) for e in events
                   if isinstance(e.get('detail'), dict)):
            raise IntegrityFailure('La decisión no coincide con su evidencia.')

    def latest_decision(self, actor, scope):
        self._authorize(actor, scope, 'read')
        with self._connect() as db:
            revision = self._latest(db, scope)
            if revision is None:
                return None
            self._decode(revision)
            row = db.execute('SELECT payload FROM decisions WHERE agency=? AND project=? AND version=? ORDER BY id DESC LIMIT 1',
                             (scope.agency, scope.project, revision['version'])).fetchone()
            if row is None:
                return None
            event = json.loads(row['payload'])
            # Detectar alteración accidental de decisiones contra su evento de auditoría.
            self._verify_decision(db, scope, event)
            return event
