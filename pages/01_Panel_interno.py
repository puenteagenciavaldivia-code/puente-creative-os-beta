import hmac
import json
import requests
import streamlit as st
from creative_handoff import build_handoff
from strategic_audit import audit_briefing
from review_workflow import new_review, validate_review, prepare_reviewed_package
from design_catalog import search_catalog, category_names
from design_methodology import BIBLIOGRAPHY, CRITERIA
from ai_art_direction import propose_with_ai
from creative_preselection import preselect
from clarifications import build_request, validate_reply, attach_reply

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
    c2.metric("Marcados para revisión",sum(x.get("status")=="apto_para_revision" for x in items))
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
right.write("**Completitud orientativa:** "+str(chosen.get("score",0))+"/100")
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
st.divider()
st.markdown("### Revisión estratégica del equipo · Beta 0.8")
st.caption("Las respuestas originales no se modifican. Esta revisión permanece en la sesión hasta que descargues el archivo. No se guarda en Sheets ni Drive.")
review_key="puente_review_"+str(record.get("submission_id"))
if review_key not in st.session_state:
    st.session_state[review_key]=new_review(record,audit)

with st.expander("Recuperar una revisión guardada"):
    imported=st.file_uploader("Archivo JSON exportado anteriormente",type=["json"],key="import_"+review_key)
    if imported is not None and st.button("Cargar revisión",key="load_"+review_key):
        if imported.size>200_000:
            st.error("El archivo supera el límite de 200 KB.")
        else:
            try:
                candidate=json.loads(imported.getvalue().decode("utf-8"))
                if not isinstance(candidate,dict) or candidate.get("schema_version")!="puente_review_0_8" or candidate.get("submission_id")!=record.get("submission_id"):
                    st.error("El archivo no corresponde a este briefing o versión.")
                else:
                    st.session_state[review_key]=candidate
                    # Clear widgets so imported values are applied on next render.
                    for key in list(st.session_state.keys()):
                        if str(key).startswith("rev_widget_"+review_key):
                            del st.session_state[key]
                    st.rerun()
            except (UnicodeDecodeError,ValueError,TypeError):
                st.error("No se pudo leer el archivo JSON.")

review=st.session_state[review_key]
review["responsable"]=st.text_input("Responsable de la revisión",value=review.get("responsable",""),key="rev_widget_"+review_key+"_responsable")
st.markdown("#### 1. Aclaraciones del cliente")
st.caption("Puedes preparar una mini ficha para el cliente con solo las preguntas seleccionadas.")
ids_default=[q.get("id") for q in questions if q.get("prioridad")=="alta"]
selected_ids=st.multiselect(
    "Preguntas que enviaremos al cliente",
    options=[q.get("id") for q in questions],
    default=ids_default,
    format_func=lambda qid:next((q.get("pregunta",qid) for q in questions if q.get("id")==qid),qid),
    key="questions_to_send_"+review_key
)
if selected_ids:
    packet=build_request(record,audit,selected_ids)
    st.download_button("Descargar mini ficha para el cliente (JSON)",
        data=json.dumps(packet,ensure_ascii=False,indent=2),
        file_name="puente-preguntas-"+str(record.get("submission_id",""))[:8]+".json",
        mime="application/json",key="download_questions_"+review_key)
    st.caption("El cliente abre «Aclaraciones» en Creative OS, carga el archivo y descarga sus respuestas. En beta el envío no es automático.")
with st.expander("Importar respuestas complementarias"):
    upload_reply=st.file_uploader("Archivo JSON que envió el cliente",type=["json"],key="reply_"+review_key)
    if upload_reply is not None and st.button("Validar e importar respuestas",key="import_reply_"+review_key):
        if upload_reply.size>200_000:
            st.error("Archivo demasiado grande.")
        else:
            try:
                reply=json.loads(upload_reply.getvalue().decode("utf-8"))
                validate_reply(reply,record,audit)
                st.session_state[review_key]=attach_reply(st.session_state[review_key],reply,record,audit)
                st.rerun()
            except (ValueError,TypeError,UnicodeDecodeError) as exc:
                st.error("No se pudo importar: "+str(exc))
    supplement=review.get("aclaraciones_cliente",{}).get("respuestas",[])
    if supplement:
        st.info("Hay respuestas recibidas. Puente debe verificarlas antes de marcar preguntas como confirmadas.")
        for extra in supplement:
            st.markdown("**"+extra.get("pregunta","")+"**")
            st.write(extra.get("respuesta",""))

st.caption("Confirma solo información realmente comprobada. Puedes descartar falsas alarmas con una explicación.")
for question in questions:
    qid=str(question.get("id",""))
    item=review.get("revision",{}).get(qid,{})
    with st.expander(question.get("area","")+" · "+question.get("pregunta","")):
        current=item.get("estado","pendiente")
        choices=["pendiente","confirmado","aclarar","descartado"]
        state=st.selectbox("Estado",choices,index=choices.index(current) if current in choices else 0,key="rev_widget_"+review_key+"_"+qid+"_state")
        note=st.text_area("Evidencia o motivo de la decisión",value=item.get("nota",""),key="rev_widget_"+review_key+"_"+qid+"_note",height=80)
        review.setdefault("revision",{})[qid]={"estado":state,"nota":note}

