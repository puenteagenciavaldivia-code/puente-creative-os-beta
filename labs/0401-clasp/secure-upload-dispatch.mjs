/**
 * PUENTE 04.01 - Despachador de ensayo con frontera de confianza explícita.
 * NO es endpoint web, NO usa OAuth real y NO está conectado al receptor GAS.
 * Las credenciales de transporte permanecen dentro de transport(), nunca
 * forman parte de request ni se devuelven al cliente.
 */
import { authorizeUploadRequest } from './upload-gateway.mjs';
import { createHash } from 'node:crypto';

const MAX_BYTES = 3 * 1024 * 1024;
const TYPES = new Map([
  ['application/pdf', /\.pdf$/i], ['image/png', /\.png$/i],
  ['image/jpeg', /\.jpe?g$/i], ['image/webp', /\.webp$/i],
]);

function fail(code) {
  return Object.freeze({ ok: false, code });
}

function sha256(data) {
  return createHash('sha256').update(data).digest('hex');
}

function checkFile(file, attachmentKey) {
  if (!file || typeof file !== 'object' ||
      typeof file.name !== 'string' || file.name.length < 1 || file.name.length > 100 ||
      !/^[\\p{L}\\p{N}][\\p{L}\\p{N}._ -]{0,99}$/u.test(file.name) ||
      typeof file.mime !== 'string' || typeof file.data !== 'string' ||
      typeof attachmentKey !== 'string' || !/^[a-f0-9]{64}$/.test(attachmentKey))
    return false;
  const extension = TYPES.get(file.mime);
  if (!extension || !extension.test(file.name) ||
      file.data.length === 0 || file.data.length % 4 !== 0 ||
      file.data.length > 4 * Math.ceil(MAX_BYTES / 3) ||
      !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(file.data))
    return false;

  const bytes = Buffer.from(file.data, 'base64');
  if (!bytes.length || bytes.length > MAX_BYTES || bytes.toString('base64') !== file.data)
    return false;
  const header = bytes.subarray(0, 12).toString('hex');
  const signature = {
    'application/pdf': /^255044462d/,
    'image/png': /^89504e470d0a1a0a/,
    'image/jpeg': /^ffd8ff/,
    'image/webp': /^52494646........57454250/,
  }[file.mime];
  if (!signature?.test(header)) return false;
  const canonical = JSON.stringify([file.name, file.mime, sha256(bytes)]);
  return sha256(Buffer.from(canonical, 'utf8')) === attachmentKey;
}

/**
 * dispatchUpload() SOLO se debe llamar desde un servidor de confianza.
 * identityServices obtiene identidad y permisos desde fuentes verificadas.
 * transport es un cliente privado que guarda el token de servicio FUERA del request.
 * Está prohibido usar esto como prueba de un servicio real integrado.
 */
export async function dispatchUpload(request, { identityServices, transport } = {}) {
  if (!request || !checkFile(request.file, request.attachmentKey)) return fail('INVALID_FILE');
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
