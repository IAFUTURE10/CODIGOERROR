from __future__ import annotations

import re
import unicodedata
from copy import deepcopy


DEFAULT_CONTEXTS = [
    "Windows 11",
    "Windows 10",
    "después de actualizar",
    "en una laptop",
    "en PC de escritorio",
    "al iniciar sesión",
    "al abrir un programa",
    "después de instalar drivers",
    "con conexión WiFi",
    "en equipos con SSD",
    "tras reiniciar",
    "sin perder archivos",
    "en modo seguro",
    "con cuenta de usuario nueva",
]


BLUEPRINTS = {
    "windows": {
        "area": "servicios de Windows, archivos del sistema y configuración",
        "topics": [
            "Windows Update se queda buscando actualizaciones",
            "la barra de tareas no responde",
            "el menú inicio no abre",
            "Microsoft Store no descarga aplicaciones",
            "Windows se queda en preparando reparación automática",
            "el explorador de archivos se reinicia",
            "la pantalla azul aparece al iniciar",
            "Windows Defender no activa la protección",
            "el sistema entra con perfil temporal",
            "el instalador MSI muestra error",
            "la activación de Windows falla",
            "la búsqueda de Windows no encuentra archivos",
            "el portapapeles no funciona",
            "el modo seguro no arranca",
            "las actualizaciones se revierten",
            "el inicio tarda demasiado",
        ],
    },
    "pc-laptops": {
        "area": "energía, pantalla, memoria, almacenamiento y placa",
        "topics": [
            "laptop enciende pero no muestra imagen",
            "PC prende y se apaga al instante",
            "laptop no carga la batería",
            "el ventilador suena fuerte sin abrir programas",
            "BIOS no detecta el disco",
            "PC se congela sin pantalla azul",
            "laptop se apaga al conectar el cargador",
            "teclado integrado deja de responder",
            "touchpad no funciona",
            "la pantalla parpadea al mover la tapa",
            "la RAM no aparece completa",
            "el equipo no despierta de suspensión",
            "USB-C no carga la laptop",
            "la laptop se calienta demasiado",
            "la cámara integrada no aparece",
            "el arranque queda en logo del fabricante",
        ],
    },
    "gaming": {
        "area": "lanzadores, DirectX, librerías, drivers gráficos y permisos",
        "topics": [
            "Steam no abre",
            "Epic Games se queda cargando",
            "un juego se cierra al iniciar",
            "DirectX muestra error al abrir un juego",
            "falta un archivo DLL al ejecutar el juego",
            "el juego abre en pantalla negra",
            "el mando no funciona en PC",
            "el anticheat impide iniciar",
            "el juego no usa la GPU dedicada",
            "los FPS bajan después de actualizar",
            "la instalación queda pausada",
            "el overlay causa cierre inesperado",
            "el guardado en la nube no sincroniza",
            "el audio del juego se corta",
            "el launcher pide reparar archivos",
            "el juego muestra error de memoria",
        ],
    },
    "android": {
        "area": "red, permisos, servicios de Google, almacenamiento y apps",
        "topics": [
            "Android se conecta al WiFi pero no navega",
            "Google Play queda en descarga pendiente",
            "una app se cierra sola",
            "el teléfono no recibe notificaciones",
            "Bluetooth no encuentra dispositivos",
            "Android no reconoce la tarjeta SD",
            "la cámara muestra error",
            "el almacenamiento aparece lleno",
            "los servicios de Google fallan",
            "la pantalla táctil responde lento",
            "el móvil se reinicia solo",
            "la batería baja demasiado rápido",
            "la copia de seguridad no avanza",
            "el hotspot no comparte Internet",
            "las apps no se actualizan",
            "Android no descarga archivos",
        ],
    },
    "internet": {
        "area": "DNS, IP, router, adaptadores de red y proveedor",
        "topics": [
            "WiFi conectado sin Internet",
            "DNS no responde",
            "la conexión se corta cada pocos minutos",
            "el router no entrega IP",
            "Internet funciona por cable pero no por WiFi",
            "la velocidad baja de repente",
            "la red aparece como no identificada",
            "VPN bloquea la navegación",
            "la puerta de enlace no responde",
            "el ping sube demasiado",
            "las páginas cargan lento",
            "el adaptador WiFi desaparece",
            "la red 5 GHz no aparece",
            "el proxy impide conectarse",
            "el router reinicia la conexión",
            "el equipo pierde Internet al suspender",
        ],
    },
    "navegadores": {
        "area": "caché, DNS, certificados, extensiones y perfil del navegador",
        "topics": [
            "ERR_CONNECTION_RESET aparece en Chrome",
            "DNS_PROBE_FINISHED_NXDOMAIN bloquea una web",
            "Chrome no carga páginas",
            "Edge se cierra al abrir",
            "Firefox muestra error de certificado",
            "las extensiones bloquean sitios",
            "el perfil del navegador se corrompe",
            "las descargas quedan bloqueadas",
            "el navegador consume mucha memoria",
            "YouTube no reproduce videos",
            "el modo incógnito sí funciona",
            "las cookies no se guardan",
            "el certificado no es válido",
            "el navegador abre páginas solo",
            "la sincronización no inicia sesión",
            "el autocompletado no funciona",
        ],
    },
    "almacenamiento": {
        "area": "discos, SSD, particiones, SMART, caché y espacio libre",
        "topics": [
            "disco al 100% en Windows",
            "SSD no aparece en BIOS",
            "USB pide formatear antes de usar",
            "Windows no asigna letra al disco",
            "la partición aparece como RAW",
            "el disco muestra alerta SMART",
            "el explorador tarda en abrir carpetas",
            "no se puede expulsar una unidad",
            "el disco externo se desconecta",
            "la copia de archivos se queda en 0%",
            "la unidad aparece protegida contra escritura",
            "el SSD baja mucho su velocidad",
            "Administración de discos no inicializa",
            "la papelera no se vacía",
            "el almacenamiento se llena solo",
            "Windows no detecta un NVMe",
        ],
    },
    "graficos": {
        "area": "GPU, monitor, cable, controlador y aceleración gráfica",
        "topics": [
            "driver NVIDIA no instala",
            "driver AMD falla al actualizar",
            "pantalla negra después de instalar driver",
            "Windows usa adaptador de pantalla básico",
            "el monitor no detecta señal",
            "la resolución correcta no aparece",
            "la pantalla parpadea",
            "el juego no usa la GPU dedicada",
            "el panel de control NVIDIA no abre",
            "la GPU se calienta demasiado",
            "aparecen artefactos en pantalla",
            "HDMI no da imagen",
            "DisplayPort pierde señal",
            "la aceleración de hardware causa cierres",
            "la segunda pantalla no aparece",
            "el brillo no cambia",
        ],
    },
    "audio": {
        "area": "salida de audio, micrófono, servicios, Bluetooth y drivers",
        "topics": [
            "no hay sonido en Windows",
            "micrófono no funciona",
            "audio Bluetooth se corta",
            "Realtek no aparece",
            "Windows cambia la salida de audio",
            "el volumen se baja solo",
            "una app no tiene sonido",
            "el audio por HDMI no funciona",
            "los auriculares no se detectan",
            "el micrófono suena bajo",
            "Discord no detecta el micrófono",
            "el sonido sale con eco",
            "el servicio de audio no responde",
            "el panel de sonido no abre",
            "el audio se retrasa",
            "el dispositivo de salida desaparece",
        ],
    },
    "drivers": {
        "area": "controladores, administrador de dispositivos y compatibilidad",
        "topics": [
            "dispositivo USB no reconocido",
            "código 43 en Administrador de dispositivos",
            "código 10 no puede iniciar",
            "driver desconocido aparece con advertencia",
            "Windows instala un driver incorrecto",
            "Bluetooth no aparece en dispositivos",
            "adaptador WiFi desaparece",
            "driver de chipset falta",
            "impresora no instala controlador",
            "driver de audio se reinstala solo",
            "controlador gráfico se revierte",
            "touchpad pierde el driver",
            "cámara muestra dispositivo desconocido",
            "driver firmado no se instala",
            "Windows Update rompe un driver",
            "el controlador queda en bucle de instalación",
        ],
    },
    "perifericos": {
        "area": "USB, Bluetooth, energía, permisos y controladores externos",
        "topics": [
            "teclado no funciona",
            "mouse se desconecta",
            "impresora aparece sin conexión",
            "cámara web no se detecta",
            "escáner no responde",
            "monitor externo no aparece",
            "mando Bluetooth no empareja",
            "auriculares USB no suenan",
            "webcam muestra pantalla negra",
            "impresora no imprime aunque tiene tinta",
            "teclado escribe símbolos incorrectos",
            "mouse tiene doble clic",
            "lector de tarjetas no lee SD",
            "hub USB pierde conexión",
            "tableta gráfica no responde",
            "micrófono externo no aparece",
        ],
    },
    "programas": {
        "area": "permisos, perfiles, complementos, dependencias e instalación",
        "topics": [
            "Office no abre y queda cargando",
            "un programa no abre en Windows",
            "la instalación se queda congelada",
            "la app muestra error de permisos",
            "el programa se cierra sin mensaje",
            "la aplicación pide .NET Framework",
            "el software no detecta Internet",
            "el programa queda en segundo plano",
            "la app no guarda configuración",
            "el desinstalador no funciona",
            "el instalador dice acceso denegado",
            "la licencia no se activa",
            "la actualización del programa falla",
            "el perfil de usuario rompe la app",
            "la app abre en blanco",
            "el programa consume mucha CPU",
        ],
    },
    "codigos-error": {
        "area": "origen del código, servicio afectado, dependencia y contexto",
        "topics": [
            "error 0x80070002",
            "error 0xc000007b",
            "error 0x800f081f",
            "error 0x80070422",
            "error 0x8024402c",
            "error 0x80070005",
            "error 0x80073712",
            "error 0x803f8001",
            "error 0x0000007e",
            "error 0x00000116",
            "código 43",
            "código 10",
            "error DNS_PROBE_FINISHED_NXDOMAIN",
            "error ERR_CONNECTION_RESET",
            "error DXGI_DEVICE_REMOVED",
            "error Play Store descarga pendiente",
        ],
    },
}


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value.lower()).strip("-")
    return re.sub(r"-+", "-", slug)[:92].strip("-")


