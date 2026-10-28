# Beta 0.2 — Recepción automática de briefings en Google Sheets

## Qué se ha implementado
La app Streamlit envía un JSON a un webhook de Google Apps Script SOLO cuando existen los secretos `SHEETS_WEBHOOK_URL` y `SHEETS_WEBHOOK_TOKEN`. Si falta la configuración, sigue funcionando la descarga manual. Si falla el envío, se muestra un error y se conserva la descarga JSON.

## Configuración (por el propietario de la hoja)
1. Crear una hoja NUEVA y privada en Google Sheets, por ejemplo «PUENTE Creative OS — Briefings Beta».
2. Desde la hoja, abrir **Extensiones → Apps Script** y pegar el contenido de `apps_script.gs`; guardar.
3. En **Configuración del proyecto → Propiedades de secuencia de comandos**, añadir `WEBHOOK_TOKEN` con un valor aleatorio largo (mínimo recomendado 32 caracteres). No poner este secreto en GitHub.
4. **Implementar → Nueva implementación → Aplicación web**. Ejecutar como **Yo**; acceso **Cualquier usuario**; autorizar. Copiar URL terminada en `/exec`. La aplicación web será pública, pero rechazará peticiones sin token.
5. En Streamlit Community Cloud, abrir la app → Settings → Secrets y agregar:
   ```toml
   SHEETS_WEBHOOK_URL = "https://script.google.com/macros/s/URL_REAL/exec"
   SHEETS_WEBHOOK_TOKEN = "EL_MISMO_TOKEN_SECRETO"
   ```
6. Guardar; esperar reinicio, realizar una prueba ficticia y revisar la pestaña **Respuestas** de la hoja.
7. Verificar que la hoja permanezca privada; no compartirla con los participantes.

## Limitaciones y privacidad
- Este montaje necesita configurar Google Apps Script manualmente. El conector ChatGPT de Drive no equivale a credenciales del servidor Streamlit.
- El webhook usa token compartido: útil como piloto reducido, no como autenticación robusta para un SaaS.
- Streamlit Community Cloud y Apps Script pueden tener límites de recursos; probar en baja escala.
- La hoja guarda texto libre: pedir consentimiento informado y no recolectar datos personales sensibles o confidenciales.
- El formulario calcula cobertura de campos y alertas básicas, no comprensión estratégica por IA.
- Guardar únicamente los datos necesarios; definir quién accede, tiempo de conservación y borrado antes de invitar a personas reales.
- Si se modifica el Apps Script, se debe actualizar la implementación existente para publicar la nueva versión.


## Beta 0.3 — Adjuntos visuales
- La sección «Universo visual» permite PNG/JPG/WEBP/PDF, máximo 5 archivos, 3 MB cada uno.
- Los archivos se transmiten uno a uno al mismo webhook y se almacenan en una carpeta privada de Drive del propietario («PUENTE Creative OS — Adjuntos»), bajo subcarpetas con ID del briefing.
- La columna K «adjuntos_drive» almacena los enlaces. No compartir la carpeta con acceso público.
- Se exige consentimiento para compartir los archivos. Solo usar material de prueba hasta comprobar el recorrido completo.
- **Es obligatorio actualizar el proyecto Apps Script ya creado manualmente**: sustituir Código.gs por el apps_script.gs actual; Guardar; Implementar > Administrar implementaciones > Editar > Nueva versión > Implementar. Revisar la autorización adicional de Drive.
- Mantener exactamente la implementación anterior, la URL /exec y el token; no crear otra app web.
- Prueba: completar un briefing ficticio, adjuntar un PNG pequeño, finalizar, comprobar la columna K y el archivo en Drive. Si aparece error, revisar Ejecuciones de Apps Script y repetir con otro briefing.
- Limitaciones: no se verifica el contenido real más allá del MIME y extensión declarados; no admite SVG, archivos grandes ni videos. Antes de recibir datos de clientes reales, se necesitan mejoras de seguridad, validación, borrado/retención y pruebas de carga.