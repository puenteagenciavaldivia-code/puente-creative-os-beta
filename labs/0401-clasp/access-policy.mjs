/**
 * PUENTE 04.01 · policy de autorización por ámbito.
 * Módulo de diseño y pruebas, NO conectado aún al receptor GAS.
 *
 * actor y memberships DEBEN provenir de un emisor de identidad confiable
 * verificado en servidor; nunca de valores declarados en la solicitud HTTP.
 */
const ROLES = Object.freeze({
  ADMIN: 'Administrador',
  CREATIVE: 'Dirección creativa',
  PRODUCTION: 'Producción',
  READONLY: 'Consulta',
});
const ACTIONS = Object.freeze({
  READ: 'briefing.read',
  UPLOAD: 'attachment.write',
  REVIEW: 'briefing.review',
  APPROVE: 'briefing.approve',
  AUDIT: 'audit.read',
});
const PERMISSIONS = Object.freeze({
  [ROLES.ADMIN]: [ACTIONS.READ, ACTIONS.UPLOAD, ACTIONS.REVIEW, ACTIONS.APPROVE, ACTIONS.AUDIT],
  [ROLES.CREATIVE]: [ACTIONS.READ, ACTIONS.UPLOAD, ACTIONS.REVIEW, ACTIONS.APPROVE],
  [ROLES.PRODUCTION]: [ACTIONS.READ, ACTIONS.UPLOAD],
  [ROLES.READONLY]: [ACTIONS.READ],
});

function deny(reason) {
  return Object.freeze({ allow: false, reason });
}

/**
 * @param {object} input Datos provenientes de una sesión ya validada en servidor.
 * @param {string} input.actorId ID de identidad confiable.
 * @param {string} input.clientId Ámbito al que pertenece el briefing.
 * @param {string} input.action Acción solicitada.
 * @param {object} input.trustedDirectory Directorio de membresías creado por el servidor.
 * @param {object} input.submission Registro persistido de briefing, no valores del cliente.
 */
export function authorize({ actorId, clientId, action, trustedDirectory, submission } = {}) {
  if (!actorId || !clientId || !action || typeof actorId !== 'string' ||
      typeof clientId !== 'string' || typeof action !== 'string') return deny('MISSING_SCOPE');
  if (!Object.values(ACTIONS).includes(action)) return deny('UNKNOWN_ACTION');
  if (!trustedDirectory || typeof trustedDirectory !== 'object' || !submission ||
      typeof submission !== 'object') return deny('UNTRUSTED_CONTEXT');
  if (submission.clientId !== clientId || submission.status !== 'active') return deny('SUBMISSION_DENIED');
  const membership = trustedDirectory[actorId]?.[clientId];
  if (!membership || membership.active !== true || !Object.hasOwn(PERMISSIONS, membership.role))
    return deny('NO_ACTIVE_MEMBERSHIP');
  if (!PERMISSIONS[membership.role].includes(action)) return deny('ROLE_DENIED');
  if (action === ACTIONS.UPLOAD && submission.filesConsent !== true)
    return deny('CONSENT_REQUIRED');
  return Object.freeze({ allow: true, reason: 'AUTHORIZED' });
}
export { ROLES, ACTIONS };
