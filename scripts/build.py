"""Build a finite editorial library. Legacy routes are notices, never generated guides."""
from __future__ import annotations
import html
import json
import shutil
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree.ElementTree import Element, SubElement, tostring

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
DATA = ROOT / 'data'
def read(name): return json.loads((DATA / name).read_text(encoding='utf-8'))
SITE = read('site.json')
GUIDES = read('reviewed-guides.json')
CATEGORIES = read('categories.json')
LEGACY = read('retired-routes.json')
BASE = SITE['base_path'].rstrip('/')
ORIGIN = SITE['site_url'].rstrip('/')
UPDATED = '2026-10-14'
LEGAL = ['sobre-codigo-error', 'contacto', 'privacidad', 'cookies']
def esc(value): return html.escape(str(value), quote=True)
def route(guide): return guide['category'] + '/' + guide['slug']
def href(path=''): return BASE + '/' + (path.strip('/') + '/' if path else '')
def absolute(path=''): return ORIGIN + '/' + (path.strip('/') + '/' if path else '')
def asset(path): return BASE + '/' + path.lstrip('/')
def write(path, text):
    target = DOCS / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding='utf-8')
def write_page(path, text): write(path.strip('/') + '/index.html' if path else 'index.html', text)
def ul(items): return '<ul>' + ''.join('<li>' + esc(x) + '</li>' for x in items) + '</ul>'

def page(path, title, description, body, *, index=True, schema=None):
    robots = 'index,follow' if index else 'noindex,follow'
    canonical = '<link rel="canonical" href="' + esc(absolute(path)) + '">' if index else ''
    verification = SITE.get('verification', {}).get('google_site_verification', '')
    verification_meta = '<meta name="google-site-verification" content="' + esc(verification) + '">' if verification else ''
    ownership_meta = '<meta name="google-adsense-account" content="' + esc(SITE['adsense']['client_id']) + '">' if index else ''
    structured = '<script type="application/ld+json">' + json.dumps(schema, ensure_ascii=False).replace('<', '\\u003c') + '</script>' if schema else ''
    nav = ''.join('<a href="' + href(x) + '">' + label + '</a>' for x, label in [('publicaciones', 'Guías'), ('cuaderno-diagnostico', 'Cuaderno'), ('sobre-codigo-error', 'Método')])
    legal = ''.join('<a href="' + href(x) + '">' + label + '</a>' for x, label in [('sobre-codigo-error', 'Sobre el proyecto'), ('contacto', 'Contacto'), ('privacidad', 'Privacidad'), ('cookies', 'Cookies')])
    return f'''<!doctype html><html lang="es" data-base-path="{esc(BASE)}"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | Código Error</title><meta name="description" content="{esc(description)}">
<meta name="robots" content="{robots}">{canonical}{verification_meta}{ownership_meta}
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(absolute(path))}"><meta property="og:type" content="website">
<meta name="theme-color" content="#00020E"><link rel="icon" href="{asset('assets/icons/favicon.svg')}" type="image/svg+xml">
<link rel="stylesheet" href="{asset('assets/css/styles.css')}">{structured}</head><body>
<a class="skip-link" href="#contenido">Saltar al contenido</a>
<header class="site-header"><div class="header-inner"><a class="brand" href="{href()}"><span class="brand-mark" aria-hidden="true">CE</span>Código <span class="brand-error">Error</span></a><nav class="top-nav" aria-label="Principal">{nav}</nav></div></header>
<main id="contenido" class="container">{body}</main>
<footer class="site-footer"><div class="container"><p>Código Error · Guías de diagnóstico en español. Información general; cada equipo puede necesitar soporte específico.</p><nav class="footer-links" aria-label="Información del sitio">{legal}</nav></div></footer>
<script src="{asset('assets/js/app.js')}" defer></script></body></html>'''

def cards(guides):
    return '<div class="article-grid" data-guide-list>' + ''.join(f'''<article class="article-card" data-guide-card data-search="{esc(g['title'] + ' ' + ' '.join(g['keywords']))}"><span class="pill">{esc(g['category'])}</span><h2><a href="{href(route(g))}">{esc(g['title'])}</a></h2><p>{esc(g['summary'])}</p></article>''' for g in guides) + '</div>'
