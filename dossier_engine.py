"""Isolated creative-direction-first dossier engine. No network or active-repo writes."""
from __future__ import annotations
import hashlib, json, html, re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

VERSION = 'puente.dossier.v0.2'
ROUTES = ('undecided','manual','hybrid','ai')
MODES = ('creative_only','production_optional')
REQUIRED = ('brand','brief','audience','communication_problem','objective','constraints','directions','comparison','source_register')
DIRECTION_FIELDS = ('id','name','insight','big_idea','promise','visual_system','typography','photography','composition','differentiation','risks','applications','references')
CHANNELS = ('feed','carousel','story','reel')

def digest(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def clean_text(x, minimum=5):
    return isinstance(x,str) and len(x.strip()) >= minimum

def validate_dossier(d):
    errors=[]; warnings=[]
    if not isinstance(d,dict):return {'errors':['dossier must be object'],'warnings':warnings}
    # Boundary checks prevent malformed imported JSON from crashing set/iteration/render.
    dirs=d.get('directions', [])
    sources=d.get('source_register', [])
    if not isinstance(dirs,list) or not isinstance(sources,list):
        return {'errors':['directions and source_register must be lists'],'warnings':[]}
    for item in dirs:
        if not isinstance(item,dict):
            return {'errors':['direction must be object'],'warnings':[]}
        for key in ('id','visual_signature'):
            if not isinstance(item.get(key),str) or not item[key].strip():
                return {'errors':[key+' must be nonempty string'],'warnings':[]}
        for key in ('references','risks'):
            if not isinstance(item.get(key),list) or not all(isinstance(v,str) for v in item[key]):
                return {'errors':[key+' must contain text'],'warnings':[]}
    for source in sources:
        if not isinstance(source,dict) or not isinstance(source.get('id'),str):
            return {'errors':['source must have text id'],'warnings':[]}
    if d.get('schema_version')!=VERSION:errors.append('schema_version incompatible')
    for k in REQUIRED:
        if k not in d:errors.append(f'missing field: {k}')
    for k in ('brand','brief','audience','communication_problem','objective'):
        if not clean_text(d.get(k),6):errors.append(f'{k}: insufficient information')
    if not isinstance(d.get('constraints'),list) or not all(clean_text(x,3) for x in d.get('constraints',[])):
        errors.append('constraints must contain text')
    directions=d.get('directions')
    if not isinstance(directions,list) or len(directions) not in (2,3):
        errors.append('exactly 2 or 3 comparative directions required');directions=[]
    ids=[]; signatures=[]
    for idx,p in enumerate(directions):
        if not isinstance(p,dict):errors.append(f'direction {idx+1} invalid');continue
        ids.append(p.get('id'));signatures.append(p.get('visual_signature'))
        for k in DIRECTION_FIELDS:
            if k not in p:errors.append(f'direction {idx+1}: missing {k}')
            elif k not in ('id','risks','applications','references') and not clean_text(p[k],6):errors.append(f'direction {idx+1}: {k} too short')
        if not isinstance(p.get('risks'),list) or not p['risks']:errors.append(f'direction {idx+1}: risks missing')
        app=p.get('applications',{})
        if not isinstance(app,dict) or set(CHANNELS)-set(app):errors.append(f'direction {idx+1}: incomplete channel applications')
        elif any(not clean_text(app[x],8) for x in CHANNELS):errors.append(f'direction {idx+1}: application underdeveloped')
        if not isinstance(p.get('references'),list) or not p['references']:errors.append(f'direction {idx+1}: references missing')
        if not isinstance(p.get('visual_signature'),str) or not p['visual_signature'].strip():errors.append(f'direction {idx+1}: missing visual_signature')
    if len(set(ids))!=len(ids):errors.append('duplicate direction IDs')
    if len(set(signatures))!=len(signatures):errors.append('duplicate visual signatures')
    names=[p.get('name','').casefold().strip() for p in directions if isinstance(p.get('name'),str)]
    if len(set(names))!=len(names):errors.append('duplicate direction names')
    comparison=d.get('comparison',{})
    if not isinstance(comparison,dict):errors.append('comparison must be object');comparison={}
    for k in ('criteria','tradeoffs','recommendation','rejected_reasons'):
        if not comparison.get(k):errors.append('comparison missing '+k)
    if not isinstance(comparison.get('criteria'),list) or not all(clean_text(x,3) for x in comparison.get('criteria',[])):
        errors.append('comparison criteria must contain text')
    if not clean_text(comparison.get('tradeoffs'),12):errors.append('comparison tradeoffs insufficient')
    if comparison.get('recommendation') not in ids:errors.append('recommended direction does not exist')
    if not isinstance(comparison.get('rejected_reasons'),dict):
        errors.append('rejected_reasons must be object')
    if isinstance(comparison.get('rejected_reasons'),dict):
        for i in ids:
            if i!=comparison.get('recommendation') and not clean_text(comparison['rejected_reasons'].get(i),12):errors.append('insufficient rejection rationale for '+str(i))
    sources=d.get('source_register',[])
    if not isinstance(sources,list):errors.append('source register invalid');sources=[]
    source_ids=set()
    for s in sources:
        if not isinstance(s,dict) or not clean_text(s.get('id'),1) or not all(clean_text(s.get(k),3) for k in ('type','origin','usage')):
            errors.append('incomplete source provenance');continue
        if s['id'] in source_ids: errors.append('duplicate source id')
        source_ids.add(s['id'])
        if s['type'] not in ('client','internal','public','licensed','unverified'):errors.append('invalid source type')
        if s['type']=='unverified':warnings.append('unverified reference '+s['id'])
    for p in directions:
        if isinstance(p,dict):
            for ref in p.get('references',[]):
                if ref not in source_ids:errors.append(f'unknown source reference: {ref}')
    if d.get('requested_route','undecided') not in ROUTES:errors.append('invalid production route')
    # Prevent accidental conflation of creative sign-off with production sign-off.
    if d.get('production_approved') is True:errors.append('production approval must not be embedded into creative dossier')
    if not d.get('competitor_research_confirmed',False):warnings.append('competitive research not independently verified')
    return {'errors':errors,'warnings':warnings}

def prepare(d):
    result=validate_dossier(d)
    return {'schema_version':VERSION,'status':'blocked' if result['errors'] else 'ready_for_creative_review',
            'dossier':deepcopy(d),'hash':digest(d),'validation':result,'creative_approval':None,
            'production_route':'undecided'}

def approve_creative(package, reviewer, selection, rationale, approved=True):
    pkg=deepcopy(package)
    if validate_dossier(pkg['dossier'])['errors']:raise ValueError('Cannot approve invalid dossier')
    if not isinstance(approved,bool):raise ValueError('Approval must be boolean')
    if digest(pkg['dossier'])!=pkg['hash']:raise ValueError('Dossier changed since validation')
    if not clean_text(reviewer,3) or not clean_text(rationale,25):raise ValueError('Real reviewer and rationale required')
    valid_ids={v['id'] for v in pkg['dossier']['directions']}
    if selection not in valid_ids:raise ValueError('Unknown direction')
    pkg['creative_approval']={'reviewer':reviewer,'selected_direction':selection,'rationale':rationale,
         'approval_hash':pkg['hash'],'approved':bool(approved),'timestamp':datetime.now(timezone.utc).isoformat()}
    pkg['status']='creative_approved' if approved else 'creative_rejected'
    return pkg

def handoff(pkg, route):
    if route not in ROUTES:raise ValueError('Unknown route')
    if digest(pkg['dossier'])!=pkg['hash']:raise ValueError('Changed dossier invalidates approvals')
    approval=pkg.get('creative_approval') or {}
    if approval.get('approved') is not True or approval.get('approval_hash')!=pkg['hash']:raise ValueError('No valid creative approval')
    if validate_dossier(pkg['dossier'])['errors']:raise ValueError('Invalid dossier')
    concept=next((v for v in pkg['dossier']['directions'] if v['id']==approval.get('selected_direction')),None)
    if concept is None or not clean_text(approval.get('reviewer'),3):raise ValueError('Invalid creative approval')
    base={'brand':pkg['dossier']['brand'],'approved_concept':concept,'creative_hash':pkg['hash'],
          'approval_reviewer':approval['reviewer'],'route':route,'production_approved':False}
    if route=='undecided':return {'status':'creative_delivery_complete','production_required':False,**base}
    if route=='manual':return {'status':'designer_handoff','deliverables':['creative_dossier','visual_language','channel_examples','reference_register','guardrails'],**base}
    if route=='hybrid':return {'status':'hybrid_scope_pending','requires':['asset_selections','license_checks','designer_role','piece_briefs'],**base}
    return {'status':'ai_scope_pending','requires':['individual_piece_briefs','text_approval','asset_rights','qa_output','human_final_review'],**base}

def dossier_html(d):
    """Offline, printable HTML. Escapes any supplied user strings to prevent injection."""
    validation=validate_dossier(d)
    if validation['errors']:raise ValueError('Cannot render invalid dossier')
    e=lambda v:html.escape(str(v),quote=True)
    sections=[]
    for p in d.get('directions',[]):
        apps=''.join(f'<li><b>{e(k.title())}</b> — {e(p["applications"].get(k,""))}</li>' for k in CHANNELS)
        risks=''.join('<li>'+e(x)+'</li>' for x in p['risks'])
        sections.append(f'''<section class="concept"><div class="eyebrow">DIRECCIÓN {e(p['id'])}</div><h2>{e(p['name'])}</h2>
        <blockquote>{e(p['big_idea'])}</blockquote><div class="two"><div><h3>Insight</h3><p>{e(p['insight'])}</p><h3>Sistema visual</h3><p>{e(p['visual_system'])}</p><h3>Fotografía</h3><p>{e(p['photography'])}</p></div>
        <div><h3>Promesa</h3><p>{e(p['promise'])}</p><h3>Tipografía</h3><p>{e(p['typography'])}</p><h3>Composición</h3><p>{e(p['composition'])}</p></div></div>
        <h3>Aplicaciones indicativas (no artes finales)</h3><ul>{apps}</ul><h3>Riesgos y límites</h3><ul>{risks}</ul><p><b>Diferenciador:</b> {e(p['differentiation'])}</p></section>''')
    refs=''.join(f'<li><b>{e(x.get("id"))}</b> · {e(x.get("type"))} · {e(x.get("origin"))} — {e(x.get("usage"))}</li>' for x in d.get('source_register',[]))
    rec=d.get('comparison',{}).get('recommendation','')
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(d.get('brand'))} · Dirección creativa</title>
    <style>@page{{size:A4;margin:17mm}}*{{box-sizing:border-box}}body{{font:15px/1.55 Arial,sans-serif;color:#152639;background:#f6f1eb;margin:0}}main{{max-width:900px;margin:auto;background:#fff;padding:42px 52px}}h1,h2,blockquote{{font-family:Georgia,serif}}h1{{font-size:43px;line-height:1.1}}h2{{font-size:33px;margin:4px 0 20px}}h3{{font-size:13px;text-transform:uppercase;letter-spacing:.12em;color:#b56b4c}}p,li{{max-width:75ch}}.eyebrow{{text-transform:uppercase;letter-spacing:.22em;color:#b56b4c;font-size:11px;font-weight:bold}}.hero{{padding:30px 0 40px;border-bottom:5px solid #c17d61}}.concept{{padding:35px 0;border-bottom:1px solid #ded7d0;break-inside:avoid}}blockquote{{font-size:24px;margin:18px 0 26px;padding-left:16px;border-left:4px solid #c17d61}}@media(max-width:620px){{main{{padding:24px}}.two{{grid-template-columns:1fr!important}}h1{{font-size:32px}}}}.two{{display:grid;grid-template-columns:1fr 1fr;gap:35px}}.small{{color:#65717b;font-size:12px}}.decision{{background:#f5eee7;padding:20px;margin-top:25px}}@media print{{body{{background:white}}main{{padding:0}}.concept{{break-inside:auto}}}}</style></head>
    <body><main><header class="hero"><div class="eyebrow">PUENTE CREATIVE OS · PROPUESTA DE DIRECCIÓN DE ARTE</div><h1>{e(d.get('brand'))}</h1><p><b>Brief:</b> {e(d.get('brief'))}</p><p><b>Público:</b> {e(d.get('audience'))}</p><p><b>Problema:</b> {e(d.get('communication_problem'))}</p><p><b>Objetivo:</b> {e(d.get('objective'))}</p><p class="small">Dossier exploratorio · No equivale a piezas finales ni a aprobación del cliente.</p></header>
    {''.join(sections)}<section><h3>Restricciones del encargo</h3><ul>{''.join('<li>'+e(x)+'</li>' for x in d.get('constraints',[]))}</ul></section><section class="decision"><h3>Recomendación editorial para revisión humana</h3><h2>{e(rec)}</h2><p>{e(d.get('comparison',{}).get('tradeoffs',''))}</p><h3>Criterios de comparación</h3><p>{e(d.get('comparison',{}).get('criteria',''))}</p><h3>Motivos para no priorizar otras rutas</h3><ul>{''.join('<li><b>'+e(k)+'</b>: '+e(v)+'</li>' for k,v in d.get('comparison',{}).get('rejected_reasons',{}).items())}</ul></section><section><h3>Procedencia de referencias</h3><ul>{refs}</ul><p class="small">Advertencias de investigación: {e('; '.join(validation['warnings']) or 'Sin advertencias registradas')}</p></section></main></body></html>'''

def write_dossier(d,path):
    p=Path(path);p.write_text(dossier_html(d),encoding='utf-8');return p
