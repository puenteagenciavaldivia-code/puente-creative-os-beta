# PUENTE Creative OS · 04.01 · Acta de evidencia y pendientes del receptor
Fecha de revisión: 2026-11-20. Estado: validación real de un ensayo sintético; cierre integral 04.01 NO autorizado.

## Fuentes comprobadas
- GitHub: rama `lab/0401-clasp`, basada en `audit/0401-native-and-streamlit-20261119`. El laboratorio conserva `receiver/Receiver.js`, `receiver/LabChecks.js`, `receiver/appsscript.json` y las pruebas Node.
- GitHub Actions: ejecución #11 verde en rama de auditoría, mostrada por el operador; corresponde a los 28 tests del motor, 14 de adjuntos del cliente y 3 de Streamlit.
- Codex informó 17 pruebas Node y suite Python de 224 casos aprobados. Estas cantidades pertenecen a su informe de ejecución; no son pruebas reales de concurrencia Google.
- Evidencia visual facilitada por el operador el 2026-11-20: proyecto GAS aislado con `LabChecks.gs`, `Receiver.gs` y servicio avanzado Drive; registro de `runSyntheticLab0401` con `test_pass_independent_submission`, `test_pass_revoked_replay`, `test_pass_drive_file_count` y `Se completó la ejecución`. La captura no incluye los diez códigos completos ni una exportación íntegra de logs.
- El ejecutor `runSyntheticLab0401` realiza 10 comprobaciones y retorna `PASS: 10 checks; see execution logs` si las diez pasan. La ejecución de Apps Script finalizó, lo que permite inferir que no saltó una excepción; no sustituye el respaldo íntegro del registro.

## Resultado observado
1. Creación y subida de 3 fuentes en un proyecto nuevo mediante `clasp`: comprobada por captura Terminal.
2. Ejecución editor-only sobre servicios reales de Apps Script/Drive: completada sin error visible.
3. Rechazo de credencial incorrecta, consentimiento no otorgado, contenido alterado; escritura inicial, replay, interrupción sintética tras crear, recuperación, envíos independientes, revocación, recuento de archivos: definidas por `LabChecks.js`. La captura muestra éxito explícito de los controles finales; consolidar log completo para certificar 10/10 de forma documental.
4. Se crearon **tres proyectos de laboratorio** al ejecutar repetidamente `create-lab.mjs`. Solo el último se utilizó para la ejecución presentada; los dos anteriores requieren inventario y eliminación autorizada, sin tocar proyectos históricos.

## Límites y riesgos no cerrados
| Control | Estado | Evidencia de cierre requerida |
| --- | --- | --- |
| Reintento secuencial e interrupción sintética | Ejecutado en Google | Exportar log completo y cotejar conteo e IDs sin publicar datos sensibles |
| Concurrencia real de dos invocaciones independientes | PENDIENTE | Dos ejecuciones paralelas contra el mismo envío y clave; una reserva/un archivo, resultados OK/RETRY y reconciliación |
| Timeout de red real y reconexión del cliente Streamlit | PENDIENTE | Ensayo privado de transporte; confirmar un archivo en Drive tras pérdida de confirmación |
| Autorización de submission real y revocación de consentimiento | PENDIENTE | Integración confiable de altas/revocaciones en servidor; no aceptar solo consentimiento enviado por cliente |
| Separación multioperador, rol y ámbito por cliente | PENDIENTE | Matriz de acceso con dos identidades sintéticas y prueba cruzada de lectura/escritura/denegación |
| Cuotas Script Properties, Drive y tiempos límite | PENDIENTE | Carga escalonada, alertas, recuperación y política de retención |
| Seguridad del transporte y despliegue | NO AUTORIZADO | Análisis de riesgo y revisión antes de habilitar web app; no publicar URL/secretos |
| Limpieza de proyectos duplicados y carpeta sintética | PENDIENTE | Verificar IDs, aprobación de eliminación y respaldo de resultados |

## Decisión de ingeniería
- **Aprobación parcial:** implementación aislada y ensayo real sintético con finalización satisfactoria.
- **No afirmar:** exactamente-una-vez de extremo a extremo en producción, permiso multioperador resuelto, receptor conectado a briefings reales o cierre de 04.01.
- No modificar `main`, no hacer merge, no reutilizar GAS-AUTH01/GAS-AUDIT01, no cargar datos reales, no repetir `runSyntheticLab0401` sobre el proyecto ya usado.
- Próximo bloque seguro: diseñar el ensayo de concurrencia y timeout para un **cuarto proyecto nuevo**, con validación previa de permisos y control de limpieza; no ejecutar ni desplegar sin autorización expresa.
