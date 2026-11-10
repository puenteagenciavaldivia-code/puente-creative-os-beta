"""PUENTE Creative OS — Dossier creativo autónomo (beta experimental).
La app no genera imágenes, no envía datos a IA ni autoriza producción.
"""
import json
import hmac
import streamlit as st
from strategic_audit import audit_briefing
from creative_dossier_bridge import prepare_for_brief, finalize_from_review, deliver_creative
from dossier_engine import validate_dossier, dossier_html

st.set_page_config(page_title="Dossier creativo | PUENTE",page_icon="🎨",layout="wide")
st.title("Dirección creativa · Dossier profesional")
st.caption("Tu dirección creativa es el entregable principal. Diseñar y producir con IA es opcional.")

# Mantener control coherente con el panel interno; no enviar información a servicios externos.
try:
    required_password=st.secrets.get("ADMIN_PANEL_PASSWORD","")
except (KeyError,FileNotFoundError):
    required_password=""
if not required_password:
    st.error("No está configurada la protección del panel.")
    st.stop()
if not st.session_state.get("puente_admin_ok",False):
    st.warning("Inicia sesión primero en el Escritorio creativo.")
    st.stop()

items=st.session_state.get("admin_items") or []
if not items:
    st.info("Primero carga tus briefings en el Escritorio creativo. Esta vista no consulta credenciales ni APIs.")
    st.stop()

options={str(x.get("submission_id")):x for x in items if x.get("submission_id")}
sid=st.selectbox("Marca / briefing",list(options),format_func=lambda k:str(options[k].get("brand") or "Sin nombre")+" · "+k[:8])
selected=options[sid]
record={"submission_id":sid,"answers":selected.get("answers") or {},
        "diagnostic":selected.get("diagnostic") or {}}
diagnostic=record["diagnostic"]
audit=diagnostic.get("strategic_audit")
if not isinstance(audit,dict):
    audit=audit_briefing(record["answers"],diagnostic)
review=st.session_state.get("puente_review_"+sid)
if not isinstance(review,dict):
    st.warning("Abre este briefing en el Escritorio creativo y completa primero su revisión de dirección de arte.")
    st.stop()

st.markdown("### 1. Importar propuesta desarrollada")
st.write("Importa el dossier estructurado preparado y revisado por el equipo. No se realizan llamadas automáticas a IA.")
uploaded=st.file_uploader("Dossier JSON",type=["json"],key="dossier_json_"+sid)
if uploaded is not None and st.button("Validar propuesta",type="primary"):
    try:
        raw=uploaded.getvalue()
        if len(raw)>250000:raise ValueError("Dossier demasiado grande (máximo 250 KB).")
        parsed=json.loads(raw.decode("utf-8-sig"))
        package=prepare_for_brief(record,parsed)
        st.session_state["dcp_package_"+sid]=package
    except (UnicodeError,ValueError,TypeError,json.JSONDecodeError) as exc:
        st.error("No fue posible validar el dossier: "+str(exc))

package=st.session_state.get("dcp_package_"+sid)
if not package:
    st.info("Importa un dossier para visualizar las alternativas. La producción no es necesaria para cerrar el trabajo.")
    st.stop()

validation=validate_dossier(package["dossier"])
if validation["errors"]:
    st.error("El dossier presenta errores: "+"; ".join(validation["errors"]))
    st.stop()
if validation["warnings"]:
    st.warning("Observaciones por verificar: "+"; ".join(validation["warnings"]))
st.success("Estructura del dossier válida. Falta aprobar la dirección creativa.")

dossier=package["dossier"]
st.markdown("### 2. Comparar alternativas")
for direction in dossier["directions"]:
    with st.expander(str(direction["name"]),expanded=False):
        st.markdown("**Idea principal:** "+str(direction["big_idea"]))
        st.write("Fundamento:",direction["insight"])
        st.write("Sistema visual:",direction["visual_system"])
        st.write("Fotografía:",direction["photography"])
        st.write("Tipografía:",direction["typography"])
        st.write("Diferenciación:",direction["differentiation"])
        st.write("Riesgos:",direction["risks"])
st.info("Recomendación del dossier: "+str(dossier["comparison"]["recommendation"])+". La decisión válida es la registrada por Puente.")

st.markdown("### 3. Aprobar y entregar la dirección creativa")
st.caption("Se utiliza la revisión humana de Dirección de arte. No se exige autorización de producción.")
if st.button("Verificar aprobación creativa",key="approve_dcp_"+sid):
    try:
        approved=finalize_from_review(package,record,audit,review)
        st.session_state["dcp_approved_"+sid]=approved
        st.success("Dirección creativa validada con la revisión de Puente.")
    except (ValueError,TypeError,KeyError) as exc:
        st.error("No es posible aprobar la entrega: "+str(exc))

approved=st.session_state.get("dcp_approved_"+sid)
if approved:
    if approved.get("hash")!=package.get("hash") or approved.get("source_briefing_hash")!=package.get("source_briefing_hash"):
        st.session_state.pop("dcp_approved_"+sid,None)
        st.warning("La propuesta cambió. Revisa nuevamente la dirección.")
        st.stop()
    route_labels={"undecided":"Entregar solo dirección creativa (sin producción)",
      "manual":"Entregar para diseño propio / Photoshop / Illustrator",
      "hybrid":"Solicitar alcance de producción híbrida",
      "ai":"Solicitar alcance de producción con IA"}
    route=st.selectbox("Destino posterior (opcional)",list(route_labels),
      format_func=lambda x:route_labels[x],key="dcp_route_"+sid)
    try:
        output=deliver_creative(approved,route)
        st.download_button("Descargar dossier HTML imprimible",
            dossier_html(dossier),file_name="puente-dossier-"+sid[:12]+".html",mime="text/html")
        st.download_button("Descargar respaldo aprobado JSON",
            json.dumps({"approval":approved["creative_approval"],"handoff":output,
                        "dossier":dossier},ensure_ascii=False,indent=2),
            file_name="puente-dossier-"+sid[:12]+".json",mime="application/json")
        if route in ("ai","hybrid"):
            st.warning("Ruta solicitada; todavía falta autorizar el alcance y la producción por separado.")
        else:
            st.success("Puedes cerrar el trabajo con el dossier. No necesitas producir piezas con IA.")
    except (ValueError,TypeError,KeyError) as exc:
        st.error("La entrega se encuentra bloqueada: "+str(exc))

st.caption("Beta: autenticación compartida no apta para datos sensibles. Documento demostrativo, no arte final.")
