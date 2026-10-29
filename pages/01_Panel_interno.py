"""PUENTE Creative OS — escritorio de gestión interna (Beta 1.0)."""
import io
import json
import secrets
import unittest
import requests
import hmac
import streamlit as st
from creative_handoff import build_handoff
from strategic_audit import audit_briefing
from review_workflow import new_review,validate_review,prepare_reviewed_package
from clarifications import build_request,validate_reply,attach_reply
from creative_exchange import build_creative_prompt, import_creative_json
from graphic_production import FORMAT_PRESETS, build_piece, build_production_plan, production_prompt, export_plan
from design_catalog import search_catalog,category_names
from design_methodology import BIBLIOGRAPHY,CRITERIA
from dashboard_helpers import public_clarification_url,invitation_copy,whatsapp_share_url,mailto_url

st.set_page_config(page_title="Escritorio creativo | PUENTE",page_icon="🌉",layout="wide")
st.markdown("""<style>
.block-container{max-width:1260px;padding-top:1.4rem}
h1,h2,h3{letter-spacing:-.035em}
div[data-testid="stMetric"]{background:rgba(128,128,128,.055);padding:14px;border-radius:13px}
</style>""",unsafe_allow_html=True)
try:
    cfg={k:st.secrets.get(k,"") for k in (
        "ADMIN_PANEL_PASSWORD","ADMIN_READ_TOKEN","SHEETS_WEBHOOK_URL",
        "CLARIFICATIONS_ADMIN_TOKEN","APP_PUBLIC_URL")}
except (KeyError,FileNotFoundError):
    cfg={}
password=cfg.get("ADMIN_PANEL_PASSWORD","")
read_token=cfg.get("ADMIN_READ_TOKEN","")
endpoint=cfg.get("SHEETS_WEBHOOK_URL","")
if not (password and read_token and endpoint):
    st.error("Configuración incompleta: faltan credenciales del panel o del receptor.")
    st.stop()
if not st.session_state.get("puente_admin_ok"):
    st.title("Acceso interno · Puente")
    st.caption("Creative OS · Este espacio es exclusivo del equipo.")
    with st.form("login"):
        typed=st.text_input("Contraseña",type="password")
        login=st.form_submit_button("Entrar",type="primary")
    if login:
        if hmac.compare_digest(typed,password):
            st.session_state.puente_admin_ok=True
            st.rerun()
        else:
            st.error("Contraseña incorrecta.")
    st.stop()

def call_backend(action,payload,timeout=30):
    r=requests.post(endpoint,json={"action":action,**payload},timeout=timeout)
    r.raise_for_status()
    if r.text.strip() in ("DENIED","ERROR","INVALID","EXPIRED","CLOSED","QUOTA","ALREADY_SENT"):
        raise RuntimeError("El receptor respondió: "+r.text.strip())
    data=r.json()
    if not isinstance(data,dict) or not data.get("ok",True):
        raise RuntimeError("Respuesta no reconocida del receptor.")
    return data

def load_items():
    try:
        r=requests.post(endpoint,json={"action":"admin_list","admin_token":read_token},timeout=35)
        r.raise_for_status()
        if r.text.strip() in ("DENIED","ERROR"):
            raise RuntimeError("No se pudo validar el permiso de lectura.")
        data=r.json()
        if not isinstance(data.get("items"),list):
            raise ValueError("Formato inesperado.")
        st.session_state["admin_items"]=data["items"]
    except (ValueError,requests.RequestException,RuntimeError) as exc:
        st.error("No fue posible cargar los briefings: "+str(exc))

with st.sidebar:
    st.markdown("### 🌉 PUENTE")
    st.caption("Creative OS · Escritorio creativo")
    if st.button("Actualizar briefings",use_container_width=True):
        load_items()
    with st.expander("Verificación técnica"):
        if st.button("Ejecutar pruebas internas"):
            output=io.StringIO()
            tests=unittest.TestLoader().discover("tests","test_*.py")
            result=unittest.TextTestRunner(stream=output,verbosity=2).run(tests)
            if result.wasSuccessful() and result.testsRun>0:
                st.success(str(result.testsRun)+" pruebas satisfactorias.")
            else:
                st.error("Se encontraron errores en las pruebas.")
            st.code(output.getvalue())
    if st.button("Cerrar sesión",use_container_width=True):
        st.session_state.puente_admin_ok=False
        st.session_state.pop("admin_items",None)
        st.rerun()
    st.caption("Beta: utilizar datos ficticios hasta cerrar la evaluación de seguridad.")

