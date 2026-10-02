"""Comprueba inferencia, formulario, descarga y HTML autónomo con Chromium."""
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from threading import Thread
import json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}'
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
        page=browser.new_page(accept_downloads=True)
        errors=[]; page.on('pageerror',lambda e: errors.append(str(e)))
        page.goto(base+'/web/',wait_until='networkidle')
        ref=json.loads((ROOT/'reference_predictions.json').read_text())
        actual=page.evaluate('(rows)=>rows.map(window.predictSyngas)',ref['inputs'])
        delta=max(abs(a-b) for row,expected in zip(actual,ref['predictions']) for a,b in zip(row,expected))
        assert delta<1e-4,delta
        page.get_by_role('button',name='Predecir calidad del syngas').click()
        assert page.locator('#prediction').is_visible()
        with page.expect_download() as info:
            page.get_by_role('button',name='Descargar resultado').click()
        result=json.loads(Path(info.value.path()).read_text())
        assert result['units']['inputs']['T']=='K'
        page.locator('#T').fill('1100')
        assert page.locator('#download').is_disabled()
        page.get_by_role('button',name='Predecir calidad del syngas').click()
        assert 'T' in page.locator('#warnings').inner_text()
        page.locator('#C').fill('101')
        page.get_by_role('button',name='Predecir calidad del syngas').click()
        assert 'entre 0 y 100' in page.locator('#form-error').inner_text()
        page.locator('#C').fill('')
        assert not page.locator('#C').evaluate('(e)=>e.checkValidity()')
        page.get_by_role('button',name='Cargar ejemplo').click()
        page.get_by_role('button',name='Predecir calidad del syngas').click()
        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.goto(base+'/Syngas_Lab.html',wait_until='load')
        # All inference runs even when subsequent network requests are denied.
        page.route('**/*',lambda route:route.abort())
        page.get_by_role('button',name='Predecir calidad del syngas').click()
        assert page.locator('#prediction').is_visible()
        assert not errors,errors
        browser.close()
        print(f'PASS: 26 predicciones vs TensorFlow (máx. {delta:.2g}), unidades, descarga, recálculo, validación, móvil y HTML sin dependencias de red.')
finally:
    server.shutdown();server.server_close()
