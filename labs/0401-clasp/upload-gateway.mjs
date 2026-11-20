/**
 * PUENTE 04.01 - Puerta de autorizacion aislada para pruebas.
 * No es verificador OIDC ni endpoint desplegado.
 * Solo acepta identidad verificada y datos del repositorio confiable
 * proporcionados mediante dependencias del lado servidor.
 */
import { authorize, ACTIONS } from './access-policy.mjs';

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const SHA256 = /^[0-9a-f]{64}$/;

function reject(reason) {
  return Object.freeze({ allow: false, reason });
}

/**
 * @param {object} request Solicitud no confiable: solo submissionId, attachmentKey y accessToken.
 * @param {object} services Implementaciones de servidor: verifyIdentity, findSubmission, membershipsFor.
 * Los services NO deben usar campos actorId/role/clientId/filesConsent de request.
 */
export async function authorizeUploadRequest(request, services) {
  if (!request || typeof request !== 'object' || !services ||
      typeof services.verifyIdentity !== 'function' ||
      typeof services.findSubmission !== 'function' ||
      typeof services.membershipsFor !== 'function') return reject('UNTRUSTED_CONTEXT');
  const { submissionId, attachmentKey, accessToken } = request;
  if (typeof submissionId !== 'string' || !UUID.test(submissionId) ||
      typeof attachmentKey !== 'string' || !SHA256.test(attachmentKey) ||
      typeof accessToken !== 'string' || accessToken.length < 1) return reject('INVALID_REQUEST');

  try {
    const identity = await services.verifyIdentity(accessToken);
    if (!identity || identity.verified !== true || typeof identity.subject !== 'string' ||
        identity.subject.length === 0) return reject('IDENTITY_DENIED');

    const record = await services.findSubmission(submissionId);
    if (!record || record.id !== submissionId ||
        typeof record.clientId !== 'string' || record.clientId.length === 0)
      return reject('SUBMISSION_DENIED');

    const memberships = await services.membershipsFor(identity.subject);
    if (!memberships || typeof memberships !== 'object' || Array.isArray(memberships))
      return reject('MEMBERSHIP_UNAVAILABLE');
    // Scope is extracted from trusted storage, not from the request payload.
    const trustedDirectory = Object.create(null);
    trustedDirectory[identity.subject] = memberships;
    const decision = authorize({
      actorId: identity.subject,
      clientId: record.clientId,
      action: ACTIONS.UPLOAD,
      submission: record,
      trustedDirectory,
    });
    if (!decision.allow) return decision;
    // Only the server consumes this decision; it is NOT a standalone client capability.
    return Object.freeze({
      allow: true,
      reason: 'AUTHORIZED',
      scope: Object.freeze({
        actorId: identity.subject,
        clientId: record.clientId,
        submissionId: record.id,
        attachmentKey,
      }),
    });
  } catch (_) {
    // No stack, token or internal store errors sent to a client.
    return reject('AUTHORIZATION_UNAVAILABLE');
  }
}
