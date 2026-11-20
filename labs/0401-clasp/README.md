# PUENTE Creative OS 04.01 · Receptor aislado

Implementación de laboratorio basada en [el contrato 04.01](../../docs/0401-receptor-adjuntos-contrato.md). La rama de referencia remota estaba en `3d9379e46563eaf6e33c5ee0a3ac2868ff747fce` al validar. Sus archivos de pruebas y su flujo de auditoría se conservaron. La verificación real en Google Apps Script está pendiente.

## Auditoría del receptor Beta

La ruta Beta guarda en una hoja fija y reutiliza archivos por nombre. Un nombre repetido con bytes distintos puede devolver `OK` para el archivo equivocado. Ante una interrupción simulada después de crear el archivo, recupera su enlace por nombre. El token rechaza accesos inválidos y se exige un envío conocido, pero Beta acepta adjuntos sin consentimiento persistido y acepta texto declarado como PDF. Guarda enlaces en Sheets sin un registro durable de operaciones. El cliente Python genera una clave y guarda confirmaciones en sesión.

## Receptor del laboratorio

- `receiver/Receiver.js` conserva la forma de solicitud `attachments`, limita a un archivo por solicitud y calcula la misma clave que el cliente Python. Comprueba firma inicial, MIME, extensión, nombre, base64 canónico, SHA-256, 3 MiB por archivo y cinco reservas por envío. La firma inicial comprueba coherencia de tipo y permite archivos estructuralmente incompletos.
- Verifica el hash del token de servicio y el consentimiento persistido del envío. El ensayo crea los UUID en el servidor y persiste su estado. La autoridad de escritura es una cuenta de laboratorio dedicada y la única credencial de transporte tendría alcance para los envíos autorizados del proyecto. La conexión con el alta de briefings y su flujo de revocación queda fuera del laboratorio. El ensayo revoca un UUID bajo el mismo script lock.
- Bajo `LockService`, guarda en Script Properties un ID generado por Drive antes de crear el archivo. Todos los reintentos usan ese mismo ID. Confirma tras verificar SHA-256, nombre, MIME, carpeta y permisos. El mismo contenido en envíos diferentes usa reservas independientes. Una reserva ambigua sigue ocupando un cupo y queda disponible para reconciliación.
- Drive avanzado v3 usa `drive.file`. La carpeta se crea en la unidad de la cuenta de laboratorio y se verifica que solo tenga el permiso del propietario antes de escribir. El receptor verifica también el archivo. Las propiedades contienen el estado actual, el ID, el hash y las marcas de tiempo. Cloud Logging recibe códigos fijos y un UUID de correlación, sin contenido, nombre, credenciales, IDs de envíos ni IDs de Drive.
- Ante errores o cuotas de almacenamiento, el registro falla cerrado a `RETRY`. Las propiedades se conservan durante el ensayo para evitar que caduque la idempotencia mientras exista el archivo. Tras guardar evidencia sintética, retirar juntos la carpeta y el proyecto desechables. Las cuotas, la retención efectiva de Cloud Logging y la concurrencia entre ejecuciones reales requieren verificación en Google.

## Alta de un proyecto nuevo

El mantenedor habilita la [API de Apps Script](https://script.google.com/home/usersettings) y autoriza clasp 3.4.1 con la cuenta Google dedicada al laboratorio. `node labs/0401-clasp/create-lab.mjs` crea un proyecto independiente desde un directorio nuevo bajo `.local/0401-clasp/` y sube únicamente las tres fuentes de `receiver/`. Rechaza IDs como argumentos. La configuración generada queda ignorada por Git. El comando prepara el código de un proyecto privado y no crea despliegues.

Tras esa autorización, abrir el proyecto nuevo y conceder `drive.file` a `runSyntheticLab0401` en el editor. Con un proyecto Cloud estándar asociado, su administrador debe habilitar también Google Drive API. El ensayo crea su propia carpeta y fixtures, ejecuta diez comprobaciones usando Drive real y elimina el hash de la credencial temporal al terminar. La ejecución del editor cubre la ruta `doPost` mediante eventos sintéticos. Una carrera real y un timeout de transporte requieren dos invocaciones independientes a un acceso privado del laboratorio. Las pruebas locales simulan contención y pérdida de confirmación.

## Evidencia local

- GitHub Actions reportó éxito para la [ejecución de referencia](https://github.com/puenteagenciavaldivia-code/puente-creative-os-beta/actions/runs/44652180768). Localmente pasaron las mismas 45 pruebas (28 del motor, 14 de adjuntos y 3 de Streamlit), y la suite Python completa pasó 224 pruebas.
- Pasaron 17 pruebas Node. Se ejecutó el código del receptor en una VM con dobles de Drive, Properties, ContentService y LockService, incluidos los diez controles del ejecutor del editor. También se probó el alta de un proyecto nuevo con un doble de clasp.
- En el entorno Codex, `clasp show-authorized-user` inicialmente informó `Not logged in.`. Posteriormente el operador autorizó `clasp` desde su Mac, creó tres proyectos aislados y mostró una ejecución completada de `runSyntheticLab0401` en Google Apps Script/Drive real. **La ejecución sintética real terminó correctamente, pero concurrencia independiente, timeout de transporte y cierre integral continúan pendientes**. Véase [acta de evidencia del 20-11-2026](ACTA-EVIDENCIA-2026-11-20.md).

```sh
python -m pip install -r requirements-test-oidc.txt
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false python -m unittest discover -s tests
node --test labs/0401-clasp/*.test.mjs
```

## Integración de permisos: estado del laboratorio

- `access-policy.mjs` y `access-policy.test.mjs`: matriz de autorizaciones puras por rol y cliente.
- `upload-gateway.mjs` y `upload-gateway.test.mjs`: diseño de verificación de identidad de servidor y vinculación del briefing.
- `secure-upload-dispatch.mjs` y `secure-upload-dispatch.test.mjs`: flujo sintético con transporte privado inyectado, rechazo de suplantación y manejo explícito de timeouts ambiguos.
- **Estas piezas NO están conectadas a Apps Script ni constituyen OIDC real.** Debe verificarse identidad real de servidor, permisos de almacenamiento y revocación antes de habilitar clientes.
- [Criterios de cierre G01–G09](CLOSURE-GATE.md) y [acta de evidencia](ACTA-EVIDENCIA-2026-11-20.md).

El flujo de CI `lab-0401-security.yml` ejecuta los tests `*.test.mjs` al publicar cambios en la rama `lab/0401-clasp`. Comprobar que el último run sea verde antes de afirmar aprobación.
