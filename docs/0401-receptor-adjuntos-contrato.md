# PUENTE 04.01 — Contrato pendiente del receptor de adjuntos
Fecha: 2026-11-19. Estado: diseño para validacion; NO desplegado.

## Problema
Un cliente puede recibir timeout despues de que Apps Script ya guardo un archivo. El reintento de Streamlit NO demuestra si la primera escritura ocurrio. El registro de confirmaciones en sesion reduce repeticiones conocidas pero no garantiza idempotencia tras perdida de sesion o comunicacion.

## Contrato propuesto (no afirmar implementacion)
- Solicitud: accion attachments; submission_id emitido por servidor en el briefing; attachment_key deterministica del nombre/MIME/SHA-256 del contenido; lista de un archivo por solicitud.
- La identidad y autorizacion nunca derivan del rol declarado por el cliente. Validar token en servidor con comparacion apropiada y privilegios minimos; no registrar secretos.
- Validar MIME por contenido y metadatos, base64 estricto, tamano maximo, cantidad por submission, nombre seguro y vinculacion al briefing.
- Clave unica durable: (submission_id, attachment_key), sin confiar solo en ScriptCache o SessionState.
- Bajo LockService (o transaccion equivalente), consultar el estado durable ANTES de escribir. Un registro CONFIRMED retorna OK sin crear otro archivo.
- Para resultados inciertos, guardar un estado PENDING con correlacion y verificar Drive antes de reintentar. No asumir que un timeout significa que no hubo escritura.
- Mantener metadatos de Drive fileId y hash de contenido; restaurar/reconciliar PENDING si el proceso se interrumpe. Evitar que dos procesos creen el mismo contenido simultaneamente.
- Respuestas HTTP con semantica estable: OK unicamente cuando el registro durable y el archivo estan confirmados. Errores no se transforman silenciosamente en OK.
- Evitar publicar webhook o credenciales de laboratorio. Guardar evidencias sinteticas y prevenir escrituras repetidas en clientes.

## Pruebas de aceptacion (aun NO ejecutadas en Apps Script)
1. Mismo submission + misma key, dos solicitudes secuenciales => un solo archivo y respuesta OK en ambas.
2. Dos envios simultaneos de la misma key => un unico archivo, lock o transaccion comprobada.
3. Falla despues de crear archivo antes de confirmar => reconciliacion por fileId/hash, nunca duplicacion silenciosa.
4. Timeout del cliente despues de commit => reintento OK, sin crear archivo nuevo.
5. Misma key con bytes diferentes => rechazo.
6. Submission inexistente o sin consentimiento => denegacion sin escritura.
7. Dos submission distintos con el mismo contenido => dos vinculos independientes autorizados.
8. MIME, tamano y base64 invalidos => denegacion.
9. Limites de ejecucion y retencion => dictamen explicito; respaldo de evidencia.
10. Revocacion de autorizacion entre etapas => bloqueo antes de efecto segun politica.

## Condicion de cierre
Hasta verificar la implementacion real y observar estas pruebas sobre un proyecto AISLADO, marcar idempotencia del receptor como PENDIENTE. No repetir GAS-AUDIT01 existente ni limpiar ScriptProperties historicas.
