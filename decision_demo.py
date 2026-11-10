"""Laboratorio local persistente con identidades SIMULADAS; no es un login."""
import json
import os
import uuid
from pathlib import Path
import streamlit as st
from decision_store import Actor, Scope, DecisionStore
from review_workflow import new_review

st.set_page_config(page_title='PUENTE · Decisiones de laboratorio', page_icon='🌉', layout='wide')
st.title('Decisiones creativas con historial')
st.warning('LABORATORIO: identidades simuladas seleccionables. No autentica Google ni protege datos reales.')
paths = sorted((Path(__file__).parent/'examples').glob('*_synthetic.json'))
path = st.selectbox('Caso ficticio', paths, format_func=lambda p:p.stem.replace('_synthetic','').replace('_',' ').title())
fixture = json.loads(path.read_text(encoding='utf-8'))
scope = Scope('AGENCIA-FICTICIA', fixture['record']['submission_id'])
identity = st.selectbox('Identidad simulada', ['direccion-ficticia','operacion-ficticia'])
actor = Actor('laboratorio-local', identity)
def policy(who, target, action):
    if target.agency != 'AGENCIA-FICTICIA' or not target.project.startswith('SYNTH-') or who.issuer != 'laboratorio-local':
        return False
    if who.subject == 'direccion-ficticia':
        return action in {'read','write','decide','history'}
    if who.subject == 'operacion-ficticia':
        return action in {'read','write','history'}
    return False

store_path = os.environ.get('PUENTE_DECISION_LAB_PATH') or str(Path(__file__).parent/'.local/decision_demo.sqlite')
store = DecisionStore(store_path,policy)
current = store.load_latest(actor,scope)
version = current['version'] if current else 0
version_display = st.empty()
version_display.metric('Versión persistida', version)
st.caption('Guardar una nueva versión invalida las decisiones anteriores. La producción permanece sin autorizar.')
if st.button('Guardar nueva versión ficticia',type='primary'):
    try:
        version = store.save_revision(actor,scope,fixture['record'],fixture['audit'],
                                      new_review(fixture['record'],fixture['audit']),fixture['dossier'],version)
        current = store.load_latest(actor,scope)
        version_display.metric('Versión persistida', version)
        st.success('Versión '+str(version)+' guardada con su evento de auditoría.')
    except (ValueError,PermissionError) as exc:
        st.error(str(exc))
if current:
    directions = {d['id']:d['name'] for d in current['package']['dossier']['directions']}
    selected = st.selectbox('Alternativa',list(directions),format_func=directions.get)
    rationale = st.text_area('Fundamento de la decisión')
    decision = st.selectbox('Decisión',['Aprobar dirección creativa','Rechazar propuesta'])
    confirmed = st.checkbox('He revisado la versión y las alternativas ficticias')
    if st.button('Guardar decisión', disabled=not confirmed):
        key = 'decision_request_'+scope.project+'_'+identity+'_'+str(version)
        if key not in st.session_state:
            st.session_state[key] = str(uuid.uuid4())
        try:
            store.decide(actor,scope,version,selected,rationale,st.session_state[key],decision.startswith('Aprobar'))
            st.session_state.pop(key,None)
            st.success('Decisión persistida. No habilita producción.')
        except (ValueError,PermissionError) as exc:
            st.error(str(exc))
    latest = store.latest_decision(actor,scope)
    if latest:
        st.write('Última decisión de esta versión: '+latest['package']['status'])
        st.download_button('Descargar decisión',json.dumps(latest,ensure_ascii=False,indent=2),
                           'puente-decision-ficticia.json','application/json')
    else:
        st.info('Esta versión todavía no tiene una decisión.')
history = store.history(actor,scope)
st.subheader('Historial persistido')
st.dataframe([{'fecha':e['at'],'actor':e['subject'],'acción':e['action'],'resultado':e['result']}
              for e in history],hide_index=True)
st.download_button('Descargar historial',json.dumps(history,ensure_ascii=False,indent=2),
                   'puente-historial-ficticio.json','application/json')
