# Código Error

Biblioteca de diagnóstico tecnológico en español publicada en https://iafuture10.github.io/CODIGOERROR/.

La edición actual sustituye la expansión automática de 2.500 publicaciones por **8 guías concretas**, cada una con alcance, síntomas observables, acción, resultado esperado, decisión siguiente, reversión, límites y fuentes primarias. No se publican variantes creadas cambiando solo el sistema o el título. No se afirman pruebas físicas sobre equipos que no se han examinado.

## Desarrollo y validación

Se necesita Python 3.12. La generación no instala paquetes externos ni requiere npm, sharp o servicios remotos.

```bash
python3 -m unittest discover -s tests -v
node --check assets/app.js
python3 scripts/build.py
python3 scripts/validate.py
```

`docs/` es un resultado generado e ignorado por Git. Para probar conservando el prefijo de producción, crea un enlace de desarrollo fuera del checkout:

```bash
mkdir -p /tmp/codigo-error-preview
ln -sfn /workspace/CODIGOERROR/docs /tmp/codigo-error-preview/CODIGOERROR
python3 -m http.server 8000 --bind 127.0.0.1 --directory /tmp/codigo-error-preview
```

Abre http://127.0.0.1:8000/CODIGOERROR/. No cambies `base_path` para una prueba local.

El control opcional de navegador usa Playwright y Chromium ya instalados en el entorno:

```bash
python3 scripts/browser_check.py
```

Comprueba búsqueda sin distinción de tildes, exportación del cuaderno, entradas tratadas como texto, eliminación de comprobaciones, diseño móvil, navegación sin JavaScript y un aviso de publicación retirada. No instala Playwright en producción.

## Fuentes y contenido

- `data/reviewed-guides.json`: única biblioteca de guías activas. La fecha `updated` cambia cuando cambia contenido editorial, nunca por compilar.
- `data/source-checks.json`: registro de URLs oficiales que respondieron HTTP 200 el 14 de octubre de 2026. Es una comprobación de accesibilidad, no una prueba física ni una garantía de validez futura.
- `data/retired-routes.json`: inventario de las 2.500 rutas de la edición anterior, sin su contenido de plantilla.
- `data/categories.json`: nombres de las categorías históricas; sus páginas siguen accesibles, pero no entran en el sitemap.
- `data/site.json`: identidad, URL y datos de configuración existentes del propietario.
- `assets/app.js`: búsqueda sobre enlaces visibles y cuaderno que mantiene notas en memoria y exporta texto local.

Para añadir una guía, documenta un problema concreto y conserva todos los campos del esquema. Incluye referencias primarias y registra su comprobación real. La validación rechaza pasos sin observación, decisión o reversión, rutas duplicadas y fuentes no primarias/no comprobadas. Nunca inventes resultados de pruebas, tiempos universales o datos de contacto.

## Rutas antiguas e indexación

Las guías activas, inicio, biblioteca y cuaderno forman **11 URLs indexables**. `sitemap.xml`, sitemap de texto y sitemaps secundarios contienen solo esas URLs. El buscador y la navegación editorial muestran únicamente las guías activas.

La ruta antigua `internet/wifi-conectado-sin-internet-windows-11/` conserva su dirección con la nueva guía sustancial. Las otras 2.499 rutas se sirven como avisos breves de retirada con `noindex,follow`, sin esquema Article, anuncios, analítica ni redirecciones a diagnósticos ajenos. GitHub Pages no permite declarar HTTP 410 por archivo: el aviso devuelve 200 y su exclusión depende de que el buscador vuelva a rastrearlo. No bloquees estas rutas en robots.txt mientras necesiten ver `noindex`.

Las páginas legales y categorías quedan accesibles con `noindex,follow`. Una categoría sin guía no simula contenido disponible. La página 404 también queda sin indexación ni anuncios.

## Publicidad, privacidad y contacto

Los identificadores públicos existentes de AdSense, Search Console y GA4 se mantienen en `site.json`; no se inventan nuevos. Las páginas indexables conservan el metadato de cuenta AdSense para verificar propiedad. `ads.txt` mantiene el editor configurado.

**Los anuncios, GA4 y CookieYes están pausados en el HTML de esta versión.** No se carga código externo ni se escriben cookies/almacenamiento persistente del proyecto. El cuaderno se pierde al cerrar o recargar salvo que descargues el informe; no envía sus datos. Las políticas describen ese comportamiento actual y distinguen el alojamiento de GitHub y los destinos externos.

No basta con cambiar un flag para activar anuncios. Antes de reactivarlos, revisa la configuración real del gestor de consentimiento, las regiones de destino y la política de privacidad. Conserva sin publicidad las páginas de error, retirada y utilidad administrativa. No se garantiza la aprobación de AdSense; su evaluación también incluye el sitio servido y la cuenta.

El canal existente de contacto es GitHub Issues del repositorio. Se explica que es público, requiere cuenta y no debe recibir datos personales. No se publica un correo privado que el propietario no haya confirmado.

## Despliegue

GitHub Actions valida en los pull requests y publica únicamente desde `main` o ejecución manual. Pages debe usar **GitHub Actions** como fuente. No se modifica la configuración remota ni se publica durante esta revisión.

La raíz de la cuenta (`IAFUTURE10/IAFUTURE10.github.io`) administra `https://iafuture10.github.io/ads.txt`, el sitemap raíz y la portada de la cuenta; este repositorio administra `/CODIGOERROR/`. Mantén los dos sitemaps coherentes. Este proyecto es independiente de las antiguas copias IA FUTURE de la cuenta SSJ-ARIEL.
