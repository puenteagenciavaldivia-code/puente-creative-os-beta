"""Real Chromium QA: attachment replacement revokes previously granted consent."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = os.environ.get("PUENTE_QA_URL", "http://127.0.0.1:8766")
OUT = Path(os.environ.get("PUENTE_QA_OUT", "qa_artifacts"))
OUT.mkdir(exist_ok=True, parents=True)
CHECK_LABEL = "Confirmo que tengo permiso para compartir estos archivos con Agencia Puente para evaluar este briefing."
results = {}


def check(name, passed):
    results[name] = bool(passed)
    if not passed:
        raise AssertionError(name)


def fill(page, label, value):
    element = page.get_by_label(label, exact=True)
    element.fill(value)
    element.press("Tab")
    page.wait_for_timeout(900)


def next_page(page):
    b = page.get_by_role("button", name="Continuar →", exact=True)
    for _ in range(20):
        if b.is_enabled():
            b.click()
            return
        page.wait_for_timeout(500)
    raise AssertionError("continue_button_disabled")


with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.get_by_text("Descubramos tu marca.").wait_for(timeout=60000)
        fill(page, "¿Cómo se llama tu marca?", "Prueba Sintética Adjuntos")
        fill(page, "¿Qué hace tu negocio?", "Negocio ficticio de prueba.")
        next_page(page)
        page.get_by_text("2/5 · Negocio").wait_for(timeout=30000)
        fill(page, "¿Cuáles son tus productos o servicios?", "Servicios ficticios.")
        fill(page, "¿Qué valoran tus clientes de lo que haces?", "Respuesta ficticia.")
        next_page(page)
        page.get_by_text("3/5 · Público").wait_for(timeout=30000)
        fill(page, "¿Cómo son las personas que te compran hoy?", "Personas ficticias.")
        next_page(page)
        page.get_by_text("4/5 · Universo visual").wait_for(timeout=30000)
        check("visual_section", True)

        uploader = page.locator('input[type="file"]')
        check("file_uploader_present", uploader.count() == 1)
        uploader.set_input_files({"name": "marca-a.png", "mimeType": "image/png", "buffer": b"synthetic-logo-a"})
        page.get_by_text("1 archivo(s) preparados para enviar al finalizar.", exact=True).wait_for(timeout=30000)
        check("first_file_selected", True)
        page.get_by_text(CHECK_LABEL, exact=True).click()
        page.wait_for_timeout(500)
        check("first_consent_given", page.get_by_label(CHECK_LABEL, exact=True).is_checked())

        uploader.set_input_files({"name": "marca-b.png", "mimeType": "image/png", "buffer": b"synthetic-logo-b"})
        page.wait_for_timeout(1200)
        check("new_file_addition_revokes_consent", not page.get_by_label(CHECK_LABEL, exact=True).is_checked())
        check("addition_keeps_both_files", page.get_by_text("2 archivo(s) preparados para enviar al finalizar.", exact=True).count() > 0)
        check("continue_blocked_without_consent", page.get_by_role("button", name="Continuar →", exact=True).is_disabled())
        page.screenshot(path=str(OUT / "attachment_consent_revoked.png"), full_page=True)

        uploader.set_input_files([])
        page.wait_for_timeout(1100)
        check("empty_selection_resets_count", page.get_by_text("2 archivo(s) preparados para enviar al finalizar.", exact=True).count() == 0)
        check("empty_selection_resets_consent", not page.get_by_label(CHECK_LABEL, exact=True).is_checked())
        page.screenshot(path=str(OUT / "attachment_selection_empty.png"), full_page=True)
    except Exception as exc:
        results["error"] = str(exc)
        page.screenshot(path=str(OUT / "attachment_failure.png"), full_page=True)
        raise
    finally:
        (OUT / "attachment_browser_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        browser.close()
print(json.dumps(results))
