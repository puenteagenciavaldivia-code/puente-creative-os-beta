#!/usr/bin/env python3
"""Auditoría 04.01: formulario Streamlit real, datos ficticios, sin secretos."""
import json
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = os.environ.get("PUENTE_QA_URL", "http://127.0.0.1:8766")
OUT = Path(os.environ.get("PUENTE_QA_OUT", "qa_artifacts"))
OUT.mkdir(parents=True, exist_ok=True)
results = {}
def verify(name, condition):
    results[name] = bool(condition)
    if not condition:
        raise AssertionError(name)

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900}, accept_downloads=True)
    errors = []
    page.on("pageerror", lambda err: errors.append(str(err)))
    try:
        page.goto(BASE, wait_until="domcontentloaded", timeout=60000)
        page.get_by_text("Descubramos tu marca.").wait_for(timeout=60000)
        verify("initial_page", True)
        verify("manual_delivery_without_secrets", page.get_by_text("todavía no hay recepción automática", exact=False).count() > 0)
        page.get_by_label("¿Cómo se llama tu marca?", exact=True).fill("Taller Río - Prueba Sintética")
        page.get_by_label("¿Qué hace tu negocio?", exact=True).fill("Taller ficticio de reparación de bicicletas para pruebas.")
        page.get_by_role("button", name="Continuar →").click()
        page.get_by_text("2/5 · Negocio").wait_for(timeout=30000)
        verify("step_2", True)
        page.get_by_label("¿Cuáles son tus productos o servicios?", exact=True).fill("Servicio sintético de mantenimiento y reparación de bicicletas.")
        page.get_by_label("¿Qué valoran tus clientes de lo que haces?", exact=True).fill("Información de reparaciones comprensible y precios transparentes en este caso ficticio.")
        page.get_by_role("button", name="Continuar →").click()
        page.get_by_text("3/5 · Público").wait_for(timeout=30000)
        verify("step_3", True)
        page.get_by_label("¿Cómo son las personas que te compran hoy?", exact=True).fill("Personas ficticias que se movilizan en bicicleta.")
        page.get_by_role("button", name="Continuar →").click()
        page.get_by_text("4/5 · Universo visual").wait_for(timeout=30000)
        verify("step_4", True)
        page.get_by_label("¿Tienes un logotipo o colores que uses siempre?", exact=True).click()
        page.get_by_text("No tenemos identidad visual", exact=True).last.click()
        page.get_by_role("button", name="Continuar →").click()
        page.get_by_text("5/5 · Objetivos y producción").wait_for(timeout=30000)
        verify("step_5", True)
        page.get_by_label("¿Qué te gustaría conseguir con tus publicaciones?", exact=True).click()
        page.get_by_text("Conseguir consultas", exact=True).last.click()
        page.get_by_label("¿En qué redes o medios estás presente?", exact=True).click()
        page.get_by_text("Instagram", exact=True).last.click()
        page.get_by_label("Acepto participar voluntariamente en esta prueba.", exact=True).check()
        page.get_by_role("button", name="Revisar respuestas →").click()
        page.get_by_text("Revisa tus respuestas antes de enviarlas").wait_for(timeout=30000)
        verify("review_screen", True)
        verify("answers_preserved", page.get_by_text("Taller Río - Prueba Sintética").count() > 0)
        page.get_by_role("button", name="Confirmar y enviar").click()
        page.get_by_text("¡Gracias por participar!").wait_for(timeout=30000)
        verify("finished_screen", True)
        download_button = page.get_by_role("button", name="Descargar mis respuestas (JSON)")
        verify("download_available", download_button.count() > 0)
        with page.expect_download(timeout=30000) as download_info:
            download_button.click()
        download = download_info.value
        saved = OUT / "briefing_sintetico.json"
        download.save_as(saved)
        doc = json.loads(saved.read_text(encoding="utf-8"))
        verify("json_contains_fictional_brand", doc.get("answers", {}).get("nombre") == "Taller Río - Prueba Sintética")
        verify("no_upload_claim", page.get_by_text("Adjuntos guardados en Google Drive.").count() == 0)
        verify("no_browser_errors", not errors)
        page.screenshot(path=str(OUT / "desktop_finished.png"), full_page=True)
        mobile = browser.new_page(viewport={"width": 390, "height": 844})
        mobile.goto(BASE, wait_until="domcontentloaded", timeout=60000)
        mobile.get_by_text("Descubramos tu marca.").wait_for(timeout=60000)
        verify("mobile_usable", mobile.locator("body").evaluate("(e) => e.scrollWidth <= window.innerWidth + 12"))
        mobile.screenshot(path=str(OUT / "mobile_initial.png"), full_page=True)
    except Exception as exc:
        results["error"] = str(exc)
        page.screenshot(path=str(OUT / "failure.png"), full_page=True)
        raise
    finally:
        (OUT / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        browser.close()
print(json.dumps(results, ensure_ascii=False))
if not all(v for v in results.values() if isinstance(v, bool)):
    sys.exit(1)
