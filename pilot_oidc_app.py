"""Entrada INDEPENDIENTE para piloto local; apagada por defecto. Sin backend Beta."""
import importlib.util
import json
import os
import uuid
from pathlib import Path

import streamlit as st

from decision_store import DecisionStore, Scope
from native_pilot_access import NativePilotAccess
from review_workflow import new_review


def main():
    st.set_page_config(page_title='PUENTE · Piloto OIDC aislado', page_icon='🌉')
    st.title('PUENTE · Piloto de identidad')
    st.warning('Solo proyectos ficticios. No conecta Beta, Apps Script ni datos de clientes.')
    if os.environ.get('PUENTE_OIDC_PILOT_ENABLED') != '1':
        st.info('Piloto desactivado. No se inicia Google ni se crea una base.')
        return
    if not all(hasattr(st, name) for name in ('login', 'logout', 'user')):
        st.error('Este piloto requiere la versión OIDC del entorno independiente.')
        return
    if importlib.util.find_spec('authlib') is None:
        st.error('Falta la dependencia OIDC del entorno de piloto. No se inicia acceso.')
        return
    # Solo se admite esta entrada local. No usar esta comprobación como control de red.
    try:
        if st.get_option('server.address') not in ('localhost', '127.0.0.1'):
            raise ValueError()
        auth = st.secrets['auth']
        if (auth.get('redirect_uri') != 'http://localhost:8501/oauth2callback'
                or auth.get('server_metadata_url') != 'https://accounts.google.com/.well-known/openid-configuration'
                or auth.get('expose_tokens') or auth.get('client_kwargs')):
            raise ValueError()
        audience = auth['client_id']
        if not all(isinstance(auth.get(k), str) and auth[k].strip()
                   for k in ('client_id', 'client_secret', 'cookie_secret')):
            raise ValueError()
        if len(auth['cookie_secret']) < 32:
            raise ValueError()
        raw_path = os.environ['PUENTE_OIDC_PILOT_DB']
        path = Path(raw_path)
        if not path.is_absolute() or path.is_symlink() or not path.is_file():
            raise ValueError()
        # Evitar crear un registro vacío o abrir accidentalmente una base Beta.
        import sqlite3
        with sqlite3.connect(path.as_uri()+'?mode=ro', uri=True) as db:
            tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {'pilot_users', 'pilot_access_meta'} <= tables:
                raise ValueError()
    except Exception:
        st.error('Configuración del piloto incompleta o no aislada. No se inicia acceso.')
        return
    if not st.user.is_logged_in:
        if st.button('Identificarme con Google'):
            st.login()
        return
    if st.button('Cerrar sesión'):
        st.logout()
        return
    # Claims suministrados por Streamlit tras su callback nativo. Nunca text_input/JSON.
    user = dict(st.user)
    user['is_logged_in'] = st.user.is_logged_in
    try:
        access = NativePilotAccess(path, audience)
        projects = access.projects(user)
        actor = access.actor(user)
        store = DecisionStore(path, access.policy(user))
        fixtures = {}
        for source in (Path(__file__).parent/'examples').glob('*_synthetic.json'):
            fixture = json.loads(source.read_text(encoding='utf-8'))
            project = fixture['record']['submission_id']
            if project in projects:
                fixtures[project] = fixture
        if not fixtures:
            st.info('No hay fixtures correspondientes a los proyectos asignados.')
            return
        project = st.selectbox('Proyecto ficticio autorizado', sorted(fixtures))
        scope = Scope('AGENCIA-FICTICIA', project)
        fixture = fixtures[project]
        current = store.load_latest(actor, scope)
        version = current['version'] if current else 0
        st.metric('Versión persistida', version)
        if st.button('Guardar versión ficticia'):
            store.save_revision(actor, scope, fixture['record'], fixture['audit'],
                                new_review(fixture['record'], fixture['audit']), fixture['dossier'], version)
            st.rerun()
        if current:
            directions = {d['id']: d['name'] for d in current['package']['dossier']['directions']}
            st.json(current['package']['dossier'])
            selected = st.selectbox('Dirección creativa', list(directions), format_func=directions.get)
            rationale = st.text_area('Fundamento de la decisión humana')
            decision = st.selectbox('Decisión', ['Aprobar', 'Rechazar'])
            confirmed = st.checkbox('He revisado esta versión ficticia')
            if st.button('Registrar decisión', disabled=not confirmed):
                key = ('pilot_request', actor.subject, project, version)
                if key not in st.session_state:
                    st.session_state[key] = str(uuid.uuid4())
                store.decide(actor, scope, version, selected, rationale, st.session_state[key], decision == 'Aprobar')
                st.session_state.pop(key, None)
                st.success('Decisión registrada. No autoriza producción.')
            latest = store.latest_decision(actor, scope)
            if latest:
                st.write('Estado: '+latest['package']['status'])
        events = store.history(actor, scope)
        st.dataframe([{'fecha': e['at'], 'acción': e['action'], 'resultado': e['result']} for e in events])
        st.caption('Exportaciones deshabilitadas en este paso; no hay enlaces de descarga que eludan una nueva autorización.')
    except PermissionError:
        st.error('Acceso denegado o vencido. Contacta al responsable o vuelve a identificarte.')
        # Bootstrap explícito: solo el propietario ve su propio identificador;
        # no se registra una cuenta ni se le concede permiso por iniciar sesión.
        try:
            enrollment_actor = access.actor(user)
        except PermissionError:
            return
        if st.checkbox('Mostrar mi identificador para solicitar alta al responsable'):
            st.code(enrollment_actor.subject, language=None)
            st.caption('Comparte este identificador solo por el canal privado acordado. No es un alta ni una aprobación.')
    except Exception:
        st.error('Operación no completada. Revisar el registro local sin publicar datos ni credenciales.')


if __name__ == '__main__':
    main()
