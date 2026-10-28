import json
import base64
import re
import uuid
import requests
from datetime import datetime, timezone
import streamlit as st

st.set_page_config(page_title="PUENTE Creative OS | Beta 0.1", page_icon="🌉", layout="centered")
st.markdown("""<style>.block-container{max-width:780px;padding-top:2rem}h1{letter-spacing:-.04em}</style>""",unsafe_allow_html=True)
SECTIONS=[
("Identidad",[
("nombre","¿Cómo se llama tu marca?","text"),
("negocio","¿Qué hace tu negocio?","area"),
("personalidad","¿Qué características describen a tu marca?","area"),
("recuerdo","¿Cómo te gustaría que la recordaran?","area")]),
("Negocio",[
("productos","¿Cuáles son tus productos o servicios?","area"),
("diferencia","¿Por qué te eligen frente a otras alternativas?","area"),
("destacar","¿Qué aspecto de tu negocio quieres destacar?","area"),
("competencia","¿Qué marcas son referentes o competidores?","area")]),
("Público",[
("publico","¿Quiénes te compran actualmente?","area"),
("publico_nuevo","¿A quiénes quisieras llegar?","area"),
("dudas","¿Qué dudas tienen las personas antes de elegirte?","area"),
("tono","¿Cómo te gustaría hablar con tus clientes?","tone")]),
("Universo visual",[
("identidad_visual","¿Ya cuentas con una identidad visual?","visual"),
("elementos","¿Qué elementos visuales deben mantenerse?","area"),
("referentes","¿Qué marcas o diseños te gustan y por qué?","area"),
("evitar","¿Qué estilos o elementos quisieras evitar?","area")]),
("Objetivos y producción",[
("objetivo","¿Qué te gustaría conseguir con la comunicación?","goal"),
("canales","¿Qué canales utilizas?","channels"),
("materiales","¿Qué fotografías, videos o archivos tienes?","area"),
("condiciones","¿Hay fechas o condiciones importantes?","area")])]
OPTIONS={
"tone":["Cercano","Profesional","Didáctico","Divertido","Sereno","Aún no lo sé"],
"visual":["Sí, tenemos manual de marca","Tenemos logo, pero no manual","No tenemos identidad visual"],
"goal":["Aumentar ventas","Conseguir consultas","Dar a conocer mi marca","Fidelizar clientes","Educar al público","Aún no lo sé"],
"channels":["Instagram","Facebook","WhatsApp","TikTok","Web","Google","Otros"]}
WEIGHTS={"identidad":15,"propuesta_de_valor":20,"audiencia":15,"objetivos":20,"visual":15,"diferenciacion":10,"operacion":5}
DIMENSIONS={
"identidad":["nombre","negocio","personalidad","recuerdo"],
"propuesta_de_valor":["productos","diferencia","destacar"],
"audiencia":["publico","publico_nuevo","dudas","tono"],
"objetivos":["objetivo","canales"],
"visual":["identidad_visual","elementos","referentes"],
"diferenciacion":["competencia","evitar"],
"operacion":["materiales","condiciones"]}
def diagnose(a):
    scores={}
    total=0
    for dim,fields in DIMENSIONS.items():
        filled=sum(bool(a.get(k)) for k in fields)
        score=round(5*filled/len(fields),2)
        scores[dim]=score
        total+=score*WEIGHTS[dim]/5
    flags=[]
    for field in ["diferencia","publico","objetivo"]:
        val=str(a.get(field,"")).strip().lower()
        if val in ["buena calidad","somos los mejores","todo el mundo","somos diferentes","crecer"]:
            flags.append({"field":field,"issue":"Respuesta demasiado general","quote":a[field]})
    if a.get("identidad_visual")=="No tenemos identidad visual":
        flags.append({"field":"identidad_visual","issue":"Identidad visual por definir"})
    status="apto_para_revision" if total>=80 and not flags else ("insuficiente" if total<60 else "requiere_aclaracion")
    return {"score":round(total,1),"dimension_scores":scores,"flags":flags,"status":status,"human_review_required":True,"approved":False,"engine":"deterministic_beta_0_1"}
