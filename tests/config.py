"""
Константы и конфигурация для тестирования сайта studia-54.com.
Все настройки находятся в одном месте — изменяй здесь, не трогая тесты.
"""

# ── Основные параметры ──────────────────────────────────────────────────────

BASE_URL = "https://studia-54.com"

TARGET_PAGES = [
    "/",
    "/about",
    "/contacts",
    "/services",
    "/portfolio",
    "/blog",
    "/career",
    "/policy",
    "/agreement",
    "/sitemap",
    "/en",
]

# Страницы, которые проверяются детально (SEO, a11y, функционал)
DETAIL_PAGES = ["/", "/about", "/contacts", "/services", "/portfolio", "/blog"]

# Страницы с формами
FORM_PAGES = ["/", "/contacts", "/about"]

# ── HTTP-заголовки ───────────────────────────────────────────────────────────

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}

# ── Таймауты (секунды) ───────────────────────────────────────────────────────

DEFAULT_TIMEOUT = 15
SHORT_TIMEOUT = 10

# ── SEO-пороги ───────────────────────────────────────────────────────────────

SEO = {
    "title_min": 10,
    "title_max": 70,
    "description_min": 50,
    "description_max": 160,
}

# ── Пороги производительности (секунды) ─────────────────────────────────────

PERF = {
    "fast": 2.0,  # рекомендуемый максимум
    "slow": 5.0,  # критичный максимум
    "ttfb": 1.0,  # Time To First Byte
}

# ── Страницы с повышенными требованиями к кешу ───────────────────────────────

CACHE_CHECK_PAGES = ["/", "/about", "/services", "/portfolio"]

# ── Alt-тексты, которые считаются бессмысленными ────────────────────────────

GENERIC_ALT_TEXTS = {"img", "image", "photo", "pic", "icon", "logo", "brand", "poster"}

# ── Схемы ссылок, которые пропускаются при проверке ─────────────────────────

SKIP_LINK_SCHEMES = {"mailto", "tel", "javascript", "data"}
SKIP_LINK_PATTERNS = ["/icons/", ".svg", ".pdf", ".zip"]
