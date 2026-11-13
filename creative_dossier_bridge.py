"""Adaptador optativo de Creative OS Beta 1.1 al dossier autónomo.
No produce piezas, no cambia Google, no simula aprobaciones humanas.
"""
from __future__ import annotations
from dossier_engine import prepare, approve_creative, handoff, digest, validate_dossier
from review_workflow import validate_review

def prepare_for_brief(record,dossier):
    if not isinstance(record,dict) or not record.get("submission_id"):
        raise ValueError("Briefing sin identificador")
    brand=str((record.get("answers") or {}).get("nombre") or "").strip()
    if not brand:raise ValueError("Marca ausente del briefing")
    if not isinstance(dossier,dict) or brand.casefold() not in str(dossier.get("brand","")).casefold():
        raise ValueError("La marca del dossier no corresponde al briefing")
    package=prepare(dossier)
    package["source_briefing_id"]=str(record["submission_id"])
    package["source_briefing_hash"]=digest(record)
    return package

def finalize_from_review(package,record,audit,review):
    if not isinstance(package,dict) or not isinstance(record,dict):
        raise ValueError("Paquete o briefing inválido")
    if str(record.get("submission_id"))!=package.get("source_briefing_id") or digest(record)!=package.get("source_briefing_hash"):
        raise ValueError("El briefing cambió: revisar dossier")
    errors=validate_review(review,record,audit)
    if errors:raise ValueError("Revisión incompleta: "+"; ".join(errors))
    if validate_dossier(package.get("dossier"))["errors"]:raise ValueError("Dossier incompleto")
    selection=str(review.get("direccion_seleccionada") or "").strip().casefold()
    matches=[d for d in package["dossier"]["directions"] if d["name"].strip().casefold()==selection]
    if len(matches)!=1:raise ValueError("La selección no coincide con el dossier")
    return approve_creative(package,str(review["responsable"]),matches[0]["id"],str(review["observaciones"]))

def deliver_creative(package,route="undecided"):
    return handoff(package,route)
