"""Módulo aislado: dirección creativa autónoma, producción siempre opcional."""
from __future__ import annotations
import hashlib, html, json
from copy import deepcopy
from datetime import datetime, timezone

VERSION="puente.dossier.v0.2"
ROUTES=("undecided","manual","hybrid","ai")
CHANNELS=("feed","carousel","story","reel")
FIELDS=("id","name","insight","big_idea","promise","visual_system","typography","photography","composition","differentiation","risks","applications","references")

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def _text(value,length=6):
    return isinstance(value,str) and len(value.strip())>=length

def validate_dossier(d):
    errors=[]; warnings=[]
    if not isinstance(d,dict):return {"errors":["El dossier debe ser un objeto"],"warnings":[]}
    if d.get("schema_version")!=VERSION:errors.append("Versión incompatible")
    for k in ("brand","brief","audience","communication_problem","objective"):
        if not _text(d.get(k)):errors.append("Campo incompleto: "+k)
    if not isinstance(d.get("constraints"),list):errors.append("Faltan restricciones")
    directions=d.get("directions")
    if not isinstance(directions,list) or len(directions) not in (2,3):
        errors.append("Se requieren 2–3 conceptos");directions=[]
    ids=[];signatures=[]
    for index,p in enumerate(directions,1):
        if not isinstance(p,dict):errors.append("Concepto no válido: "+str(index));continue
        ids.append(p.get("id"));signatures.append(p.get("visual_signature"))
        for key in FIELDS:
            if key not in p:errors.append("Falta "+key+" en concepto "+str(index))
            elif key not in ("id","risks","applications","references") and not _text(p[key]):errors.append("Campo breve: "+key)
        if not isinstance(p.get("visual_signature"),str) or not p["visual_signature"].strip():errors.append("Firma visual ausente")
        if not isinstance(p.get("risks"),list) or not p["risks"]:errors.append("Riesgos ausentes")
        apps=p.get("applications")
        if not isinstance(apps,dict) or any(not _text(apps.get(k),8) for k in CHANNELS):errors.append("Aplicaciones de formatos incompletas")
        if not isinstance(p.get("references"),list) or not p["references"]:errors.append("Referencias ausentes")
    if len(ids)!=len(set(map(str,ids))):errors.append("IDs de conceptos repetidos")
    if len(signatures)!=len(set(map(str,signatures))):errors.append("Lenguajes visuales repetidos")
    comparison=d.get("comparison")
    if not isinstance(comparison,dict):comparison={};errors.append("Comparación ausente")
    for key in ("criteria","tradeoffs","recommendation","rejected_reasons"):
        if not comparison.get(key):errors.append("Comparación incompleta: "+key)
    if comparison.get("recommendation") not in ids:errors.append("Recomendación no corresponde a concepto")
    reasons=comparison.get("rejected_reasons")
    if isinstance(reasons,dict):
        for i in ids:
            if i!=comparison.get("recommendation") and not _text(reasons.get(i),12):errors.append("Falta justificación de alternativa descartada")
    sources=d.get("source_register")
    if not isinstance(sources,list):sources=[];errors.append("Faltan fuentes")
    known=set()
    for s in sources:
        if not isinstance(s,dict) or not all(_text(s.get(k),3) for k in ("id","type","origin","usage")):
            errors.append("Fuente incompleta");continue
        if s["id"] in known:errors.append("ID de fuente repetido")
        known.add(s["id"])
        if s["type"] not in ("client","internal","public","licensed","unverified"):errors.append("Tipo de fuente inválido")
        if s["type"]=="unverified":warnings.append("Referencia no verificada: "+s["id"])
    for p in directions:
        if isinstance(p,dict):
            for ref in p.get("references",[]) if isinstance(p.get("references"),list) else []:
                if ref not in known:errors.append("Referencia inexistente: "+str(ref))
    if d.get("requested_route","undecided") not in ROUTES:errors.append("Ruta de producción no válida")
    if d.get("production_approved") is True:errors.append("La aprobación de producción no pertenece al dossier")
    if not d.get("competitor_research_confirmed"):warnings.append("Investigación competitiva sin verificación independiente")
    return {"errors":errors,"warnings":warnings}

