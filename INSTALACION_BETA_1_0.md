# Instalación Beta 1.0 — PUENTE Creative OS

## Qué está en código
1. `pages/01_Panel_interno.py`: escritorio de cinco pestañas (Resumen, Aclaraciones, Dirección de arte, Producción, Documentos), protegido por contraseña beta.
2. `pages/02_Aclaraciones.py`: responde por enlace privado de 7 días, una sola respuesta, con consentimiento; fallback JSON.
3. `apps_script.gs`: crea invitaciones, las valida por SHA-256, expira enlaces, recibe respuestas y registra estados en pestaña independiente `Aclaraciones`; permite un envío de correo por invitación vía MailApp.
4. `dashboard_helpers.py`: enlaces para WhatsApp, correo y formulario; `ai_art_direction.py`: modelos y estimación del costo del texto por tokens.
5. **Sin API en esta fase**: la pestaña Dirección de arte prepara un encargo para ChatGPT y permite importar propuestas con citas verificables. No hay llamadas automáticas ni consumo de API desde el panel.

## Activación de enlaces (requiere intervención del administrador)
A. **Google Apps Script**:
- Abrir el proyecto independiente *PUENTE Creative OS — Receptor Briefings*.
- Sustituir su código por la versión actualizada de `apps_script.gs` desde GitHub (preservar siempre una copia/versión previa).
- Abrir Configuración del proyecto → Propiedades del script, crear `CLARIFICATIONS_ADMIN_TOKEN` con un valor aleatorio fuerte distinto de `WEBHOOK_TOKEN` y `ADMIN_READ_TOKEN`. No guardar el valor en código ni en GitHub.
- Guardar y desplegar como **Nueva versión** en la implementación web existente (no crear una implementación pública diferente sin motivo).
- Autorizar los permisos de `MailApp` si Apps Script los solicita; el correo sale desde la cuenta del propietario del script.

B. **Streamlit Community Cloud**, misma app existente, Settings → Secrets:
```toml
# Valores de ejemplo, NO pegarlos literalmente.
CLARIFICATIONS_ADMIN_TOKEN = "VALOR_PRIVADO_IDÉNTICO_A_LA_PROPIEDAD_DEL_SCRIPT"
APP_PUBLIC_URL = "https://NOMBRE_REAL_DE_TU_APP.streamlit.app"
# No se requiere OPENAI_API_KEY en esta fase
```
Mantener los cuatro secretos anteriores. La URL pública es la de la aplicación real, **no la del administrador**. No publicar credenciales en chats, tickets, commits ni capturas.

C. **Flujo interno**:
1. El equipo inicia sesión en el escritorio, selecciona marca → Aclaraciones.
2. Revisa y selecciona preguntas, pulsa **Crear enlace privado por 7 días**.
3. Comparte enlace por WhatsApp (abre app sin enviar automáticamente), correo con plantilla (abre su cliente de email) o botón **Enviar correo automáticamente desde Puente** (requiere permiso MailApp; máximo un envío por enlace).
4. El cliente abre el enlace y escribe respuestas; la app solo guarda datos si valida token, consentimiento y respuestas. Es una invitación de un solo uso; no debe reenviarse.
5. Puente pulsa **Consultar respuestas y estados**; las respuestas siguen marcadas `received_unverified` hasta su validación humana.
6. En **Documentos**, el botón **Guardar revisión en Sheets** agrega una versión de la decisión humana a la pestaña `Revisiones`, con responsable. **Recuperar última revisión guardada** permite continuar el trabajo. Esto requiere la nueva versión de Apps Script; las exportaciones JSON siguen disponibles como respaldo.

## Privacidad y límites
- Token aleatorio opaco de 256 bits, hash SHA-256 en la hoja; vence después de siete días y se cierra tras primer envío.
- Enlace de portador: **quien tenga el enlace puede responder**, no confirma identidad; no es apto para datos sensibles.
- Pestaña `Aclaraciones` almacena preguntas, respuestas, identificación de briefing y estados; el acceso depende de la configuración privada del Spreadsheet.
- El contenido de las preguntas se envía por Apps Script; no enviar datos personales sensibles ni información confidencial durante la beta.
- La contraseña compartida actual del panel **no es autenticación de producción**. Necesita usuarios individuales, permisos por rol, auditoría de cambios, límites de solicitudes y revisión de seguridad para manejar clientes reales.
- Los enlaces y tokens de sesión solo se mantienen en Streamlit durante la sesión actual; si se pierde el enlace antes de compartirlo, crear otro. En la hoja queda el hash, no el token recuperable.
- La entrega directa de correos está sujeta a cuotas y permisos de Google Apps Script, y requiere aprobación explícita del envío.
- El envío automático a WhatsApp **no** está implementado: el botón abre WhatsApp para compartir el enlace y evita costos o integración no autorizada.

## Dirección de arte con ChatGPT: sin API, sin cargos de API
- La pestaña **Dirección de arte** proporciona un archivo TXT de investigación que reúne el briefing, vacíos, catálogo y metodología bibliográfica.
- El equipo debe **revisar el texto antes de compartirlo** en ChatGPT, eliminar información confidencial y asegurar la autorización de uso de los datos.
- ChatGPT puede desarrollar tres opciones y devolver un JSON estructurado; el panel permite validarlo e importarlo, sin aprobar automáticamente.
- Si el JSON falla la validación de categorías, nombres o citas literales, no se importa. También es posible registrar las corrientes manualmente.
- `ai_art_direction.py` queda archivado para una fase posterior. No es necesario configurar `OPENAI_API_KEY` ni pagar una API adicional.
- La biblioteca y las referencias profesionales son un marco de evaluación inicial: no afirmar que se leyeron los libros completos ni que las propuestas están históricamente demostradas.

## Pruebas manuales obligatorias antes de utilizar con clientes
- En el panel, **Ejecutar pruebas internas** y verificar que todas pasan.
- Verificar que un enlace generado presenta solo las preguntas seleccionadas.
- Enviar respuestas de prueba y comprobar estado `received_unverified`.
- Probar que una segunda respuesta con el mismo enlace es rechazada.
- Probar expiración, token falso, solicitud no autorizada y cambio de briefing.
- Comprobar envío de un solo correo autorizado, recepción y que no hay reenvío accidental.
- Verificar que el panel no llama a ninguna API de IA; revisar el TXT y una importación JSON de prueba.
- Revisar móviles y contraste de lectura de la nueva interfaz.
- Volver a validar la implementación y permisos antes de trabajar con datos reales.

## Todavía pendiente
- Validar el guardado y recuperación de revisiones tras publicar Apps Script; agregar autenticación individual y auditoría de modificaciones.
- PDF modular de entregables según plan contratado (no incluir manual de marca por defecto).
- Credenciales de acceso individuales, permisos, revisión profesional de seguridad y controles antiabuso.
- Validación completa de extremo a extremo tras el redeploy de Apps Script. GitHub no actualiza automáticamente el script desplegado.
