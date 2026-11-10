"""Proyección explícita de entrega al cliente, independiente del expediente interno."""
from html import escape
from copy import deepcopy
from dossier_adapter import verify_context
from dossier_engine import handoff

DELIVERABLES={'strategy','direction','comparison','sources'}


def client_delivery(package,record,audit,contract):
    verify_context(package,record,audit)
    selected=handoff(package,'undecided')['approved_concept']
    if not isinstance(contract,dict) or contract.get('submission_id')!=record['submission_id']:
        raise ValueError('Contrato ajeno al proyecto.')
    if not isinstance(contract.get('version'),str) or not contract['version'].strip():
        raise ValueError('Falta la versión contractual.')
    included=contract.get('included_deliverables')
    if not isinstance(included,list) or not included or not all(isinstance(x,str) and x in DELIVERABLES for x in included):
        raise ValueError('Entregables contractuales inválidos.')
    dossier=package['dossier']
    out={'brand':dossier['brand'],'contract_version':contract['version'],'production_approved':False,'sections':{}}
    if 'strategy' in included:
        out['sections']['strategy']={k:dossier[k] for k in ('audience','objective')}
    if 'direction' in included:
        out['sections']['direction']={k:selected[k] for k in ('name','big_idea','promise','visual_system','typography','photography','composition','applications')}
    if 'comparison' in included:
        summary=dossier.get('client_summary')
        if not isinstance(summary,str) or len(summary.strip())<25:
            raise ValueError('La comparación necesita un resumen específico revisado para cliente.')
        out['sections']['comparison']=summary
    if 'sources' in included:
        out['sections']['sources']=[{k:s[k] for k in ('origin','usage')}
            for s in dossier['source_register'] if s.get('type') in ('public','licensed') and s.get('approved_for_client') is True]
    return deepcopy(out)


def client_html(delivery):
    """Solo renderiza la proyección; no renderizar directamente un expediente interno."""
    e=lambda x:escape(str(x),quote=True)
    labels={'strategy':'Objetivo y público','direction':'Dirección creativa','comparison':'Comparación',
            'sources':'Referencias aprobadas','audience':'Público','objective':'Objetivo','name':'Propuesta',
            'big_idea':'Idea madre','promise':'Promesa comunicacional','visual_system':'Sistema visual',
            'typography':'Tipografía','photography':'Tratamiento fotográfico','composition':'Composición',
            'applications':'Aplicaciones','feed':'Publicación','carousel':'Carrusel','story':'Historia',
            'reel':'Reel','origin':'Origen','usage':'Uso'}
    def render(value):
        if isinstance(value,dict):return ''.join('<h3>'+e(labels.get(k,k))+'</h3>'+render(v) for k,v in value.items())
        if isinstance(value,list):return '<ul>'+''.join('<li>'+render(v)+'</li>' for v in value)+'</ul>'
        return '<p>'+e(value)+'</p>'
    return ('<!doctype html><html lang="es"><meta charset="utf-8"><title>'+e(delivery['brand'])+'</title>'
            '<style>body{font:16px/1.6 Arial;max-width:850px;margin:40px auto;padding:20px;color:#152639}h1,h2{font-family:Georgia}h2{border-top:2px solid #bc7759;padding-top:20px}@page{margin:20mm}</style>'
            '<h1>'+e(delivery['brand'])+'</h1><p>Propuesta creativa · Contrato '+e(delivery['contract_version'])+'</p>'
            +''.join('<h2>'+e(labels.get(k,k))+'</h2>'+render(v) for k,v in delivery['sections'].items())
            +'<p>Producción y publicación requieren autorización independiente.</p></html>')
