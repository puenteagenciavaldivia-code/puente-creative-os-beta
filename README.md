# PUENTE Creative OS — Beta 1.1

Sistema experimental de Agencia Puente para recopilar briefings, detectar vacíos estratégicos, solicitar aclaraciones y preparar decisiones de dirección de arte con revisión humana.

## Interfaces
- `app.py`: briefing para cliente.
- `pages/01_Panel_interno.py`: escritorio interno en pestañas de Resumen, Aclaraciones, Dirección de arte, Producción y Documentos; incluye fichas individuales de producción con formatos exactos.
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

## Producción gráfica guiada

El módulo `graphic_production.py` genera fichas de pieza y encargos de diseño por formato. Los encargos solamente se habilitan tras resolver la auditoría y registrar la aprobación humana de una dirección de arte. La exportación no crea una imagen ni un arte final. Consultar [FLUJO_PRODUCCION_GRAFICA.md](FLUJO_PRODUCCION_GRAFICA.md).

## Próximos hitos
Autenticación individual, permisos de acceso, protección de datos de producción, integración probada de extremo a extremo y documentos PDF modulares según el plan comercial contratado. El historial básico de revisiones se habilita con el nuevo script, pero todavía no reemplaza una auditoría de seguridad.
# Dirección Creativa Primero — rama Creative OS 1.0

La continuación de persistencia está en `experiment/creative-os-1-decisions`. Para probar historial local con identidades **simuladas**:

```bash
streamlit run decision_demo.py
```

Usa exclusivamente fixtures. Guarda una versión, decide con dirección ficticia, abre otra sesión y consulta el historial. Operación ficticia puede guardar propuestas, pero no aprobarlas. La base queda en `.local/decision_demo.sqlite` (excluida de Git). El selector de identidad no es autenticación: no usar esta demo con datos reales ni exponerla como servicio.

Esta rama añade dossier profesional HTML/PDF y revisión creativa independiente de la producción. Para una demo local sin Google, claves ni clientes reales:

```bash
python -m pip install -r requirements.txt
streamlit run dossier_demo.py
```

Tres casos ficticios y sus dossiers están en `examples/`. El panel existente incorpora una pestaña **Dossier**, conservando sus controles de acceso. La demo no valida identidad real ni usa el backend. Las decisiones se guardan solo en sesión y pueden exportarse; no sustituyen auditoría durable.

Pruebas: `python -m unittest discover -s tests -v`.

Estado, evidencias y pendientes: [revisión de Creative OS 1.0](docs/CREATIVE_OS_1_REVISION.md). **No desplegado; 04.01 abierta.**
