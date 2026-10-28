import json
import base64
import uuid
import requests
from datetime import datetime, timezone
import streamlit as st

st.set_page_config(page_title="PUENTE Creative OS | Beta 0.7", page_icon="🌉", layout="centered")
st.markdown("""<style>.block-container{max-width:780px;padding-top:2rem}h1{letter-spacing:-.04em}</style>""",unsafe_allow_html=True)
SECTIONS=[
("Identidad",[
("nombre","¿Cómo se llama tu marca?","text"),
("negocio","¿Qué hace tu negocio?","area"),
("personalidad","Si tu negocio fuera una persona, ¿cómo sería?","area"),
("recuerdo","Cuando alguien recomiende tu negocio, ¿qué te gustaría que dijera?","area")]),
("Negocio",[
("productos","¿Cuáles son tus productos o servicios?","area"),
("diferencia","¿Qué valoran tus clientes de lo que haces?","area"),
("destacar","¿Qué te gustaría mostrar primero de tu negocio?","area"),
("competencia","¿Qué otros negocios se parecen al tuyo o te sirven de ejemplo?","area")]),
("Público",[
("publico","¿Cómo son las personas que te compran hoy?","area"),
("publico_nuevo","¿Qué otras personas te gustaría que conocieran tu negocio?","area"),
("dudas","¿Qué te suelen preguntar antes de comprar?","area"),
("tono","¿Cómo te gustaría hablar con tus clientes?","tone")]),
("Universo visual",[
("identidad_visual","¿Tienes un logotipo o colores que uses siempre?","visual"),
("elementos","¿Qué colores, fotos o elementos de tu marca quieres conservar?","area"),
("referentes","¿Qué publicaciones, locales o marcas te gustan visualmente? ¿Por qué?","area"),
("evitar","¿Qué colores, fotos o estilos definitivamente no te gustan?","area")]),
("Objetivos y producción",[
("objetivo","¿Qué te gustaría conseguir con tus publicaciones?","goal"),
("canales","¿En qué redes o medios estás presente?","channels"),
("materiales","¿Qué fotos, videos o archivos de tu negocio tienes disponibles?","area"),
("condiciones","¿Hay fechas o detalles que debamos tener en cuenta?","area")])]
OPTIONS={
"tone":["Cercano","Profesional","Didáctico","Divertido","Sereno","Aún no lo sé"],
"visual":["Sí, tenemos manual de marca","Tenemos logo, pero no manual","No tenemos identidad visual"],
"goal":["Aumentar ventas","Conseguir consultas","Dar a conocer mi marca","Fidelizar clientes","Educar al público","Aún no lo sé"],
"channels":["Instagram","Facebook","WhatsApp","TikTok","Web","Google","Otros"]}
from briefing_quality import diagnose, field_quality
from creative_handoff import build_handoff
from strategic_audit import audit_briefing
from briefing_guidance import SECTION_INTROS, HELP, EXAMPLES
# Streamlit removes widget state when the widget is absent from a rerun.
# Keep form data separately so navigating between steps does not erase prior answers.
if "answers_store" not in st.session_state: st.session_state.answers_store={}
def save_visible_page():
    for key,_,_ in SECTIONS[st.session_state.step][1]:
        if key in st.session_state:
            value=st.session_state[key]
            st.session_state.answers_store[key]="" if value=="Selecciona una opción" else value
    for key in ("autorizacion","accion","files_consent"):
        if key in st.session_state:
            st.session_state.answers_store[key]=st.session_state[key]
def restore_widget(key):
    if key not in st.session_state and key in st.session_state.answers_store:
        st.session_state[key]=st.session_state.answers_store[key]
if "step" not in st.session_state:st.session_state.step=0
if "finished" not in st.session_state:st.session_state.finished=False
if "attachments_store" not in st.session_state: st.session_state.attachments_store=[]
st.caption("AGENCIA PUENTE · CREATIVE OS · BETA PRIVADA")
try:
    st.page_link("pages/01_Panel_interno.py", label="Acceder al panel interno de Puente", icon="🔒")
except Exception:
    st.caption("El panel interno aún no está disponible en esta implementación. El briefing sigue funcionando.")
