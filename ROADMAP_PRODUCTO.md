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