def category_contexts(slug: str) -> list[str]:
    shared = DEFAULT_CONTEXTS
    by_category = {
        "windows": ["Windows 11 24H2", "Windows 10 22H2", "después de Windows Update", "en instalación limpia"],
        "pc-laptops": ["laptop Dell", "laptop HP", "laptop Lenovo", "PC gamer", "equipo antiguo"],
        "gaming": ["Windows 11", "Steam", "Epic Games", "laptop gamer", "PC con GPU dedicada"],
        "android": ["Android 14", "Samsung Galaxy", "Xiaomi", "Motorola", "después de actualizar Android"],
        "internet": ["Windows 11", "router doméstico", "red WiFi 5 GHz", "VPN activa", "laptop conectada por WiFi"],
        "navegadores": ["Chrome", "Microsoft Edge", "Firefox", "perfil nuevo", "modo incógnito"],
        "almacenamiento": ["Windows 11", "SSD NVMe", "disco externo USB", "laptop", "PC de escritorio"],
        "graficos": ["NVIDIA", "AMD Radeon", "Intel Graphics", "monitor externo", "laptop con GPU híbrida"],
        "audio": ["Windows 11", "Realtek", "auriculares Bluetooth", "micrófono USB", "HDMI"],
        "drivers": ["Windows 11", "después de actualizar", "Administrador de dispositivos", "laptop", "PC recién formateada"],
        "perifericos": ["Windows 11", "USB 3.0", "Bluetooth", "laptop", "PC de escritorio"],
        "programas": ["Windows 11", "cuenta estándar", "después de actualizar", "perfil nuevo", "instalación limpia"],
        "codigos-error": ["Windows 11", "Windows Update", "al instalar un programa", "al abrir un juego", "después de actualizar"],
    }
    return by_category.get(slug, []) + shared