if "admin_items" not in st.session_state:
    load_items()
items=st.session_state.get("admin_items",[])
st.title("Escritorio creativo")
st.caption("Del briefing a las decisiones de dirección de arte · Acceso exclusivo del equipo")
if not items:
    st.info("Todavía no hay briefings visibles o no se pudieron cargar.")
    st.stop()
c1,c2,c3=st.columns(3)
c1.metric("Briefings recibidos",len(items))
c2.metric("Listos para revisión",sum(x.get("status")=="apto_para_revision" for x in items))
c3.metric("Con material adjunto",sum(bool(x.get("attachments")) for x in items))
search=st.text_input("Buscar un cliente",placeholder="Escribe el nombre de la marca")
visible=[x for x in items if search.casefold().strip() in str(x.get("brand","")).casefold()]
if not visible:
    st.info("No encontramos esa marca.")
    st.stop()
choice=st.selectbox("Proyecto",range(len(visible)),
    format_func=lambda i:str(visible[i].get("brand") or "Sin nombre")+" · "+
        str(visible[i].get("submitted_at") or "")[:10]+" · "+
        str(visible[i].get("submission_id") or "")[:8])
selected=visible[choice]
answers=selected.get("answers") or {}
diag=selected.get("diagnostic") or {}
audit=diag.get("strategic_audit")
if not isinstance(audit,dict):audit=audit_briefing(answers,diag)
questions=audit.get("preguntas_priorizadas",[])
record={"submission_id":selected.get("submission_id"),
        "submitted_at":selected.get("submitted_at"),
        "answers":answers,"diagnostic":diag,
        "attachments":selected.get("attachments") or []}
handoff=build_handoff(record)
handoff["auditoria_estrategica"]=audit
rid="puente_review_"+str(record["submission_id"])
if rid not in st.session_state:
    st.session_state[rid]=new_review(record,audit)
review=st.session_state[rid]
st.divider()
st.subheader(str(selected.get("brand") or "Sin nombre"))
st.caption("Completitud orientativa: "+str(selected.get("score",0))+
           "/100 · No equivale a aprobación estratégica.")
tabs=st.tabs(["Resumen","Aclaraciones","Dirección de arte","Producción","Documentos"])

with tabs[0]:
    st.markdown("#### La marca en pocas palabras")
    st.write(answers.get("negocio") or "El cliente no describió todavía el negocio.")
    x,y=st.columns(2)
    with x:
        st.markdown("**Público principal**")
        st.write(answers.get("publico") or "Sin definir")
        st.markdown("**Diferenciación declarada**")
        st.write(answers.get("diferencia") or "Sin definir")
    with y:
        st.markdown("**Objetivo**")
        st.write(answers.get("objetivo") or "Sin definir")
        st.markdown("**Canales**")
        st.write(", ".join(answers.get("canales",[])) or "Sin definir")
    with st.expander("Leer las respuestas originales del cliente"):
        for key,value in answers.items():
            if value not in ("",None,[]):
                st.markdown("**"+key.replace("_"," ").capitalize()+"**")
                st.write(", ".join(map(str,value)) if isinstance(value,list) else value)
    with st.expander("Adjuntos originales"):
        if record["attachments"]:
            for i,link in enumerate(record["attachments"],1):
                if isinstance(link,str) and link.startswith("https://drive.google.com/"):
                    st.link_button("Abrir adjunto "+str(i),link)
        else:st.caption("No hay adjuntos registrados.")
    with st.expander("Diagnóstico técnico"):
        st.json(diag)
    st.download_button("Descargar briefing original",json.dumps(record,ensure_ascii=False,indent=2),
        file_name="puente-briefing.json",mime="application/json")

