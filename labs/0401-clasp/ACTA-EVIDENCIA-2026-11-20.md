# PUENTE Creative OS · 04.01 · Acta de evidencia y pendientes del receptor
Fecha de revisión: 2026-11-20. Estado: validación real de un ensayo sintético; cierre integral 04.01 NO autorizado.

## Fuentes comprobadas
- GitHub: rama `lab/0401-clasp`, basada en `audit/0401-native-and-streamlit-20261119`. El laboratorio conserva `receiver/Receiver.js`, `receiver/LabChecks.js`, `receiver/appsscript.json` y las pruebas Node.
- GitHub Actions: ejecución #11 verde en rama de auditoría, mostrada por el operador; corresponde a los 28 tests del motor, 14 de adjuntos del cliente y 3 de Streamlit.
- Codex informó 17 pruebas Node y suite Python de 224 casos aprobados. Estas cantidades pertenecen a su informe de ejecución; no son pruebas reales de concurrencia Google.
- Evidencia visual facilitada por el operador el 2026-11-20: proyecto GAS aislado con `LabChecks.gs`, `Receiver.gs` y servicio avanzado Drive; registro de `runSyntheticLab0401` con `test_pass_independent_submission`, `test_pass_revoked_replay`, `test_pass_drive_file_count` y `Se completó la ejecución`. La captura no incluye los diez códigos completos ni una exportación íntegra de logs.
- El ejecutor `runSyntheticLab0401` realiza 10 comprobaciones y retorna `PASS: 10 checks; see execution logs` si las diez pasan. La ejecución de Apps Script finalizó, lo que permite inferir que no saltó una excepción; no sustituye el respaldo íntegro del registro.

## Resultado observado
1. Creación y subida de 3 fuentes en un proyecto nuevo mediante `clasp`: comprobada por captura Terminal.
2. Ejecución editor-only sobre servicios reales de Apps Script/Drive: completada sin error visible.
3. Rechazo de credencial incorrecta, consentimiento no otorgado, contenido alterado; escritura inicial, replay, interrupción sintética tras crear, recuperación, envíos independientes, revocación, recuento de archivos: definidas por `LabChecks.js`. La captura muestra éxito explícito de los controles finales; consolidar log completo para certificar 10/10 de forma documental.
4. Se crearon **tres proyectos de laboratorio** al ejecutar repetidamente `create-lab.mjs`. Solo el último se utilizó para la ejecución presentada; los dos anteriores requieren inventario y eliminación autorizada, sin tocar proyectos históricos.

## Límites y riesgos no cerrados
| Control | Estado | Evidencia de cierre requerida |
| --- | --- | --- |
| Reintento secuencial e interrupción sintética | Ejecutado en Google | Exportar log completo y cotejar conteo e IDs sin publicar datos sensibles |
| Concurrencia real de dos invocaciones independientes | PENDIENTE | Dos ejecuciones paralelas contra el mismo envío y clave; una reserva/un archivo, resultados OK/RETRY y reconciliación |
| Timeout de red real y reconexión del cliente Streamlit | PENDIENTE | Ensayo privado de transporte; confirmar un archivo en Drive tras pérdida de confirmación |
| Autorización de submission real y revocación de consentimiento | PENDIENTE | Integración confiable de altas/revocaciones en servidor; no aceptar solo consentimiento enviado por cliente |
| Separación multioperador, rol y ámbito por cliente | PENDIENTE | Matriz de acceso con dos identidades sintéticas y prueba cruzada de lectura/escritura/denegación |
| Cuotas Script Properties, Drive y tiempos límite | PENDIENTE | Carga escalonada, alertas, recuperación y política de retención |
| Seguridad del transporte y despliegue | NO AUTORIZADO | Análisis de riesgo y revisión antes de habilitar web app; no publicar URL/secretos |
| Limpieza de proyectos duplicados y carpeta sintética | PENDIENTE | Verificar IDs, aprobación de eliminación y respaldo de resultados |