st.markdown("#### Biblioteca de corrientes y lenguajes visuales")
st.caption("Una corriente histórica, una técnica, un recurso y un tratamiento fotográfico no son equivalentes. La biblioteca ayuda a investigar; no recomienda automáticamente.")
with st.expander("Explorar biblioteca visual",expanded=False):
    cat=st.selectbox("Tipo de referencia",category_names(),key="catalog_cat")
    query=st.text_input("Buscar por nombre, rasgo o uso",key="catalog_query")
    catalog_results=search_catalog(query,cat)
    st.caption(str(len(catalog_results))+" referencias disponibles para esta búsqueda")
    for item in catalog_results[:25]:
        st.markdown("**"+item["nombre"]+"** · "+item["categoria"])
        st.caption("Rasgos: "+", ".join(item["rasgos"])+" | Usos posibles: "+", ".join(item["aplicaciones"]))
        st.caption("Precauciones: "+", ".join(item["riesgos"]))
    if len(catalog_results)>25:
        st.caption("Refina la búsqueda para consultar el resto de resultados.")

st.markdown("#### Investigación y sugerencias de IA")
st.caption("Las propuestas son hipótesis para la dirección de arte. No se muestran al cliente y nunca se aprueban automáticamente.")
with st.expander("Método y referencias bibliográficas"):
    for item in BIBLIOGRAPHY:
        st.markdown("**"+item["autor"]+" — "+item["titulo"]+"**")
        st.caption(item["edicion"]+" · "+item["uso"]+" "+item["alcance"])
        st.link_button("Ver fuente editorial",item["url"])
    st.markdown("**Criterios de evaluación utilizados**")
    for name,question in CRITERIA.items():
        st.write("• "+name.replace("_"," ").capitalize()+": "+question)
try:
    ai_key=st.secrets.get("OPENAI_API_KEY","")
    ai_model=st.secrets.get("OPENAI_MODEL","gpt-4.1-mini")
except (KeyError,FileNotFoundError):
    ai_key=""
    ai_model="gpt-4.1-mini"
if not ai_key:
    st.warning("IA generativa todavía no conectada. Falta OPENAI_API_KEY en los Secrets privados del servidor. La biblioteca y el análisis por reglas siguen disponibles.")
else:
    st.caption("Motor generativo disponible. Modelo configurado: "+ai_model+". La API tiene costo separado de ChatGPT.")
    consent_ai=st.checkbox("Confirmo que este briefing es de prueba o tengo autorización para enviar sus respuestas al servicio de IA.",
        key="ai_consent_"+review_key)
    if st.button("Investigar tres corrientes madre con IA",type="primary",
                 disabled=not consent_ai,key="research_ai_"+review_key):
        try:
            with st.spinner("Analizando hipótesis de dirección creativa..."):
                proposals=propose_with_ai(answers,ai_key,model=ai_model)
            st.session_state["ai_proposals_"+review_key]=proposals
            review["corrientes"]=[
                {"nombre":p["nombre"],"fundamento":p["argumento"]+
                     " Evidencia: "+", ".join(e["campo"]+": "+e["cita_respuesta"] for e in p["evidencias"]),
                 "diferenciacion":p["contraste"],"riesgos":p["riesgos"]}
                for p in proposals["propuestas"]
            ]
            review["direccion_seleccionada"]=None
            review["autorizacion_produccion"]=False
            for widget_key in list(st.session_state):
                if str(widget_key).startswith("rev_widget_"+review_key+"_"):
                    del st.session_state[widget_key]
            st.rerun()
        except (ValueError,RuntimeError,requests.RequestException) as exc:
            st.error("La investigación no pudo completarse: "+str(exc))
result_ai=st.session_state.get("ai_proposals_"+review_key)
if isinstance(result_ai,dict):
    st.info("Se generaron tres propuestas para evaluar, no para aprobar automáticamente.")
    st.write("**Lectura del briefing:** "+result_ai.get("diagnostico",""))
    for i,proposal in enumerate(result_ai.get("propuestas",[]),1):
        with st.expander(str(i)+". "+proposal["nombre"]+" · Hipótesis IA"):
            st.write("**Fundamento:** "+proposal["argumento"])
            st.write("**Composición e imagen:** "+proposal["sistema_visual"])
            st.write("**Tipografía:** "+proposal["tipografia"])
            st.write("**Fotografía:** "+proposal["tratamiento_fotografico"])
            st.write("**Aplicaciones:** "+proposal["aplicaciones"])
            st.write("**Diferenciación:** "+proposal["contraste"])
            st.write("**Riesgos:** "+proposal["riesgos"])
            st.write("**Validar:** "+proposal["criterios_verificar"])
            st.markdown("**Evidencia literal del cliente**")
            for evidence in proposal["evidencias"]:
                st.caption(evidence["campo"]+": «"+evidence["cita_respuesta"]+"»")
