import json
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
if "step" not in st.session_state:st.session_state.step=0
if "finished" not in st.session_state:st.session_state.finished=False
st.caption("AGENCIA PUENTE · CREATIVE OS · BETA PRIVADA")
st.title("Descubramos tu marca.")
st.write("Este cuestionario busca conocer tu negocio para probar nuestro sistema creativo. Responde con tus palabras, sin necesidad de conocimientos de diseño.")
st.warning("Prueba experimental. No ingreses datos sensibles ni confidenciales. Tus respuestas no se guardan ni se envían automáticamente: al finalizar podrás descargarlas y compartirlas con quien te invitó.")
if not st.session_state.finished:
    p=st.session_state.step
    st.progress((p+1)/5)
    st.subheader(f"{p+1}/5 · {SECTIONS[p][0]}")
    for key,label,kind in SECTIONS[p][1]:
        if kind=="text": st.text_input(label,key=key)
        elif kind=="area":st.text_area(label,key=key,height=90)
        elif kind=="channels":st.multiselect(label,OPTIONS[kind],key=key)
        else:st.selectbox(label,["Selecciona una opción"]+OPTIONS[kind],key=key)
    if p==3 and st.session_state.get("identidad_visual") in OPTIONS["visual"][:2]:
        st.selectbox("¿Puedes compartir archivos gráficos autorizados?",["Selecciona una opción","Sí","Debo confirmar","No"],key="autorizacion")
    if p==4:
        st.selectbox("¿Qué acción quieres que haga alguien después de ver una publicación?",["Selecciona una opción","Consultar","Comprar","Reservar","Visitar el local","Seguir la marca","No lo sé"],key="accion")
        st.checkbox("Acepto participar voluntariamente en esta prueba.",key="consent")
    left,right=st.columns(2)
    with left:
        if st.button("← Volver",disabled=p==0,use_container_width=True):
            st.session_state.step-=1;st.rerun()
    with right:
        if p<4:
            if st.button("Continuar →",type="primary",use_container_width=True):
                st.session_state.step+=1;st.rerun()
        elif st.button("Terminar",type="primary",disabled=not st.session_state.get("consent",False),use_container_width=True):
            answer={}
            for _,fs in SECTIONS:
                for key,_,_ in fs:
                    v=st.session_state.get(key,"")
                    answer[key]="" if v=="Selecciona una opción" else v
            answer["autorizacion"]=st.session_state.get("autorizacion","")
            answer["accion"]=st.session_state.get("accion","")
            record={"submitted_at":datetime.now(timezone.utc).isoformat(),"answers":answer,"diagnostic":diagnose(answer)}
            st.session_state["export"]=record
            st.session_state.finished=True;st.rerun()
else:
    st.success("¡Gracias por participar!")
    st.write("Descarga el archivo y envíaselo por WhatsApp o correo a quien te invitó. Esta beta no recibe respuestas automáticamente.")
    st.download_button("Descargar mis respuestas (JSON)",json.dumps(st.session_state["export"],ensure_ascii=False,indent=2),file_name="briefing-puente.json",mime="application/json",type="primary")
    if st.button("Comenzar otro briefing"):
        for _,fs in SECTIONS:
            for key,_,_ in fs:st.session_state.pop(key,None)
        for k in ["autorizacion","accion","consent","export"]:st.session_state.pop(k,None)
        st.session_state.step=0;st.session_state.finished=False;st.rerun()