## Decisión de ingeniería
- **Aprobación parcial:** implementación aislada y ensayo real sintético con finalización satisfactoria.
- **No afirmar:** exactamente-una-vez de extremo a extremo en producción, permiso multioperador resuelto, receptor conectado a briefings reales o cierre de 04.01.
- No modificar `main`, no hacer merge, no reutilizar GAS-AUTH01/GAS-AUDIT01, no cargar datos reales, no repetir `runSyntheticLab0401` sobre el proyecto ya usado.
- Próximo bloque seguro: diseñar el ensayo de concurrencia y timeout para un **cuarto proyecto nuevo**, con validación previa de permisos y control de limpieza; no ejecutar ni desplegar sin autorización expresa.

## Tanda adicional: concurrencia simulada y autorización — 2026-11-20

- Se agregaron tres pruebas a `receiver.test.mjs` para verificar intercalación determinista bajo un bloqueo compartido: mismo adjunto, envío distinto y revocación/permisos tras confirmación. El segundo intento devuelve `RETRY` mientras la primera invocación mantiene el lock; después debe completar o rechazar sin reservar un segundo ID para el mismo adjunto.
- Se creó el flujo de GitHub Actions [PUENTE 04.01 seguridad y concurrencia simulada](../../.github/workflows/lab-0401-security.yml) para ejecutar `node --test labs/0401-clasp/*.test.mjs` en cada push de `lab/0401-clasp`, con evidencia sintética como artefacto.
- **Estado de esta tanda al registrar el acta:** código de las pruebas y workflow comprometidos en GitHub; **el resultado del nuevo CI no se ha verificado**. No marcar las tres pruebas como aprobadas hasta inspeccionar su ejecución.
- Estas pruebas **no representan dos solicitudes HTTP reales a Apps Script**; tampoco validan autorizaciones entre distintas cuentas Google. Esos controles permanecen pendientes.

## Matriz mínima de cierre de seguridad multioperador

| Identidad/escenario | Requisito de seguridad | Estado |
| --- | --- | --- |
| Operador A autorizado sobre envío A | Puede registrar adjunto A con consentimiento persistido | Por validar con identidades reales de laboratorio |
| Operador B sin permiso sobre envío A | No puede crear, leer ni confirmar adjunto A | No implementado en el modelo del receptor actual: autenticación por token de servicio compartido |
| Operador A revocado | Reintentos posteriores rechazados sin nuevas escrituras | Ensayo sintético Google con UUID revocado; falta end-to-end |
| Operador con permiso sobre envío B | Mismo contenido no se confunde con envío A | Ensayo sintético Google completo; falta identidad por operador |
| Administrador de laboratorio | Puede auditar sin publicar secretos, archivos ni clientes | Logs sintéticos parciales; revisión de acceso a registros pendiente |

**Bloqueador de integración productiva:** el receptor de laboratorio utiliza un token de servicio y estados de consentimiento sintéticos. Se requiere un emisor confiable de permisos de envío y un control de acceso por rol/cliente antes de cualquier publicación. No desplegar un webhook público ni considerar concluida 04.01.

## Tanda siguiente: autorización multioperador — diseño ejecutable aislado

