"""Biblioteca curada de referencias para explorar corrientes, técnicas y enfoques."""
import json
from pathlib import Path

CATALOG_PATH=Path(__file__).with_name("design_catalog.json")

def read_catalog():
    data=json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    items=data.get("corrientes",[])
    if not isinstance(items,list):
        raise ValueError("Formato de catálogo inválido")
    return items

def search_catalog(query="",category="Todas"):
    items=read_catalog()
    text=query.strip().casefold()
    return [item for item in items if
        (category=="Todas" or item.get("categoria")==category)
        and (not text or text in " ".join(str(x) for k,v in item.items()
             for x in (v if isinstance(v,list) else [v])).casefold())]

def category_names():
    return ["Todas"]+sorted({item.get("categoria","") for item in read_catalog()})