st.title("Descubramos tu marca.")
st.write("Queremos conocer tu negocio. Responde como si se lo contaras a alguien en una conversación. No necesitas saber de diseño ni publicidad.")
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
    if st.session_state.get("review_ready",False):
        st.subheader("Revisa tus respuestas antes de enviarlas")
        st.write("Revisa lo que escribiste. Puedes corregir cualquier sección. Nada se enviará hasta que confirmes.")
        for index,(section,fields) in enumerate(SECTIONS):
            with st.expander(section):
                for key,label,kind in fields:
                    value=st.session_state.answers_store.get(key,"")
                    st.markdown("**"+label+"**")
                    st.write(", ".join(value) if isinstance(value,list) else (str(value) if value else "Sin respuesta"))
                if st.button("Corregir "+section,key="edit_"+str(index)):
                    st.session_state.review_ready=False
                    st.session_state.step=index
                    st.rerun()
        st.caption("Archivos preparados: "+str(len(st.session_state.attachments_store))+". Evita incluir datos personales sensibles.")
        left,right=st.columns(2)
        with left:
            if st.button("← Volver a editar",use_container_width=True):
                st.session_state.review_ready=False
                st.session_state.step=4
                st.rerun()
        with right:
            if st.button("Confirmar y enviar",type="primary",use_container_width=True):
                answer={}
                for _,fields in SECTIONS:
                    for key,_,_ in fields:
                        value=st.session_state.answers_store.get(key,"")
                        answer[key]="" if value=="Selecciona una opción" else value
                answer["autorizacion"]=st.session_state.answers_store.get("autorizacion","")
                answer["accion"]=st.session_state.answers_store.get("accion","")
                diagnostic=diagnose(answer)
                diagnostic["strategic_audit"]=audit_briefing(answer,diagnostic)
                record={"submission_id":str(uuid.uuid4()),"submitted_at":datetime.now(timezone.utc).isoformat(),"answers":answer,"diagnostic":diagnostic}
                st.session_state.saved=False
                st.session_state.files_saved=False
                st.session_state.save_error=""
                st.session_state.export=record
                st.session_state.finished=True
                st.session_state.review_ready=False
                st.rerun()
    else:
        p=st.session_state.step
        st.progress((p+1)/5)
        st.subheader(f"{p+1}/5 · {SECTIONS[p][0]}")
        intro, example=SECTION_INTROS[SECTIONS[p][0]]
        st.write(intro)
        st.caption(example)
        for key,label,kind in SECTIONS[p][1]:
            restore_widget(key)
            if kind=="text":
                st.text_input(label,key=key,placeholder=EXAMPLES.get(key,""),help=HELP.get(key,""))
            elif kind=="area":
                st.text_area(label,key=key,height=110,placeholder=EXAMPLES.get(key,""),help=HELP.get(key,""))
            elif kind=="channels":
                st.multiselect(label,OPTIONS[kind],key=key,help=HELP.get(key,""))
            else:
                st.selectbox(label,["Selecciona una opción"]+OPTIONS[kind],key=key,help=HELP.get(key,""))
            # Orientación amable durante el llenado, sin bloquear el formulario.
            if kind=="area" and st.session_state.get(key):
                quality,_=field_quality(key,st.session_state.get(key))
                if quality < 0.75:
                    st.caption("Sugerencia: agrega un ejemplo de tu experiencia. Una o dos frases concretas nos ayudan a entenderte mejor.")
        if p==3 and st.session_state.get("identidad_visual") in OPTIONS["visual"][:2]:
            restore_widget("autorizacion")
            st.selectbox("¿Puedes compartir archivos gráficos autorizados?",["Selecciona una opción","Sí","Debo confirmar","No"],key="autorizacion")
        if p==3:
            st.markdown("#### Archivos de tu marca (opcional)")
            st.caption("PNG, JPG, WEBP o PDF. Máximo 3 MB por archivo y 5 archivos. No incluyas datos personales sensibles.")
            uploaded=st.file_uploader("Adjunta logotipos, fotografías o referencias",type=["png","jpg","jpeg","webp","pdf"],accept_multiple_files=True,key="brand_uploads")
            if uploaded:
                if len(uploaded)>5 or any(x.size>3*1024*1024 for x in uploaded) or any((x.type not in ("image/png","image/jpeg","image/webp","application/pdf")) for x in uploaded):
                    st.error("Se permiten hasta 5 archivos de máximo 3 MB cada uno. Ajusta los adjuntos antes de continuar.")
                else:
                    st.session_state.attachments_store=[{"name":x.name,"mime":x.type,"data":base64.b64encode(x.getvalue()).decode("ascii")} for x in uploaded]
            if st.session_state.attachments_store:
                st.caption(f"{len(st.session_state.attachments_store)} archivo(s) preparados para enviar al finalizar.")
            restore_widget("files_consent")
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
            st.caption("Para avanzar, responde las preguntas principales de esta etapa. Las demás son opcionales.")
        left,right=st.columns(2)
        with left:
            if st.button("← Volver",disabled=p==0,use_container_width=True):
                save_visible_page();st.session_state.step-=1;st.rerun()
        with right:
            files_ok=not st.session_state.attachments_store or (st.session_state.get("files_consent",False) or st.session_state.answers_store.get("files_consent",False))
            if p<4:
                if st.button("Continuar →",type="primary",disabled=(bool(missing) or (p==3 and not files_ok)),use_container_width=True):
                    save_visible_page();st.session_state.step+=1;st.rerun()
            elif st.button("Revisar respuestas →",type="primary",disabled=(bool(missing) or not st.session_state.get("consent",False) or not files_ok),use_container_width=True):
                save_visible_page()
                st.session_state.review_ready=True
                st.rerun()
