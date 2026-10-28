"""Cliente: respuesta complementaria aislada de la ficha principal."""
import json
import streamlit as st
from clarifications import validate_request, build_reply

st.set_page_config(page_title="Aclaraciones | Puente Creative OS",page_icon="🌉",layout="centered")
st.caption("PUENTE CREATIVE OS · FORMULARIO COMPLEMENTARIO")
st.title("Nos faltan algunos detalles")
st.write("Tu negocio ya tiene un briefing registrado. Este formulario permite responder solo algunas preguntas adicionales, sin empezar de nuevo.")
st.info("Beta experimental: evita datos personales sensibles, financieros o confidenciales. Las respuestas solo se descargan en tu dispositivo y debes compartir el archivo con Puente por un medio acordado.")
upload=st.file_uploader("Carga la ficha de preguntas que te compartió Puente (JSON)",type=["json"])
if upload is None:
    st.stop()
if upload.size>100_000:
    st.error("La ficha supera el límite de 100 KB.")
    st.stop()
try:
    request=validate_request(json.loads(upload.getvalue().decode("utf-8")))
except (ValueError,TypeError,UnicodeDecodeError):
    st.error("No podemos leer esta ficha. Solicita una nueva a Puente.")
    st.stop()
st.subheader(request.get("marca") or "Tu marca")
st.write(request.get("instrucciones",""))
with st.form("answers"):
    entries={}
    for i,question in enumerate(request["preguntas"],1):
        qid=question["id"]
        st.markdown("**"+str(i)+". "+question["pregunta"]+"**")
        entries[qid]=st.text_area("Tu respuesta",height=95,
                                  placeholder="Responde con tus palabras. Si no sabes, puedes escribir «Necesito ayuda».",
                                  key="clarify_"+request["submission_id"]+"_"+qid)
    confirmed=st.checkbox("Confirmo que mis respuestas pueden ser revisadas por Agencia Puente para este briefing.")
    submitted=st.form_submit_button("Preparar respuestas",type="primary")
if submitted:
    if not confirmed:
        st.error("Necesitamos tu autorización para continuar.")
    elif any(not value.strip() for value in entries.values()):
        st.error("Responde cada pregunta o escribe «Necesito ayuda» si todavía no puedes definirla.")
    else:
        st.session_state["clarifications_reply"]=build_reply(request,entries)
        st.success("¡Gracias! Tus respuestas están preparadas.")
reply=st.session_state.get("clarifications_reply")
if reply and reply.get("submission_id")==request["submission_id"]:
    st.download_button("Descargar respuestas para Puente (JSON)",
        data=json.dumps(reply,ensure_ascii=False,indent=2),
        file_name="puente-aclaraciones-"+request["submission_id"][:8]+".json",
        mime="application/json")
    st.caption("Después de descargarlo, comparte el archivo con el equipo de Puente. Este formulario no envía ni guarda automáticamente tus respuestas.")