with tabs[1]:
    st.markdown("#### Aclaraciones del cliente")
    st.caption("Solo las preguntas realmente necesarias. Puente puede descartar alertas antes de enviarlas.")
    hi=sum(q.get("prioridad")=="alta" for q in questions)
    a,b=st.columns(2)
    a.metric("Prioridad alta",hi)
    b.metric("Otras consultas",len(questions)-hi)
    if not questions:
        st.success("Las reglas no identificaron aclaraciones nuevas. Requiere igualmente revisión humana.")
    else:
        for q in questions:
            with st.expander(q.get("pregunta","Pregunta")):
                st.caption("Prioridad "+str(q.get("prioridad","media"))+
                           " · "+str(q.get("motivo","")))
        ids=[q.get("id") for q in questions]
        preferred=[q["id"] for q in questions if q.get("prioridad")=="alta"]
        selected_ids=st.multiselect("Seleccionar preguntas que recibirá el cliente",
            ids,default=preferred,
            format_func=lambda x:next((q["pregunta"] for q in questions if q.get("id")==x),x))
        if selected_ids:
            mini=build_request(record,audit,selected_ids)
            with st.expander("Descarga de respaldo"):
                st.download_button("Descargar ficha JSON",json.dumps(mini,ensure_ascii=False,indent=2),
                    file_name="puente-preguntas-"+str(record["submission_id"])[:8]+".json",
                    mime="application/json")
            st.markdown("##### Crear enlace seguro para el cliente")
            admin_token=cfg.get("CLARIFICATIONS_ADMIN_TOKEN","")
            public_url=cfg.get("APP_PUBLIC_URL","")
            if not admin_token or not public_url:
                st.warning("Para activar enlaces faltan CLARIFICATIONS_ADMIN_TOKEN y/o APP_PUBLIC_URL en Secrets. Además debes publicar la nueva versión de Apps Script.")
            else:
                if st.button("Crear enlace privado por 7 días",type="primary",key="make_link_"+rid):
                    token=secrets.token_hex(32)
                    try:
                        link=public_clarification_url(public_url,token)
                        call_backend("clarify_create",{
                            "admin_token":admin_token,"access_token":token,
                            "submission_id":record["submission_id"],
                            "brand":str(answers.get("nombre") or ""),
                            "questions":mini["preguntas"]})
                        st.session_state["active_invite_"+rid]={"token":token,"link":link}
                        st.success("Enlace creado. Solo permite una respuesta y vence en siete días.")
                    except (ValueError,requests.RequestException,RuntimeError) as exc:
                        st.error("No se pudo crear el enlace: "+str(exc))
                invite=st.session_state.get("active_invite_"+rid)
                if invite:
                    link=invite["link"]
                    message=invitation_copy(answers.get("nombre",""),link)
                    st.code(link,language="text")
                    st.link_button("Compartir en WhatsApp",whatsapp_share_url(message))
                    contact=st.text_input("Correo del cliente",placeholder="cliente@empresa.cl",key="mail_"+rid)
                    if contact:
                        try:
                            st.link_button("Abrir mi correo con mensaje listo",
                                mailto_url(contact,answers.get("nombre",""),message))
                        except ValueError as exc:st.warning(str(exc))
                        if st.button("Enviar correo automáticamente desde Puente",key="send_"+rid):
                            try:
                                call_backend("clarify_send_email",{
                                    "admin_token":admin_token,"access_token":invite["token"],
                                    "email":contact,"link":link})
                                st.success("Google Apps Script confirmó el envío del correo.")
                            except (RuntimeError,requests.RequestException) as exc:
                                st.error("No pudimos confirmar el envío: "+str(exc))
    st.markdown("##### Respuestas recibidas en el receptor")
    admin_token=cfg.get("CLARIFICATIONS_ADMIN_TOKEN","")
    if admin_token:
        if st.button("Consultar respuestas y estados",key="read_answers_"+rid):
            try:
                data=call_backend("clarify_list",{"admin_token":admin_token})
                st.session_state["clarification_index"]=data.get("items",[])
            except (RuntimeError,requests.RequestException) as exc:
                st.error("No fue posible consultar las aclaraciones: "+str(exc))
        entries=[x for x in st.session_state.get("clarification_index",[])
                 if x.get("submission_id")==record["submission_id"]]
        if entries:
            for i,entry in enumerate(entries,1):
                with st.expander("Solicitud "+str(i)+" · "+str(entry.get("status","pending"))):
                    st.caption("Creada: "+str(entry.get("created_at_utc",""))+
                               " · Vence: "+str(entry.get("expires_at_utc","")))
                    for response in entry.get("answers",[]):
                        st.markdown("**"+str(response.get("id",""))+"**")
                        st.write(response.get("respuesta",""))
                    st.caption("Las respuestas recibidas no se consideran verificadas automáticamente.")
        else:st.caption("No hay respuestas consultadas de este proyecto.")
    st.markdown("##### Validación de las preguntas por el equipo")
    for q in questions:
        qid=q["id"];old=review.get("revision",{}).get(qid,{})
        with st.expander(q["pregunta"]+" · Estado interno"):
            options=["pendiente","aclarar","confirmado","descartado"]
            state=st.selectbox("Estado",options,index=options.index(old.get("estado")) if old.get("estado") in options else 0,
                               key="rev_state_"+rid+"_"+qid)
            note=st.text_area("Evidencia o motivo",value=old.get("nota",""),
                              key="rev_note_"+rid+"_"+qid)
            review.setdefault("revision",{})[qid]={"estado":state,"nota":note}
    st.caption("Una respuesta no resuelve por sí sola una pregunta: debe confirmarla el responsable.")