- Nuevo `access-policy.mjs`: política **fail-closed** para los roles Administrador, Dirección creativa, Producción y Consulta. El acceso depende conjuntamente de membresía activa del operador en el cliente, estado persistido del briefing, permiso de acción y consentimiento de adjuntos. Un Administrador no adquiere acceso automático a otros clientes.
- Nuevo `access-policy.test.mjs`: ocho pruebas de autorización: administrador por ámbito, Producción, Dirección Creativa, Consulta, ámbito cruzado, membresía revocada, briefing revocado y contexto no confiable.
- El flujo `lab-0401-security.yml` ejecuta `node --test labs/0401-clasp/*.test.mjs`, incluyendo las pruebas intercaladas del receptor y estas nuevas pruebas; **CI pendiente de inspección**.
- **Límite esencial:** este módulo es una política pura de referencia. **NO está conectado al receptor GAS, a OIDC real ni a las cuentas de operadores**. No afirmar que el control multioperador esté desplegado o validado de extremo a extremo.
- Integración pendiente: un backend de identidad verifica el token OIDC; resuelve el operador y sus membresías desde una fuente autorizada; localiza el cliente y estado del briefing desde almacenamiento persistente; aplica `authorize` antes de conceder una operación; revoca sesiones y permisos bajo política definida; evita exponer tokens de servicio compartidos a navegadores o clientes Streamlit.
- El emisor de permisos de subida debe emitir un derecho efímero vinculado a `submission_id`, `attachment_key`, `client_id` y al actor autorizado, de alcance limitado, con revocación y auditoría. **No implementado**.

## Tanda de integración de autorización en entorno aislado — 2026-11-20

- Creado `upload-gateway.mjs`: puerta de acceso de referencia. Obtiene sujeto exclusivamente mediante `services.verifyIdentity(accessToken)`, identidad marcada verificada, resolución del briefing por `services.findSubmission(submissionId)` y membresías mediante `services.membershipsFor(subject)`; aplica `authorize` desde `access-policy.mjs`.
- Los campos `actorId`, `role`, `clientId` y `filesConsent` declarados en la solicitud se ignoran. La respuesta aprobada incluye solo alcance servidor (actor, cliente, submission, attachment key), sin token y congelado como objeto.
- Se agregaron **nueve pruebas** de esta puerta en `upload-gateway.test.mjs`: autorización legítima, suplantación de rol y cliente, verificación de identidad, acceso cruzado, consentimiento y revocación del briefing, revocación de membresía, identidad de registro, fallas internas sin fuga de secretos y entrada malformada.
- El workflow existente `lab-0401-security.yml` descubre los archivos `*.test.mjs` y está preparado para estas nuevas pruebas. **Su ejecución y resultado siguen sin confirmación disponible en esta sesión**.
- **Limitación crítica:** los métodos `verifyIdentity`, `findSubmission` y `membershipsFor` son interfaces inyectadas; las pruebas usan implementaciones sintéticas. **No existe aquí un validador real de OIDC, una BD de membresías conectada, ni un puente de autorización desplegado hacia Apps Script**. La política no protege el receptor por sí sola.
- Requisitos pendientes antes de integración: validar emisor/audiencia/firma/expiración del token con bibliotecas y claves actualizadas; revocación de sesiones y permisos; ámbito inmutable de tenant/cliente; origen confiable de consentimiento; emisión de autorización efímera y verificación por servidor; ensayos de dos identidades reales y HTTP concurrente bajo entorno privado.

## Tanda de integridad de adjuntos — 2026-11-20
- El despachador aislado `secure-upload-dispatch.mjs` valida ahora el tamaño decodificado (3 MiB), base64 canónico, MIME por firma inicial, nombre seguro y la huella `attachment_key` derivada de nombre/MIME/SHA-256 de los bytes.
- Se reemplazó la huella ficticia en `secure-upload-dispatch.test.mjs` por una calculada desde los bytes, y se incorporaron tres pruebas negativas: contenido alterado manteniendo la clave, cambios de nombre/MIME y base64/firma inválidos.
- Tras revisar el archivo guardado se detectó y corrigió el escape de la expresión regular Unicode para nombres seguros, en commit `3d9fa7c`.
- **Límite de certificación:** los cambios quedaron en GitHub; los resultados del CI de este commit aún no están verificados desde esta conversación. No elevar estatus de las pruebas a aprobadas sin inspeccionar los logs.
- Esta validación es una barrera adicional del lado del despachador Node y **no sustituye** verificación redundante en el receptor GAS ni demuestra transporte o identidad real.