def search():
    return '''<div class="diagnostic-search" data-search-root hidden><label for="guide-search">Filtrar guías por síntoma o sistema</label><input id="guide-search" type="search" data-search-input placeholder="WiFi, Steam, micrófono…"><p data-search-status role="status" aria-live="polite"></p></div><noscript><p>Las guías completas están enlazadas abajo; puedes usar la búsqueda de tu navegador.</p></noscript>'''
def render_home():
    body = f'''<section class="hero"><p class="eyebrow">Antes de cambiar algo, observa</p><h1>¿Dónde empieza el fallo?</h1><p class="lead">Distingue un problema del equipo, la aplicación o la red con una comparación a la vez. Cada guía explica qué observar, cuándo avanzar y cómo volver al estado anterior.</p><p><a class="button-link" href="{href('cuaderno-diagnostico')}">Anotar mis comprobaciones</a></p></section>
<section class="section"><h2>Elige el síntoma que coincide</h2><p>Si el error o el sistema no coincide con una guía, evita aplicar sus pasos por parecido. Anota el mensaje exacto y consulta al fabricante.</p>{search()}{cards(GUIDES)}</section>
<section class="section"><h2>Tres decisiones antes de reparar</h2><div class="diagnostic-grid"><article class="diagnostic-card"><h3>¿Hay datos sin copia?</h3><p>Una unidad que pide formato no está necesariamente vacía. Cancela y conserva el original antes de reparar o recuperar.</p></article><article class="diagnostic-card"><h3>¿Falla en otro dispositivo?</h3><p>Comparar en la misma red o con un cable compatible ayuda a separar el equipo de lo que lo rodea.</p></article><article class="diagnostic-card"><h3>¿Puedes revertir el cambio?</h3><p>Anota el ajuste anterior, modifica una sola variable y vuelve atrás si la prueba no aporta mejora.</p></article></div></section>'''
    write_page('', page('', 'Diagnóstico de fallos sin cambios a ciegas', SITE['description'], body))

def render_guide(g):
    path = route(g)
    steps = ''.join(f'''<section class="diagnostic-step" id="paso-{n}"><h2>{esc(s['title'])}</h2><p>{esc(s['action'])}</p><dl><dt>Qué observar</dt><dd>{esc(s['expected'])}</dd><dt>Decisión siguiente</dt><dd>{esc(s['next'])}</dd><dt>Cómo volver atrás</dt><dd>{esc(s['undo'])}</dd></dl></section>''' for n, s in enumerate(g['steps'], 1))
    toc = ''.join(f'<li><a href="#paso-{n}">{esc(s["title"])}</a></li>' for n, s in enumerate(g['steps'], 1))
    faq = ''.join(f'<details><summary>{esc(f["question"])}</summary><p>{esc(f["answer"])}</p></details>' for f in g['faq'])
    sources = '<ul>' + ''.join(f'<li><a href="{esc(s["url"])}" rel="noopener noreferrer">{esc(s["title"])}</a></li>' for s in g['sources']) + '</ul>'
    body = f'''<section class="page-hero"><nav class="breadcrumb" aria-label="Ruta"><a href="{href()}">Inicio</a> / <a href="{href('publicaciones')}">Guías</a></nav><h1>{esc(g['h1'])}</h1><p class="lead">{esc(g['summary'])}</p><p>Contenido del proyecto Código Error · Actualizado: <time datetime="{g['updated']}">{g['updated']}</time> · <a href="{href('sobre-codigo-error')}">Método y límites</a></p></section>
<div class="article-layout"><article class="article-body"><h2>Cuándo sirve esta guía</h2>{ul(g['scope'])}<h2>Señales que puedes comparar</h2>{ul(g['symptoms'])}<h2>Antes de empezar</h2>{ul(g['quick_checks'])}{steps}<section class="stop-note"><h2>Cuándo detenerte</h2>{ul(g['stop_conditions'])}</section><h2>Preguntas frecuentes</h2>{faq}<h2>Fuentes primarias y alcance</h2>{sources}<p>Las referencias explican funciones y límites de las herramientas. Esta guía organiza un diagnóstico general; no describe pruebas físicas realizadas sobre tu equipo.</p><p><a href="{href('contacto')}">Informar de un error o proponer una corrección</a></p></article><aside class="toc"><nav aria-label="En esta guía"><h2>Pasos de diagnóstico</h2><ol>{toc}</ol></nav><p><a href="{href('cuaderno-diagnostico')}">Guardar mis observaciones en un archivo</a></p></aside></div>'''
    schema = {'@context': 'https://schema.org', '@type': 'Article', 'headline': g['title'], 'description': g['summary'], 'dateModified': g['updated'], 'author': {'@type': 'Organization', 'name': 'Código Error'}, 'mainEntityOfPage': absolute(path), 'citation': [s['url'] for s in g['sources']]}
    write_page(path, page(path, g['title'], g['meta_description'], body, schema=schema))