def make_article(category: dict, topic: str, context: str, index: int, date_value: str) -> dict:
    slug_base = slugify(f"{topic} {context}")
    issue = topic[0].lower() + topic[1:] if topic else topic
    area = BLUEPRINTS[category["slug"]]["area"]
    title = f"{topic} en {context}: causas y solución"
    if len(title) > 78:
        title = f"{topic}: solución en {context}"
    meta = (
        f"Soluciona {issue} en {context}. Revisa {area}, señales del fallo, "
        "comprobaciones rápidas y pasos seguros antes de reinstalar."
    )
    h1 = f"{topic} en {context}: diagnóstico paso a paso"
    return {
        "slug": f"{slug_base}-{index:04d}",
        "category": category["slug"],
        "title": title,
        "meta_description": meta,
        "h1": h1,
        "summary": (
            f"Guía para diagnosticar {issue} en {context}, separando configuración, "
            f"{area} y señales que indican cuándo conviene escalar la reparación."
        ),
        "date_published": date_value,
        "date_modified": date_value,
        "keywords": [
            f"{issue} {context}",
            f"solución {issue}",
            f"{category['name']} {context}",
            f"diagnóstico {issue}",
        ],
        "symptoms": [
            f"El problema aparece como {issue} en {context}.",
            "El fallo se repite después de reiniciar o volver a intentar la acción.",
            f"Otras funciones relacionadas con {category['name']} pueden seguir funcionando.",
        ],
        "quick_checks": [
            "Anota el mensaje exacto y cuándo empezó el fallo.",
            "Prueba una acción simple para separar fallo temporal de fallo persistente.",
            "Evita reinstalar o formatear antes de revisar los puntos de diagnóstico.",
        ],
        "sections": [
            {
                "h2": f"Por qué ocurre {issue}",
                "paragraphs": [
                    (
                        f"En {context}, este fallo suele aparecer cuando uno de los componentes de "
                        f"{area} queda bloqueado, desactualizado o con una configuración que no coincide con el uso real."
                    ),
                    (
                        "La clave es confirmar si el error depende del dispositivo, del usuario, de una actualización reciente "
                        "o de una dependencia que otros programas también usan."
                    ),
                ],
            },
            {
                "h2": "Comprobaciones rápidas antes de aplicar cambios",
                "h3": "Aísla el origen antes de tocar configuración avanzada",
                "steps": [
                    "Reinicia el equipo o dispositivo y prueba de nuevo una sola vez.",
                    "Comprueba si el fallo ocurre con otra cuenta, red, cable, puerto o programa equivalente.",
                    "Revisa actualizaciones recientes, drivers instalados y cambios de configuración.",
                    "Guarda una captura del mensaje o código para comparar si cambia durante el diagnóstico.",
                ],
            },
            {
                "h2": "Solución recomendada en orden seguro",
                "h3": "Avanza de menor a mayor riesgo",
                "steps": [
                    f"Repara primero los ajustes relacionados con {area}.",
                    "Limpia caché o reinicia servicios solo si el síntoma apunta a datos temporales dañados.",
                    "Actualiza o revierte drivers y dependencias si el problema empezó después de un cambio.",
                    "Usa restauración, reparación o reinstalación solo cuando las pruebas previas confirmen daño persistente.",
                ],
            },
            {
                "h2": "Cuándo pedir soporte técnico",
                "paragraphs": [
                    (
                        "Si el error aparece junto con apagados, pérdida de datos, ruidos físicos, reinicios constantes "
                        "o fallos en varias áreas, conviene detener cambios agresivos y priorizar respaldo o diagnóstico profesional."
                    )
                ],
            },
        ],
        "faq": [
            {
                "q": f"¿{topic} significa que debo reinstalar?",
                "a": "No como primer paso. Reinstalar solo tiene sentido después de confirmar que ajustes, caché, servicios, drivers o dependencias no corrigen el origen.",
            },
            {
                "q": f"¿Puedo aplicar esta solución en {context} sin perder archivos?",
                "a": "Las comprobaciones iniciales no borran archivos. Aun así, si hay señales de disco dañado o pérdida de datos, haz respaldo antes de continuar.",
            },
        ],
        "caption": f"Diagnóstico visual para {issue} en {context}, con ruta de causa, comprobación y solución.",
        "generated": True,
    }


