# Código Error

Código Error es una web estática de diagnóstico tecnológico en español, preparada para GitHub Pages, SEO técnico, Google AdSense, GA4 y Search Console.

## Qué incluye

- Arquitectura escalable por datos para 2500 guías generadas.
- Categorías: Windows, PC/Laptops, Gaming, Android, Internet, Navegadores, Almacenamiento, Gráficos, Audio, Drivers, Periféricos, Programas y Códigos de error.
- Buscador por código, síntoma, programa o categoría.
- URLs limpias con páginas `index.html` por ruta.
- `title`, `meta description`, H1/H2/H3 y contenido único por artículo.
- Canonicals, Open Graph, Twitter Cards y schema JSON-LD.
- Breadcrumbs visibles y `BreadcrumbList` schema.
- `Article`, `WebSite` y `Organization` schema.
- Imágenes locales WebP con `alt`, `figcaption`, `loading="lazy"` y dimensiones.
- `robots.txt`, `ads.txt`, `site.webmanifest`, favicon e iconos placeholder.
- `sitemap.xml` único con todas las URLs, más `sitemap-index.xml` y sitemaps separados por categoría como respaldo.
- Página 404, privacidad, cookies, contacto y sobre el proyecto.
- Workflow de GitHub Pages con generación y validación automática.

## Estructura

```text
data/
  site.json          Configuración de dominio, AdSense, GA4, Search Console y marca
  categories.json    Categorías principales y estrategia long-tail
  articles.json      Artículos semilla revisables manualmente
scripts/
  build.py           Genera la web estática en docs/
  content_scale.py   Expande la matriz long-tail hasta 2500 publicaciones
  optimize-images.mjs Convierte imágenes de contenido a WebP
  make_desktop_copy.py Crea una copia navegable directamente desde el Escritorio
  validate.py        Valida metadatos, schema, sitemaps e imágenes básicas
docs/                Sitio final listo para publicar en GitHub Pages
.github/workflows/
  pages.yml          Deploy automático con GitHub Actions
```

## Integraciones de Google

La configuración de producción vive en `data/site.json`. En este repositorio ya están cargados el token de Search Console, el ID de medición de GA4, el cliente de AdSense y los tres slots publicitarios de Código Error.

Si el proyecto se migra a otra cuenta o propiedad, reemplaza esos valores en `data/site.json`:

Edita `data/site.json`:

```json
{
  "site_url": "https://TU-USUARIO.github.io/codigo-error",
  "base_path": "/codigo-error",
  "verification": {
    "google_site_verification": "TOKEN_DE_SEARCH_CONSOLE"
  },
  "analytics": {
    "ga4_measurement_id": "G-XXXXXXXXXX"
  },
  "adsense": {
    "client_id": "ca-pub-XXXXXXXXXXXXXXXX",
    "publisher_id_for_ads_txt": "pub-XXXXXXXXXXXXXXXX",
    "slots": {
      "in_article": "1234567890",
      "sidebar": "1234567891",
      "responsive": "1234567892"
    }
  }
}
```

Si usas dominio propio, cambia:

```json
"site_url": "https://tudominio.com",
"base_path": ""
```

Después regenera el sitio:

```bash
python scripts/build.py
node scripts/optimize-images.mjs
python scripts/validate.py
```

## Publicaciones y escala

El sitio genera 2500 publicaciones desde una matriz long-tail controlada. Las 20 entradas de `data/articles.json` son semillas editoriales; el resto se genera desde `scripts/content_scale.py` combinando categoría, síntoma, contexto y ruta de diagnóstico.

Esto evita tener que escribir 2500 archivos a mano, pero no elimina la revisión editorial: para AdSense conviene publicar por lotes, revisar Search Console y mejorar las páginas que reciban impresiones.

Para cambiar el total:

```json
"content": {
  "target_articles": 2500
}
```

## Agregar artículos manuales sin duplicar contenido

Agrega nuevos objetos a `data/articles.json`. Cada artículo debe tener:

- `slug` único.
- `category` existente.
- `title`, `meta_description` y `h1` propios.
- `keywords` long-tail reales.
- `symptoms`, `quick_checks`, `sections`, `faq` y `caption`.

El generador creará automáticamente:

- URL limpia.
- Página HTML.
- Breadcrumb visible y schema.
- Article schema.
- Imagen diagnóstica local.
- Entrada en buscador.
- Entrada en el sitemap de su categoría.

## Desplegar en GitHub Pages

1. Usa el repositorio `IAFUTURE10/CODIGOERROR`.
2. Sube estos archivos a la rama `main`.
3. En GitHub, ve a `Settings > Pages`.
4. En `Build and deployment`, selecciona `GitHub Actions`.
5. Ejecuta el workflow `Deploy Código Error to GitHub Pages` o empuja un cambio a `main`.
6. Cuando termine, revisa `https://iafuture10.github.io/CODIGOERROR/`.

También puedes publicar desde `docs/` usando la opción clásica de Pages, pero el workflow incluido es más seguro porque regenera y valida antes de desplegar.

## Search Console y sitemap

Cuando la URL esté publicada:

1. Agrega la propiedad en Google Search Console.
2. Copia el token de verificación en `data/site.json`.
3. Regenera y vuelve a desplegar.
4. Envía el sitemap canónico de la raíz:

```text
https://iafuture10.github.io/sitemap.xml
```

## AdSense

Antes de solicitar revisión o activar anuncios reales en otra cuenta:

1. Reemplaza el cliente `ca-pub`.
2. Reemplaza el identificador `pub` usado para `ads.txt`.
3. Reemplaza los tres slots publicitarios.
4. Regenera el sitio para actualizar `ads.txt` y las etiquetas de anuncio.
5. Mantén publicadas las páginas de privacidad, cookies, contacto y sobre el proyecto con datos reales.

## Desarrollo local

```bash
python scripts/build.py
node scripts/optimize-images.mjs
python scripts/validate.py
python -m http.server 8000 --directory docs
```

Para GitHub Pages de proyecto, los enlaces se generan con `base_path: "/CODIGOERROR"`. Si pruebas localmente y quieres enlaces desde raíz local, cambia temporalmente `base_path` a `""`, regenera y no publiques ese cambio.

AdSense consulta `ads.txt` en la raíz del host. Además del archivo generado dentro del proyecto, la cuenta publica `https://iafuture10.github.io/ads.txt` desde el repositorio raíz `IAFUTURE10/IAFUTURE10.github.io`. Ese repositorio también publica `https://iafuture10.github.io/sitemap.xml` con todas las URLs indexables para Search Console.

## Copia para el Escritorio

```bash
python scripts/build.py
node scripts/optimize-images.mjs
python scripts/make_desktop_copy.py "C:\Users\Admin\Desktop\Codigo Error Web"
```

La copia de Escritorio ajusta los enlaces para abrir `index.html` directamente sin depender de GitHub Pages.
