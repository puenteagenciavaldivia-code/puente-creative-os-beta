# DCP-02 — Dirección creativa primero (integración experimental)

**Estado: rama experimental; PR borrador; sin despliegue.**

## Decisión de producto
El dossier creativo es un resultado completo y utilizable por un diseñador. La producción es opcional: `undecided` (sin producción), `manual`, `hybrid` o `ai`. Elegir una ruta NO autoriza producir ni publicar.

## Archivos
- `dossier_engine.py`: valida dos o tres propuestas diferenciadas, comparativa, registro de fuentes, dossier HTML preliminar e integridad por SHA-256.
- `creative_dossier_bridge.py`: conecta el dossier con el briefing y `review_workflow.validate_review` sin exigir `autorizacion_produccion`.
- `tests/test_dossier_integration.py`: pruebas negativas, rutas y bloqueos.

## Alcance real
No altera Streamlit, revisión existente, producción gráfica, Apps Script, Google Sheets, credenciales ni el despliegue. El módulo es importable por la aplicación cuando se valide la interfaz. No hay un botón habilitado ni un dossier publicable automáticamente.

## Seguridad y exactitud
- El hash detecta cambios de contenido **pero NO verifica identidad ni constituye firma criptográfica**. El campo responsable es texto libre. Implementar roles/autenticación antes de producción real.
- La equivalencia de marca y corrientes se valida contra briefing/review; no reemplaza una revisión humana.
- El HTML es solo una maqueta textual inicial, no un moodboard curado. Las fuentes `unverified` se advierten, no se consideran aprobadas.
- La producción opcional requiere nuevas autorizaciones, control de derechos, textos y QA. Su flujo existente no se modifica.

## Pruebas e integración
Ejecutar desde raíz: `python -m unittest discover -s tests -v`.

Antes de fusionar a `main`: revisar y ejecutar toda la suite real en la rama, prueba de integración de interfaz Streamlit, prueba de seguridad de aprobaciones e identidad, comprobar no regresión en briefing y Google Apps Script, y validar dossier real con director de arte. Fusión y despliegue son decisiones separadas.

## Estado del proyecto
Etapa 04.01 abierta. Etapa 04.02 no iniciada.
