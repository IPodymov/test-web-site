"""
Вспомогательные функции для тестов.
Все функции — чистые (pure functions), без побочных эффектов.
"""

from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from tests.config import (
    BASE_URL,
    DEFAULT_TIMEOUT,
    SKIP_LINK_SCHEMES,
    SKIP_LINK_PATTERNS,
)


def get_soup(
    session: requests.Session, path: str
) -> tuple[requests.Response, BeautifulSoup]:
    """
    Загрузить страницу и вернуть (response, soup).

    Принудительно задаёт UTF-8 — сайт отдаёт кириллицу в UTF-8,
    но requests иногда определяет кодировку как ISO-8859-1.
    """
    url = BASE_URL + path if path.startswith("/") else path
    response = session.get(url, timeout=DEFAULT_TIMEOUT)
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "lxml")
    return response, soup


def fetch_raw(session: requests.Session, path: str, **kwargs) -> requests.Response:
    """Выполнить GET-запрос с принудительной кодировкой UTF-8."""
    url = BASE_URL + path if path.startswith("/") else path
    response = session.get(url, **kwargs)
    response.encoding = "utf-8"
    return response


def is_link_excluded(href: str) -> bool:
    """
    Вернуть True, если ссылку следует пропустить при проверке.
    Пропускаются: mailto:, tel:, javascript:, data:, SVG/PDF/архивы.
    """
    if not href:
        return True
    scheme = urlparse(href).scheme
    if scheme in SKIP_LINK_SCHEMES:
        return True
    return any(pattern in href for pattern in SKIP_LINK_PATTERNS)


def collect_internal_links(soup: BeautifulSoup, base_url: str = BASE_URL) -> list[str]:
    """
    Извлечь все уникальные внутренние ссылки со страницы.

    Нормализует URL: убирает якоря и query-параметры,
    чтобы /about и /about#team считались одной ссылкой.
    Возвращает отсортированный список для детерминированного порядка тестов.
    """
    links: set[str] = set()
    base_netloc = urlparse(base_url).netloc

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        if is_link_excluded(href):
            continue
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        if parsed.netloc == base_netloc:
            clean = parsed._replace(fragment="", query="").geturl()
            links.add(clean)

    return sorted(links)
