# PUENTE Creative OS — decisiones de producto pendientes y método acordado

Fecha: 2026-10-28. Documento de planificación, **no funcionalidad desplegada**.

## Prioridad 1: resolver vacíos del briefing sin repetir la ficha

1. El diagnóstico detecta dudas con código único, prioridad, motivo y evidencia del briefing.
2. Puente revisa y descarta falsos positivos. Las preguntas críticas pendientes se transforman en una **mini ficha de aclaraciones** individual por marca.
3. Las preguntas adicionales deben estar redactadas en lenguaje cotidiano, con ejemplos breves y opción «No lo sé / Necesito ayuda».
4. El cliente recibe solo las preguntas pertinentes, no todo el formulario nuevamente. Una pregunta adicional debe tener contexto y explicar para qué se necesita.
5. Cada respuesta complementaria se guarda junto al identificador original del briefing, con fecha, versión y procedencia; nunca sustituye silenciosamente la respuesta original.
6. La auditoría vuelve a evaluarse usando respuestas originales + aclaraciones. Puente confirma o rechaza la resolución de cada alerta.
7. Estados: **pendiente → enviada al cliente → respondida → verificada por Puente → resuelta**, con rama «descartada con motivo».
8. No basta con una respuesta extensa: los datos operativos (precios, permisos, disponibilidad, protocolos, presupuestos) requieren comprobación contra fuentes proporcionadas por el cliente.
9. Para una beta segura, no incluir vínculos públicos con datos personales sin autenticación, expiración y control de acceso.
10. El trabajo creativo puede iniciarse en investigación con algunas dudas; producción y afirmaciones verificables requieren resolver los bloqueos críticos.

## Prioridad 2: paquetización y entregables condicionados por contrato

**Regla básica: el contrato determina lo incluido; el diagnóstico no amplía automáticamente el alcance.**

- Definir catálogo de planes editable por Puente (identificador, nombre comercial, servicios, cantidad de piezas, rondas de cambios, entregables, formatos, aprobaciones, exclusiones, plazo, precio y condiciones de uso).
- Asociar cada briefing a `plan_id` y versión del contrato, con opción de servicios adicionales aprobados.
- Separar: **ficha estratégica interna** (siempre para Puente) de **documento PDF para cliente** (solo secciones y entregables contratados).
- Un plan básico de administración de redes **no incluye un manual de marca** por defecto. Puede recibir resumen de objetivos, tono, calendario o guía breve de aplicación si está contratado.
- Plan intermedio: guía de comunicación y pautas visuales de aplicación, si están contratadas; no llamarla «manual de marca» si no define la identidad integral.
- Plan de branding: sistema de identidad, normas y aplicaciones; manual de marca solo cuando figure como entregable del contrato.
- El alcance y el precio no deben inferirse solo del número de respuestas. Si el briefing necesita trabajo extra, generar una propuesta de adicional para aprobación, no entregarlo gratis.
- Generar PDF de cliente a partir de una plantilla modular con portada, servicios contratados, alcance, estrategia aprobada, piezas, calendarios, revisión, condiciones y anexos habilitados según plan.
- Separar información confidencial interna, hipótesis y borradores del PDF externo.
- Añadir trazabilidad: `plan_id`, `contract_version`, `included_deliverables`, `approved_addons`, `document_version`, `approved_by`.

## Secuencia de desarrollo sugerida

1. Beta 0.9 — Bandeja de aclaraciones + estado humano de preguntas y registro por briefing (primero almacenamiento seguro y autenticación).
2. Beta 1.0 — Planes configurables, matriz de alcance contractual y previsualización del documento para cliente.
3. Beta 1.1 — Generación modular de PDF, control de versiones, aprobaciones y pruebas de que ningún plan recibe entregables ajenos.
4. Iteración posterior — Integración con interpretación semántica de IA, recomendación de corrientes madre, revisión de derechos y controles de privacidad.

## Criterios de aceptación

- BOSQUE ADENTRO puede recibir solo preguntas pendientes (por ejemplo precios, reservas, clima, seguridad, cupos) sin repetir las veinte originales.
- Puente distingue automáticamente información «mencionada» de información «verificada», sin emitir aprobación por palabras clave.
- Plan básico genera un documento básico sin manual de marca.
- Plan branding genera manual solo si el contrato lo incluye.
- Los documentos exhiben únicamente entregables, afirmaciones y permisos aprobados.
- La prueba de control de alcance asegura que un plan no filtre apartados de otro.

Este archivo mantiene las decisiones pendientes dentro del repositorio. No programa un aviso futuro ni implementa estas funciones por sí solo.


## Actualización 2026-10-28 — Beta 0.9 (implementación de prueba)

- **Mini ficha ya programada**: el administrador descarga solo preguntas pendientes y la página pública `pages/02_Aclaraciones.py` permite responderlas y exportar respuestas. El intercambio es manual por JSON para no crear URLs sin autenticación ni almacenar datos no protegidos. Existe importación interna con correspondencia de identificadores, siempre sin verificación automática.
- **Propuestas de corrientes con IA**: `ai_art_direction.py` y panel interno permiten investigar tres alternativas con la API solo si se configura `OPENAI_API_KEY` en Secrets y el administrador confirma autorización. Sin clave hay `creative_preselection.py`, un borrador por reglas etiquetado expresamente como NO IA. El cliente no ve las decisiones.
- **Fundamento bibliográfico**: `METODO_DIRECCION_ARTE.md` distingue fuentes editoriales consultadas y el límite de no haber leído los libros íntegros. `design_methodology.py` incluye criterios operativos auditables.
- **No completado**: persistencia segura de aclaraciones y revisiones, envío automático a clientes, autenticación por usuario, integración API real con clave válida y prueba de extremo a extremo en Streamlit, auditoría histórica individual de cada corriente, PDF modular por plan.
- Los documentos por contrato permanecen en el roadmap. No confundir el alcance de beta con entrega de producción o validación de seguridad.


## Actualización 2026-10-28 — Beta 1.0: interfaz y enlaces
- Programado: escritorio en cinco pestañas, enlace privado de siete días y un único uso, correos de invitación mediante MailApp con confirmación, botón de WhatsApp, recepción automática en hoja `Aclaraciones`, sin validación automática de la información recibida.
- Programado: integración opcional de IA con saldo/clave externa y costos estimados por tokens; el equipo sigue siendo director de arte.
- **Pendiente de activar:** copiar el script del repositorio al proyecto Apps Script, redeploy, configurar secretos y probar los endpoints en vivo.
- **Pendiente de implementar:** control de usuario por rol, registro histórico de aprobaciones, PDF por plan, límites mensuales reales de gasto, mensajes automáticos de WhatsApp.
- Referencia de instalación: `INSTALACION_BETA_1_0.md`.