def expand_articles(seed_articles: list[dict], categories: list[dict], target: int, date_value: str) -> list[dict]:
    if target <= len(seed_articles):
        return deepcopy(seed_articles[:target])

    expanded = deepcopy(seed_articles)
    seen_routes = {f"{article['category']}/{article['slug']}" for article in expanded}
    seen_titles = {article["title"] for article in expanded}
    category_count = len(categories)
    base_quota = target // category_count
    remainder = target % category_count

    for category_index, category in enumerate(categories):
        desired = base_quota + (1 if category_index < remainder else 0)
        current = sum(1 for article in expanded if article["category"] == category["slug"])
        need = max(0, desired - current)
        topics = BLUEPRINTS[category["slug"]]["topics"]
        contexts = category_contexts(category["slug"])
        generated_for_category = 0
        serial = 1
        while generated_for_category < need:
            topic = topics[(serial - 1) % len(topics)]
            context = contexts[((serial - 1) // len(topics)) % len(contexts)]
            article = make_article(category, topic, context, serial, date_value)
            route = f"{article['category']}/{article['slug']}"
            if route not in seen_routes and article["title"] not in seen_titles:
                expanded.append(article)
                seen_routes.add(route)
                seen_titles.add(article["title"])
                generated_for_category += 1
            serial += 1

    serial = 1
    while len(expanded) < target:
        category = categories[serial % category_count]
        topic = BLUEPRINTS[category["slug"]]["topics"][serial % len(BLUEPRINTS[category["slug"]]["topics"])]
        context = f"caso avanzado {serial}"
        article = make_article(category, topic, context, serial + 9000, date_value)
        route = f"{article['category']}/{article['slug']}"
        if route not in seen_routes and article["title"] not in seen_titles:
            expanded.append(article)
            seen_routes.add(route)
            seen_titles.add(article["title"])
        serial += 1

    return expanded[:target]
