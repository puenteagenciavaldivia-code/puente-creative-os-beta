import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createHash } from 'node:crypto';
import { dispatchUpload } from './secure-upload-dispatch.mjs';

const id = 'd0000000-0000-4000-8000-000000000001';
const file = { name: 'prueba.pdf', mime: 'application/pdf', data: Buffer.from('%PDF-1.4\nprueba').toString('base64') };
const sha = value => createHash('sha256').update(value).digest('hex');
const fingerprint = item => sha(JSON.stringify([item.name, item.mime, sha(Buffer.from(item.data, 'base64'))]));
const key = fingerprint(file);
const request = { submissionId: id, attachmentKey: key, accessToken: 'legit', file };

function setup() {
  const trustedRecord = { id, clientId: 'clientA', status: 'active', filesConsent: true };
  const permissions = {
    alpha: { clientA: { active: true, role: 'Producción' } },
    beta: { clientB: { active: true, role: 'Administrador' } },
  };
  let calls = 0;
  const identityServices = {
    verifyIdentity: async token => token === 'legit'
      ? { verified: true, subject: 'alpha' }
      : token === 'other'
        ? { verified: true, subject: 'beta' }
        : null,
    findSubmission: async submission => submission === id ? trustedRecord : null,
    membershipsFor: async actor => permissions[actor] ?? null,
  };
  const transport = async () => { calls++; return 'OK'; };
  return { trustedRecord, permissions, identityServices, transport, calls: () => calls };
}
const run = (req, env, transport = env.transport) => dispatchUpload(req, {
  identityServices: env.identityServices,
  transport,
});

test('autorización legítima puede llegar al transporte y confirmar', async () => {
  const env = setup();
  const seen = [];
  const result = await run(request, env, async payload => {
    seen.push(payload);
    return 'OK';
  });
  assert.deepEqual(result, { ok: true, code: 'CONFIRMED' });
  assert.equal(seen[0].clientId, 'clientA');
  assert.equal(seen[0].actorId, 'alpha');
  assert.equal(seen[0].submissionId, id);
  assert.equal(seen[0].attachmentKey, key);
  assert.ok(!('accessToken' in seen[0]));
});

test('suplantación de identidad, cliente y rol no invoca el transporte', async () => {
  const env = setup();
  const result = await run({ ...request, accessToken: 'other', role: 'Administrador',
    clientId: 'clientA', actorId: 'alpha' }, env);
  assert.equal(result.ok, false);
  assert.equal(result.code, 'NO_ACTIVE_MEMBERSHIP');
  assert.equal(env.calls(), 0);
});

test('revocación de consentimiento y membresía bloquea antes de Drive', async () => {
  const env = setup();
  env.trustedRecord.filesConsent = false;
  assert.equal((await run(request, env)).code, 'CONSENT_REQUIRED');
  env.trustedRecord.filesConsent = true;
  env.permissions.alpha.clientA.active = false;
  assert.equal((await run(request, env)).code, 'NO_ACTIVE_MEMBERSHIP');
  assert.equal(env.calls(), 0);
});

test('briefing inactivo nunca llega a receptor', async () => {
  const env = setup();
  env.trustedRecord.status = 'revoked';
  assert.equal((await run(request, env)).code, 'SUBMISSION_DENIED');
  assert.equal(env.calls(), 0);
});

test('timeout mantiene ambigüedad y no declara escritura exitosa', async () => {
  const env = setup();
  const result = await run(request, env, async () => { throw new Error('Synthetic timeout'); });
  assert.deepEqual(result, { ok: false, code: 'RETRY_UNCERTAIN' });
  assert.doesNotMatch(JSON.stringify(result), /Synthetic timeout/);
});

test('un resultado no esperado tampoco se transforma en OK', async () => {
  const env = setup();
  for (const result of ['FAIL', null, '', { status: 'OK' }]) {
    assert.equal((await run(request, env, async () => result)).code, 'UNCONFIRMED');
  }
  assert.equal((await run(request, env, async () => 'RETRY')).code, 'RETRY');
  assert.equal((await run(request, env, async () => 'DENIED')).code, 'DENIED');
  assert.equal((await run(request, env, async () => 'INVALID')).code, 'INVALID');
});

test('archivos inválidos se rechazan antes de identidad y transporte', async () => {
  const env = setup();
  for (const candidate of [
    { ...file, name: 'prueba.exe' },
    { ...file, mime: 'application/javascript' },
    { ...file, data: '%%%badbase64' },
    { ...file, data: 'AA==' + 'x'.repeat(4 * 1024 * 1024 + 1) },
    null,
  ]) {
    assert.equal((await run({ ...request, file: candidate }, env)).code, 'INVALID_FILE');
  }
  assert.equal(env.calls(), 0);
});

test('sin verificador o transporte no permite operación', async () => {
  const env = setup();
  assert.equal((await dispatchUpload(request, {
    identityServices: env.identityServices,
  })).code, 'TRANSPORT_UNAVAILABLE');
  assert.equal((await dispatchUpload(request, {
    transport: env.transport,
  })).code, 'UNTRUSTED_CONTEXT');
  assert.equal(env.calls(), 0);
});

test('contenido manipulado con clave antigua se rechaza antes del transporte', async () => {
  const env = setup();
  const altered = { ...file, data: Buffer.from('%PDF-1.4\\ncontenido cambiado').toString('base64') };
  const result = await run({ ...request, file: altered }, env);
  assert.deepEqual(result, { ok: false, code: 'INVALID_FILE' });
  assert.equal(env.calls(), 0);
});

test('nombre o MIME modificados invalidan la huella del adjunto', async () => {
  const env = setup();
  for (const changed of [
    { ...file, name: 'otra.pdf' },
    { ...file, mime: 'image/png', name: 'prueba.png' },
    { ...file, name: '../prueba.pdf' },
  ]) {
    assert.equal((await run({ ...request, file: changed }, env)).code, 'INVALID_FILE');
  }
  assert.equal(env.calls(), 0);
});

test('base64 no canónico y firma MIME incoherente fallan antes de autorización', async () => {
  const env = setup();
  for (const changed of [
    { ...file, data: 'YQ======' },
    { ...file, data: Buffer.from('texto que no es PDF').toString('base64') },
    { ...file, data: '' },
  ]) {
    assert.equal((await run({ ...request, file: changed }, env)).code, 'INVALID_FILE');
  }
  assert.equal(env.calls(), 0);
});
