"""Interfaz compartida del dossier; no llama a backend ni genera imágenes."""
import json
import streamlit as st
import streamlit.components.v1 as components
from dossier_engine import dossier_html, handoff
from dossier_adapter import parse_dossier, bind_dossier, approve_bound, quality_evidence, verify_context, research_request
from dossier_pdf import dossier_pdf


def render_dossier_workspace(record, audit, review, sample=None):
    sid = str(record['submission_id'])
    prefix = 'dossier_' + sid
    st.subheader('Dossier de dirección creativa')
    st.caption('Compara alternativas, registra la decisión humana y entrega dirección de arte. La producción se decide después.')
    with st.expander('Preparar investigación manual con ChatGPT'):
        st.caption('Revisa el contenido antes de compartirlo; los campos de contenido pueden contener datos privados.')
        request = st.text_area('Encargo editable', research_request(record,audit), height=140, key=prefix+'_request')
        st.download_button('Descargar encargo de dossier', request, 'puente-encargo-dossier.txt', 'text/plain',key=prefix+'_request_download')
    raw = st.text_area('Dossier JSON', value=json.dumps(sample, ensure_ascii=False, indent=2) if sample else '',
                       height=160, key=prefix+'_input')
    if st.button('Validar dossier', key=prefix+'_validate', type='primary'):
        st.session_state.pop(prefix+'_package', None)
        try:
            pkg = bind_dossier(parse_dossier(raw), record, audit)
            if pkg['validation']['errors']:
                st.error('Corrige el dossier: ' + '; '.join(pkg['validation']['errors']))
            else:
                st.session_state[prefix+'_package'] = pkg
        except (ValueError, TypeError, KeyError) as exc:
            st.error(str(exc))
    pkg = st.session_state.get(prefix+'_package')
    if not pkg:
        st.info('Valida dos o tres alternativas para abrir la comparación y el dossier.')
        return
    try:
        verify_context(pkg, record, audit)
    except ValueError as exc:
        st.error(str(exc))
        return
    # Editing the text invalidates downloads/sign-off until the new import is validated.
    try:
        if parse_dossier(raw) != pkg['dossier']:
            st.warning('El texto cambió. Valida nuevamente antes de continuar.')
            return
    except ValueError:
        st.warning('Valida el JSON actualizado antes de continuar.')
        return
    for warning in pkg['validation']['warnings']:
        st.warning(warning)
    st.dataframe(quality_evidence(pkg['dossier'], record), hide_index=True, use_container_width=True)
    st.caption('Las citas se contrastan con el briefing. Las firmas visuales son metadatos; no miden originalidad ni calidad estética.')
    cols = st.columns(len(pkg['dossier']['directions']))
    for col, direction in zip(cols, pkg['dossier']['directions']):
        with col:
            st.markdown('### '+direction['name'])
            st.write(direction['big_idea'])
            st.caption('Diferenciación')
            st.write(direction['differentiation'])
            st.caption('Riesgos')
            st.write('; '.join(direction['risks']))
    html = dossier_html(pkg['dossier'])
    with st.expander('Previsualizar dossier imprimible', expanded=True):
        components.html(html, height=640, scrolling=True)
    st.download_button('Descargar dossier HTML', html, 'puente-dossier.html', 'text/html', key=prefix+'_html')
    st.download_button('Descargar dossier PDF', dossier_pdf(pkg['dossier']), 'puente-dossier.pdf', 'application/pdf', key=prefix+'_pdf')
    st.caption('Abre el HTML y usa Imprimir → Guardar como PDF. Es un borrador exploratorio hasta revisión humana.')
    st.markdown('#### Decisión creativa')
    choices = {d['id']: d['name'] for d in pkg['dossier']['directions']}
    chosen = st.selectbox('Alternativa seleccionada', list(choices), format_func=choices.get, key=prefix+'_chosen')
    reviewer = st.text_input('Responsable de revisión creativa', key=prefix+'_reviewer')
    rationale = st.text_area('Fundamento de la decisión', key=prefix+'_rationale')
    confirmed = st.checkbox('Confirmo que revisé las alternativas y sus fuentes', key=prefix+'_confirm')
    if st.button('Registrar decisión creativa', key=prefix+'_approve', disabled=not confirmed):
        try:
            pkg = approve_bound(pkg, record, audit, review, reviewer, chosen, rationale)
            st.session_state[prefix+'_package'] = pkg
            st.success('Decisión registrada en esta sesión. Descarga el expediente para conservarla.')
        except ValueError as exc:
            st.error(str(exc))
    st.download_button('Descargar expediente de revisión', json.dumps(pkg, ensure_ascii=False, indent=2),
                       'puente-expediente.json', 'application/json', key=prefix+'_json')
    approval = pkg.get('creative_approval') or {}
    if approval.get('approved'):
        st.caption('Dirección registrada: '+choices[approval['selected_direction']]+'. Responsable: '+approval['reviewer'])
        if chosen != approval['selected_direction'] or reviewer != approval['reviewer'] or rationale != approval['rationale']:
            st.warning('La decisión editada requiere registrarse nuevamente antes de descargar el traspaso.')
            return
        route = st.selectbox('Ruta posterior opcional', ['undecided', 'manual', 'hybrid', 'ai'],
                            format_func={'undecided':'Solo dirección creativa', 'manual':'Diseño manual',
                                         'hybrid':'Producción híbrida', 'ai':'Producción con IA'}.get, key=prefix+'_route')
        output = handoff(pkg, route)
        st.download_button('Descargar traspaso', json.dumps(output, ensure_ascii=False, indent=2),
                           'puente-traspaso.json', 'application/json', key=prefix+'_handoff')
        st.info('La decisión creativa no autoriza producción ni publicación. El traspaso requiere revisar alcance y permisos.')
