"""Optional real-browser check (requires Playwright and system Chromium)."""
import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]
BASE = json.loads((ROOT / 'data/site.json').read_text())['base_path'].rstrip('/')
class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith(BASE + '/'): self.path = self.path[len(BASE):]
        super().do_GET()
    def log_message(self, *_): pass

def main():
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=str(ROOT / 'docs')))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    origin = f'http://127.0.0.1:{server.server_port}' + BASE + '/'
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
            context = browser.new_context(accept_downloads=True)
            page = context.new_page(); errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(origin)
            assert page.locator('[data-guide-card]:visible').count() == 8
            page.locator('#guide-search').fill('MICROFONO')
            assert page.locator('[data-guide-card]:visible').count() == 1
            assert 'Micrófono' in page.locator('[data-guide-card]:visible').inner_text()
            page.locator('#guide-search').fill('sin guía para esta búsqueda zzz')
            assert page.locator('[data-guide-card]:visible').count() == 0
            assert 'No hay una guía' in page.locator('[data-search-status]').inner_text()
            page.goto(origin + 'cuaderno-diagnostico/')
            page.locator('#download-report').click()
            assert 'Añade' in page.locator('#notebook-status').inner_text()
            page.locator('#device').fill('Portátil de prueba; Windows 11')
            page.locator('#symptom').fill('No recibe voz en llamada')
            payload = '<img src=x onerror="window.injected=1">'
            page.locator('#action').fill(payload)
            page.locator('#result').fill('El medidor de Windows sí se mueve')
            page.locator('#next').fill('Revisar entrada elegida en la aplicación')
            page.get_by_role('button', name='Añadir al informe').click()
            assert page.locator('#observations li').count() == 1
            assert page.locator('#observations img').count() == 0
            assert page.evaluate('window.injected || 0') == 0
            with page.expect_download() as download:
                page.locator('#download-report').click()
            exported = Path(download.value.path()).read_text(encoding='utf-8')
            assert 'Portátil de prueba' in exported and payload in exported and 'medidor de Windows' in exported
            page.get_by_role('button', name='Eliminar comprobación 1').click()
            assert page.locator('#observations li').count() == 0
            page.set_viewport_size({'width': 390, 'height': 844})
            page.goto(origin + 'internet/wifi-conectado-sin-internet-windows-11/')
            assert page.locator('.diagnostic-step').count() == 6
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path='/tmp/codigo-error-mobile.png', full_page=True)
            assert not errors, errors
            nojs = browser.new_context(java_script_enabled=False)
            bare = nojs.new_page(); bare.goto(origin)
            assert bare.locator('[data-guide-card]:visible').count() == 8
            assert bare.locator('[data-search-root]:visible').count() == 0
            bare.goto(origin + 'cuaderno-diagnostico/')
            assert bare.locator('noscript pre').is_visible()
            bare.goto(origin + 'gaming/steam-no-abre-windows-11/')
            assert bare.locator('h1').inner_text() == 'Esta guía se ha retirado'
            assert bare.locator('meta[name="robots"]').get_attribute('content') == 'noindex,follow'
            browser.close()
            print('Browser passed: accent-insensitive search, notebook validation/export/XSS/removal, mobile layout, no-JS access and legacy notice.')
    finally:
        server.shutdown(); server.server_close(); thread.join()
if __name__ == '__main__': main()
