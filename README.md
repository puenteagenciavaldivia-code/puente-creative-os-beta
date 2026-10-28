# PUENTE Creative OS — Beta 1.0

Sistema experimental de Agencia Puente para recopilar briefings, detectar vacíos estratégicos, solicitar aclaraciones y preparar decisiones de dirección de arte con revisión humana.

## Interfaces
- `app.py`: briefing para cliente.
- `pages/01_Panel_interno.py`: escritorio interno en pestañas de Resumen, Aclaraciones, Dirección de arte, Producción y Documentos.
- `pages/02_Aclaraciones.py`: respuestas complementarias desde enlaces de un solo uso y vencimiento, o respaldo por archivo JSON.

## Integraciones
- Google Apps Script + Google Sheets: briefings recibidos y, **después de actualizar la implementación**, aclaraciones en `Aclaraciones` y versiones de aprobaciones en `Revisiones`.
- MailApp: envío de correos por acción explícita del equipo.
- WhatsApp: abre la interfaz de compartir, sin envío automático.
- **Investigación creativa en ChatGPT (sin API)**: el panel prepara un encargo con briefing y metodología, y permite importar tres propuestas justificadas mediante JSON. La dirección de arte se aprueba exclusivamente por el equipo.
- El código experimental de API sigue separado en `ai_art_direction.py`, pero **no hay ningún botón que llame a la API en el panel de esta fase**.

**No se deben subir datos personales sensibles ni información privada de clientes durante esta beta**. El control de acceso compartido y la revisión de seguridad no son adecuados todavía para un lanzamiento comercial.

## Implementación
Leer primero [INSTALACION_BETA_1_0.md](INSTALACION_BETA_1_0.md). El código de Apps Script en GitHub **no actualiza** por sí mismo la implementación ya publicada: necesita nueva versión y configuración de secretos.

Para ejecutar pruebas: `python -m unittest discover -s tests -v`. También existe una opción dentro del panel protegido.

## Investigación creativa
Consultar [METODO_DIRECCION_ARTE.md](METODO_DIRECCION_ARTE.md). La biblioteca es inicial y no equivale a un estudio exhaustivo de todos los libros ni movimientos. El director de arte aprueba o rechaza las alternativas.

## Próximos hitos
Autenticación individual, permisos de acceso, protección de datos de producción, integración probada de extremo a extremo y documentos PDF modulares según el plan comercial contratado. El historial básico de revisiones se habilita con el nuevo script, pero todavía no reemplaza una auditoría de seguridad.