with tabs[2]:
    st.markdown("#### Dirección de arte · Tres alternativas")
    st.caption("La investigación se prepara para ChatGPT y la decisión creativa la toma Puente. Las hipótesis nunca aparecen en el formulario del cliente.")
    with st.expander("Biblioteca de referencias y fuentes"):
        cat=st.selectbox("Categoría",category_names())
        term=st.text_input("Buscar corriente o concepto")
        found=search_catalog(term,cat)
        st.caption(str(len(found))+" entradas")
        for item in found[:15]:
            st.markdown("**"+item["nombre"]+"** · "+item["categoria"])
            st.caption("Rasgos: "+", ".join(item["rasgos"]))
            st.caption("Investigación: "+item.get("validacion_historica","pendiente"))
        st.markdown("**Fuentes de metodología**")
        for source in BIBLIOGRAPHY:
            st.markdown("["+source["titulo"]+"]("+source["url"]+") · "+source["alcance"])
    st.markdown("##### Investigación con ChatGPT · Sin API")
    st.info("Cuando el briefing y sus aclaraciones estén listos, prepara la investigación aquí. ChatGPT sugerirá corrientes; tú las compararás y aprobarás. No se ejecuta ni cobra una API desde el panel.")
    if any(review.get("revision",{}).get(q["id"],{}).get("estado") not in ("confirmado","descartado") for q in questions):
        st.warning("Hay aclaraciones pendientes. Puedes investigar de manera preliminar, pero no aprobar producción.")
    prompt=build_creative_prompt(answers,audit)
    with st.expander("Revisar el contenido antes de compartirlo"):
        approved_prompt=st.text_area("Texto de investigación",value=prompt,height=260,
            key="creative_prompt_preview_"+rid,
            help="Revisa que no haya información privada, confidencial o sin autorización.")
    st.download_button("Descargar encargo de investigación para ChatGPT (.txt)",
        data=approved_prompt.encode("utf-8"),
        file_name="puente-investigacion-"+str(record["submission_id"])[:8]+".txt",
        mime="text/plain",key="creative_prompt_download_"+rid)
    st.caption("El archivo contiene exactamente el texto revisado en el desplegable. Abre ChatGPT, pega el encargo y analiza las alternativas antes de registrar la decisión.")
    with st.expander("Importar tres alternativas estructuradas de ChatGPT"):
        raw=st.text_area("Pega solamente el JSON de propuestas",height=180,key="creative_json_"+rid)
        if st.button("Validar e importar propuestas",key="import_directions_"+rid):
            if len(raw)>100_000:
                st.error("El texto es demasiado grande.")
            else:
                try:
                    proposals=import_creative_json(raw,answers)
                    review["corrientes"]=proposals
                    review["direccion_seleccionada"]=None
                    review["autorizacion_produccion"]=False
                    for key in list(st.session_state):
                        if str(key).startswith("direction_"+rid):
                            del st.session_state[key]
                    st.rerun()
                except (ValueError,TypeError,KeyError) as exc:
                    st.error("No fue posible importar: "+str(exc))
    old_currents=review.get("corrientes") or []
    number=st.selectbox("Alternativas a comparar",[2,3],index=1 if len(old_currents)==3 else 0,
                        key="direction_"+rid+"_count")
    new_currents=[]
    for i in range(number):
        previous=old_currents[i] if i<len(old_currents) and isinstance(old_currents[i],dict) else {}
        with st.expander("Alternativa "+str(i+1),expanded=i==0):
            name=st.text_input("Corriente madre",value=previous.get("nombre",""),key="direction_"+rid+"_name_"+str(i))
            reason=st.text_area("Fundamento",value=previous.get("fundamento",""),
                     key="direction_"+rid+"_reason_"+str(i))
            contrast=st.text_area("Diferencia frente a otras alternativas",
                     value=previous.get("diferenciacion",""),key="direction_"+rid+"_contrast_"+str(i))
            risk=st.text_area("Riesgos",value=previous.get("riesgos",""),
                     key="direction_"+rid+"_risk_"+str(i))
            new_currents.append({"nombre":name,"fundamento":reason,
                        "diferenciacion":contrast,"riesgos":risk})
    review["corrientes"]=new_currents
    names=[x["nombre"].strip() for x in new_currents if x["nombre"].strip()]
    available=["Sin seleccionar"]+names
    selected_direction=review.get("direccion_seleccionada")
    selected_i=available.index(selected_direction) if selected_direction in available else 0
    chosen_name=st.selectbox("Dirección elegida por Puente",available,index=selected_i,
                      key="direction_"+rid+"_chosen")
    review["direccion_seleccionada"]=None if chosen_name=="Sin seleccionar" else chosen_name
    review["observaciones"]=st.text_area("Justificación editorial del director de arte",
        value=review.get("observaciones",""),key="direction_"+rid+"_justification")
    with st.expander("Criterios profesionales de evaluación"):
        for key,value in CRITERIA.items():
            st.write("**"+key.replace("_"," ").capitalize()+"** · "+value)

