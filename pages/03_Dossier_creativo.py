"""Conserva la navegación del PR DCP-02 sin otro flujo de aprobación."""
import streamlit as st

st.set_page_config(page_title='Dossier creativo | PUENTE', page_icon='🎨')
st.title('Dirección creativa · Dossier profesional')
st.info('El dossier se revisa en el Escritorio creativo, dentro de la ficha del briefing.')
st.page_link('pages/01_Panel_interno.py', label='Abrir el Escritorio creativo', icon='🎨')
st.caption('La producción manual, híbrida o con IA se decide después de la dirección creativa. Esta página no concede acceso ni registra aprobaciones.')