else:
    st.success("¡Gracias por participar!")
    st.write("El equipo de Puente revisará la información. Si necesitamos aclarar algo, te lo consultaremos.")
    if storage_enabled and not st.session_state.get("saved"):
        try:
            response=requests.post(SHEETS_URL,json={"token":SHEETS_TOKEN,"record":st.session_state["export"]},timeout=15)
            if response.status_code != 200 or response.text.strip() != "OK":
                raise RuntimeError("No se pudo confirmar el guardado.")
            st.session_state.saved=True
            st.session_state.save_error=""
        except Exception:
            st.session_state.save_error="No pudimos confirmar que se guardó el briefing. Conserva tu archivo JSON y compártelo con Puente."
    if storage_enabled and st.session_state.get("saved") and st.session_state.attachments_store and not st.session_state.get("files_saved"):
        try:
            if not st.session_state.answers_store.get("files_consent"):
                raise RuntimeError("Falta la autorización para compartir los archivos.")
            payload={"submission_id":st.session_state["export"]["submission_id"],"brand":st.session_state["export"]["answers"].get("nombre","Marca"),"files":st.session_state.attachments_store}
            for item in payload["files"]:
                try:
                    r=requests.post(SHEETS_URL,json={"action":"attachments","token":SHEETS_TOKEN,"submission_id":payload["submission_id"],"brand":payload["brand"],"files":[item]},timeout=75)
                except requests.exceptions.Timeout:
                    raise RuntimeError("Tiempo de espera agotado al enviar el adjunto.")
                except requests.exceptions.RequestException:
                    raise RuntimeError("Error de comunicación HTTPS con el receptor de Google.")
                response_code=r.text.strip()
                if r.status_code!=200:
                    raise RuntimeError(f"Respuesta HTTP {r.status_code} del receptor.")
                if response_code!="OK":
                    allowed_errors={"DENIED":"El receptor rechazó la autorización.","INVALID":"El receptor rechazó los datos o el tipo de archivo.","ERROR":"Error interno de Google Apps Script al procesar el adjunto."}
                    raise RuntimeError(allowed_errors.get(response_code,"El receptor devolvió una respuesta inesperada (no OK)."))
            st.session_state.files_saved=True
            st.session_state.pop("files_error",None)
        except Exception as exc:
            st.session_state.files_error=str(exc)
        if not st.session_state.get("files_saved"):
            st.warning("El briefing se guardó, pero no se confirmó la recepción de los adjuntos.")
            st.error("Diagnóstico del envío: "+st.session_state.get("files_error","Error no identificado."))
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
        for k in ["autorizacion","accion","consent","files_consent","brand_uploads","export","saved","files_saved","save_error","review_ready"]:st.session_state.pop(k,None)
        st.session_state.attachments_store=[];st.session_state.answers_store={};st.session_state.step=0;st.session_state.finished=False;st.rerun()