def render_directory():
    write_page('publicaciones', page('publicaciones', 'Todas las guías disponibles', 'Biblioteca de guías con síntomas, comprobaciones, decisiones y fuentes primarias.', '<section class="page-hero"><h1>Guías de diagnóstico</h1><p>Elige por el síntoma y el sistema que usas. El diagnóstico comienza con observaciones, no con una receta universal.</p>' + search() + '</section>' + cards(GUIDES)))
    for c in CATEGORIES:
        selected = [g for g in GUIDES if g['category'] == c['slug']]
        content = cards(selected) if selected else f'<p>Actualmente no hay una guía específica publicada para esta categoría. Consulta <a href="{href("publicaciones")}">las guías disponibles</a> o registra el mensaje y consulta al soporte oficial de tu programa.</p>'
        write_page(c['slug'], page(c['slug'], c['name'] + ': guías disponibles', 'Consulta las guías que coinciden con tu síntoma.', '<section class="page-hero"><h1>' + esc(c['name']) + '</h1><p>Aplica solo pasos que coincidan con tu dispositivo y mensaje.</p></section>' + content, index=False))

def render_legal():
    issue = 'https://github.com/IAFUTURE10/CODIGOERROR/issues/new'
    sections = {
        'sobre-codigo-error': ('Sobre Código Error y su método', f'''<h2>Propósito y responsable del proyecto</h2><p>Código Error es un proyecto de diagnóstico tecnológico en español publicado desde el repositorio <a href="https://github.com/IAFUTURE10/CODIGOERROR">IAFUTURE10/CODIGOERROR</a>. No está afiliado a Microsoft, Google, Valve o fabricantes mencionados.</p><h2>Qué contiene una guía</h2><p>Un síntoma y alcance concretos, comprobaciones observables, un cambio cada vez, resultado esperado, decisión siguiente y límites para detenerse. Las referencias enlazan documentación primaria; no son una afirmación de que todos los equipos se hayan probado físicamente.</p><h2>Cómo se corrige y actualiza</h2><p>La fecha visible corresponde a una edición de contenido, no a la fecha de compilación. Un cambio de título no crea una nueva guía. Los avisos de antiguas publicaciones permanecen fuera de buscador, navegación editorial y sitemap.</p><h2>Información y límites</h2><p>Las instrucciones son información general. Daño físico, riesgo de pérdida de datos o equipos administrados necesitan soporte competente. No se promete reparar todos los casos ni sustituir el diagnóstico del fabricante.</p><p><a href="{href('contacto')}">Canal público de correcciones</a></p>'''),
        'contacto': ('Contacto y correcciones', f'''<p>El canal disponible del proyecto es <a href="{issue}">abrir una incidencia pública en GitHub</a>. Requiere una cuenta de GitHub. También puedes consultar <a href="https://github.com/IAFUTURE10/CODIGOERROR/issues">incidencias existentes</a>.</p><h2>Qué incluir</h2><p>URL de la guía, paso concreto, sistema y versión, texto del error sin información privada, qué esperabas y qué observaste. Para corregir contenido, añade una referencia oficial que lo explique.</p><h2>Qué evitar en una incidencia pública</h2><p>No publiques contraseñas, claves, documentos privados, direcciones, números de serie completos o capturas que los muestren. Los registros pueden contener rutas con tu nombre: revísalos antes de adjuntarlos.</p><h2>Privacidad y alcance del canal</h2><p>No hay un formulario privado ni un correo verificado publicado en este repositorio. Puedes consultar aquí cómo funciona el sitio y sugerir correcciones generales; no envíes solicitudes con datos personales por el canal público. Este canal no ofrece asistencia urgente ni garantiza un plazo de respuesta.</p>'''),
        'privacidad': ('Política de privacidad', f'''<p>Fecha de esta versión: {UPDATED}. El sitio publicado es https://iafuture10.github.io/CODIGOERROR/ y pertenece al proyecto del repositorio IAFUTURE10/CODIGOERROR.</p><h2>Datos dentro del sitio</h2><p>La búsqueda filtra guías en tu navegador. El cuaderno mantiene lo escrito en memoria de la página y no lo envía a un servidor. Cuando descargas un informe, el archivo queda en el dispositivo que elegiste. No hay cuentas ni formularios que recojan datos en esta web.</p><h2>Alojamiento y registros</h2><p>GitHub Pages sirve los archivos y puede tratar datos técnicos de las peticiones, como IP y agente del navegador, conforme a <a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement">su política de privacidad</a>. El proyecto no controla esos registros.</p><h2>Publicidad, analítica y cookies</h2><p>Esta versión no carga anuncios, Google Analytics ni un gestor de cookies externo. Los identificadores del propietario se conservan en la configuración del repositorio para su revisión, pero no se ejecutan en el sitio. Cualquier activación deberá actualizar esta política y aplicar el consentimiento requerido.</p><h2>Enlaces y contacto</h2><p>Al seguir enlaces externos se aplican las políticas del destino. GitHub Issues es público y requiere cuenta. Usa <a href="{href('contacto')}">la página de contacto</a> para conocer sus límites; no publiques información personal.</p>'''),
        'cookies': ('Cookies y almacenamiento del navegador', '''<h2>Esta versión</h2><p>El código del proyecto no establece cookies ni usa localStorage, sessionStorage o IndexedDB para guardar búsquedas o notas. El cuaderno funciona en memoria y pierde su contenido al cerrar o recargar, salvo que hayas descargado un informe.</p><h2>Servicios externos</h2><p>No se cargan anuncios ni analítica en esta versión. Al salir hacia GitHub, Microsoft, Google o Steam, esos servicios pueden usar sus propias cookies y políticas. El alojamiento de GitHub Pages se describe en la política de privacidad.</p><h2>Cambios futuros</h2><p>La incorporación de publicidad o medición requiere revisar esta información, configurar el consentimiento que corresponda y verificar qué servicios se activan. Esta página describe el comportamiento actual.</p>'''),
    }
    for path, (title, content) in sections.items():
        write_page(path, page(path, title, title + ' del proyecto Código Error.', '<section class="page-hero"><h1>' + esc(title) + '</h1></section><article class="article-body legal-content">' + content + '</article>', index=False))

