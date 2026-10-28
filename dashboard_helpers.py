"""UI helpers for the Creative OS dashboard."""
import re
from urllib.parse import quote, urlencode

def public_clarification_url(app_url,access_token):
    if not isinstance(app_url,str) or not re.fullmatch(
        r"https://[a-z0-9][a-z0-9-]*\.streamlit\.app(?:/)?",app_url.strip(),re.I):
        raise ValueError("Configura APP_PUBLIC_URL con la URL https://...streamlit.app")
    if not re.fullmatch(r"[0-9a-f]{64}",str(access_token)):
        raise ValueError("Token de invitación inválido.")
    base=app_url.strip().rstrip("/")
    return base+"/Aclaraciones?"+urlencode({"t":access_token})

def invitation_copy(brand,link):
    brand=str(brand or "tu marca").strip()[:100]
    body=("Hola,\n\nDesde Agencia Puente necesitamos aclarar unos detalles "
          "para seguir preparando la propuesta de "+brand+". "
          "Puedes responderlos directamente aquí:\n"+link+
          "\n\nEl enlace vence en 7 días y solo permite una respuesta. "
          "Si necesitas ayuda, responde a este mensaje.\n\nEquipo Puente")
    return body

def whatsapp_share_url(message):
    return "https://wa.me/?text="+quote(message,safe="")

def mailto_url(address,brand,message):
    if not isinstance(address,str) or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",address.strip()):
        raise ValueError("Correo electrónico inválido.")
    return "mailto:"+address.strip()+"?"+urlencode({
        "subject":"PUENTE · Una consulta breve sobre "+str(brand)[:100],
        "body":message})
