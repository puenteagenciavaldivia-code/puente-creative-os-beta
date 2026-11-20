import assert from 'node:assert/strict';
import { test } from 'node:test';
import { generateKeyPairSync, sign } from 'node:crypto';
import { createGoogleIdentityAdapter } from './google-identity-adapter.mjs';

const clientId = '123456789-puente-lab.apps.googleusercontent.com';
const issuer = 'https://accounts.google.com';
const key = generateKeyPairSync('rsa', { modulusLength: 2048 });
const otherKey = generateKeyPairSync('rsa', { modulusLength: 2048 });
const now = 1_800_000_000;
const encode = obj => Buffer.from(JSON.stringify(obj)).toString('base64url');
const pub = { ...key.publicKey.export({ format: 'jwk' }), kid: 'google-lab-key', alg: 'RS256', use: 'sig' };
function jwt(claims = {}, signingKey = key.privateKey) {
  const content = encode({ alg: 'RS256', typ: 'JWT', kid: 'google-lab-key' }) + '.' +
    encode({ iss: issuer, aud: clientId, sub: 'google-sub-123', iat: now - 10, exp: now + 120, ...claims });
  return content + '.' + sign('RSA-SHA256', Buffer.from(content), signingKey).toString('base64url');
}
function setup(overrides = {}) {
  let calls = 0;
  let currentMs = now * 1000;
  const state = { keys: [pub], ok: true, maxAge: 600, ...overrides };
  const fetchJwks = async (url, options) => {
    calls++;
    assert.equal(url, 'https://www.googleapis.com/oauth2/v3/certs');
    assert.equal(options.redirect, 'error');
    return {
      ok: state.ok,
      json: async () => ({ keys: state.keys }),
      headers: { get: () => 'public, max-age=' + state.maxAge },
    };
  };
  const adapter = createGoogleIdentityAdapter({
    clientId, fetchJwks, nowMs: () => currentMs,
  });
  return { adapter, state, calls: () => calls, advance: ms => { currentMs += ms; } };
}

test('token Google sintético válido verifica la firma y devuelve sub', async () => {
  const env = setup();
  assert.deepEqual(await env.adapter.verifyIdentity(jwt()), { verified: true, subject: 'google-sub-123' });
  assert.equal(env.calls(), 1);
});
test('caché pública evita descargar claves en cada solicitud', async () => {
  const env = setup();
  await env.adapter.verifyIdentity(jwt());
  await env.adapter.verifyIdentity(jwt());
  assert.equal(env.calls(), 1);
  env.advance(601_000);
  assert.equal((await env.adapter.verifyIdentity(jwt())).verified, false); // expired jwt
  assert.equal(env.calls(), 2);
});
test('JWT con audiencia errónea y firma falsa queda denegado', async () => {
  const env = setup();
  assert.equal((await env.adapter.verifyIdentity(jwt({ aud: 'attacker-app' }))).verified, false);
  assert.equal((await env.adapter.verifyIdentity(jwt({}, otherKey.privateKey))).verified, false);
});
test('no aceptar otros emisores ni token vencido', async () => {
  const env = setup();
  assert.equal((await env.adapter.verifyIdentity(jwt({ iss: 'https://attacker.test' }))).verified, false);
  assert.equal((await env.adapter.verifyIdentity(jwt({ exp: now - 120 }))).verified, false);
});
test('Google indisponible: fail closed, sin token ni errores internos', async () => {
  const env = setup({ ok: false });
  const actual = await env.adapter.verifyIdentity(jwt());
  assert.deepEqual(actual, { verified: false, code: 'IDENTITY_DENIED' });
});
test('JWKS vacío y claves repetidas se rechazan', async () => {
  const empty = setup({ keys: [] });
  assert.equal((await empty.adapter.verifyIdentity(jwt())).verified, false);
  const dup = setup({ keys: [pub, pub] });
  assert.equal((await dup.adapter.verifyIdentity(jwt())).verified, false);
});
test('client ID no configurado o client ID mal formado impide iniciar', () => {
  assert.throws(() => createGoogleIdentityAdapter({ fetchJwks: async () => {} }));
  assert.throws(() => createGoogleIdentityAdapter({ clientId: 'other-app', fetchJwks: async () => {} }));
});
test('no se descargan claves para tokens inválidos', async () => {
  const env = setup();
  for (const bad of [null, '', 'bad', 'x'.repeat(12001)]) {
    assert.equal((await env.adapter.verifyIdentity(bad)).verified, false);
  }
  assert.equal(env.calls(), 0);
});