def render_notebook():
    body = '''<section class="page-hero"><h1>Cuaderno de diagnóstico</h1><p class="lead">Registra una comparación a la vez y prepara un informe para el soporte. Funciona en este navegador; las notas no se envían.</p><p>Descarga el informe antes de cerrar o recargar. Evita datos personales y contraseñas.</p></section>
<section class="article-body" id="notebook"><label for="device">Equipo, sistema y versión</label><input id="device" placeholder="Ejemplo: portátil con Windows 11"><label for="symptom">Mensaje exacto y cuándo empezó</label><textarea id="symptom" rows="3"></textarea><form id="observation-form" hidden><fieldset><legend>Añadir una comprobación</legend><label for="action">Qué comparaste o cambiaste</label><textarea id="action" required rows="2"></textarea><label for="result">Qué observaste</label><textarea id="result" required rows="2"></textarea><label for="next">Decisión siguiente y cómo revertir</label><textarea id="next" rows="2"></textarea><button type="submit" class="button-link">Añadir al informe</button></fieldset></form><ol id="observations"></ol><button id="download-report" type="button" class="button-link" hidden>Descargar informe .txt</button><p id="notebook-status" role="status" aria-live="polite"></p><noscript><h2>Plantilla para copiar sin JavaScript</h2><pre>Equipo y versión:
Síntoma y hora de inicio:
1. Acción o comparación:
   Resultado observado:
   Decisión siguiente:
   Ajuste anterior / reversión:
Preguntas para soporte:</pre><p>Puedes copiar esta plantilla y completarla en un editor de texto local.</p></noscript></section>'''
    write_page('cuaderno-diagnostico', page('cuaderno-diagnostico', 'Cuaderno local de diagnóstico y exportación', 'Anota equipo, mensaje y comparaciones y descarga un informe sin enviar datos al sitio.', body))

