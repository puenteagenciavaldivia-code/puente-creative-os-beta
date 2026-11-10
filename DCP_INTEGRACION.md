# DCP-02 — Dirección creativa primero (integración experimental)

**Estado: reconciliación experimental del PR #1 y la candidata OIDC; sin main ni despliegue.**

## Decisión de producto
El dossier creativo es un resultado completo y utilizable por un diseñador. La producción es opcional: `undecided` (sin producción), `manual`, `hybrid` o `ai`. Elegir una ruta NO autoriza producir ni publicar.

## Archivos
- `dossier_engine.py`: valida dos o tres propuestas diferenciadas, comparativa, registro de fuentes, dossier HTML preliminar e integridad por SHA-256.
- `creative_dossier_bridge.py`: conserva los nombres del PR, delegando al único `dossier_adapter.py`. `prepare_for_brief` exige ahora auditoría explícita. La importación verifica marca exacta y la aprobación requiere citas exactas del briefing.
- `dossier_ui.py`: única UI de dossier, usada por el Escritorio y la demo. `pages/03_Dossier_creativo.py` conserva la navegación del PR mediante un enlace al Escritorio, sin otro formulario de aprobación.
- `tests/test_dossier_integration.py`: pruebas negativas, rutas y bloqueos.

## Alcance real
Se resolvieron conflictos de motor, pruebas y CI conservando la implementación más completa de la candidata. No se migra una aprobación vieja automáticamente ni se publican recursos Google. El texto responsable de una revisión local no acredita identidad. Las decisiones protegidas utilizan DecisionStore con política del servidor; no llamar a la capa de compatibilidad para eludirla.

## Seguridad y exactitud
- El hash detecta cambios de contenido **pero NO verifica identidad ni constituye firma criptográfica**. El campo responsable es texto libre. Implementar roles/autenticación antes de producción real.
- La equivalencia de marca y corrientes se valida contra briefing/review; no reemplaza una revisión humana.
- El HTML es solo una maqueta textual inicial, no un moodboard curado. Las fuentes `unverified` se advierten, no se consideran aprobadas.
- La producción opcional requiere nuevas autorizaciones, control de derechos, textos y QA. Su flujo existente no se modifica.

## Pruebas e integración
Ejecutar desde raíz: `python -m unittest discover -s tests -v`.

El workflow general sustituye la segunda ejecución completa de DCP: una sola matriz Python 3.11/3.12 con Streamlit 1.67.0 y criptografía obligatoria. La dependencia del piloto requiere esa versión; no se declara que el login nuevo funcione en 1.40 ni que se haya actualizado el Mac histórico. No se instala ni cambia el entorno Mac probado anteriormente.

La rama experimental conserva ambos historiales Git. El PR #1 queda intacto; su CI verde anterior no equivale a validar esta conciliación. Evidencia local y límites actuales: `docs/CREATIVE_OS_1_REVISION.md`.

Antes de fusionar a `main`: revisar y ejecutar toda la suite real en la rama, prueba de integración de interfaz Streamlit, prueba de seguridad de aprobaciones e identidad, comprobar no regresión en briefing y Google Apps Script, y validar dossier real con director de arte. Fusión y despliegue son decisiones separadas.

## Estado del proyecto
Etapa 04.01 abierta. Etapa 04.02 no iniciada.
