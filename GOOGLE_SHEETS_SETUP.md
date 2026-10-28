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


## Beta 0.7 — Auditoría estratégica automática sin IA externa
- Al confirmar un briefing, Streamlit ejecuta `audit_briefing` sobre sus respuestas antes de enviarlo a Google Sheets; el resultado queda en `diagnostico_json.strategic_audit`.
- La auditoría sugiere aclaraciones transversales sobre precios, conversión, objetivos medibles, permisos de uso de materiales y presupuesto, más comprobaciones específicas para turismo, gastronomía y profesiones con contenidos técnicos sensibles.
- Cada pregunta mantiene un identificador, campos de origen, motivo, área y prioridad. Son hipótesis de información pendiente, no hechos demostrados.
- En Panel interno aparece una nueva sección **Auditoría estratégica automática**, con exportación JSON independiente. Para briefings anteriores, se calcula en la consulta sin alterar los registros históricos.
- La ficha de entrada creativa incluye la auditoría; nunca aprueba arquetipos, corrientes madre o propuestas de producción.
- No requiere modificar Apps Script, Google Sheets ni los secretos actuales; funciona con el receptor de datos ya desplegado.
- Es un sistema de reglas locales sin costo por llamadas a modelos externos. **No es análisis semántico con ChatGPT ni realiza vigilancia autónoma**. La auditoría ocurre cuando el cliente envía la ficha y se puede ver al actualizar el panel.
- No mostrar la auditoría al cliente: su destinatario es el equipo interno. Pruebas previstas en `tests/test_briefing_quality.py`.
- Pendiente de certificación: despliegue en Streamlit, acceso seguro de personal real, ejercicios de regresión y revisión manual de falsos positivos.


## Beta 0.8 — Ficha estratégica editable (revisión humana)
- En el Panel interno, selecciona un briefing y despliega **Revisión estratégica del equipo**.
- Cada pregunta de auditoría permite marcar **pendiente**, **confirmado**, **aclarar** o **descartado**. Para confirmar o descartar debe explicarse el motivo. La evidencia debe contrastarse con el cliente o documentación real.
- Compara **dos o tres corrientes madre**. Cada una necesita nombre, fundamento basado en respuestas, diferenciación y riesgos. Se prohíben alternativas duplicadas por nombre y nunca se elige automáticamente.
- Un responsable escribe la justificación y elige una dirección. Se bloquea la aprobación de producción si hay preguntas sin resolver, una alternativa incompleta, contradicciones en la elección o consultas al cliente pendientes.
- Se puede descargar una **revisión JSON** para retomarla en otra sesión, y volver a cargarla desde el panel. La importación comprueba versión y `submission_id`, con un tamaño máximo de 200 KB.
- La **exportación del paquete creativo** incluye la ficha inicial, revisión editorial, bloqueos y estado de autorización. No cambia las respuestas originales ni escribe decisiones en Google Sheets/Drive.
- Los datos de revisión se mantienen únicamente en la sesión hasta exportarlos; **NO hay persistencia automática**. No cerrar el navegador sin descargar el JSON.
- Solo realizar pruebas internas con datos ficticios: siguen pendientes autentificación por usuario, permisos granulares, registro auditable de cambios, almacenamiento persistente y control de acceso de producción.
- Pruebas nuevas en `tests/test_briefing_quality.py` comprueban controles de aprobación, comparación de dos enfoques y prevención de cargar revisiones de otro briefing.


