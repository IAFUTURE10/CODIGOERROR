"""Validate the complete publication boundary, links and source contracts."""
from __future__ import annotations
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
from xml.etree import ElementTree
ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
NS = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
def data(name): return json.loads((ROOT / 'data' / name).read_text(encoding='utf-8'))
def require(condition, message):
    if not condition: raise AssertionError(message)
def guide_route(g): return g['category'] + '/' + g['slug']
def validate_data():
    guides, categories, legacy = data('reviewed-guides.json'), data('categories.json'), data('retired-routes.json')
    require(bool(guides), 'Editorial library is empty')
    routes, titles = set(), set()
    categories = {c['slug'] for c in categories}
    checked = {s['url'] for s in data('source-checks.json') if s['status'] == 200}
    allowed_hosts = {'support.microsoft.com', 'learn.microsoft.com', 'support.google.com', 'help.steampowered.com'}
    for g in guides:
        path = guide_route(g)
        require(re.fullmatch(r'[a-z0-9-]+/[a-z0-9-]+', path), 'Unsafe route: ' + path)
        require(path not in routes and g['title'] not in titles, 'Duplicate editorial guide: ' + path)
        routes.add(path); titles.add(g['title'])
        require(g['category'] in categories, 'Unknown category: ' + path)
        require(not g.get('generated'), 'Automatically expanded guide in active library')
        for key in ('title', 'h1', 'summary', 'meta_description', 'updated'):
            require(isinstance(g.get(key), str) and g[key].strip(), f'{path}: missing {key}')
        require(re.fullmatch(r'\d{4}-\d{2}-\d{2}', g['updated']), 'Missing editorial date: ' + path)
        require(len(g['steps']) >= 4, 'Guide needs a diagnostic sequence: ' + path)
        for s in g['steps']:
            for key in ('title', 'action', 'expected', 'next', 'undo'):
                require(bool(s.get(key, '').strip()), f'{path}: step missing {key}')
        for key in ('scope', 'symptoms', 'quick_checks', 'stop_conditions', 'sources'):
            require(bool(g.get(key)), f'{path}: missing {key}')
        for source in g['sources']:
            u = urlsplit(source['url'])
            require(u.scheme == 'https' and u.hostname in allowed_hosts, 'Non-primary reference: ' + source['url'])
            require(source['url'] in checked, 'Reference lacks recorded HTTP check: ' + source['url'])
    require(len(legacy) == len(set(legacy)), 'Duplicate legacy routes')
    require(all(re.fullmatch(r'[a-z0-9-]+/[a-z0-9-]+', p) for p in legacy), 'Unsafe legacy route')

class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []; self.ids = set(); self.robots = ''; self.canonical = ''; self.h1 = 0; self.title = False; self.description = False; self.scripts = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            require(a['id'] not in self.ids, 'Duplicate element ID: ' + a['id']); self.ids.add(a['id'])
        if tag == 'meta' and a.get('name') == 'robots': self.robots = a.get('content', '')
        if tag == 'meta' and a.get('name') == 'description': self.description = bool(a.get('content'))
        if tag == 'link' and a.get('rel') == 'canonical': self.canonical = a.get('href', '')
        if tag == 'h1': self.h1 += 1
        if tag == 'title': self.title = True
        if tag in ('a', 'link') and a.get('href'): self.links.append(a['href'])
        if tag in ('script', 'img') and a.get('src'): self.links.append(a['src'])
        if tag == 'script' and a.get('src'): self.scripts.append(a['src'])

def main():
    validate_data()
    site, guides, legacy = data('site.json'), data('reviewed-guides.json'), data('retired-routes.json')
    origin = site['site_url'].rstrip('/') + '/'; base = site['base_path'].rstrip('/')
    active = {guide_route(g) for g in guides}
    expected = {'', 'publicaciones', 'cuaderno-diagnostico'} | active
    root = ElementTree.parse(DOCS / 'sitemap.xml').getroot()
    require(root.tag.endswith('urlset'), 'Main sitemap must contain URLs')
    sitemap_urls = [e.text for e in root.findall('sm:url/sm:loc', NS)]
    require(len(sitemap_urls) == len(set(sitemap_urls)), 'Duplicate sitemap entries')
    require(set(sitemap_urls) == {origin + (p + '/' if p else '') for p in expected}, 'Sitemap exposes retired or utility routes')
    require((DOCS / 'sitemap-urls.txt').read_text().splitlines() == sitemap_urls, 'Text sitemap differs from XML')
    search = json.loads((DOCS / 'search-index.json').read_text())
    require({s['p'].rstrip('/') for s in search} == active, 'Search exposes retired guides')
    paths = list(DOCS.rglob('*.html')); parsed = {}; indexable = set()
    for path in paths:
        text = path.read_text(encoding='utf-8'); p = Page(); p.feed(text); parsed[path.resolve()] = p
        require(p.title and p.description and p.h1 == 1, 'Missing metadata or unique H1: ' + str(path))
        require('adsbygoogle' not in text and 'googletagmanager' not in text and 'cdn-cookieyes' not in text, 'Unreviewed service loader: ' + str(path))
        require(not any(urlsplit(src).netloc for src in p.scripts), 'External executable script: ' + str(path))
        rel = path.relative_to(DOCS).as_posix()
        path_route = '' if rel == 'index.html' else rel.removesuffix('/index.html')
        if 'noindex' not in p.robots:
            indexable.add(path_route)
            require(p.canonical == origin + (path_route + '/' if path_route else ''), 'Canonical mismatch: ' + str(path))
        if path_route in set(legacy) - active:
            require('noindex' in p.robots and 'application/ld+json' not in text, 'Retired page still acts as a publication: ' + path_route)
    require(indexable == expected, 'HTML publication boundary differs from sitemap')
    for path, page in parsed.items():
        for link in page.links:
            u = urlsplit(link)
            if u.scheme or u.netloc: continue
            if u.path.startswith('/'):
                require(u.path == base or u.path.startswith(base + '/'), 'Link escapes project base: ' + link)
                target = DOCS / unquote(u.path[len(base):].lstrip('/'))
            else: target = path.parent / unquote(u.path)
            if target.is_dir(): target /= 'index.html'
            require(target.exists(), f'Broken link in {path}: {link}')
            if u.fragment and target.suffix == '.html':
                require(unquote(u.fragment) in parsed[target.resolve()].ids, f'Broken anchor in {path}: {link}')
    for g in guides:
        text = (DOCS / guide_route(g) / 'index.html').read_text()
        require('application/ld+json' in text, 'Guide missing article schema')
        require(all(s['url'].replace('&', '&amp;') in text for s in g['sources']), 'Guide omitted references')
    for sitemap in (DOCS / 'sitemaps').glob('*.xml'):
        locs = [e.text for e in ElementTree.parse(sitemap).getroot().findall('sm:url/sm:loc', NS)]
        require(set(locs) <= set(sitemap_urls), 'Category sitemap leaks retired URLs')
    print(f'Validated all {len(paths)} HTML pages, all local links/anchors, {len(active)} guides and {len(expected)} indexable URLs; retired pages have no advertising or article schema.')
if __name__ == '__main__': main()