with tabs[3]:
    st.markdown("#### Preparación para producción")
    review["responsable"]=st.text_input("Responsable de la aprobación",
        value=review.get("responsable",""),key="responsible_"+rid)
    review["autorizacion_produccion"]=st.checkbox(
        "Confirmo que he revisado los datos y autorizo preparar producción.",
        value=bool(review.get("autorizacion_produccion")),key="production_"+rid)
    errors=validate_review(review,record,audit)
    if errors:
        st.warning(str(len(errors))+" requisitos sin resolver. No se autoriza producción.")
        with st.expander("Ver bloqueos",expanded=True):
            for e in errors:st.write("• "+e)
    elif review["autorizacion_produccion"]:
        st.success("Revisión completada y autorización registrada para esta sesión.")
    else:
        st.info("Revisión completa; falta autorización expresa.")
    st.markdown("**Información para iniciar cada tarea**")
    for name,item in handoff["preparacion"].items():
        with st.expander(name.replace("_"," ").capitalize()):
            st.write("Por completar: "+(", ".join(item["informacion_pendiente"]) or "Revisión humana pendiente"))
    st.caption("La autorización de esta beta no sustituye un registro auditado de permisos ni el contrato.")
    st.divider()
    st.markdown("#### Taller de piezas gráficas")
    st.caption("Define una ficha por publicación o reel. Los formatos se especifican antes de generar; la ejecución se desbloquea solo con una dirección aprobada.")
    templates={"Por confirmar":None,"Redes básico (referencial)":"basico",
               "Redes ampliado (referencial)":"ampliado",
               "Branding (referencial)":"branding"}
    selected_contract=st.selectbox("Plan contratado",list(templates),
        help="Selección informativa: verificar contra la cotización o contrato antes de entregar piezas.",
        key="graphics_contract_"+rid)
    saved_pieces=review.get("production_pieces")
    if not isinstance(saved_pieces,list):
        saved_pieces=[]
    default_count=len(saved_pieces) if saved_pieces else 1
    piece_count=st.number_input("Cantidad de piezas a preparar",min_value=1,max_value=30,
        value=min(default_count,30),step=1,key="graphics_count_"+rid)
    editable=[]
    for n in range(int(piece_count)):
        previous=saved_pieces[n] if n<len(saved_pieces) and isinstance(saved_pieces[n],dict) else {}
        with st.expander("Pieza "+str(n+1)+" · "+str(previous.get("titulo") or "Nueva"),expanded=n==0):
            formats=list(FORMAT_PRESETS)
            original_kind=previous.get("formato_id")
            kind=st.selectbox("Formato de publicación",formats,
                index=formats.index(original_kind) if original_kind in formats else 0,
                format_func=lambda k:FORMAT_PRESETS[k]["label"]+
                    " ("+str(FORMAT_PRESETS[k]["width"])+"×"+str(FORMAT_PRESETS[k]["height"])+")",
                key="graphics_format_"+rid+"_"+str(n))
            title=st.text_input("Tema / título",value=previous.get("titulo",""),
                key="graphics_title_"+rid+"_"+str(n))
            objective=st.text_area("Objetivo de esta pieza",value=previous.get("objetivo",""),
                height=75,key="graphics_objective_"+rid+"_"+str(n))
            main_message=st.text_area("Mensaje principal",value=previous.get("mensaje_principal",""),
                height=75,key="graphics_message_"+rid+"_"+str(n))
            cta=st.text_input("Llamado a la acción",value=previous.get("cta",""),
                key="graphics_cta_"+rid+"_"+str(n))
            visual=st.text_area("Dirección visual y composición",value=previous.get("instrucciones_visuales",""),
                height=85,key="graphics_visual_"+rid+"_"+str(n))
            assets=st.text_input("Fotografías / logos disponibles y autorizados",value=previous.get("activos_fuente",""),
                key="graphics_assets_"+rid+"_"+str(n))
            caption=st.text_area("Pie de texto de la publicación",value=previous.get("copy",""),
                height=95,key="graphics_copy_"+rid+"_"+str(n))
            editable.append(build_piece(record["submission_id"],n+1,kind,title,objective,
                main_message,cta,visual,assets,caption))
    review["production_pieces"]=editable
    review["production_plan_id"]=templates[selected_contract]
    notes=st.text_area("Notas generales del director de arte",
        value=review.get("production_notes",""),height=90,key="graphics_notes_"+rid)
    review["production_notes"]=notes
    graphic_plan=build_production_plan(record,review,audit,editable,notes,templates[selected_contract])
    if graphic_plan["bloqueos"]:
        st.warning("El plan de producción todavía está bloqueado. "+
                   str(len(graphic_plan["bloqueos"]))+" condiciones requieren revisión.")
        with st.expander("Ver requisitos pendientes para producir"):
            for blocker in graphic_plan["bloqueos"]:
                st.write("• "+blocker)
    else:
        st.success("Fichas completas: puedes preparar los encargos individuales de producción gráfica.")
        for p in editable:
            with st.expander("Encargo listo: "+p["titulo"]):
                st.code(production_prompt(graphic_plan,p),language="text")
                st.download_button("Descargar encargo "+p["piece_id"].split("-")[-1],
                    production_prompt(graphic_plan,p),
                    file_name="puente-"+p["piece_id"]+".txt",
                    mime="text/plain",key="export_piece_"+p["piece_id"])
    st.download_button("Exportar planificación de piezas (JSON)",
        export_plan(graphic_plan),
        file_name="puente-produccion-"+str(record["submission_id"])[:8]+".json",
        mime="application/json",key="export_production_"+rid)
    st.caption("La planificación se conserva junto a la revisión interna al pulsar «Guardar revisión en Sheets» en Documentos. Las piezas finales se deben diseñar, revisar y exportar por separado.")

