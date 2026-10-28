import hmac
import json
import requests
import streamlit as st
from creative_handoff import build_handoff
from strategic_audit import audit_briefing

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
    with st.expander("Verificación técnica"):
        st.caption("Ejecuta pruebas locales del análisis y el traspaso creativo. No modifica briefings ni archivos.")
        if st.button("Ejecutar pruebas internas"):
            import unittest
            import io
            output=io.StringIO()
            suite=unittest.TestLoader().discover(start_dir="tests",pattern="test_*.py")
            results=unittest.TextTestRunner(stream=output,verbosity=2).run(suite)
            if results.wasSuccessful() and results.testsRun>0:
                st.success(str(results.testsRun)+" pruebas satisfactorias.")
            else:
                st.error("Las pruebas detectaron errores o no se ejecutaron.")
            st.code(output.getvalue(),language="text")

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
if (chosen.get("diagnostic") or {}).get("engine")=="heuristic_beta_0_5":
    st.caption("Evaluación Beta 0.5: reglas heurísticas de claridad. No es comprensión semántica ni aprobación creativa.")
else:
    st.caption("Registro anterior a la Beta 0.5: puntuación basada en completitud. No equivale a calidad estratégica.")

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
if diag.get("follow_up_questions"):
    st.markdown("### Preguntas de seguimiento sugeridas")
    for item in diag["follow_up_questions"]:
        st.write("• "+str(item.get("question","")))
if diag.get("flags"):
    with st.expander("Alertas de calidad detectadas"):
        for item in diag["flags"]:
            st.write(str(item.get("field",""))+": "+str(item.get("issue","")))
st.markdown("### Auditoría estratégica automática")
audit=diag.get("strategic_audit")
if not isinstance(audit,dict):
    audit=audit_briefing(answers,diag)
    st.caption("Auditoría calculada ahora para un registro anterior; no modifica el diagnóstico guardado.")
else:
    st.caption("Auditoría generada automáticamente al enviar el briefing.")
st.info("Esta revisión identifica preguntas posibles mediante reglas. No interpreta profundamente ni aprueba la campaña.")
st.write("**Estado:** Pendiente de revisión humana")
questions=audit.get("preguntas_priorizadas",[])
if questions:
    high=sum(x.get("prioridad")=="alta" for x in questions)
    medium=sum(x.get("prioridad")!="alta" for x in questions)
    a,b=st.columns(2)
    a.metric("Preguntas prioritarias",high)
    b.metric("Aclaraciones secundarias",medium)
if questions:
    st.markdown("#### Preguntas para aclarar antes de crear")
    for i,item in enumerate(questions,1):
        st.markdown("**"+str(i)+". "+item.get("pregunta","")+"**")
        st.caption(item.get("area","")+" · Prioridad "+item.get("prioridad","media")+" · "+item.get("motivo",""))
else:
    st.caption("Sin alertas adicionales detectadas por reglas. Esto no significa que no existan vacíos.")
with st.expander("Información aprovechable para Puente"):
    for item in audit.get("informacion_aprovechable",[]):
        st.write("**"+item.get("area","")+":** "+item.get("observacion",""))
st.download_button("Descargar auditoría estratégica (JSON)",
    data=json.dumps(audit,ensure_ascii=False,indent=2),
    file_name="puente-auditoria-estrategica.json",mime="application/json")

with st.expander("Ver diagnóstico técnico"):
    st.json(diag)

record={"submission_id":chosen.get("submission_id"),"submitted_at":chosen.get("submitted_at"),"answers":answers,"diagnostic":diag,"attachments":links}
handoff=build_handoff(record)
handoff["auditoria_estrategica"]=audit
st.markdown("### Ficha de entrada a Creative OS")
st.caption("Ordena las declaraciones del cliente. No selecciona corrientes madre ni sustituye la revisión del equipo.")
for group, content in handoff["bloques"].items():
    with st.expander(group.replace("_"," ").capitalize()):
        for key,value in content["declaraciones_del_cliente"].items():
            st.write("**"+key.replace("_"," ").capitalize()+":**",value)
        if content["por_consultar"]:
            st.caption("Por consultar: "+", ".join(content["por_consultar"]))
st.markdown("### Preparación para el trabajo creativo")
for task, details in handoff["preparacion"].items():
    st.write("**"+task.replace("_"," ").capitalize()+"** · "+
             ("Información por complementar: "+", ".join(details["informacion_pendiente"])
              if details["informacion_pendiente"] else "Información declarada disponible. Requiere revisión humana."))
st.download_button("Exportar ficha para Creative OS (JSON)",
    data=json.dumps(handoff,ensure_ascii=False,indent=2),
    file_name="puente-ficha-creative-os.json",mime="application/json")
st.download_button("Exportar este briefing (JSON)",data=json.dumps(record,ensure_ascii=False,indent=2),file_name="briefing-interno.json",mime="application/json")
