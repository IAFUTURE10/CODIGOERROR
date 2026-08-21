from __future__ import annotations

import hashlib
import html
import json
import math
import shutil
import struct
import zlib
from datetime import date
from pathlib import Path

from content_scale import expand_articles


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs"
SOURCE_ASSETS = ROOT / "assets" / "source"


def read_json(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


SITE = read_json("site.json")
CATEGORIES = read_json("categories.json")
CATEGORY_BY_SLUG = {category["slug"]: category for category in CATEGORIES}
SEED_ARTICLES = read_json("articles.json")

BASE_PATH = SITE["base_path"].rstrip("/")
SITE_URL = SITE["site_url"].rstrip("/")
TODAY = date.today().isoformat()
CONTENT_TARGET = int(SITE.get("content", {}).get("target_articles", len(SEED_ARTICLES)))
ARTICLES = expand_articles(SEED_ARTICLES, CATEGORIES, CONTENT_TARGET, TODAY)
IMAGE_EXT = "webp"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def route_url(route: str = "") -> str:
    route = route.strip("/")
    base = BASE_PATH
    if route:
        return f"{base}/{route}/" if base else f"/{route}/"
    return f"{base}/" if base else "/"


def absolute_url(route: str = "") -> str:
    route = route.strip("/")
    return f"{SITE_URL}/{route}/" if route else f"{SITE_URL}/"


def asset_url(path: str) -> str:
    clean_path = path.strip("/")
    return f"{BASE_PATH}/{clean_path}" if BASE_PATH else f"/{clean_path}"


def absolute_asset_url(path: str) -> str:
    return f"{SITE_URL}/{path.strip('/')}"


def article_route(article: dict) -> str:
    return f"{article['category']}/{article['slug']}"


def category_route(category: dict) -> str:
    return category["slug"]


def ensure_clean_docs() -> None:
    docs_resolved = DOCS.resolve()
    root_resolved = ROOT.resolve()
    if docs_resolved.parent != root_resolved:
        raise RuntimeError(f"Unexpected docs path: {docs_resolved}")
    if DOCS.exists():
        shutil.rmtree(DOCS)
    for folder in [
        DOCS,
        DOCS / "assets" / "css",
        DOCS / "assets" / "js",
        DOCS / "assets" / "images",
        DOCS / "assets" / "icons",
        DOCS / "sitemaps",
    ]:
        folder.mkdir(parents=True, exist_ok=True)


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def write_png(path: Path, width: int, height: int, pixels: bytearray) -> None:
    raw = bytearray()
    stride = width * 3
    for y in range(height):
        raw.append(0)
        start = y * stride
        raw.extend(pixels[start : start + stride])
    payload = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + png_chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def blend(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(max(0, min(255, int(a[i] + (b[i] - a[i]) * t))) for i in range(3))


def color_from_seed(seed: str, index: int) -> tuple[int, int, int]:
    digest = hashlib.sha256(f"{seed}:{index}".encode()).digest()
    palette = [
        hex_to_rgb("#003B96"),
        hex_to_rgb("#034A68"),
        hex_to_rgb("#24046B"),
        (22, 188, 136),
        (238, 176, 59),
        (210, 69, 79),
    ]
    base = palette[digest[0] % len(palette)]
    lift = 0.08 + (digest[1] / 255) * 0.22
    return blend(base, (255, 255, 255), lift)


def make_canvas(width: int, height: int, seed: str) -> bytearray:
    bg = hex_to_rgb("#00020E")
    petrol = hex_to_rgb("#034A68")
    purple = hex_to_rgb("#24046B")
    pixels = bytearray(bytes(bg) * (width * height))
    seed_mix = hashlib.sha256(seed.encode()).digest()
    draw_rect(pixels, width, height, 0, 0, width, int(height * 0.62), petrol, 0.18)
    draw_rect(pixels, width, height, 0, 0, int(width * 0.44), height, purple, 0.16)
    draw_rect(pixels, width, height, int(width * 0.62), 0, int(width * 0.38), height, petrol, 0.24)
    for i in range(7):
        x = int((seed_mix[i] / 255) * width) - int(width * 0.12)
        y = int((seed_mix[i + 7] / 255) * height) - int(height * 0.08)
        draw_rect(pixels, width, height, x, y, int(width * 0.24), int(height * 0.16), color_from_seed(seed, i), 0.08)
    return pixels


def draw_rect(
    pixels: bytearray,
    width: int,
    height: int,
    x: int,
    y: int,
    w: int,
    h: int,
    color: tuple[int, int, int],
    alpha: float = 1.0,
) -> None:
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(width, x + w), min(height, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    if alpha < 1:
        color = blend(hex_to_rgb("#00020E"), color, alpha)
    row = bytes(color) * (x1 - x0)
    for yy in range(y0, y1):
        start = (yy * width + x0) * 3
        pixels[start : start + len(row)] = row


def draw_frame(
    pixels: bytearray,
    width: int,
    height: int,
    x: int,
    y: int,
    w: int,
    h: int,
    color: tuple[int, int, int],
    thickness: int = 3,
    alpha: float = 1.0,
) -> None:
    draw_rect(pixels, width, height, x, y, w, thickness, color, alpha)
    draw_rect(pixels, width, height, x, y + h - thickness, w, thickness, color, alpha)
    draw_rect(pixels, width, height, x, y, thickness, h, color, alpha)
    draw_rect(pixels, width, height, x + w - thickness, y, thickness, h, color, alpha)


def draw_grid(pixels: bytearray, width: int, height: int, seed: str) -> None:
    line = blend(hex_to_rgb("#034A68"), (255, 255, 255), 0.1)
    offset = hashlib.sha256(seed.encode()).digest()[2] % 48
    for x in range(-offset, width, 72):
        draw_rect(pixels, width, height, x, 0, 1, height, line, 0.14)
    for y in range(offset, height, 72):
        draw_rect(pixels, width, height, 0, y, width, 1, line, 0.12)


def draw_diagnostic_scene(path: Path, seed: str, width: int = 960, height: int = 540, hero: bool = False) -> None:
    pixels = make_canvas(width, height, seed)
    draw_grid(pixels, width, height, seed)
    blue = hex_to_rgb("#003B96")
    petrol = hex_to_rgb("#034A68")
    purple = hex_to_rgb("#24046B")
    white = (236, 244, 255)
    green = (22, 188, 136)
    amber = (238, 176, 59)
    red = (210, 69, 79)

    margin = int(width * 0.08)
    panel_w = int(width * (0.58 if hero else 0.64))
    panel_h = int(height * 0.56)
    panel_x = margin
    panel_y = int(height * 0.22)
    draw_rect(pixels, width, height, panel_x, panel_y, panel_w, panel_h, (3, 10, 28), 0.72)
    draw_frame(pixels, width, height, panel_x, panel_y, panel_w, panel_h, blue, 4, 0.78)
    draw_rect(pixels, width, height, panel_x, panel_y, panel_w, 38, blue, 0.48)

    for i, dot in enumerate([red, amber, green]):
        draw_rect(pixels, width, height, panel_x + 18 + i * 26, panel_y + 13, 13, 13, dot, 0.92)

    digest = hashlib.sha256(seed.encode()).digest()
    for row in range(9 if hero else 7):
        y = panel_y + 68 + row * int(panel_h * 0.075)
        x = panel_x + 34
        color = [white, green, amber, blue][(digest[row] + row) % 4]
        length = int(panel_w * (0.25 + digest[row] / 255 * 0.48))
        draw_rect(pixels, width, height, x, y, length, 7, color, 0.82)
        draw_rect(pixels, width, height, x, y + 15, int(length * 0.72), 5, petrol, 0.72)

    card_x = panel_x + int(panel_w * 0.58)
    card_y = panel_y + int(panel_h * 0.31)
    card_w = int(panel_w * 0.34)
    card_h = int(panel_h * 0.46)
    draw_rect(pixels, width, height, card_x, card_y, card_w, card_h, purple, 0.46)
    draw_frame(pixels, width, height, card_x, card_y, card_w, card_h, color_from_seed(seed, 9), 3, 0.78)
    for i in range(4):
        draw_rect(
            pixels,
            width,
            height,
            card_x + 20,
            card_y + 26 + i * 34,
            int(card_w * (0.42 + (digest[12 + i] / 255) * 0.38)),
            11,
            [green, amber, red, blue][i],
            0.75,
        )

    right_x = int(width * 0.73)
    for i in range(5):
        box_w = int(width * (0.12 + digest[18 + i] / 255 * 0.1))
        box_h = int(height * 0.075)
        box_y = int(height * (0.16 + i * 0.13))
        color = color_from_seed(seed, i)
        draw_rect(pixels, width, height, right_x, box_y, box_w, box_h, color, 0.4)
        draw_frame(pixels, width, height, right_x, box_y, box_w, box_h, color, 2, 0.75)

    if hero:
        draw_rect(pixels, width, height, int(width * 0.65), int(height * 0.71), int(width * 0.23), 12, green, 0.74)
        draw_rect(pixels, width, height, int(width * 0.65), int(height * 0.76), int(width * 0.17), 9, amber, 0.66)

    write_png(path, width, height, pixels)


def generate_images() -> None:
    images = DOCS / "assets" / "images"
    icons = DOCS / "assets" / "icons"
    draw_diagnostic_scene(images / "codigo-error-hero.png", "codigo-error-hero", 960, 540, True)
    hero_v2 = SOURCE_ASSETS / "codigo-error-hero-v2.png"
    if hero_v2.exists():
        shutil.copy2(hero_v2, images / hero_v2.name)
    draw_diagnostic_scene(images / "codigo-error-og.png", "codigo-error-og", 960, 504, True)
    for category in CATEGORIES:
        draw_diagnostic_scene(images / f"category-{category['slug']}.png", f"category:{category['slug']}", 640, 360)
    draw_diagnostic_scene(icons / "icon-192.png", "icon-192", 192, 192)
    draw_diagnostic_scene(icons / "icon-512.png", "icon-512", 512, 512)
    (icons / "favicon.svg").write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="10" fill="#00020E"/><path d="M14 20h21v7H22v10h13v7H14z" fill="#F4F8FF"/><path d="M38 20h12l-9 24H29z" fill="#D2454F"/><path d="M40 20h10v7H37z" fill="#003B96"/></svg>""",
        encoding="utf-8",
    )


def css() -> str:
    return """
:root {
  --bg: #00020E;
  --panel: #061126;
  --panel-2: #091A32;
  --purple: #24046B;
  --blue: #003B96;
  --petrol: #034A68;
  --neutral: #686A79;
  --text: #F4F8FF;
  --muted: #B7C2D7;
  --line: rgba(244, 248, 255, 0.13);
  --success: #16BC88;
  --warning: #EEB03B;
  --danger: #D2454F;
  color-scheme: dark;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background:
    radial-gradient(circle at 18% 0%, rgba(36, 4, 107, 0.38), transparent 34rem),
    radial-gradient(circle at 84% 12%, rgba(0, 59, 150, 0.26), transparent 28rem),
    linear-gradient(180deg, #00020E 0%, #020817 54%, #00020E 100%);
  color: var(--text);
  line-height: 1.6;
}

a { color: inherit; text-decoration: none; }
a:hover { color: #DCEAFF; }
img { max-width: 100%; display: block; }
button, input { font: inherit; }

.site-header {
  position: sticky;
  top: 0;
  z-index: 20;
  border-bottom: 1px solid var(--line);
  background: rgba(0, 2, 14, 0.86);
  backdrop-filter: blur(18px);
}

.header-inner, .container {
  width: min(1180px, calc(100% - 32px));
  margin: 0 auto;
}

.header-inner {
  min-height: 72px;
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: 22px;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-weight: 900;
  letter-spacing: 0;
}

.brand-mark {
  width: 38px;
  height: 38px;
  border: 1px solid rgba(244, 248, 255, 0.22);
  background: linear-gradient(135deg, #003B96, #24046B 62%, #00020E);
  display: grid;
  place-items: center;
  border-radius: 8px;
  color: #fff;
  font-weight: 900;
}

.brand-error { color: #FF6B78; }

.top-nav {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  flex-wrap: wrap;
}

.top-nav a {
  color: var(--muted);
  padding: 8px 10px;
  border-radius: 7px;
  font-size: 0.92rem;
}

.top-nav a:hover,
.top-nav a[aria-current="page"] {
  background: rgba(0, 59, 150, 0.28);
  color: var(--text);
}

.hero {
  position: relative;
  padding: 64px 0 42px;
  overflow: hidden;
}

.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 0.86fr);
  gap: 34px;
  align-items: center;
}

.eyebrow {
  color: #9EB9FF;
  font-weight: 800;
  text-transform: uppercase;
  font-size: 0.78rem;
  letter-spacing: 0.08em;
}

h1, h2, h3 {
  line-height: 1.12;
  letter-spacing: 0;
  margin: 0;
}

h1 {
  font-size: clamp(2.35rem, 6vw, 5.4rem);
  max-width: 820px;
}

h2 { font-size: clamp(1.7rem, 3vw, 2.55rem); margin-bottom: 18px; }
h3 { font-size: 1.15rem; margin: 22px 0 10px; }
p { margin: 0 0 16px; color: var(--muted); }

.lead {
  font-size: 1.16rem;
  max-width: 720px;
  color: #D9E4F8;
}

.diagnostic-search {
  margin-top: 28px;
  position: relative;
}

.search-box {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  border: 1px solid rgba(244, 248, 255, 0.18);
  background: rgba(5, 16, 38, 0.88);
  padding: 10px;
  border-radius: 8px;
  box-shadow: 0 18px 60px rgba(0, 0, 0, 0.28);
}

.search-box input {
  min-width: 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--text);
  padding: 13px 12px;
}

.search-box button,
.button-link {
  border: 0;
  background: linear-gradient(135deg, #003B96, #034A68);
  color: #fff;
  padding: 12px 16px;
  border-radius: 7px;
  font-weight: 800;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 44px;
}

.button-link.secondary {
  background: rgba(244, 248, 255, 0.08);
  border: 1px solid var(--line);
}

.search-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.query-chip, .tag, .pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid rgba(244, 248, 255, 0.14);
  background: rgba(244, 248, 255, 0.06);
  color: #D9E4F8;
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 0.84rem;
}

button.query-chip {
  appearance: none;
  font: inherit;
  cursor: pointer;
  text-align: left;
  transition: border-color 160ms ease, background-color 160ms ease, color 160ms ease;
}

button.query-chip:hover,
button.query-chip:focus-visible {
  border-color: rgba(158, 185, 255, 0.7);
  background: rgba(0, 59, 150, 0.28);
  color: #FFFFFF;
  outline: none;
}

.search-results {
  position: absolute;
  inset-inline: 0;
  top: calc(100% + 10px);
  z-index: 30;
  display: none;
  border: 1px solid rgba(244, 248, 255, 0.16);
  background: rgba(0, 2, 14, 0.98);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 24px 72px rgba(0, 0, 0, 0.38);
}

.search-results.is-open { display: block; }
.search-result {
  display: block;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(244, 248, 255, 0.08);
}
.search-result strong { display: block; }
.search-result span { color: var(--muted); font-size: 0.92rem; }

.hero-visual figure,
.article-figure,
.category-figure {
  margin: 0;
  border: 1px solid rgba(244, 248, 255, 0.14);
  background: rgba(5, 16, 38, 0.72);
  border-radius: 8px;
  overflow: hidden;
}

.hero-visual img { width: 100%; aspect-ratio: 16 / 9; object-fit: cover; }
figcaption {
  padding: 10px 12px;
  color: #AAB7CC;
  font-size: 0.86rem;
  border-top: 1px solid rgba(244, 248, 255, 0.1);
}

.section {
  padding: 46px 0;
  border-top: 1px solid rgba(244, 248, 255, 0.07);
}

.section-heading {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 18px;
  margin-bottom: 22px;
}

.section-heading p { max-width: 650px; }

.category-grid,
.article-grid,
.diagnostic-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.publication-directory {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.publication-group {
  content-visibility: auto;
  contain-intrinsic-size: 720px;
}

.publication-list {
  columns: 2;
  column-gap: 22px;
  margin: 0;
  padding-left: 18px;
}

.publication-list li {
  break-inside: avoid;
  margin: 0 0 8px;
  color: var(--muted);
}

.publication-list a {
  color: #DCE6F9;
  font-size: 0.92rem;
}

.category-card,
.article-card,
.diagnostic-card,
.info-panel {
  border: 1px solid rgba(244, 248, 255, 0.12);
  background: linear-gradient(180deg, rgba(9, 26, 50, 0.92), rgba(3, 12, 30, 0.92));
  border-radius: 8px;
  padding: 18px;
}

.category-card img,
.article-card img {
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  border-radius: 7px;
  margin-bottom: 13px;
  border: 1px solid rgba(244, 248, 255, 0.1);
}

.category-card h3,
.article-card h3,
.diagnostic-card h3 {
  margin-top: 0;
}

.article-card p,
.category-card p { font-size: 0.94rem; }

.status-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-top: 20px;
}

.status-tile {
  border: 1px solid rgba(244, 248, 255, 0.12);
  background: rgba(244, 248, 255, 0.055);
  border-radius: 8px;
  padding: 14px;
}
.status-tile strong { display: block; font-size: 1.28rem; }
.status-tile span { color: var(--muted); font-size: 0.88rem; }

.breadcrumb {
  color: #AAB7CC;
  font-size: 0.9rem;
  margin: 28px 0 20px;
}
.breadcrumb a { color: #D9E4F8; }
.breadcrumb span { margin: 0 8px; color: var(--neutral); }

.page-hero {
  padding: 40px 0 28px;
}

.page-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.82fr) minmax(280px, 0.38fr);
  gap: 24px;
  align-items: start;
}

.article-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 30px;
  align-items: start;
}

.article-body {
  border: 1px solid rgba(244, 248, 255, 0.12);
  background: rgba(5, 16, 38, 0.74);
  border-radius: 8px;
  padding: 26px;
}

.article-body h2 { margin-top: 34px; }
.article-body h2:first-child { margin-top: 0; }
.article-body ul,
.article-body ol { color: #DCE6F9; padding-left: 22px; }
.article-body li { margin: 8px 0; }

.toc,
.sidebar-panel {
  position: sticky;
  top: 92px;
  border: 1px solid rgba(244, 248, 255, 0.12);
  background: rgba(5, 16, 38, 0.76);
  border-radius: 8px;
  padding: 18px;
}

.toc a {
  display: block;
  color: var(--muted);
  padding: 6px 0;
  border-bottom: 1px solid rgba(244, 248, 255, 0.07);
  font-size: 0.92rem;
}

.checklist {
  display: grid;
  gap: 10px;
  margin: 18px 0;
}
.checklist div {
  border-left: 3px solid var(--success);
  background: rgba(22, 188, 136, 0.08);
  padding: 10px 12px;
  color: #DCE6F9;
}

.symptom-list {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin: 18px 0 26px;
}
.symptom-list li {
  list-style: none;
  margin: 0;
  border: 1px solid rgba(244, 248, 255, 0.11);
  background: rgba(244, 248, 255, 0.055);
  border-radius: 8px;
  padding: 12px;
}

.ad-slot {
  margin: 28px 0;
  min-height: 280px;
  overflow: hidden;
  text-align: center;
}

.ad-label {
  display: block;
  margin-bottom: 8px;
  color: #7F8CA3;
  font-size: 0.72rem;
  text-transform: uppercase;
}

.ad-slot .adsbygoogle {
  min-height: 250px;
}

.faq-item {
  border-top: 1px solid rgba(244, 248, 255, 0.1);
  padding: 16px 0 0;
  margin-top: 16px;
}
.faq-item strong { display: block; color: var(--text); margin-bottom: 8px; }

.site-footer {
  margin-top: 56px;
  border-top: 1px solid var(--line);
  background: rgba(0, 2, 14, 0.72);
  padding: 32px 0;
}

.footer-grid {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 22px;
  align-items: start;
}
.footer-links {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: var(--muted);
}

.not-found {
  min-height: 68vh;
  display: grid;
  align-items: center;
}

@media (max-width: 980px) {
  .hero-grid,
  .page-grid,
  .article-layout {
    grid-template-columns: 1fr;
  }
  .category-grid,
  .article-grid,
  .diagnostic-grid,
  .publication-directory,
  .symptom-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .toc,
  .sidebar-panel {
    position: static;
  }
}

@media (max-width: 680px) {
  .header-inner {
    grid-template-columns: 1fr;
    padding: 12px 0;
  }
  .top-nav { justify-content: flex-start; overflow-x: auto; flex-wrap: nowrap; }
  h1 { font-size: 2.35rem; }
  .hero { padding-top: 38px; }
  .search-box { grid-template-columns: 1fr; }
  .category-grid,
  .article-grid,
  .diagnostic-grid,
  .publication-directory,
  .status-row,
  .symptom-list {
    grid-template-columns: 1fr;
  }
  .publication-list { columns: 1; }
  .article-body { padding: 18px; }
  .section-heading { display: block; }
  .footer-grid { grid-template-columns: 1fr; }
}
""".strip()


def js() -> str:
    return """
(function () {
  const basePath = document.documentElement.dataset.basePath || "";
  const inputs = Array.from(document.querySelectorAll("[data-search-input]"));
  if (!inputs.length) return;

  let index = [];
  let indexPromise;

  function loadIndex() {
    if (!indexPromise) {
      indexPromise = fetch(`${basePath}/search-index.json`)
        .then((response) => {
          if (!response.ok) throw new Error("Search index unavailable");
          return response.json();
        })
        .then((data) => { index = data; })
        .catch(() => { index = []; });
    }
    return indexPromise;
  }

  function normalize(value) {
    return value.toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "");
  }

  function resultUrl(item) {
    const root = basePath || ".";
    return `${root}/${item.p}`.replace(/([^:])\\/+/g, "$1/");
  }

  function score(item, query) {
    const haystack = normalize([
      item.t,
      item.c,
      item.k.join(" ")
    ].join(" "));
    const q = normalize(query);
    if (!q) return 0;
    if (normalize(item.t).includes(q)) return 12;
    if (haystack.includes(q)) return 8;
    return q.split(/\\s+/).filter((part) => part.length > 2 && haystack.includes(part)).length;
  }

  function rankedResults(query, limit = 7) {
    return index
      .map((item) => ({ item, score: score(item, query) }))
      .filter((entry) => entry.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, limit);
  }

  function renderResults(input) {
    const query = input.value.trim();
    const container = input.closest("[data-search-root]").querySelector("[data-search-results]");
    if (!container) return;
    if (query.length < 2) {
      container.classList.remove("is-open");
      container.innerHTML = "";
      return;
    }
    const results = rankedResults(query);
    if (!results.length) {
      container.innerHTML = `<div class="search-result"><strong>Sin resultados exactos</strong><span>Prueba escribir el código, síntoma o categoría con otras palabras.</span></div>`;
      container.classList.add("is-open");
      return;
    }
    container.innerHTML = results.map(({ item }) => `
      <a class="search-result" href="${resultUrl(item)}">
        <strong>${item.t}</strong>
        <span>${item.c} · Abrir diagnóstico paso a paso</span>
      </a>
    `).join("");
    container.classList.add("is-open");
  }

  inputs.forEach((input) => {
    const root = input.closest("[data-search-root]");
    const submit = root.querySelector("[data-search-submit]");
    const suggestions = Array.from(root.querySelectorAll("[data-search-query]"));

    async function openBestResult() {
      const query = input.value.trim();
      if (!query) {
        input.focus();
        return;
      }
      await loadIndex();
      renderResults(input);
      const best = rankedResults(query, 1)[0];
      if (best) window.location.href = resultUrl(best.item);
    }

    input.addEventListener("input", () => loadIndex().then(() => renderResults(input)));
    input.addEventListener("focus", () => loadIndex().then(() => renderResults(input)));
    input.addEventListener("keydown", async (event) => {
      if (event.key !== "Enter") return;
      event.preventDefault();
      await openBestResult();
    });

    submit.addEventListener("click", openBestResult);
    suggestions.forEach((suggestion) => {
      suggestion.addEventListener("click", async () => {
        input.value = suggestion.dataset.searchQuery || suggestion.textContent.trim();
        input.focus();
        await loadIndex();
        renderResults(input);
      });
    });
  });

  document.addEventListener("click", (event) => {
    if (event.target.closest("[data-search-root]")) return;
    document.querySelectorAll("[data-search-results]").forEach((el) => {
      el.classList.remove("is-open");
    });
  });
})();
""".strip()


def common_schema() -> list[dict]:
    logo = absolute_asset_url(SITE["publisher"]["logo"])
    return [
        {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": SITE["publisher"]["name"],
            "url": SITE_URL + "/",
            "logo": logo,
        }
    ]


def breadcrumb_schema(items: list[tuple[str, str]]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": index + 1,
                "name": label,
                "item": absolute_url(route),
            }
            for index, (label, route) in enumerate(items)
        ],
    }


def faq_schema(article: dict) -> dict | None:
    if not article.get("faq"):
        return None
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["q"],
                "acceptedAnswer": {"@type": "Answer", "text": item["a"]},
            }
            for item in article["faq"]
        ],
    }


def render_head(meta: dict, schemas: list[dict]) -> str:
    image = meta.get("image", f"assets/images/codigo-error-og.{IMAGE_EXT}")
    canonical = meta["canonical"]
    title = meta["title"]
    description = meta["description"]
    robots = meta.get("robots", "index,follow,max-image-preview:large")
    schema_html = "\n".join(
        f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False, separators=(",", ":"))}</script>'
        for schema in schemas
        if schema
    )
    return f"""
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="{esc(robots)}">
  <meta name="theme-color" content="{esc(SITE['social']['theme_color'])}">
  <meta name="google-site-verification" content="{esc(SITE['verification']['google_site_verification'])}">
  <link rel="canonical" href="{esc(canonical)}">
  <link rel="manifest" href="{asset_url('site.webmanifest')}">
  <link rel="icon" href="{asset_url('assets/icons/favicon.svg')}" type="image/svg+xml">
  <link rel="apple-touch-icon" href="{asset_url('assets/icons/icon-192.png')}">
  <link rel="preconnect" href="https://www.googletagmanager.com">
  <link rel="preconnect" href="https://pagead2.googlesyndication.com">
  <meta property="og:type" content="{esc(meta.get('og_type', 'website'))}">
  <meta property="og:locale" content="es_ES">
  <meta property="og:site_name" content="{esc(SITE['name'])}">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{esc(canonical)}">
  <meta property="og:image" content="{esc(absolute_asset_url(image))}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:site" content="{esc(SITE['social']['twitter_handle'])}">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(description)}">
  <meta name="twitter:image" content="{esc(absolute_asset_url(image))}">
  <link rel="stylesheet" href="{asset_url('assets/css/styles.css')}">
  <script async src="https://www.googletagmanager.com/gtag/js?id={esc(SITE['analytics']['ga4_measurement_id'])}"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', '{esc(SITE['analytics']['ga4_measurement_id'])}');
  </script>
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={esc(SITE['adsense']['client_id'])}" crossorigin="anonymous"></script>
  {schema_html}
</head>
""".strip()


def nav(current: str = "") -> str:
    links = "\n".join(
        f'<a href="{route_url(category_route(category))}" {"aria-current=\"page\"" if current == category["slug"] else ""}>{esc(category["nav_label"])}</a>'
        for category in CATEGORIES
    )
    return f"""
<header class="site-header">
  <div class="header-inner">
    <a class="brand" href="{route_url()}">
      <span class="brand-mark">CE</span>
      <span>Código <span class="brand-error">Error</span></span>
    </a>
    <nav class="top-nav" aria-label="Categorías principales">
      {links}
    </nav>
  </div>
</header>
""".strip()


def footer() -> str:
    return f"""
<footer class="site-footer">
  <div class="container footer-grid">
    <div>
      <a class="brand" href="{route_url()}"><span class="brand-mark">CE</span><span>Código <span class="brand-error">Error</span></span></a>
      <p>{esc(SITE['tagline'])}</p>
    </div>
    <nav class="footer-links" aria-label="Páginas legales y editoriales">
      <a href="{route_url('sobre-codigo-error')}">Sobre el proyecto</a>
      <a href="{route_url('privacidad')}">Privacidad</a>
      <a href="{route_url('cookies')}">Cookies</a>
      <a href="{route_url('contacto')}">Contacto</a>
      <a href="{route_url('publicaciones')}">Todas las publicaciones</a>
      <a href="{asset_url('sitemap.xml')}">Sitemap</a>
    </nav>
  </div>
</footer>
<script src="{asset_url('assets/js/search.js')}" defer></script>
""".strip()


def search_component(
    label: str = "Busca por código, síntoma o programa",
    examples: list[str] | None = None,
    component_id: str = "search-main",
) -> str:
    examples = examples or ["0xc000007b", "WiFi conectado sin Internet", "Steam no abre", "ERR_CONNECTION_RESET"]
    results_id = f"{component_id}-results"
    chips = "".join(
        f'<button class="query-chip" type="button" data-search-query="{esc(example)}">{esc(example)}</button>'
        for example in examples[:4]
    )
    return f"""
<div class="diagnostic-search" data-search-root>
  <label class="eyebrow" for="{esc(component_id)}">{esc(label)}</label>
  <div class="search-box">
    <input id="{esc(component_id)}" data-search-input type="search" placeholder="Escribe un error, código o problema..." autocomplete="off" aria-controls="{esc(results_id)}">
    <button type="button" data-search-submit aria-label="Buscar diagnóstico">Buscar</button>
  </div>
  <div class="search-meta" aria-label="Ejemplos de búsqueda">{chips}</div>
  <div id="{esc(results_id)}" class="search-results" data-search-results role="listbox" aria-live="polite"></div>
</div>
""".strip()


def ad_block(slot: str = "in_article") -> str:
    slot_id = SITE["adsense"]["slots"][slot]
    if slot == "in_article":
        format_attributes = 'data-ad-layout="in-article" data-ad-format="fluid"'
        ad_style = "display:block; text-align:center;"
    else:
        format_attributes = 'data-ad-format="auto" data-full-width-responsive="true"'
        ad_style = "display:block"
    return f"""
<aside class="ad-slot ad-slot-{esc(slot)}" aria-label="Espacio publicitario">
  <span class="ad-label">Publicidad</span>
  <ins class="adsbygoogle"
       style="{ad_style}"
       data-ad-client="{esc(SITE['adsense']['client_id'])}"
       data-ad-slot="{esc(slot_id)}"
       {format_attributes}></ins>
  <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
</aside>
""".strip()


def layout(route: str, meta: dict, body: str, current: str = "", schemas: list[dict] | None = None) -> str:
    all_schemas = common_schema()
    if schemas:
        all_schemas.extend(schemas)
    return f"""<!doctype html>
<html lang="{esc(SITE['language'])}" data-base-path="{esc(BASE_PATH)}">
{render_head(meta, all_schemas)}
<body>
  {nav(current)}
  <main>
    {body}
  </main>
  {footer()}
</body>
</html>
"""


def write_page(route: str, html_text: str) -> None:
    route = route.strip("/")
    target = DOCS / route / "index.html" if route else DOCS / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html_text, encoding="utf-8")


def article_card(article: dict) -> str:
    category = CATEGORY_BY_SLUG[article["category"]]
    image = f"assets/images/category-{category['slug']}.{IMAGE_EXT}"
    return f"""
<article class="article-card">
  <a href="{route_url(article_route(article))}">
    <img src="{asset_url(image)}" alt="{esc(article['caption'])}" loading="lazy" decoding="async" width="640" height="360">
    <span class="pill">{esc(category['name'])}</span>
    <h3>{esc(article['title'])}</h3>
    <p>{esc(article['summary'])}</p>
  </a>
</article>
""".strip()


def render_home() -> None:
    stats = [
        ("13", "categorías SEO"),
        (str(len(ARTICLES)), "publicaciones"),
        ("2500", "URLs long-tail"),
        ("Schema", "Article + Breadcrumb"),
    ]
    stat_html = "".join(f'<div class="status-tile"><strong>{esc(num)}</strong><span>{esc(label)}</span></div>' for num, label in stats)
    category_html = "\n".join(
        f"""
<article class="category-card">
  <a href="{route_url(category_route(category))}">
    <img src="{asset_url(f"assets/images/category-{category['slug']}.{IMAGE_EXT}")}" alt="{esc(category['caption'])}" loading="lazy" decoding="async" width="640" height="360">
    <h3>{esc(category['name'])}</h3>
    <p>{esc(category['intro'])}</p>
  </a>
</article>
""".strip()
        for category in CATEGORIES
    )
    latest = sorted(ARTICLES, key=lambda item: item["date_modified"], reverse=True)[:6]
    latest_html = "\n".join(article_card(article) for article in latest)
    diagnostic_cards = [
        ("No conozco mi código de error", "Empieza por el síntoma visible: pantalla negra, sin Internet, app que no abre, disco al 100% o dispositivo no reconocido."),
        ("Tengo un código 0x", "Busca el código exacto y revisa contexto: actualización, instalación, juego, .NET, driver o sistema."),
        ("Falló después de actualizar", "Prioriza revertir driver, limpiar caché de actualización, restaurar sistema o confirmar compatibilidad."),
    ]
    diagnostic_html = "".join(f'<article class="diagnostic-card"><h3>{esc(title)}</h3><p>{esc(text)}</p></article>' for title, text in diagnostic_cards)
    body = f"""
<section class="hero">
  <div class="container hero-grid">
    <div>
      <p class="eyebrow">Centro de diagnóstico digital</p>
      <h1>¿Qué está fallando?</h1>
      <p class="lead">Encuentra códigos de error, causas probables y soluciones paso a paso para Windows, PC, gaming, Android, Internet, drivers, periféricos y programas.</p>
      {search_component()}
      <div class="status-row">{stat_html}</div>
    </div>
    <div class="hero-visual">
      <figure>
        <img src="{asset_url(f'assets/images/codigo-error-hero-v2.{IMAGE_EXT}')}" alt="Centro digital con paneles de diagnóstico de hardware, red y sistema" width="1440" height="810" fetchpriority="high" decoding="async">
        <figcaption>Diagnóstico tecnológico organizado por código, síntoma, dispositivo y programa.</figcaption>
      </figure>
    </div>
  </div>
</section>
<section class="section">
  <div class="container">
    <div class="section-heading">
      <div>
        <p class="eyebrow">Diagnóstico por área</p>
        <h2>Categorías preparadas para crecer sin duplicar contenido</h2>
      </div>
      <p>Cada categoría agrupa intención de búsqueda, síntomas y códigos relacionados para construir una arquitectura SEO escalable.</p>
    </div>
    <div class="category-grid">{category_html}</div>
  </div>
</section>
<section class="section">
  <div class="container">
    <div class="section-heading">
      <div>
        <p class="eyebrow">Primeras guías</p>
        <h2>Contenido inicial real y organizado</h2>
      </div>
      <a class="button-link secondary" href="{route_url('codigos-error')}">Ver códigos</a>
    </div>
    <div class="article-grid">{latest_html}</div>
    <p><a class="button-link secondary" href="{route_url('publicaciones')}">Ver las {len(ARTICLES)} publicaciones</a></p>
  </div>
</section>
<section class="section">
  <div class="container">
    <div class="section-heading">
      <div>
        <p class="eyebrow">Flujo de diagnóstico</p>
        <h2>Busca como lo hace el usuario: por síntoma, contexto o código</h2>
      </div>
    </div>
    <div class="diagnostic-grid">{diagnostic_html}</div>
  </div>
</section>
""".strip()
    website_schema = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE["name"],
        "url": SITE_URL + "/",
        "potentialAction": {
            "@type": "SearchAction",
            "target": f"{SITE_URL}/?q={{search_term_string}}",
            "query-input": "required name=search_term_string",
        },
    }
    meta = {
        "title": "Código Error: soluciones para errores de Windows, PC, Android e Internet",
        "description": SITE["description"],
        "canonical": absolute_url(),
        "image": f"assets/images/codigo-error-og.{IMAGE_EXT}",
    }
    write_page("", layout("", meta, body, schemas=[website_schema]))


def render_category(category: dict) -> None:
    articles = [article for article in ARTICLES if article["category"] == category["slug"]]
    cards = "\n".join(article_card(article) for article in articles)
    body = f"""
<section class="page-hero">
  <div class="container">
    <nav class="breadcrumb"><a href="{route_url()}">Inicio</a><span>/</span>{esc(category['name'])}</nav>
    <div class="page-grid">
      <div>
        <p class="eyebrow">Categoría de diagnóstico</p>
        <h1>{esc(category['h1'])}</h1>
        <p class="lead">{esc(category['intro'])}</p>
        {search_component(
            f"Busca códigos y problemas de {category['name']}",
            examples=category["keywords"],
            component_id=f"search-{category['slug']}",
        )}
      </div>
      <figure class="category-figure">
        <img src="{asset_url(f"assets/images/category-{category['slug']}.{IMAGE_EXT}")}" alt="{esc(category['caption'])}" loading="lazy" decoding="async" width="640" height="360">
        <figcaption>{esc(category['caption'])}</figcaption>
      </figure>
    </div>
  </div>
</section>
<section class="section">
  <div class="container">
    <div class="section-heading">
      <div>
        <h2>Guías disponibles de {esc(category['name'])}</h2>
        <p>La lista está preparada para crecer por códigos concretos, síntomas y modelos sin mezclar intenciones de búsqueda.</p>
      </div>
    </div>
    <div class="article-grid">{cards}</div>
  </div>
</section>
<section class="section">
  <div class="container">
    <div class="info-panel">
      <h2>Estrategia long-tail para {esc(category['name'])}</h2>
      <p>Esta sección prioriza búsquedas específicas como problema + sistema + contexto, por ejemplo: "{esc(category['keywords'][0])}". Cada nueva guía debe resolver una intención clara, incluir síntomas observables y conectar con diagnósticos relacionados.</p>
      <h3>Cómo se evita contenido duplicado</h3>
      <p>Los artículos se crean desde datos únicos: título, descripción, H1, pasos, preguntas frecuentes, imagen y schema por página. Si dos búsquedas comparten solución, se enlazan entre sí en lugar de publicar copias casi iguales.</p>
    </div>
  </div>
</section>
""".strip()
    schemas = [
        breadcrumb_schema([("Inicio", ""), (category["name"], category_route(category))])
    ]
    meta = {
        "title": category["title"],
        "description": category["meta_description"],
        "canonical": absolute_url(category_route(category)),
        "image": f"assets/images/category-{category['slug']}.{IMAGE_EXT}",
    }
    write_page(category_route(category), layout(category_route(category), meta, body, current=category["slug"], schemas=schemas))


def render_article(article: dict) -> None:
    category = CATEGORY_BY_SLUG[article["category"]]
    route = article_route(article)
    image = f"assets/images/category-{category['slug']}.{IMAGE_EXT}"
    tags = "".join(f'<span class="tag">{esc(keyword)}</span>' for keyword in article["keywords"][:5])
    symptoms = "".join(f"<li>{esc(item)}</li>" for item in article["symptoms"])
    checks = "".join(f"<div>{esc(item)}</div>" for item in article["quick_checks"])
    toc_links = "".join(
        f'<a href="#{section_id(article["slug"], index)}">{esc(section["h2"])}</a>'
        for index, section in enumerate(article["sections"], start=1)
    )
    section_html = []
    for index, section in enumerate(article["sections"], start=1):
        parts = [f'<h2 id="{section_id(article["slug"], index)}">{esc(section["h2"])}</h2>']
        for paragraph in section.get("paragraphs", []):
            parts.append(f"<p>{esc(paragraph)}</p>")
        if section.get("h3"):
            parts.append(f"<h3>{esc(section['h3'])}</h3>")
        if section.get("steps"):
            parts.append("<ol>" + "".join(f"<li>{esc(step)}</li>" for step in section["steps"]) + "</ol>")
        section_html.append("\n".join(parts))
    faqs = "\n".join(
        f'<div class="faq-item"><strong>{esc(item["q"])}</strong><p>{esc(item["a"])}</p></div>'
        for item in article.get("faq", [])
    )
    related = [
        item for item in ARTICLES
        if item["category"] == article["category"] and item["slug"] != article["slug"]
    ][:3]
    related_html = "\n".join(article_card(item) for item in related)
    body = f"""
<section class="page-hero">
  <div class="container">
    <nav class="breadcrumb"><a href="{route_url()}">Inicio</a><span>/</span><a href="{route_url(category_route(category))}">{esc(category['name'])}</a><span>/</span>{esc(article['title'])}</nav>
    <p class="eyebrow">Guía de diagnóstico</p>
    <h1>{esc(article['h1'])}</h1>
    <p class="lead">{esc(article['summary'])}</p>
    <div class="search-meta">{tags}</div>
  </div>
</section>
<section class="section">
  <div class="container article-layout">
    <article class="article-body">
      <figure class="article-figure">
        <img src="{asset_url(image)}" alt="{esc(article['caption'])}" loading="lazy" decoding="async" width="960" height="540">
        <figcaption>{esc(article['caption'])}</figcaption>
      </figure>
      <h2>Síntomas frecuentes</h2>
      <ul class="symptom-list">{symptoms}</ul>
      <h2>Comprobaciones rápidas antes de avanzar</h2>
      <div class="checklist">{checks}</div>
      {ad_block('in_article')}
      {"".join(section_html)}
      <h2>Preguntas frecuentes</h2>
      {faqs}
    </article>
    <aside>
      <div class="toc">
        <h3>En esta guía</h3>
        {toc_links}
      </div>
      {ad_block('sidebar')}
    </aside>
  </div>
</section>
<section class="section">
  <div class="container">
    <div class="section-heading"><h2>Diagnósticos relacionados</h2></div>
    <div class="article-grid">{related_html}</div>
  </div>
</section>
""".strip()
    article_schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": article["title"],
        "description": article["meta_description"],
        "image": absolute_asset_url(image),
        "datePublished": article["date_published"],
        "dateModified": article["date_modified"],
        "author": {"@type": "Organization", "name": SITE["author"]},
        "publisher": {
            "@type": "Organization",
            "name": SITE["publisher"]["name"],
            "logo": {
                "@type": "ImageObject",
                "url": absolute_asset_url(SITE["publisher"]["logo"]),
            },
        },
        "articleSection": category["name"],
        "mainEntityOfPage": {"@type": "WebPage", "@id": absolute_url(route)},
        "keywords": article["keywords"],
    }
    schemas = [
        breadcrumb_schema([("Inicio", ""), (category["name"], category_route(category)), (article["title"], route)]),
        article_schema,
        faq_schema(article),
    ]
    meta = {
        "title": f"{article['title']} | Código Error",
        "description": article["meta_description"],
        "canonical": absolute_url(route),
        "image": image,
        "og_type": "article",
    }
    write_page(route, layout(route, meta, body, current=category["slug"], schemas=schemas))


def section_id(slug: str, index: int) -> str:
    return f"{slug}-seccion-{index}"


def render_publications_page() -> None:
    groups = []
    for category in CATEGORIES:
        articles = [article for article in ARTICLES if article["category"] == category["slug"]]
        items = "\n".join(
            f'<li><a href="{route_url(article_route(article))}">{esc(article["title"])}</a></li>'
            for article in articles
        )
        groups.append(
            f"""
<section class="info-panel publication-group">
  <h2>{esc(category['name'])}</h2>
  <p>{len(articles)} publicaciones long-tail en esta categoría.</p>
  <ol class="publication-list">{items}</ol>
</section>
""".strip()
        )
    body = f"""
<section class="page-hero">
  <div class="container">
    <nav class="breadcrumb"><a href="{route_url()}">Inicio</a><span>/</span>Todas las publicaciones</nav>
    <p class="eyebrow">Índice completo</p>
    <h1>Todas las publicaciones de Código Error</h1>
    <p class="lead">Listado completo de las {len(ARTICLES)} URLs generadas, agrupadas por categoría para revisión editorial, rastreo interno y despliegue por lotes.</p>
    {search_component("Busca dentro de las publicaciones")}
  </div>
</section>
<section class="section">
  <div class="container publication-directory">
    {"".join(groups)}
  </div>
</section>
""".strip()
    schemas = [breadcrumb_schema([("Inicio", ""), ("Todas las publicaciones", "publicaciones")])]
    meta = {
        "title": f"Todas las publicaciones de Código Error: {len(ARTICLES)} guías SEO",
        "description": f"Índice completo de {len(ARTICLES)} publicaciones de Código Error agrupadas por Windows, PC, gaming, Android, Internet, drivers, programas y códigos.",
        "canonical": absolute_url("publicaciones"),
        "image": f"assets/images/codigo-error-og.{IMAGE_EXT}",
    }
    write_page("publicaciones", layout("publicaciones", meta, body, schemas=schemas))


def legal_pages() -> list[dict]:
    return [
        {
            "route": "sobre-codigo-error",
            "title": "Sobre Código Error | Diagnóstico tecnológico en español",
            "h1": "Sobre Código Error",
            "description": "Conoce la metodología editorial de Código Error para publicar guías técnicas claras, verificables y útiles para usuarios en español.",
            "body": [
                ("Qué es Código Error", "Código Error es una plataforma de diagnóstico tecnológico orientada a usuarios que buscan una solución concreta por código, síntoma, sistema o programa."),
                ("Metodología editorial", "Cada guía parte de una intención de búsqueda específica, organiza síntomas, comprobaciones rápidas y soluciones en orden de menor a mayor riesgo."),
                ("Escalabilidad sin duplicación", "El sitio está preparado para miles de páginas, pero cada una debe tener título, descripción, pasos, preguntas y contexto propio."),
            ],
        },
        {
            "route": "privacidad",
            "title": "Política de privacidad | Código Error",
            "h1": "Política de privacidad",
            "description": "Política de privacidad de Código Error con información sobre analítica, publicidad, cookies y contacto.",
            "body": [
                ("Datos de navegación", "Código Error utiliza Google Analytics 4 para medir de forma agregada visitas, páginas consultadas, dispositivos y fuentes de tráfico. No se deben enviar datos personales dentro de códigos, búsquedas o formularios."),
                ("Publicidad", "El sitio utiliza Google AdSense para gestionar espacios publicitarios. Google puede tratar datos técnicos y usar cookies conforme a las preferencias de consentimiento aplicables en cada región."),
                ("Contacto", "Las solicitudes de privacidad, correcciones editoriales y avisos sobre contenido pueden enviarse mediante el canal público de incidencias del repositorio de Código Error."),
            ],
        },
        {
            "route": "cookies",
            "title": "Política de cookies | Código Error",
            "h1": "Política de cookies",
            "description": "Información sobre cookies técnicas, analítica y publicidad en Código Error.",
            "body": [
                ("Cookies técnicas", "El sitio puede usar almacenamiento local para mejorar la búsqueda y preferencias básicas de navegación."),
                ("Cookies de analítica", "Google Analytics 4 puede utilizar cookies o señales equivalentes para medir visitas e interacción cuando la configuración de consentimiento lo permite."),
                ("Cookies publicitarias", "Google AdSense puede usar cookies y otras señales para medición, prevención de fraude y personalización de anuncios según la región y las preferencias del visitante."),
            ],
        },
        {
            "route": "contacto",
            "title": "Contacto | Código Error",
            "h1": "Contacto",
            "description": "Página de contacto editorial para Código Error.",
            "body": [
                ("Contacto editorial", "Para sugerir correcciones, nuevos códigos de error o mejoras de una guía, abre una incidencia pública en el repositorio de Código Error."),
                ("Sugerencias de contenido", "Incluye el sistema operativo, código exacto, mensaje completo y cuándo empezó el fallo. Eso ayuda a convertir consultas reales en guías útiles."),
                ("Aviso", "Código Error ofrece información técnica general. No reemplaza diagnóstico profesional cuando hay riesgo de pérdida de datos, daño físico o seguridad."),
            ],
        },
    ]


def render_legal_page(page: dict) -> None:
    sections = "\n".join(f"<h2>{esc(title)}</h2><p>{esc(text)}</p>" for title, text in page["body"])
    contact_link = ""
    if page["route"] == "contacto":
        contact_link = (
            '<p><a class="button-link secondary" '
            'href="https://github.com/IAFUTURE10/CODIGOERROR/issues/new" '
            'rel="noopener noreferrer">Abrir una incidencia en GitHub</a></p>'
        )
    body = f"""
<section class="page-hero">
  <div class="container">
    <nav class="breadcrumb"><a href="{route_url()}">Inicio</a><span>/</span>{esc(page['h1'])}</nav>
    <p class="eyebrow">Información del sitio</p>
    <h1>{esc(page['h1'])}</h1>
    <p class="lead">{esc(page['description'])}</p>
  </div>
</section>
<section class="section">
  <div class="container page-grid">
    <article class="article-body">{sections}{contact_link}</article>
    <aside class="sidebar-panel">
      <h3>Buscar diagnóstico</h3>
      {search_component("Busca una guía")}
    </aside>
  </div>
</section>
""".strip()
    schemas = [breadcrumb_schema([("Inicio", ""), (page["h1"], page["route"])])]
    meta = {
        "title": page["title"],
        "description": page["description"],
        "canonical": absolute_url(page["route"]),
        "image": f"assets/images/codigo-error-og.{IMAGE_EXT}",
    }
    write_page(page["route"], layout(page["route"], meta, body, schemas=schemas))


def render_404() -> None:
    meta = {
        "title": "Página no encontrada | Código Error",
        "description": "La página solicitada no existe. Busca el código de error, síntoma o categoría para encontrar un diagnóstico.",
        "canonical": absolute_url("404"),
        "robots": "noindex,follow",
        "image": f"assets/images/codigo-error-og.{IMAGE_EXT}",
    }
    body = f"""
<section class="not-found">
  <div class="container">
    <p class="eyebrow">Error 404</p>
    <h1>Página no encontrada</h1>
    <p class="lead">La ruta no existe o cambió. Busca el código, síntoma o programa para encontrar una guía relacionada.</p>
    {search_component()}
    <p><a class="button-link secondary" href="{route_url()}">Volver al inicio</a></p>
  </div>
</section>
""".strip()
    (DOCS / "404.html").write_text(layout("404", meta, body), encoding="utf-8")


def write_static_assets() -> None:
    (DOCS / "assets" / "css" / "styles.css").write_text(css(), encoding="utf-8")
    (DOCS / "assets" / "js" / "search.js").write_text(js(), encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    (DOCS / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n",
        encoding="utf-8",
    )
    (DOCS / "ads.txt").write_text(
        f"google.com, {SITE['adsense']['publisher_id_for_ads_txt']}, DIRECT, f08c47fec0942fa0\n",
        encoding="utf-8",
    )
    manifest = {
        "name": SITE["name"],
        "short_name": "Código Error",
        "description": SITE["description"],
        "lang": SITE["language"],
        "start_url": route_url(),
        "scope": route_url(),
        "display": "standalone",
        "background_color": SITE["colors"]["background"],
        "theme_color": SITE["social"]["theme_color"],
        "icons": [
            {"src": asset_url("assets/icons/icon-192.png"), "sizes": "192x192", "type": "image/png"},
            {"src": asset_url("assets/icons/icon-512.png"), "sizes": "512x512", "type": "image/png"},
        ],
    }
    (DOCS / "site.webmanifest").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def write_search_index() -> None:
    index = []
    for article in ARTICLES:
        category = CATEGORY_BY_SLUG[article["category"]]
        index.append(
            {
                "t": article["title"],
                "c": category["name"],
                "p": f"{article_route(article)}/",
                "k": article["keywords"],
            }
        )
    (DOCS / "search-index.json").write_text(
        json.dumps(index, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def xml_escape(value: str) -> str:
    return esc(value)


def sitemap_urlset(routes: list[tuple[str, str, float]]) -> str:
    entries = []
    for route, lastmod, priority in routes:
        entries.append(
            f"  <url><loc>{xml_escape(absolute_url(route))}</loc><lastmod>{lastmod}</lastmod><changefreq>weekly</changefreq><priority>{priority:.1f}</priority></url>"
        )
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(entries) + "\n</urlset>\n"


def write_sitemaps() -> None:
    page_routes: list[tuple[str, str, float]] = [("", TODAY, 1.0)]
    page_routes.extend((category_route(category), TODAY, 0.8) for category in CATEGORIES)
    page_routes.append(("publicaciones", TODAY, 0.6))
    page_routes.extend((page["route"], TODAY, 0.4) for page in legal_pages())
    (DOCS / "sitemaps" / "sitemap-pages.xml").write_text(sitemap_urlset(page_routes), encoding="utf-8")

    sitemap_paths = ["sitemaps/sitemap-pages.xml"]
    for category in CATEGORIES:
        articles = [article for article in ARTICLES if article["category"] == category["slug"]]
        routes = [(article_route(article), article["date_modified"], 0.7) for article in articles]
        path = f"sitemaps/sitemap-{category['slug']}.xml"
        (DOCS / path).write_text(sitemap_urlset(routes), encoding="utf-8")
        sitemap_paths.append(path)
    index_entries = "\n".join(
        f"  <sitemap><loc>{xml_escape(absolute_asset_url(path))}</loc><lastmod>{TODAY}</lastmod></sitemap>"
        for path in sitemap_paths
    )
    sitemap_index = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + index_entries
        + "\n</sitemapindex>\n"
    )
    for filename in ("sitemap.xml", "sitemap-index.xml"):
        (DOCS / filename).write_text(sitemap_index, encoding="utf-8")


def validate_sources() -> None:
    seen_routes = set()
    seen_titles = set()
    for category in CATEGORIES:
        if category["slug"] in seen_routes:
            raise ValueError(f"Duplicate category slug: {category['slug']}")
        seen_routes.add(category["slug"])
    for article in ARTICLES:
        if article["category"] not in CATEGORY_BY_SLUG:
            raise ValueError(f"Unknown category for article {article['slug']}: {article['category']}")
        route = article_route(article)
        if route in seen_routes:
            raise ValueError(f"Duplicate route: {route}")
        seen_routes.add(route)
        if article["title"] in seen_titles:
            raise ValueError(f"Duplicate article title: {article['title']}")
        seen_titles.add(article["title"])


def main() -> None:
    validate_sources()
    ensure_clean_docs()
    generate_images()
    write_static_assets()
    render_home()
    for category in CATEGORIES:
        render_category(category)
    for article in ARTICLES:
        render_article(article)
    render_publications_page()
    for page in legal_pages():
        render_legal_page(page)
    render_404()
    write_search_index()
    write_sitemaps()
    print(f"Generated {len(ARTICLES)} articles, {len(CATEGORIES)} categories and {len(legal_pages()) + 3} utility pages in {DOCS}")


if __name__ == "__main__":
    main()
