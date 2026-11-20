# PUENTE Creative OS 04.01 — Puerta de cierre técnico

Estado al 2026-11-20: **NO APTO PARA CIERRE DEFINITIVO**. No significa que las pruebas existentes hayan fallado: significa que faltan verificaciones de integración y evidencia independiente.

## Aprobaciones observadas
- GitHub Actions #11: usuario mostró ejecución verde de 45 tests en rama de auditoría (28 motor, 14 adjuntos, 3 Streamlit).
- Google Apps Script: usuario mostró `runSyntheticLab0401` completada, con logs de las últimas comprobaciones; recolección íntegra de los diez resultados pendiente.
- Codex: informó 17 pruebas Node en un estado anterior; se agregaron pruebas posteriores y el nuevo CI necesita lectura de los resultados.

## Componentes nuevos preparados, NO integrados en producción
- `access-policy.mjs`: permisos por rol y cliente, solo sobre estados de servidor.
- `upload-gateway.mjs`: obtiene identidad y membresías a través de interfaces inyectadas confiables; NO valida OIDC real.
- `secure-upload-dispatch.mjs`: verifica el permiso antes de intentar transporte privado y no convierte timeout en éxito; NO hay endpoint ni transporte real configurados.
- `receiver/Receiver.js`: receptor GAS aislado con token de servicio y permisos sintéticos persistidos; NO conoce el rol del usuario final.
- Los tests usan identidades ficticias y servicios simulados; ejecutar CI no equivale a validar seguridad de cuentas reales.

## Criterios obligatorios antes de firma
| Clave | Condición demostrable | Evidencia requerida | Estado |
| --- | --- | --- | --- |
| G01 | Suite del repositorio y CI Node del laboratorio verdes para último commit | Link al run + logs completos | PENDIENTE para rama lab |
| G02 | 10 checks GAS enumerados y log completo archivado | Registro íntegro, sin secretos | PARCIAL |
| G03 | Dos invocaciones realmente independientes sobre mismo `submission_id` y key | Identidad de archivo única, respuestas y reconciliación, timestamp | PENDIENTE |
| G04 | Corte real de transporte posterior a escritura y reintento desde Streamlit | Un solo archivo de Drive, confirmación persistente | PENDIENTE |
| G05 | OIDC real: firma, issuer, audience, expiración, sujeto, revocación | Evidencia del proveedor autorizado y pruebas negativas | PENDIENTE |
| G06 | Vinculación real con briefing, consentimiento, clientId y roles del servidor | Dos operadores sintéticos, permisos cruzados y revocación | PENDIENTE |
| G07 | Límites de cuotas, retención, logging y error handling | Ensayos de carga y política documentada | PENDIENTE |
| G08 | Inventario y limpieza autorizada de proyectos sintéticos duplicados | IDs verificados, decisión y ejecución documentada | PENDIENTE |
| G09 | Dictamen técnico firmado para 04.01 y plan 04.02 | Informe de auditoría con riesgos residuales | PENDIENTE |

## Decisiones de seguridad
- `main` no se modifica ni se fusionan ramas sin aprobación formal.
- No publicar una implementación web de Google Apps Script ni reusar GAS-AUTH01/GAS-AUDIT01 históricos.
- No subir archivos de clientes ni guardar secretos en repositorio/logs/chat.
- La comprobación de permisos debe repetirse en el servidor responsable de escribir el archivo, no solo en la puerta previa; entre autorización y escritura puede ocurrir revocación (TOCTOU).
- La opción de cierre alternativo sería **cerrar el laboratorio experimental** con sus límites expresos y mantener **04.01 abierta** para integración real. No equivale a declarar 04.01 cerrada.

## Continuación recomendada sin intervención manual
1. Confirmar y corregir CI de rama `lab/0401-clasp`; obtener logs íntegros.
2. Ejecutar pruebas locales de componentes y del protocolo de transporte sin credenciales reales.
3. Preparar especificación de OIDC y módulo de permisos con fuente confiable; solicitar credenciales/usuarios de prueba solo en entorno protegido cuando corresponda.
4. Preparar procedimiento para ensayos G03 y G04 sin despliegue público, definiendo previamente identidad del proyecto nuevo, desecho, cuotas, permisos, autorización y evidencia.

El cierre se permite únicamente cuando G01–G09 tienen respaldo real o una dispensa técnica explícita y aprobada, sin afirmar coberturas que no fueron ensayadas.

## Avance: verificación criptográfica OIDC/JWT (2026-11-20)

- Se incorporaron `oidc-verifier.mjs` y `oidc-verifier.test.mjs`: firma RS256 comprobada con clave pública JWK fijada desde configuración de servidor, `issuer`, `audience`, sujeto, `exp`, `iat`, `nbf`, `azp` en audiencias múltiples, rechazo de claves remotas indicadas por cabecera y de algoritmos alternativos.
- **8/8 pruebas locales Node 22 pasaron** en entorno sintético independiente, con claves RSA efímeras. Los archivos de pruebas quedaron publicados en GitHub. La ejecución de GitHub Actions del último commit **continúa por verificar**.
- La configuración no incluye proveedor real, credenciales ni conexión con `upload-gateway.mjs`, Google ni usuarios de Puente. G05 y G06 **siguen pendientes**. También queda pendiente la política operativa de rotación/descarga segura de JWKS del proveedor, validación real de tokens y revocación.
- El módulo es RS256 estricto: debe comprobarse que la autoridad OIDC elegida use ese algoritmo y los claims de identidad requeridos; no aceptarlo como adaptación universal.
