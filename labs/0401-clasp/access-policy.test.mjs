import assert from 'node:assert/strict';
import { test } from 'node:test';
import { authorize, ACTIONS, ROLES } from './access-policy.mjs';

const directory = Object.freeze({
  alice: {
    clientA: { role: ROLES.ADMIN, active: true },
    clientB: { role: ROLES.READONLY, active: true },
  },
  bob: {
    clientA: { role: ROLES.PRODUCTION, active: true },
    clientB: { role: ROLES.CREATIVE, active: false },
  },
  carol: {
    clientA: { role: ROLES.CREATIVE, active: true },
  },
  dave: {
    clientA: { role: ROLES.READONLY, active: true },
  },
});
const briefing = (clientId = 'clientA', filesConsent = true, status = 'active') =>
  ({ clientId, filesConsent, status });
const run = (actorId, clientId, action, submission = briefing(), trustedDirectory = directory) =>
  authorize({ actorId, clientId, action, submission, trustedDirectory });

test('administrador solo dentro del cliente asignado', () => {
  assert.equal(run('alice', 'clientA', ACTIONS.AUDIT).allow, true);
  assert.equal(run('alice', 'clientA', ACTIONS.APPROVE).allow, true);
  assert.equal(run('alice', 'clientB', ACTIONS.UPLOAD, briefing('clientB')).allow, false);
  assert.equal(run('alice', 'clientB', ACTIONS.READ, briefing('clientB')).allow, true);
});

test('producción puede subir con consentimiento, pero no aprobar', () => {
  assert.equal(run('bob', 'clientA', ACTIONS.UPLOAD).allow, true);
  assert.equal(run('bob', 'clientA', ACTIONS.APPROVE).allow, false);
  assert.equal(run('bob', 'clientA', ACTIONS.UPLOAD, briefing('clientA', false)).reason, 'CONSENT_REQUIRED');
  assert.equal(run('bob', 'clientA', ACTIONS.UPLOAD, briefing('clientA', 'true')).allow, false);
});

test('dirección creativa puede revisar y aprobar dentro de su ámbito', () => {
  assert.equal(run('carol', 'clientA', ACTIONS.REVIEW).allow, true);
  assert.equal(run('carol', 'clientA', ACTIONS.APPROVE).allow, true);
  assert.equal(run('carol', 'clientA', ACTIONS.AUDIT).allow, false);
});

test('consulta tiene permiso exclusivamente de lectura', () => {
  assert.equal(run('dave', 'clientA', ACTIONS.READ).allow, true);
  assert.equal(run('dave', 'clientA', ACTIONS.UPLOAD).allow, false);
  assert.equal(run('dave', 'clientA', ACTIONS.REVIEW).allow, false);
});

test('el ámbito del briefing persistido no puede alterarse mediante clientId', () => {
  assert.equal(run('alice', 'clientA', ACTIONS.READ, briefing('clientB')).reason, 'SUBMISSION_DENIED');
  assert.equal(run('carol', 'clientB', ACTIONS.APPROVE, briefing('clientA')).allow, false);
});

test('membresía revocada o ausente impide nuevas operaciones', () => {
  assert.equal(run('bob', 'clientB', ACTIONS.READ, briefing('clientB')).reason, 'NO_ACTIVE_MEMBERSHIP');
  assert.equal(run('absent', 'clientA', ACTIONS.READ).allow, false);
});

test('briefing revocado o archivado no permite usar permisos antiguos', () => {
  assert.equal(run('alice', 'clientA', ACTIONS.READ, briefing('clientA', true, 'revoked')).allow, false);
  assert.equal(run('alice', 'clientA', ACTIONS.UPLOAD, briefing('clientA', true, 'archived')).allow, false);
});

test('sin contexto confiable, acción reconocida o ámbito falla cerrado', () => {
  assert.equal(authorize({ actorId: 'alice', clientId: 'clientA', action: ACTIONS.READ, submission: briefing() }).allow, false);
  assert.equal(run('alice', 'clientA', 'attachment.delete').reason, 'UNKNOWN_ACTION');
  assert.equal(authorize({ actorId: 'alice', clientId: '', action: ACTIONS.READ, trustedDirectory: directory, submission: briefing() }).reason, 'MISSING_SCOPE');
});