def prepare(d):
    validation=validate_dossier(d)
    return {"schema_version":VERSION,"status":"blocked" if validation["errors"] else "ready_for_creative_review",
            "dossier":deepcopy(d),"hash":digest(d),"validation":validation,"creative_approval":None,"production_route":"undecided"}

def approve_creative(package,reviewer,selection,rationale,approved=True):
    pkg=deepcopy(package)
    if pkg.get("validation",{}).get("errors") or validate_dossier(pkg.get("dossier"))["errors"]:raise ValueError("Dossier inválido")
    if digest(pkg["dossier"])!=pkg.get("hash"):raise ValueError("Dossier modificado")
    if not _text(reviewer,3) or not _text(rationale,25):raise ValueError("Responsable y fundamentación obligatorios")
    if selection not in {v["id"] for v in pkg["dossier"]["directions"]}:raise ValueError("Concepto desconocido")
    pkg["creative_approval"]={"reviewer":reviewer,"selected_direction":selection,"rationale":rationale,
                              "approval_hash":pkg["hash"],"approved":bool(approved),
                              "timestamp":datetime.now(timezone.utc).isoformat()}
    pkg["status"]="creative_approved" if approved else "creative_rejected"
    return pkg

def handoff(pkg,route="undecided"):
    if route not in ROUTES:raise ValueError("Ruta desconocida")
    if digest(pkg["dossier"])!=pkg.get("hash"):raise ValueError("Cambios invalidan aprobación")
    approval=pkg.get("creative_approval") or {}
    if not approval.get("approved") or approval.get("approval_hash")!=pkg["hash"]:raise ValueError("Falta revisión creativa")
    concept=next(v for v in pkg["dossier"]["directions"] if v["id"]==approval["selected_direction"])
    base={"brand":pkg["dossier"]["brand"],"approved_concept":deepcopy(concept),"creative_hash":pkg["hash"],
          "approval_reviewer":approval["reviewer"],"route":route,"production_approved":False}
    status={"undecided":"creative_delivery_complete","manual":"designer_handoff",
            "hybrid":"hybrid_scope_pending","ai":"ai_scope_pending"}[route]
    return {"status":status,"production_required":False if route=="undecided" else None,**base}

def dossier_html(d):
    """Vista preliminar imprimible; nunca presenta prototipos como arte final."""
    e=lambda x:html.escape(str(x),quote=True)
    sections=[]
    for p in d.get("directions",[]):
        if not isinstance(p,dict):continue
        apps=p.get("applications") if isinstance(p.get("applications"),dict) else {}
        li="".join("<li><b>"+e(k)+"</b>: "+e(apps.get(k,""))+"</li>" for k in CHANNELS)
        sections.append('<section><small>PROPUESTA '+e(p.get("id"))+'</small><h2>'+e(p.get("name"))+'</h2><blockquote>'+e(p.get("big_idea"))+'</blockquote><p><b>Insight:</b> '+e(p.get("insight"))+'</p><p><b>Sistema visual:</b> '+e(p.get("visual_system"))+'</p><p><b>Tipografía:</b> '+e(p.get("typography"))+'</p><p><b>Fotografía:</b> '+e(p.get("photography"))+'</p><h3>Aplicaciones sugeridas</h3><ul>'+li+'</ul></section>')
    return '<!doctype html><html lang="es"><head><meta charset="utf-8"><title>'+e(d.get("brand"))+' | Dirección creativa</title><style>body{font:15px/1.55 Arial,sans-serif;color:#25334a;background:#f7f4ee;margin:auto;max-width:850px;padding:40px}h1,h2,blockquote{font-family:Georgia,serif}section{background:white;margin:25px 0;padding:30px;break-inside:avoid}h1{font-size:40px}small{letter-spacing:.13em;color:#b4775a}blockquote{font-size:23px;border-left:4px solid #b4775a;padding-left:20px}@media print{body{background:white;padding:0}section{padding:10px}}</style></head><body><h1>'+e(d.get("brand"))+'</h1><p>Propuesta de dirección creativa · Sujeta a revisión humana. No son artes finales.</p>'+''.join(sections)+'</body></html>'