## Biblioteca visual inicial — 41 referencias clasificadas
- `design_catalog.json` aporta 41 entradas curadas: 18 corrientes históricas, 8 enfoques, 4 tendencias, 4 técnicas, 4 lenguajes fotográficos y 3 recursos gráficos.
- `design_catalog.py` permite búsquedas por categoría, nombre, características y aplicaciones; la biblioteca está disponible desde **Panel interno → Revisión estratégica → Explorar biblioteca visual**.
- Las referencias son vocabulario de investigación, no instrucciones para copiar obras. El uso de nombres históricos no implica que todos los términos sean movimientos académicos equivalentes.
- Entre fuentes históricas para ampliar y auditar las fichas: Cooper Hewitt sobre estilo suizo (https://www.cooperhewitt.org/2018/08/05/aharmonyofcontrasts/), Departamento Federal de Asuntos Exteriores de Suiza sobre Swiss Style (https://www.aboutswitzerland.eda.admin.ch/en/swiss-style-forever-the-story-of-a-graphic-design-tradition), AIGA Eye on Design sobre New Wave (https://eyeondesign.aiga.org/why-new-wave-graphics-are-the-most-influential-designs-youve-probably-ignored/) y archivos de AIGA (https://aigadesignarchives.com/).
- El sistema todavía **no realiza recomendaciones semánticas generativas automáticas**. Para lograr esa función es necesaria una integración con un modelo de IA autorizado, controles de privacidad y evaluación contra casos reales. Mientras tanto, un diseñador puede revisar alternativas en el panel y trabajar con ChatGPT usando los briefings a los que ya tiene acceso.
- No guardar claves de APIs externas en GitHub. Nunca afirmar que una propuesta fue investigada o aprobada automáticamente cuando solo se seleccionó en la biblioteca.


## Beta 0.9 — Clarificaciones complementarias + propuestas de dirección de arte

### Mini ficha de aclaraciones
1. Desde **Panel interno → Revisión estratégica del equipo**, selecciona las preguntas que realmente faltan; descarga `puente-preguntas-<id>.json`.
2. Comparte esa ficha con el cliente por un canal acordado. Debe abrir **Aclaraciones** en la navegación de Creative OS y subir el archivo JSON.
3. La página pública complementaria solicita solo esas preguntas y consentimiento; permite descargar `puente-aclaraciones-<id>.json`. NO guarda respuestas ni envía datos a Sheets en esta beta.
4. El cliente comparte la respuesta con Puente por un canal acordado; el administrador importa el JSON desde el panel, que valida el mismo `submission_id` y los IDs de pregunta.
5. Las respuestas importadas quedan **recibidas sin verificar**; deben validarse antes de marcar preguntas como resueltas. En esta beta hay que descargar también la revisión interna para conservarlas entre sesiones.
6. Esta vía manual evita crear enlaces públicos con datos del cliente, pero aún NO es adecuada para datos privados o sensibles hasta incorporar autenticación y persistencia protegida.

### Dirección creativa
- En **Panel interno → Investigación y sugerencias de IA**, si existe `OPENAI_API_KEY` en los Secrets de Streamlit, un administrador puede autorizar y activar bajo demanda la generación de **3 propuestas** de movimientos históricos o enfoques de diseño del catálogo, nunca automáticamente ni desde la ficha pública.
- Secrets nuevos OPCIONALES (NO incluir valores en GitHub):
  ```toml
  OPENAI_API_KEY = "<configurar una clave privada válida>"
  OPENAI_MODEL = "gpt-4.1-mini"
  ```
- El motor usa la Responses API y salida JSON estructurada. Valida que los IDs pertenezcan al catálogo, que las propuestas sean distintas, que las citas literales existan dentro de las respuestas del briefing y que los fundamentos no estén vacíos. La comparación debe ser aprobada por el director de arte.
- La llamada usa `store: false`, pero **envía el texto del briefing al proveedor de IA**. No pulsar el botón sin consentimiento, autorización de uso de datos y comprensión de políticas de tratamiento. No envía archivos adjuntos. El uso de API tiene costos separados a ChatGPT.
- Si NO se configura API, se puede pulsar **Preparar tres hipótesis iniciales (reglas, sin IA)**. Es una preselección léxica de baja fiabilidad, etiquetada con su método; nunca afirmar que es investigación semántica o bibliográfica.
- Las propuestas se precargan de manera editable en la comparación de corrientes. La decisión final, los riesgos y la autorización de producción siguen bajo responsabilidad de Puente.
- El briefing público deja de mostrar un enlace directo al panel interno, pero la navegación multipágina de Streamlit puede seguir ofreciendo el nombre de la página; su contenido está protegido por la contraseña temporal de Beta.

### Bibliografía y criterio
- Revisar `METODO_DIRECCION_ARTE.md` y `design_methodology.py`. Se verificaron descripciones e índices de editores, **no textos completos** de los libros.
- Para recomendaciones profesionales confiables falta auditar individualmente las 41 fichas, aumentar referencias históricas verificadas, incorporar notas de investigación propias con licencia y evaluar resultados con dirección de arte.
- Pruebas adicionales para validación de citas, tratamiento de respuestas, aclaraciones por ID y preselección sin API.
