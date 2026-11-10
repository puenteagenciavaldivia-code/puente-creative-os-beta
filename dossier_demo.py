"""Demo local de Creative OS; fixtures públicos, sin Secrets ni conexiones."""
import json
from pathlib import Path
import streamlit as st
from review_workflow import new_review
from dossier_ui import render_dossier_workspace

st.set_page_config(page_title='PUENTE · Dirección creativa', page_icon='🌉', layout='wide')
st.title('Dirección creativa primero')
st.caption('Creative OS 1.0 · Rama experimental · Demostración con marcas ficticias')
paths = sorted((Path(__file__).parent/'examples').glob('*_synthetic.json'))
chosen = st.selectbox('Caso ficticio', [str(p) for p in paths], format_func=lambda p: Path(p).stem.replace('_synthetic','').replace('_',' ').title())
fixture = json.loads(Path(chosen).read_text(encoding='utf-8'))
audit = fixture['audit']
record = fixture['record']
review = new_review(record, audit)
with st.expander('Briefing de partida'):
    st.json(record['answers'])
render_dossier_workspace(record, audit, review, fixture['dossier'])
