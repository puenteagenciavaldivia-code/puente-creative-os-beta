/**
 * PUENTE 04.01: verifica JWT de identidad RS256 con JWKS fijado por backend.
 * NO descarga claves ni implementa OAuth flow. No enviar JWKS desde el cliente.
 * El emisor y la audiencia se configuran por servidor; reloj en segundos.
 */
import { createPublicKey, verify as verifySignature } from 'node:crypto';

const B64URL = /^[A-Za-z0-9_-]+$/;
const BAD = Object.freeze({ verified: false, code: 'IDENTITY_DENIED' });
const ALLOWED_SKEW_SECONDS = 30;

function decodeSegment(value, maxBytes) {
  if (typeof value !== 'string' || !value || !B64URL.test(value)) return null;
  const bytes = Buffer.from(value, 'base64url');
  if (!bytes.length || bytes.length > maxBytes || bytes.toString('base64url') !== value) return null;
  try { return JSON.parse(bytes.toString('utf8')); } catch { return null; }
}

export function createOidcVerifier({ issuer, audience, keys, now = () => Math.floor(Date.now() / 1000) } = {}) {
  if (typeof issuer !== 'string' || !issuer.startsWith('https://') ||
      typeof audience !== 'string' || !audience ||
      !keys || typeof keys !== 'object' || Array.isArray(keys))
    throw new Error('Trusted OIDC configuration required');

  const pinned = new Map();
  for (const [kid, jwk] of Object.entries(keys)) {
    if (!kid || kid.length > 128 || !/^[A-Za-z0-9_.-]+$/.test(kid) ||
        !jwk || jwk.kty !== 'RSA' || !jwk.n || !jwk.e ||
        (jwk.use && jwk.use !== 'sig') || (jwk.alg && jwk.alg !== 'RS256'))
      throw new Error('Invalid pinned key');
    pinned.set(kid, createPublicKey({ key: jwk, format: 'jwk' }));
  }
  if (!pinned.size) throw new Error('Missing pinned keys');

  return async function verifyIdentity(token) {
    try {
      if (typeof token !== 'string' || token.length > 12_000 || token.length < 32) return BAD;
      const parts = token.split('.');
      if (parts.length !== 3 || !parts[2] || !B64URL.test(parts[2])) return BAD;
      const header = decodeSegment(parts[0], 1024);
      const payload = decodeSegment(parts[1], 8192);
      if (!header || !payload || Array.isArray(header) || Array.isArray(payload) ||
          header.alg !== 'RS256' || typeof header.kid !== 'string' || !pinned.has(header.kid) ||
          (header.typ !== undefined && header.typ !== 'JWT') ||
          header.jku !== undefined || header.jwk !== undefined || header.x5u !== undefined ||
          typeof payload.sub !== 'string' || !payload.sub || payload.sub.length > 256 ||
          payload.iss !== issuer) return BAD;
      const aud = payload.aud;
      if (typeof aud === 'string' ? aud !== audience :
          !Array.isArray(aud) || !aud.includes(audience) ||
          aud.length !== 1 && payload.azp !== audience) return BAD;
      if (typeof payload.exp !== 'number' || !Number.isSafeInteger(payload.exp) ||
          typeof payload.iat !== 'number' || !Number.isSafeInteger(payload.iat)) return BAD;
      const current = now();
      if (!Number.isSafeInteger(current) || payload.exp <= current - ALLOWED_SKEW_SECONDS ||
          payload.iat > current + ALLOWED_SKEW_SECONDS ||
          (payload.nbf !== undefined &&
           (typeof payload.nbf !== 'number' || !Number.isSafeInteger(payload.nbf) ||
            payload.nbf > current + ALLOWED_SKEW_SECONDS))) return BAD;
      const sig = Buffer.from(parts[2], 'base64url');
      if (sig.toString('base64url') !== parts[2]) return BAD;
      const valid = verifySignature('RSA-SHA256', Buffer.from(parts[0] + '.' + parts[1]),
        pinned.get(header.kid), sig);
      return valid ? Object.freeze({ verified: true, subject: payload.sub }) : BAD;
    } catch {
      return BAD;
    }
  };
}
