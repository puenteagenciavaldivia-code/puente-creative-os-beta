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