def render_retired():
    active = {route(g) for g in GUIDES}
    for path in LEGACY:
        if path in active: continue
        body = f'<section class="page-hero"><h1>Esta guía se ha retirado</h1><p>La publicación de esta dirección pertenecía a una colección automática. Su diagnóstico no forma parte de la biblioteca actual.</p><p>No sigas pasos guardados de esa versión sin contrastarlos con el soporte oficial de tu equipo.</p><p><a class="button-link" href="{href("publicaciones")}">Consultar guías disponibles</a></p></section>'
        write_page(path, page(path, 'Publicación retirada', 'Esta dirección de la colección anterior ya no publica una guía de diagnóstico.', body, index=False))
    write('404.html', page('404', 'No encontramos esta página', 'Consulta las guías disponibles.', f'<section class="page-hero"><h1>Página no encontrada</h1><p>La dirección puede haber cambiado o no existir.</p><a href="{href("publicaciones")}">Consultar guías disponibles</a></section>', index=False))

def sitemap(routes):
    ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    root = Element('urlset', xmlns=ns)
    for path, updated in routes:
        item = SubElement(root, 'url'); SubElement(item, 'loc').text = absolute(path); SubElement(item, 'lastmod').text = updated
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(root, encoding='unicode') + '\n'
def write_indexes():
    routes = [('', UPDATED), ('publicaciones', UPDATED), ('cuaderno-diagnostico', UPDATED)] + [(route(g), g['updated']) for g in GUIDES]
    write('sitemap.xml', sitemap(routes)); write('sitemap-urls.txt', '\n'.join(absolute(p) for p, _ in routes) + '\n')
    write('sitemaps/sitemap-pages.xml', sitemap(routes[:3]))
    active_categories = sorted({g['category'] for g in GUIDES})
    for c in active_categories:
        write('sitemaps/sitemap-' + c + '.xml', sitemap([(route(g), g['updated']) for g in GUIDES if g['category'] == c]))
    index = Element('sitemapindex', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    for name in ['pages'] + active_categories:
        item = SubElement(index, 'sitemap'); SubElement(item, 'loc').text = ORIGIN + '/sitemaps/sitemap-' + name + '.xml'
    write('sitemap-index.xml', '<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(index, encoding='unicode') + '\n')
    write('search-index.json', json.dumps([{'t': g['title'], 'c': g['category'], 'p': route(g) + '/', 'k': g['keywords']} for g in GUIDES], ensure_ascii=False))
    write('robots.txt', 'User-agent: *\nAllow: /\nSitemap: ' + ORIGIN + '/sitemap.xml\n')
    write('ads.txt', 'google.com, ' + SITE['adsense']['publisher_id_for_ads_txt'] + ', DIRECT, f08c47fec0942fa0\n')
    write('.nojekyll', '')

def main():
    if DOCS.resolve().parent != ROOT.resolve(): raise RuntimeError('Unexpected output directory')
    from validate import validate_data
    validate_data()
    if DOCS.exists(): shutil.rmtree(DOCS)
    DOCS.mkdir()
    for name, target in [('styles.css', 'assets/css/styles.css'), ('app.js', 'assets/js/app.js')]: write(target, (ROOT / 'assets' / name).read_text(encoding='utf-8'))
    write('assets/icons/favicon.svg', '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#003B96"/><path d="M15 18h30v8H24v12h21v8H15z" fill="white"/></svg>')
    render_home(); render_directory(); render_notebook(); render_legal()
    for g in GUIDES: render_guide(g)
    render_retired(); write_indexes()
    retired_count = len(set(LEGACY) - {route(g) for g in GUIDES})
    print(f'Built {len(GUIDES)} editorial guides and {retired_count} legacy notices; {len(GUIDES) + 3} indexable URLs.')
if __name__ == '__main__': main()
