import assert from 'node:assert/strict';
import { test } from 'node:test';
import { authorizeUploadRequest } from './upload-gateway.mjs';

const submissionId = 'd0000000-0000-4000-8000-000000000001';
const attachmentKey = 'a'.repeat(64);
const request = Object.freeze({ submissionId, attachmentKey, accessToken: 'synthetic-token' });
function fixtures() {
  const users = {
    'synthetic-token': { verified: true, subject: 'operatorA' },
    'other-token': { verified: true, subject: 'operatorB' },
  };
  const submissions = {
    [submissionId]: { id: submissionId, clientId: 'clientA', status: 'active', filesConsent: true },
  };
  const memberships = {
    operatorA: { clientA: { active: true, role: 'Producción' } },
    operatorB: { clientB: { active: true, role: 'Administrador' } },
  };
  const services = {
    verifyIdentity: async token => users[token] ?? null,
    findSubmission: async id => submissions[id] ?? null,
    membershipsFor: async id => memberships[id] ?? null,
  };
  return { services, users, submissions, memberships };
}

test('identidad y briefing verificados conceden alcance de adjunto limitado', async () => {
  const { services } = fixtures();
  const result = await authorizeUploadRequest(request, services);
  assert.equal(result.allow, true);
  assert.deepEqual(result.scope, {
    actorId: 'operatorA', clientId: 'clientA', submissionId, attachmentKey,
  });
  assert.equal(Object.isFrozen(result.scope), true);
});

test('actor rol y cliente autodeclarados no sustituyen datos confiables', async () => {
  const { services } = fixtures();
  const forged = { ...request, actorId: 'operatorA', role: 'Administrador', clientId: 'clientA',
    filesConsent: true, accessToken: 'other-token' };
  const result = await authorizeUploadRequest(forged, services);
  assert.equal(result.allow, false);
  assert.equal(result.reason, 'NO_ACTIVE_MEMBERSHIP');
});

test('rechaza identidad no verificada, firma desconocida y ausencia de verificador', async () => {
  const { services, users } = fixtures();
  users['unverified'] = { verified: false, subject: 'operatorA' };
  assert.equal((await authorizeUploadRequest({ ...request, accessToken: 'unverified' }, services)).reason, 'IDENTITY_DENIED');
  assert.equal((await authorizeUploadRequest({ ...request, accessToken: 'wrong' }, services)).allow, false);
  assert.equal((await authorizeUploadRequest(request, { ...services, verifyIdentity: null })).allow, false);
});

test('cliente cruzado queda denegado incluso si token es legítimo', async () => {
  const { services } = fixtures();
  assert.equal((await authorizeUploadRequest({ ...request, accessToken: 'other-token' }, services)).reason, 'NO_ACTIVE_MEMBERSHIP');
});

test('consentimiento falso y estado revocado en registro del servidor bloquean', async () => {
  const { services, submissions } = fixtures();
  submissions[submissionId].filesConsent = false;
  assert.equal((await authorizeUploadRequest({ ...request, filesConsent: true }, services)).reason, 'CONSENT_REQUIRED');
  submissions[submissionId].filesConsent = true;
  submissions[submissionId].status = 'revoked';
  assert.equal((await authorizeUploadRequest(request, services)).reason, 'SUBMISSION_DENIED');
});

test('membresía revocada impide subir sin cambiar el token', async () => {
  const { services, memberships } = fixtures();
  memberships.operatorA.clientA.active = false;
  assert.equal((await authorizeUploadRequest(request, services)).reason, 'NO_ACTIVE_MEMBERSHIP');
});

test('reporte de briefing equivocado o ausente falla cerrado', async () => {
  const { services, submissions } = fixtures();
  submissions[submissionId].id = 'otro';
  assert.equal((await authorizeUploadRequest(request, services)).reason, 'SUBMISSION_DENIED');
  delete submissions[submissionId];
  assert.equal((await authorizeUploadRequest(request, services)).reason, 'SUBMISSION_DENIED');
});

test('errores internos se traducen a error genérico sin filtrar secretos', async () => {
  const { services } = fixtures();
  services.verifyIdentity = async () => { throw new Error('TOKEN-SUPER-SECRETO'); };
  const output = await authorizeUploadRequest(request, services);
  assert.deepEqual(output, { allow: false, reason: 'AUTHORIZATION_UNAVAILABLE' });
  assert.doesNotMatch(JSON.stringify(output), /TOKEN-SUPER-SECRETO/);
});

test('entrada malformada no invoca servicios de identidad', async () => {
  let calls = 0;
  const { services } = fixtures();
  services.verifyIdentity = async () => { calls++; return { verified: true, subject: 'operatorA' }; };
  for (const bad of [{ ...request, submissionId: '../escape' },
    { ...request, attachmentKey: 'not-sha' },
    { ...request, accessToken: '' },
    null]) {
    const result = await authorizeUploadRequest(bad, services);
    assert.equal(result.allow, false);
  }
  assert.equal(calls, 0);
});
