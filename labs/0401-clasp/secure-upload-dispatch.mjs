/**
 * PUENTE 04.01 - Despachador de ensayo con frontera de confianza explícita.
 * NO es endpoint web, NO usa OAuth real y NO está conectado al receptor GAS.
 * Las credenciales de transporte permanecen dentro de transport(), nunca
 * forman parte de request ni se devuelven al cliente.
 */
import { authorizeUploadRequest } from './upload-gateway.mjs';

const MAX_BYTES = 3 * 1024 * 1024;
const TYPES = new Map([
  ['application/pdf', /\.pdf$/i], ['image/png', /\.png$/i],
  ['image/jpeg', /\.jpe?g$/i], ['image/webp', /\.webp$/i],
]);

function fail(code) {
  return Object.freeze({ ok: false, code });
}

function checkFile(file) {
  if (!file || typeof file !== 'object' ||
      typeof file.name !== 'string' || file.name.length > 100 ||
      typeof file.mime !== 'string' || typeof file.data !== 'string') return false;
  const extension = TYPES.get(file.mime);
  if (!extension || !extension.test(file.name) || !/^[A-Za-z0-9+/]*={0,2}$/.test(file.data) ||
      file.data.length % 4 !== 0 || file.data.length > 4 * Math.ceil(MAX_BYTES / 3)) return false;
  return true; // Validación exacta SHA, contenido y bytes debe repetirse en receptor.
}

/**
 * dispatchUpload() SOLO se debe llamar desde un servidor de confianza.
 * identityServices obtiene identidad y permisos desde fuentes verificadas.
 * transport es un cliente privado que guarda el token de servicio FUERA del request.
 * Está prohibido usar esto como prueba de un servicio real integrado.
 */
export async function dispatchUpload(request, { identityServices, transport } = {}) {
  if (!request || !checkFile(request.file)) return fail('INVALID_FILE');
  if (typeof transport !== 'function') return fail('TRANSPORT_UNAVAILABLE');

  const decision = await authorizeUploadRequest(request, identityServices);
  if (!decision.allow) return fail(decision.reason);

  try {
    const result = await transport({
      submissionId: decision.scope.submissionId,
      attachmentKey: decision.scope.attachmentKey,
      actorId: decision.scope.actorId,
      clientId: decision.scope.clientId,
      file: request.file,
    });
    // Solo respuesta OK confirmada por receptor permite éxito.
    if (result === 'OK') return Object.freeze({ ok: true, code: 'CONFIRMED' });
    if (result === 'RETRY') return fail('RETRY');
    if (result === 'DENIED') return fail('DENIED');
    if (result === 'INVALID') return fail('INVALID');
    return fail('UNCONFIRMED');
  } catch (_) {
    // Un timeout es ambiguo: no se afirma si ocurrió la escritura.
    return fail('RETRY_UNCERTAIN');
  }
}