# Streamlit removes widget state when the widget is absent from a rerun.
# Keep form data separately so navigating between steps does not erase prior answers.
if "answers_store" not in st.session_state: st.session_state.answers_store={}
def save_visible_page():
    for key,_,_ in SECTIONS[st.session_state.step][1]:
        if key in st.session_state:
            value=st.session_state[key]
            st.session_state.answers_store[key]="" if value=="Selecciona una opción" else value
    for key in ("autorizacion","accion"):
        if key in st.session_state:
            st.session_state.answers_store[key]=st.session_state[key]
def restore_widget(key):
    if key not in st.session_state and key in st.session_state.answers_store:
        st.session_state[key]=st.session_state.answers_store[key]
if "step" not in st.session_state:st.session_state.step=0
if "finished" not in st.session_state:st.session_state.finished=False
if "attachments_store" not in st.session_state: st.session_state.attachments_store=[]
st.caption("AGENCIA PUENTE · CREATIVE OS · BETA PRIVADA")
st.title("Descubramos tu marca.")
st.write("Este cuestionario busca conocer tu negocio para probar nuestro sistema creativo. Responde con tus palabras, sin necesidad de conocimientos de diseño.")
try:
    SHEETS_URL=st.secrets.get("SHEETS_WEBHOOK_URL","")
    SHEETS_TOKEN=st.secrets.get("SHEETS_WEBHOOK_TOKEN","")
except (FileNotFoundError, KeyError):
    SHEETS_URL=""
    SHEETS_TOKEN=""
storage_enabled=bool(SHEETS_URL and SHEETS_TOKEN)
if storage_enabled:
    st.info("Prueba beta: si aceptas participar y finalizas, tus respuestas se enviarán a una hoja privada de Agencia Puente para evaluar el formulario. Evita datos personales sensibles o información confidencial.")
else:
    st.warning("Prueba experimental: todavía no hay recepción automática. Al finalizar tendrás que descargar el archivo y compartirlo manualmente. No ingreses información confidencial.")
if not st.session_state.finished:
    p=st.session_state.step
    st.progress((p+1)/5)
    st.subheader(f"{p+1}/5 · {SECTIONS[p][0]}")
    for key,label,kind in SECTIONS[p][1]:
        restore_widget(key)
        if kind=="text": st.text_input(label,key=key)
        elif kind=="area":st.text_area(label,key=key,height=90)
        elif kind=="channels":st.multiselect(label,OPTIONS[kind],key=key)
        else:st.selectbox(label,["Selecciona una opción"]+OPTIONS[kind],key=key)
    if p==3 and st.session_state.get("identidad_visual") in OPTIONS["visual"][:2]:
        restore_widget("autorizacion")
        st.selectbox("¿Puedes compartir archivos gráficos autorizados?",["Selecciona una opción","Sí","Debo confirmar","No"],key="autorizacion")
    if p==3:
        st.markdown("#### Archivos de tu marca (opcional)")
        st.caption("PNG, JPG, WEBP o PDF. Máximo 3 MB por archivo y 5 archivos. No incluyas datos personales sensibles.")
        uploaded=st.file_uploader("Adjunta logotipos, fotografías o referencias",type=["png","jpg","jpeg","webp","pdf"],accept_multiple_files=True,key="brand_uploads")
        if uploaded:
            if len(uploaded)>5 or any(x.size>3*1024*1024 for x in uploaded):
                st.error("Se permiten hasta 5 archivos de máximo 3 MB cada uno. Ajusta los adjuntos antes de continuar.")
            else:
                st.session_state.attachments_store=[{"name":x.name,"mime":x.type,"data":base64.b64encode(x.getvalue()).decode("ascii")} for x in uploaded]
        if st.session_state.attachments_store:
            st.caption(f"{len(st.session_state.attachments_store)} archivo(s) preparados para enviar al finalizar.")
        st.checkbox("Confirmo que tengo permiso para compartir estos archivos con Agencia Puente para evaluar este briefing.",key="files_consent")
    if p==4:
        restore_widget("accion")
        st.selectbox("¿Qué acción quieres que haga alguien después de ver una publicación?",["Selecciona una opción","Consultar","Comprar","Reservar","Visitar el local","Seguir la marca","No lo sé"],key="accion")
        st.checkbox("Acepto participar voluntariamente en esta prueba.",key="consent")
    required_by_step=[
        ["nombre","negocio"],
        ["productos","diferencia"],
        ["publico"],
        ["identidad_visual"],
        ["objetivo","canales"]
    ]
    missing=[k for k in required_by_step[p] if not st.session_state.get(k) or st.session_state.get(k)=="Selecciona una opción"]
    if missing:
        st.caption("Completa las preguntas esenciales para avanzar; las demás son opcionales.")
    left,right=st.columns(2)
    with left:
        if st.button("← Volver",disabled=p==0,use_container_width=True):
            save_visible_page();st.session_state.step-=1;st.rerun()
    with right:
        files_ok=not st.session_state.attachments_store or st.session_state.get("files_consent",False)
        if p<4:
            if st.button("Continuar →",type="primary",disabled=(bool(missing) or (p==3 and not files_ok)),use_container_width=True):
                save_visible_page();st.session_state.step+=1;st.rerun()
        elif st.button("Terminar",type="primary",disabled=(bool(missing) or not st.session_state.get("consent",False)),use_container_width=True):
            save_visible_page()
            answer={}
            for _,fs in SECTIONS:
                for key,_,_ in fs:
                    v=st.session_state.answers_store.get(key,"")
                    answer[key]="" if v=="Selecciona una opción" else v
            answer["autorizacion"]=st.session_state.answers_store.get("autorizacion","")
            answer["accion"]=st.session_state.answers_store.get("accion","")
            record={"submission_id":str(uuid.uuid4()),"submitted_at":datetime.now(timezone.utc).isoformat(),"answers":answer,"diagnostic":diagnose(answer)}
            st.session_state["saved"]=False
            st.session_state["files_saved"]=False
            st.session_state["save_error"]=""
            st.session_state["export"]=record
            st.session_state.finished=True;st.rerun()
