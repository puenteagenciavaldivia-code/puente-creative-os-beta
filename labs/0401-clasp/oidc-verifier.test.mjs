import assert from 'node:assert/strict';
import { test } from 'node:test';
import { generateKeyPairSync, sign } from 'node:crypto';
import { createOidcVerifier } from './oidc-verifier.mjs';

const { privateKey, publicKey } = generateKeyPairSync('rsa', { modulusLength: 2048 });
const other = generateKeyPairSync('rsa', { modulusLength: 2048 });
const issuer = 'https://identity.example.test/';
const audience = 'puente-creative-os-lab';
const now = 1_800_000_000;
const base = { iss: issuer, aud: audience, sub: 'operator-01', iat: now - 2, exp: now + 120 };
const encode = x => Buffer.from(JSON.stringify(x)).toString('base64url');
function jwt(payload = base, key = privateKey, header = { alg: 'RS256', kid: 'lab-1', typ: 'JWT' }) {
  const signingInput = encode(header) + '.' + encode(payload);
  return signingInput + '.' + sign('RSA-SHA256', Buffer.from(signingInput), key).toString('base64url');
}
const verify = createOidcVerifier({ issuer, audience, now: () => now,
  keys: { 'lab-1': { ...publicKey.export({ format: 'jwk' }), alg: 'RS256', use: 'sig' } } });

test('firma legítima con emisor, audiencia, sujeto y tiempo correcto', async () => {
  assert.deepEqual(await verify(jwt()), { verified: true, subject: 'operator-01' });
});
test('firma falsa o contenido alterado no concede identidad', async () => {
  assert.equal((await verify(jwt(base, other.privateKey))).verified, false);
  const p = jwt().split('.');
  p[1] = encode({ ...base, sub: 'Administrador' });
  assert.equal((await verify(p.join('.'))).verified, false);
});
test('algoritmos none/HS256 y claves suministradas en cabecera rechazados', async () => {
  for (const header of [
    { alg: 'none', kid: 'lab-1' },
    { alg: 'HS256', kid: 'lab-1' },
    { alg: 'RS256', kid: 'lab-1', jku: 'https://attacker.test/jwks' },
    { alg: 'RS256', kid: 'unrecognized' },
  ]) assert.equal((await verify(jwt(base, privateKey, header))).verified, false);
});
test('emisor y audiencia erróneos quedan denegados', async () => {
  assert.equal((await verify(jwt({ ...base, iss: 'https://attacker.test/' }))).verified, false);
  assert.equal((await verify(jwt({ ...base, aud: 'another-application' }))).verified, false);
});
test('expiración, nbf futuro e iat futuro bloquean', async () => {
  for (const claims of [
    { exp: now - 31 }, { nbf: now + 31 }, { iat: now + 31 }, { exp: 'tomorrow' },
  ]) assert.equal((await verify(jwt({ ...base, ...claims }))).verified, false);
});
test('audiencias múltiples requieren azp correspondiente', async () => {
  assert.equal((await verify(jwt({ ...base, aud: [audience, 'other'] }))).verified, false);
  assert.equal((await verify(jwt({ ...base, aud: [audience, 'other'], azp: audience }))).verified, true);
});
test('tokens malformados y tamaño excesivo fallan sin excepción', async () => {
  for (const token of ['', 'a.b.c', 'x'.repeat(12001), null, undefined,
      jwt().replace(/.$/, '?')]) {
    assert.equal((await verify(token)).verified, false);
  }
});
test('configuración sin anclaje de claves no arranca', () => {
  assert.throws(() => createOidcVerifier({ issuer, audience, keys: {} }));
  assert.throws(() => createOidcVerifier({ issuer: 'http://unsafe', audience, keys: { 'lab-1': publicKey.export({ format: 'jwk' }) } }));
});
