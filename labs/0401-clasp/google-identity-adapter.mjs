/**
 * PUENTE 04.01 — Adaptador de identidad Google OIDC (laboratorio).
 * clientId DEBE ser el OAuth Client ID propio de Puente configurado en el backend.
 * No reutilizar clasp, aceptar claves desde el navegador ni registrar ID tokens.
 * Sin clientId no arranca. No inicia sesiones ni implementa el flujo OAuth.
 */
import { createOidcVerifier } from './oidc-verifier.mjs';

const CERTS = 'https://www.googleapis.com/oauth2/v3/certs';
const ISSUER = 'https://accounts.google.com';
const DENIED = Object.freeze({ verified: false, code: 'IDENTITY_DENIED' });

export function createGoogleIdentityAdapter({
  clientId, fetchJwks = globalThis.fetch,
  nowMs = () => Date.now(),
} = {}) {
  if (typeof clientId !== 'string' ||
      !/^[0-9]+-[a-z0-9_-]+\.apps\.googleusercontent\.com$/.test(clientId) ||
      typeof fetchJwks !== 'function') throw new Error('Google OAuth client ID and fetch required');

  let cache = null;
  let cachedUntil = 0;
  let pending = null;

  async function refresh() {
    const response = await fetchJwks(CERTS, { method: 'GET', redirect: 'error' });
    if (!response?.ok) throw new Error('JWKS unavailable');
    const payload = await response.json();
    if (!Array.isArray(payload?.keys) || payload.keys.length < 1 ||
        payload.keys.length > 20) throw new Error('JWKS invalid');
    const keys = Object.create(null);
    for (const jwk of payload.keys) {
      if (!jwk || typeof jwk.kid !== 'string' ||
          Object.hasOwn(keys, jwk.kid)) throw new Error('JWKS key invalid');
      keys[jwk.kid] = jwk;
    }
    const verify = createOidcVerifier({
      issuer: ISSUER, audience: clientId, keys,
      now: () => Math.floor(nowMs() / 1000),
    });
    const cacheControl = response.headers?.get?.('cache-control') || '';
    const maxAge = /(?:^|,)\s*max-age=(\d+)\b/i.exec(cacheControl);
    const seconds = maxAge ? Number(maxAge[1]) : 300;
    const ttlMs = Math.max(60, Math.min(Number.isFinite(seconds) ? seconds : 300, 3600)) * 1000;
    cache = verify;
    cachedUntil = nowMs() + ttlMs;
  }

  async function verifyIdentity(token) {
    try {
      if (typeof token !== 'string' || token.length < 32 || token.length > 12_000)
        return DENIED;
      if (!cache || nowMs() >= cachedUntil) {
        if (!pending) pending = refresh().finally(() => { pending = null; });
        await pending;
      }
      return await cache(token);
    } catch {
      // No aceptar tokens si faltan claves o expira el caché y Google no responde.
      return DENIED;
    }
  }

  return Object.freeze({ verifyIdentity });
}
