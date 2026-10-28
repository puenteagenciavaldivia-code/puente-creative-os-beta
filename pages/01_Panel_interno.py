import hmac
import json
import requests
import streamlit as st

st.set_page_config(page_title="Panel interno | PUENTE Creative OS", page_icon="🌉", layout="wide")
st.title("PUENTE · Panel interno")
st.caption("Briefings recibidos · Acceso exclusivo para el equipo de Agencia Puente")

try:
    panel_password=st.secrets.get("ADMIN_PANEL_PASSWORD","")
    read_token=st.secrets.get("ADMIN_READ_TOKEN","")
    url=st.secrets.get("SHEETS_WEBHOOK_URL","")
except (FileNotFoundError,KeyError):
    panel_password=read_token=url=""

if not panel_password or not read_token or not url:
    st.error("Panel no configurado. Faltan ADMIN_PANEL_PASSWORD, ADMIN_READ_TOKEN o SHEETS_WEBHOOK_URL en Secrets.")
    st.stop()

if not st.session_state.get("puente_admin_ok",False):
    with st.form("admin_login"):
        entered=st.text_input("Contraseña del panel",type="password")
        submitted=st.form_submit_button("Entrar",type="primary")
    if submitted:
        if hmac.compare_digest(entered,panel_password):
            st.session_state.puente_admin_ok=True
            st.rerun()
        else:
            st.error("Contraseña incorrecta.")
    st.stop()

with st.sidebar:
    st.success("Acceso interno")
    if st.button("Cerrar sesión"):
        st.session_state.puente_admin_ok=False
        st.session_state.pop("admin_items",None)
        st.rerun()
    st.caption("Beta: usa solo información de prueba hasta completar la revisión de seguridad.")

def get_data():
    try:
        response=requests.post(url,json={"action":"admin_list","admin_token":read_token},timeout=30)
        response.raise_for_status()
        if response.text.strip()=="DENIED":
            raise RuntimeError("El receptor rechazó el token de lectura.")
        if response.text.strip()=="ERROR":
            raise RuntimeError("Google Apps Script devolvió un error.")
        data=response.json()
        if not isinstance(data.get("items"),list):
            raise ValueError("Respuesta de datos inesperada.")
        return data["items"]
    except (requests.RequestException,ValueError,RuntimeError) as exc:
        st.error(f"No fue posible consultar los briefings: {str(exc)}")
        return None

if st.button("Actualizar registros",type="primary") or "admin_items" not in st.session_state:
    result=get_data()
    if result is not None:
        st.session_state.admin_items=result

items=st.session_state.get("admin_items",[])
if not items:
    st.info("Aún no hay registros disponibles o no se cargaron. Puedes pulsar «Actualizar registros».")
    st.stop()

with st.container():
    c1,c2,c3=st.columns(3)
    c1.metric("Briefings visibles",len(items))
    c2.metric("Aptos para revisión",sum(x.get("status")=="apto_para_revision" for x in items))
    c3.metric("Con adjuntos",sum(bool(x.get("attachments")) for x in items))

query=st.text_input("Buscar marca",placeholder="Nombre de la marca")
filtered=[x for x in items if query.lower().strip() in str(x.get("brand","")).lower()]
if not filtered:
    st.info("No se encontraron marcas que coincidan.")
    st.stop()

names=[f"{x.get('brand','Sin nombre')} · {x.get('submitted_at','')[:16]} · {x.get('submission_id','')[:8]}" for x in filtered]
chosen=filtered[st.selectbox("Seleccionar briefing",range(len(filtered)),format_func=lambda i:names[i])]
st.divider()
st.subheader(chosen.get("brand") or "Sin nombre")
left,right=st.columns(2)
left.write("**Estado:** "+str(chosen.get("status") or "Sin estado"))
right.write("**Suficiencia:** "+str(chosen.get("score",0))+"/100")
st.caption("Diagnóstico preliminar por completitud de respuestas. Requiere revisión estratégica humana.")

answers=chosen.get("answers") or {}
if isinstance(answers,dict):
    st.markdown("### Respuestas del cliente")
    for key,value in answers.items():
        if value not in (None,"",[]):
            st.markdown("**"+str(key).replace("_"," ").capitalize()+"**")
            st.write(", ".join(map(str,value)) if isinstance(value,list) else str(value))

links=chosen.get("attachments") or []
st.markdown("### Archivos adjuntos")
if links:
    for index,link in enumerate(links,1):
        if link.startswith("https://drive.google.com/"):
            st.link_button(f"Abrir adjunto {index} en Drive",link)
else:
    st.caption("Este briefing no tiene enlaces a archivos adjuntos registrados.")

diag=chosen.get("diagnostic") or {}
with st.expander("Ver diagnóstico técnico"):
    st.json(diag)

record={"submission_id":chosen.get("submission_id"),"submitted_at":chosen.get("submitted_at"),"answers":answers,"diagnostic":diag,"attachments":links}
st.download_button("Exportar este briefing (JSON)",data=json.dumps(record,ensure_ascii=False,indent=2),file_name="briefing-interno.json",mime="application/json")
