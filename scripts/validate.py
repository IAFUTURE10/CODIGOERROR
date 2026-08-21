from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from content_scale import expand_articles


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SITE = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
SEED_ARTICLES = json.loads((ROOT / "data" / "articles.json").read_text(encoding="utf-8"))
CATEGORIES = json.loads((ROOT / "data" / "categories.json").read_text(encoding="utf-8"))
ARTICLES = expand_articles(
    SEED_ARTICLES,
    CATEGORIES,
    int(SITE.get("content", {}).get("target_articles", len(SEED_ARTICLES))),
    date.today().isoformat(),
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contains(text: str, needle: str, path: Path) -> None:
    if needle not in text:
        raise AssertionError(f"{path} missing {needle}")


def main() -> None:
    configured_values = [
        SITE["verification"]["google_site_verification"],
        SITE["analytics"]["ga4_measurement_id"],
        SITE["adsense"]["client_id"],
        SITE["adsense"]["publisher_id_for_ads_txt"],
        *SITE["adsense"]["slots"].values(),
    ]
    if any("REEMPLAZAR" in value or value == "pub-0000000000000000" for value in configured_values):
        raise AssertionError("Google service identifiers must be configured before production")

    if not (DOCS / "index.html").exists():
        raise AssertionError("docs/index.html was not generated")
    if not (DOCS / "sitemap-index.xml").exists():
        raise AssertionError("sitemap-index.xml was not generated")
    if not (DOCS / "sitemap.xml").exists():
        raise AssertionError("sitemap.xml was not generated")
    if not (DOCS / "robots.txt").exists():
        raise AssertionError("robots.txt was not generated")
    if not (DOCS / "ads.txt").exists():
        raise AssertionError("ads.txt was not generated")
    if not (DOCS / "site.webmanifest").exists():
        raise AssertionError("site.webmanifest was not generated")

    html_files = list(DOCS.rglob("*.html"))
    expected_html_count = len(ARTICLES) + len(CATEGORIES) + 7
    if len(html_files) != expected_html_count:
        raise AssertionError(f"Expected {expected_html_count} HTML files, found {len(html_files)}")

    article_paths: list[Path] = []
    for article in ARTICLES:
        path = DOCS / article["category"] / article["slug"] / "index.html"
        if not path.exists():
            raise AssertionError(f"Missing article page: {path}")
        article_paths.append(path)

    source_titles = [article["title"] for article in ARTICLES]
    source_descriptions = [article["meta_description"] for article in ARTICLES]
    if len(source_titles) != len(set(source_titles)):
        raise AssertionError("Article titles must be unique")
    if len(source_descriptions) != len(set(source_descriptions)):
        raise AssertionError("Article meta descriptions must be unique")

    utility_paths = [
        DOCS / "index.html",
        DOCS / "publicaciones" / "index.html",
        DOCS / "404.html",
    ]
    utility_paths.extend(DOCS / category["slug"] / "index.html" for category in CATEGORIES)
    utility_paths.extend(
        DOCS / route / "index.html"
        for route in ["sobre-codigo-error", "contacto", "privacidad", "cookies"]
    )

    sampled_article_paths: list[Path] = []
    for category in CATEGORIES:
        category_paths = [
            path for article, path in zip(ARTICLES, article_paths)
            if article["category"] == category["slug"]
        ]
        sampled_article_paths.extend([category_paths[0], category_paths[len(category_paths) // 2], category_paths[-1]])

    for path in utility_paths + sampled_article_paths:
        text = read(path)
        title = re.search(r"<title>(.*?)</title>", text, re.S)
        description = re.search(r'<meta name="description" content="(.*?)">', text, re.S)
        h1 = re.search(r"<h1[^>]*>", text)
        if not title or not title.group(1).strip():
            raise AssertionError(f"{path} missing title")
        if not description or not description.group(1).strip():
            raise AssertionError(f"{path} missing meta description")
        if not h1:
            raise AssertionError(f"{path} missing H1")
        assert_contains(text, '<link rel="canonical"', path)
        assert_contains(text, 'application/ld+json', path)
        assert_contains(text, 'og:title', path)
        assert_contains(text, 'twitter:card', path)
        if re.search(r"assets/images/[^\"']+\.png", text):
            raise AssertionError(f"{path} should use WebP images for content imagery")

    for category in CATEGORIES:
        sitemap = DOCS / "sitemaps" / f"sitemap-{category['slug']}.xml"
        if not sitemap.exists():
            raise AssertionError(f"Missing category sitemap: {sitemap}")

        category_page = DOCS / category["slug"] / "index.html"
        category_html = read(category_page)
        assert_contains(category_html, "data-search-root", category_page)
        assert_contains(category_html, "data-search-submit", category_page)
        assert_contains(category_html, "data-search-query", category_page)

    search_script_path = DOCS / "assets" / "js" / "search.js"
    search_script = read(search_script_path)
    assert_contains(search_script, 'querySelector("[data-search-submit]")', search_script_path)
    assert_contains(search_script, 'querySelectorAll("[data-search-query]")', search_script_path)

    for path in sampled_article_paths:
        text = read(path)
        assert_contains(text, '"@type":"Article"', path)
        assert_contains(text, '"@type":"BreadcrumbList"', path)
        assert_contains(text, "<figcaption>", path)
        assert_contains(text, ".webp", path)
        assert_contains(text, 'loading="lazy"', path)
        for image_tag in re.findall(r"<img\b[^>]*>", text):
            if 'width="' not in image_tag or 'height="' not in image_tag:
                raise AssertionError(f"{path} contains an image without stable dimensions")
        assert_contains(text, SITE["adsense"]["client_id"], path)
        assert_contains(text, SITE["adsense"]["slots"]["in_article"], path)
        assert_contains(text, SITE["adsense"]["slots"]["sidebar"], path)
        assert_contains(text, "(adsbygoogle = window.adsbygoogle || []).push({});", path)
        if len(re.findall(r"<h2", text)) < 4:
            raise AssertionError(f"{path} should contain multiple H2 headings")
        if len(re.findall(r"<h3", text)) < 2:
            raise AssertionError(f"{path} should contain H3 headings")

    search_index = json.loads((DOCS / "search-index.json").read_text(encoding="utf-8"))
    if len(search_index) != len(ARTICLES):
        raise AssertionError("Search index count does not match articles")

    if list((DOCS / "assets" / "images").glob("*.png")):
        raise AssertionError("Content images should be converted to WebP")

    print(
        f"Validated {len(html_files)} HTML routes, {len(ARTICLES)} unique articles, "
        f"{len(sampled_article_paths)} article pages in depth and {len(CATEGORIES)} category sitemaps."
    )


if __name__ == "__main__":
    main()
