"""PUENTE — QA estructural de carruseles. Laboratorio, sin despliegue.

Este módulo valida contrato/entregables; no afirma lectura visual semántica,
autenticidad del logo ni aprobación jurídica.
"""
import hashlib
import json
import struct
from pathlib import Path

SIZE=(1080,1350)
PNG_HEADER=b"\x89PNG\r\n\x1a\n"

def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()

def validate_contract(contract):
    errors=[]
    if not isinstance(contract,dict): return ["Contrato ausente"]
    for key in ("brand","post_id","topic","editorial_revision","visual_revision"):
        if not isinstance(contract.get(key),str) or not contract[key].strip():
            errors.append("Falta "+key)
    slides=contract.get("slides")
    count=contract.get("approved_slide_count")
    if type(count) is not int or count<1 or count>20:
        errors.append("Cantidad aprobada inválida")
    if not isinstance(slides,list):return errors+["Láminas ausentes"]
    if count!=len(slides):errors.append("Cantidad distinta a la editorial aprobada")
    ids=[]
    for index,s in enumerate(slides,1):
        if not isinstance(s,dict):
            errors.append("Lámina inválida");continue
        ids.append(s.get("id"))
        if s.get("topic")!=contract.get("topic"):errors.append("Tema distinto en "+str(index))
        if not s.get("headline") or not s.get("purpose"):errors.append("Falta texto o función en "+str(index))
    if len(set(map(str,ids)))!=len(ids):errors.append("Láminas duplicadas")
    if ids!=[str(i).zfill(2) for i in range(1,len(slides)+1)]:
        errors.append("Secuencia incorrecta")
    return errors

def png_dimensions(data):
    if len(data)<24 or data[:8]!=PNG_HEADER or data[12:16]!=b"IHDR":
        raise ValueError("PNG corrupto o no válido")
    return struct.unpack(">II",data[16:24])

def build_asset_record(path,source_size=None):
    blob=Path(path).read_bytes()
    size=png_dimensions(blob)
    return {"file":Path(path).name,"sha256":digest_bytes(blob),"size":list(size),
            "source_size":list(source_size) if source_size else None}

def apply_slide_patch(contract,slide_id,changes,expected_revision):
    """Actualiza un solo contenido; conserva el resto. No modifica archivos PNG."""
    if validate_contract(contract):raise ValueError("Contrato inválido")
    if contract.get("editorial_revision")!=expected_revision:
        raise ValueError("Versión editorial desactualizada")
    if set(changes)-{"headline","purpose","body"}:
        raise ValueError("Campo no autorizado para parche editorial")
    copied=json.loads(json.dumps(contract,ensure_ascii=False))
    matches=[s for s in copied["slides"] if s["id"]==slide_id]
    if len(matches)!=1:raise ValueError("Lámina no encontrada")
    matches[0].update(changes)
    copied["editorial_revision"]=expected_revision+"+patch-"+slide_id
    if validate_contract(copied):raise ValueError("Parche rompe contrato")
    return copied

def release_gate(contract,assets,source_assets=None,approvals=None):
    errors=validate_contract(contract)
    slides=contract.get("slides",[]) if isinstance(contract,dict) else []
    if len(assets)!=len(slides):errors.append("Cantidad de archivos diferente")
    sources=source_assets or {}
    for i,s in enumerate(slides):
        if i>=len(assets):break
        asset=assets[i]
        if asset.get("slide_id")!=s.get("id"):errors.append("Archivo fuera de orden")
        if asset.get("size")!=list(SIZE):errors.append("Formato de archivo incorrecto")
        src=sources.get(asset.get("sha256"))
        if not src or src.get("native") is not True:
            errors.append("No hay fuente individual nativa verificada")
    approvals=approvals or {}
    for k in ("art","legal","brand","publication"):
        if approvals.get(k) is not True:errors.append("Falta aprobación: "+k)
    return {"status":"BLOQUEADO" if errors else "APTO_ESTRUCTURAL",
            "errors":errors,
            "notice":"Los metadatos no garantizan nitidez, composición, derechos ni autenticidad."}
