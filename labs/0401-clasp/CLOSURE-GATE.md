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
