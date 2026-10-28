"""Aclaraciones: enlace privado de un solo uso; sin mostrar el briefing original."""
import json
import requests
import streamlit as st
from clarifications import validate_request, build_reply

st.set_page_config(page_title="Aclaraciones | PUENTE",page_icon="🌉",layout="centered")
st.markdown("""<style>.block-container{max-width:690px;padding-top:2rem}</style>""",unsafe_allow_html=True)
st.caption("PUENTE CREATIVE OS · ACLARACIONES")
st.title("Unos detalles para avanzar")
st.write("Gracias por compartir tu historia con Puente. Solo necesitamos aclarar algunas cosas; no tienes que completar nuevamente el briefing.")
try:
    webhook=st.secrets.get("SHEETS_WEBHOOK_URL","")
except (KeyError,FileNotFoundError):
    webhook=""
access_token=str(st.query_params.get("t","")).strip()
if access_token:
    if len(access_token)!=64 or any(x not in "0123456789abcdef" for x in access_token):
        st.error("Este enlace no es válido.")
        st.stop()
    if not webhook:
        st.error("Las aclaraciones en línea aún no están configuradas.")
        st.stop()
    try:
        response=requests.post(webhook,json={"action":"clarify_fetch","access_token":access_token},timeout=20)
        raw=response.text.strip()
        if raw in ("DENIED","EXPIRED","CLOSED"):
            st.warning("Este enlace ya no está disponible. Solicita uno nuevo al equipo de Puente.")
            st.stop()
        response.raise_for_status()
        data=response.json()
        if not data.get("ok") or not isinstance(data.get("questions"),list):
            raise ValueError("Respuesta inesperada")
    except (requests.RequestException,ValueError):
        st.error("No pudimos cargar las preguntas. Intenta nuevamente.")
        st.stop()
    st.subheader(data.get("brand","Tu marca"))
    st.caption("Enlace personal, válido por una única respuesta. Evita incluir información sensible o confidencial.")
    with st.form("online_clarifications"):
        answers=[]
        for i,q in enumerate(data["questions"],1):
            st.markdown("**"+str(i)+". "+q.get("pregunta","")+"**")
            value=st.text_area("Tu respuesta",key="web_"+access_token[:10]+"_"+str(i),
                placeholder="Cuéntanos con tus palabras. Si aún no lo sabes, escribe «Por definir».",
                max_chars=4000,height=100)
            answers.append({"id":q["id"],"respuesta":value.strip()})
        consent=st.checkbox("Autorizo que Agencia Puente revise estas respuestas para preparar mi proyecto.")
        done=st.form_submit_button("Enviar respuestas",type="primary",use_container_width=True)
    if done:
        if not consent:
            st.error("Necesitamos tu autorización para recibir estas respuestas.")
        elif any(not r["respuesta"] for r in answers):
            st.error("Responde cada pregunta o indica «Por definir».")
        else:
            try:
                r=requests.post(webhook,json={"action":"clarify_submit","access_token":access_token,"answers":answers},timeout=30)
                if r.text.strip()=="CLOSED":
                    st.warning("Este enlace ya fue utilizado o se cerró.")
                else:
                    r.raise_for_status()
                    result=r.json()
                    if not result.get("ok"):
                        raise ValueError("Respuesta inesperada")
                    st.success("¡Recibimos tus respuestas! El equipo de Puente las revisará.")
            except (requests.RequestException,ValueError):
                st.error("No logramos confirmar el envío. Conserva tus respuestas e inténtalo de nuevo.")
    st.stop()

# Modo de respaldo de Beta 0.9, solo con archivos JSON.
st.info("¿Recibiste una ficha JSON en vez de un enlace? Puedes responderla aquí. Los datos no se enviarán automáticamente.")
uploaded=st.file_uploader("Cargar preguntas compartidas por Puente",type=["json"])
if uploaded is None:
    st.stop()
if uploaded.size>100_000:
    st.error("El archivo supera los 100 KB.")
    st.stop()
try:
    question_set=validate_request(json.loads(uploaded.getvalue().decode("utf-8")))
except (ValueError,TypeError,UnicodeDecodeError):
    st.error("El archivo no tiene un formato válido.")
    st.stop()
st.subheader(question_set.get("marca") or "Tu marca")
with st.form("offline_answers"):
    entries={}
    for i,q in enumerate(question_set["preguntas"],1):
        st.markdown("**"+str(i)+". "+q["pregunta"]+"**")
        entries[q["id"]]=st.text_area("Tu respuesta",key="offline_"+str(i),max_chars=4000)
    authorized=st.checkbox("Autorizo a Puente a revisar estas respuestas.")
    submit=st.form_submit_button("Preparar respuestas")
if submit and authorized and all(x.strip() for x in entries.values()):
    st.session_state["clarifications_reply"]=build_reply(question_set,entries)
elif submit:
    st.warning("Responde todas las preguntas y marca la autorización.")
ready=st.session_state.get("clarifications_reply")
if ready and ready.get("submission_id")==question_set["submission_id"]:
    st.download_button("Descargar respuestas para Puente",data=json.dumps(ready,ensure_ascii=False,indent=2),
      file_name="puente-aclaraciones-"+question_set["submission_id"][:8]+".json",mime="application/json")
    st.caption("Comparte el archivo con Puente. Esta vía no guarda respuestas en línea.")