st.markdown("#### Preselección de exploración sin API")
st.caption("Alternativa provisional basada solo en coincidencias de palabras, no en IA. Sirve para proponer puntos de partida editables y no debe confundirse con recomendaciones estratégicas.")
if st.button("Preparar tres hipótesis iniciales (reglas, sin IA)",key="preselect_"+review_key):
    drafted=preselect(answers)
    if len(drafted)!=3:
        st.warning("No hay información suficiente para preseleccionar alternativas.")
    else:
        review["corrientes"]=[{key:item[key] for key in ("nombre","fundamento","diferenciacion","riesgos")} for item in drafted]
        review["direccion_seleccionada"]=None
        review["autorizacion_produccion"]=False
        st.session_state.pop("ai_proposals_"+review_key,None)
        for widget_key in list(st.session_state):
            if str(widget_key).startswith("rev_widget_"+review_key+"_"):
                del st.session_state[widget_key]
        st.rerun()

st.markdown("#### 2. Comparación de corrientes madre")
st.caption("Las alternativas pueden llegar sugeridas por IA y son editables. Tú decides cuáles investigar y aprobar.")

st.caption("No deben salir de una lista fija. Registra dos o tres enfoques basados en las características reales de la marca, con diferencias y riesgos.")
previous=review.get("corrientes") or []
number=st.selectbox("Alternativas a comparar",[2,3],index=1 if len(previous)==3 else 0,key="rev_widget_"+review_key+"_count")
currents=[]
for index in range(number):
    old=previous[index] if index<len(previous) and isinstance(previous[index],dict) else {}
    with st.expander("Corriente madre "+str(index+1),expanded=index==0):
        name=st.text_input("Nombre de la corriente",value=old.get("nombre",""),key="rev_widget_"+review_key+"_name_"+str(index))
        basis=st.text_area("¿Qué datos del briefing justifican investigarla?",value=old.get("fundamento",""),height=90,key="rev_widget_"+review_key+"_basis_"+str(index))
        contrast=st.text_area("¿En qué se diferencia de las otras alternativas?",value=old.get("diferenciacion",""),height=80,key="rev_widget_"+review_key+"_contrast_"+str(index))
        risks=st.text_area("¿Qué riesgos o limitaciones tiene para esta marca?",value=old.get("riesgos",""),height=80,key="rev_widget_"+review_key+"_risks_"+str(index))
        currents.append({"nombre":name,"fundamento":basis,"diferenciacion":contrast,"riesgos":risks})
review["corrientes"]=currents
names=[entry["nombre"].strip() for entry in currents if entry["nombre"].strip()]
selected=review.get("direccion_seleccionada")
options=["Sin seleccionar"]+names
chosen_index=options.index(selected) if selected in options else 0
chosen_direction=st.selectbox("Corriente madre propuesta",options,index=chosen_index,key="rev_widget_"+review_key+"_chosen")
review["direccion_seleccionada"]=None if chosen_direction=="Sin seleccionar" else chosen_direction
review["observaciones"]=st.text_area("Justificación de la dirección propuesta",value=review.get("observaciones",""),height=110,key="rev_widget_"+review_key+"_notes")
review["autorizacion_produccion"]=st.checkbox("Confirmo como responsable que se han resuelto las dudas y autorizo preparar producción.",value=bool(review.get("autorizacion_produccion")),key="rev_widget_"+review_key+"_production")
errors=validate_review(review,record,audit)
package=prepare_reviewed_package(handoff,review,audit)
if errors:
    st.warning("Revisión incompleta: "+str(len(errors))+" asuntos por resolver.")
    with st.expander("Ver condiciones pendientes"):
        for err in errors:
            st.write("• "+err)
else:
    st.success("Revisión editorial completa. "+("Producción autorizada por el responsable." if review["autorizacion_produccion"] else "Producción todavía sin autorización."))
st.download_button("Guardar revisión (JSON)",data=json.dumps(review,ensure_ascii=False,indent=2),
    file_name="puente-revision-"+str(record.get("submission_id",""))[:8]+".json",mime="application/json")
st.download_button("Exportar paquete creativo revisado (JSON)",data=json.dumps(package,ensure_ascii=False,indent=2),
    file_name="puente-paquete-creativo-"+str(record.get("submission_id",""))[:8]+".json",mime="application/json")
st.caption("Para continuar en otra sesión, descarga tu revisión y vuelve a cargar el archivo al regresar. La exportación no registra cambios en la base de datos.")

st.download_button("Exportar ficha para Creative OS (JSON)",
    data=json.dumps(handoff,ensure_ascii=False,indent=2),
    file_name="puente-ficha-creative-os.json",mime="application/json")
st.download_button("Exportar este briefing (JSON)",data=json.dumps(record,ensure_ascii=False,indent=2),file_name="briefing-interno.json",mime="application/json")
