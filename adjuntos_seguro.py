"""PUENTE 04.01: gestión fail-closed de adjuntos sintéticos para Streamlit.

No realiza envíos ni lecturas de red. Consentimiento vinculado a la selección actual.
"""
import base64

MAX_FILES = 5
MAX_SIZE = 3 * 1024 * 1024
ALLOWED_MIME = {"image/png", "image/jpeg", "image/webp", "application/pdf"}


def clear_selection(state):
    state["attachments_store"] = []
    state["files_consent"] = False
    state["answers_store"].pop("files_consent", None)


def reconcile_selection(state, uploaded):
    """Valida los bytes reales; invalida autorización ante reemplazos o fallos."""
    previous = state.get("attachments_store", [])
    if not uploaded:
        changed = bool(previous)
        clear_selection(state)
        return {"ok": True, "count": 0, "changed": changed}
    if len(uploaded) > MAX_FILES:
        clear_selection(state)
        return {"ok": False, "reason": "count"}
    selected = []
    try:
        for obj in uploaded:
            if (not isinstance(obj.name, str) or not obj.name.strip()
                    or len(obj.name) > 255 or "/" in obj.name or "\\" in obj.name
                    or obj.type not in ALLOWED_MIME
                    or not isinstance(obj.size, int) or isinstance(obj.size, bool)
                    or obj.size < 0 or obj.size > MAX_SIZE):
                raise ValueError("metadata")
            raw = obj.getvalue()
            if (not isinstance(raw, bytes) or len(raw) != obj.size
                    or len(raw) == 0 or len(raw) > MAX_SIZE):
                raise ValueError("bytes")
            selected.append({
                "name": obj.name,
                "mime": obj.type,
                "data": base64.b64encode(raw).decode("ascii"),
            })
    except Exception:
        clear_selection(state)
        return {"ok": False, "reason": "invalid_selection"}

    changed = selected != previous
    if changed:
        state["files_consent"] = False
        state["answers_store"].pop("files_consent", None)
    state["attachments_store"] = selected
    return {"ok": True, "count": len(selected), "changed": changed}
