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

## Beta 0.4 — Panel interno de revisión
- Página de Streamlit: `pages/01_Panel_interno.py`. Menú lateral «Panel interno».
- Acceso mediante contraseña `ADMIN_PANEL_PASSWORD` definida exclusivamente en los Secrets de Streamlit.
- Lectura de los 100 registros más recientes, búsqueda por marca, revisión de respuestas, suficiencia y enlaces privados de Drive.
- Receptor Apps Script requiere `ADMIN_READ_TOKEN` en **Configuración del proyecto > Propiedades de secuencia de comandos**. Este valor debe ser ALEATORIO, DIFERENTE del `WEBHOOK_TOKEN`, y no publicarse en GitHub.
- Streamlit Secrets debe incluir `ADMIN_READ_TOKEN = "mismo valor de Apps Script"` y `ADMIN_PANEL_PASSWORD = "otra contraseña exclusiva"`. Mantener sin cambios `SHEETS_WEBHOOK_URL` y `SHEETS_WEBHOOK_TOKEN`.
- Actualizar `Código.gs` con `apps_script.gs`, guardar y publicar **Nueva versión de la implementación existente** para activar la acción `admin_list`. No crear otra URL.
- Probar ingreso con contraseña incorrecta y correcta, recuperación de registros, archivos y cierre de sesión.
- Seguridad: es solo una beta, protegida con una contraseña compartida y tokens independientes. No cuenta con identidad por usuario, MFA, auditoría robusta ni controles de tasa. No usar con clientes reales ni datos confidenciales antes de implementar autenticación fuerte, seguridad contra fuerza bruta y política de retención.


## Beta 0.5 — Diagnóstico estratégico preliminar (heurístico)
- `briefing_quality.py` reemplaza la puntuación de campos simplemente llenos por una estimación de claridad y especificidad. Penaliza respuestas vacías, demasiado breves, genéricas, repetitivas o claramente de prueba.
- Los campos esenciales de negocio, servicios, diferenciación, público y objetivo impiden una calificación de «apto para revisión» si no aportan información suficiente.
- Se guardan `dimension_scores`, `field_quality`, `flags`, `follow_up_questions` y la versión del motor en el JSON del briefing, con visualización en el panel.
- Los registros anteriores conservan su puntuación original y se identifican como anteriores a la versión 0.5. No se recalculan automáticamente.
- El panel debe seguir requiriendo contraseña; ninguna respuesta ni token se añade a código público.
- No necesita cambiar Apps Script ni sus secretos: el receptor ya guarda el JSON del diagnóstico sin conocer su contenido.
- Pruebas de regresión incluidas en `tests/test_briefing_quality.py`: ejecutar `python -m unittest discover -s tests`.
- **Limitación crítica:** estas reglas no comprenden semántica, no verifican afirmaciones, no detectan contradicciones complejas ni recomiendan corrientes madre. La puntuación nunca sustituye el criterio humano; evitar uso externo hasta auditoría de falsos positivos y seguridad.


## Beta 0.6 — Cliente comprensible + ficha de entrada Creative OS
- Se mantienen las cinco etapas y las veinte preguntas, pero la redacción utiliza lenguaje cotidiano.
- Se alternan ejemplos de servicios, comercios y otros negocios para evitar orientar todas las respuestas hacia cafeterías.
- Las respuestas de texto con poca especificidad muestran una sugerencia amable. La sugerencia no bloquea el avance.
- Antes de enviar aparece una pantalla para revisar y corregir secciones. El envío ocurre únicamente después de «Confirmar y enviar».
- El cliente no ve el puntaje técnico interno: recibe una confirmación de recepción para revisión humana.
- El diagnóstico separa respuestas opcionales no informadas de respuestas obligatorias débiles. Se registra la cobertura de preguntas opcionales.
- El módulo `creative_handoff.py` transforma los datos del briefing en un objeto de traspaso estructurado: bloques de declaraciones, datos pendientes por tarea, alertas y decisiones creativas vacías.
- El panel interno permite ver la ficha y descargar `puente-ficha-creative-os.json`, sin modificar Google Sheets ni Apps Script.
- Los registros anteriores se pueden exportar en el mismo formato, pero los que no tengan análisis de calidad de Beta 0.5 se consideran pendientes de evaluación, no listos automáticamente.
- Las corrientes madre, arquetipos, conceptos, interpretación profunda y aprobación de producción siguen siendo **decisiones del equipo**, no del algoritmo.
- No publicar para clientes reales hasta validar el despliegue de Streamlit, privacidad, permisos y comportamiento del inicio de sesión. El acceso con contraseña compartida es solo para beta.
- GitHub Actions verifica sintaxis y pruebas de regresión en futuros commits (si Actions está habilitado en el repositorio).