with tabs[4]:
    st.markdown("#### Documentos y entregables")
    st.info("La generación de PDF basada en planes contratados está planificada. No se crea un manual de marca si el cliente solo contrata redes sociales.")
    st.markdown("**Historial de revisión en Google Sheets**")
    st.caption("Cuando habilitemos el receptor actualizado, cada guardado conservará una nueva versión con el responsable; nunca sobrescribe las respuestas originales.")
    admin_token=cfg.get("CLARIFICATIONS_ADMIN_TOKEN","")
    if admin_token:
        first,second=st.columns(2)
        with first:
            if st.button("Guardar revisión en Sheets",key="save_review_"+rid):
                if not str(review.get("responsable") or "").strip():
                    st.warning("Identifica primero al responsable en la pestaña Producción.")
                else:
                    try:
                        response=call_backend("review_save",{
                            "admin_token":admin_token,
                            "submission_id":record["submission_id"],
                            "review":review})
                        st.success("Revisión registrada en la hoja de historial. "+
                                   str(response.get("saved_at_utc","")))
                    except (RuntimeError,requests.RequestException) as exc:
                        st.error("No se pudo guardar: "+str(exc))
        with second:
            if st.button("Recuperar última revisión guardada",key="restore_saved_"+rid):
                try:
                    response=call_backend("review_get",{
                        "admin_token":admin_token,"submission_id":record["submission_id"]})
                    if not response.get("found"):
                        st.info("Todavía no hay revisiones guardadas de esta marca.")
                    else:
                        candidate=response.get("review") or {}
                        if candidate.get("submission_id")!=record["submission_id"] or candidate.get("schema_version")!="puente_review_0_8":
                            raise ValueError("La revisión guardada no corresponde al proyecto.")
                        st.session_state[rid]=candidate
                        for key in list(st.session_state):
                            if str(key).startswith(("rev_state_"+rid,"rev_note_"+rid,
                                  "direction_"+rid,"production_"+rid,"responsible_"+rid)):
                                del st.session_state[key]
                        st.rerun()
                except (ValueError,RuntimeError,requests.RequestException) as exc:
                    st.error("No se pudo recuperar: "+str(exc))
    else:
        st.caption("Guardado en Sheets pendiente de configuración. Puedes descargar una copia local abajo.")
    st.markdown("**Exportar trabajo de esta sesión**")
    errors=validate_review(review,record,audit)
    package=prepare_reviewed_package(handoff,review,audit)
    st.download_button("Guardar revisión interna (JSON)",
        json.dumps(review,ensure_ascii=False,indent=2),
        file_name="puente-revision-"+str(record["submission_id"])[:8]+".json",
        mime="application/json")
    st.download_button("Descargar paquete creativo (JSON)",
        json.dumps(package,ensure_ascii=False,indent=2),
        file_name="puente-paquete-"+str(record["submission_id"])[:8]+".json",
        mime="application/json")
    with st.expander("Restaurar revisión desde un archivo"):
        uploaded=st.file_uploader("Archivo JSON de revisión",type=["json"],key="recover_"+rid)
        if uploaded and st.button("Restaurar esta revisión",key="restore_"+rid):
            if uploaded.size>200000:
                st.error("Archivo demasiado grande.")
            else:
                try:
                    candidate=json.loads(uploaded.getvalue().decode("utf-8"))
                    if (not isinstance(candidate,dict) or
                        candidate.get("schema_version")!="puente_review_0_8" or
                        candidate.get("submission_id")!=record["submission_id"]):
                        raise ValueError("No corresponde al briefing.")
                    st.session_state[rid]=candidate
                    for key in list(st.session_state):
                        if key.startswith(("rev_state_"+rid,"rev_note_"+rid,
                              "direction_"+rid,"production_"+rid,"responsible_"+rid)):
                            del st.session_state[key]
                    st.rerun()
                except (ValueError,UnicodeDecodeError,TypeError) as exc:
                    st.error("No se pudo cargar la revisión: "+str(exc))
    st.caption("El guardado persistente requiere desplegar la nueva versión de Apps Script. Si no está activado, descarga tu revisión para conservarla.")