else:
    st.success("¡Gracias por participar!")
    if storage_enabled and not st.session_state.get("saved"):
        try:
            response=requests.post(SHEETS_URL,json={"token":SHEETS_TOKEN,"record":st.session_state["export"]},timeout=15)
            if response.status_code != 200 or response.text.strip() != "OK":
                raise RuntimeError("No se pudo confirmar el guardado.")
            st.session_state.saved=True
            st.session_state.save_error=""
        except Exception:
            st.session_state.save_error="No pudimos confirmar que se guardó el briefing. Conserva tu archivo JSON y compártelo con Puente."
    if st.session_state.get("saved") and st.session_state.attachments_store and not st.session_state.get("files_saved"):
        try:
            if not st.session_state.get("files_consent"):
                raise RuntimeError("Falta autorización para compartir los archivos.")
            payload={"token":SHEETS_TOKEN,"submission_id":st.session_state["export"]["submission_id"],"brand":st.session_state["export"]["answers"].get("nombre","Marca"),"files":st.session_state.attachments_store}
            for item in payload["files"]:
                r=requests.post(SHEETS_URL,json={"action":"attachments","token":SHEETS_TOKEN,"submission_id":payload["submission_id"],"brand":payload["brand"],"files":[item]},timeout=75)
                if r.status_code!=200 or r.text.strip()!="OK":
                    raise RuntimeError("No se confirmó el almacenamiento de los archivos.")
            st.session_state.files_saved=True
        except Exception:
            st.warning("El briefing se guardó, pero no se confirmó la recepción de los adjuntos. Puedes reintentar sin volver a completar el formulario.")
            if st.button("Reintentar adjuntos"): st.rerun()
    if st.session_state.get("saved"):
        st.info("Tu briefing fue recibido para revisión. El diagnóstico no constituye una aprobación creativa.")
        if st.session_state.attachments_store and st.session_state.get("files_saved"): st.success("Adjuntos guardados en Google Drive.")
    elif storage_enabled:
        st.error(st.session_state.get("save_error","Error al guardar."))
        if st.button("Reintentar envío"):
            st.rerun()
    else:
        st.write("Descarga el archivo y envíaselo por WhatsApp o correo a quien te invitó.")
    st.download_button("Descargar mis respuestas (JSON)",json.dumps(st.session_state["export"],ensure_ascii=False,indent=2),file_name="briefing-puente.json",mime="application/json",type="primary")
    if st.button("Comenzar otro briefing"):
        for _,fs in SECTIONS:
            for key,_,_ in fs:st.session_state.pop(key,None)
        for k in ["autorizacion","accion","consent","files_consent","brand_uploads","export","saved","files_saved","save_error"]:st.session_state.pop(k,None)
        st.session_state.attachments_store=[];st.session_state.answers_store={};st.session_state.step=0;st.session_state.finished=False;st.rerun()
