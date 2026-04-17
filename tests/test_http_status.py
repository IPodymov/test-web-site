"""
Тесты HTTP-статусов: доступность страниц, редиректы, 404.
"""

import pytest
import requests
from tests.config import BASE_URL, TARGET_PAGES as PAGES, REQUEST_HEADERS as HEADERS


class TestHttpStatus:
    """Проверка HTTP-статусов основных страниц."""

    @pytest.mark.parametrize("path", PAGES)
    def test_page_returns_200(self, http_session, path):
        """Каждая страница должна возвращать HTTP 200."""
        url = BASE_URL + path
        response = http_session.get(url, timeout=15)
        assert response.status_code == 200, (
            f"Страница {url} вернула {response.status_code} вместо 200"
        )

    def test_robots_txt_accessible(self, http_session):
        """robots.txt должен быть доступен."""
        url = BASE_URL + "/robots.txt"
        response = http_session.get(url, timeout=10)
        assert response.status_code == 200, (
            f"robots.txt недоступен: статус {response.status_code}"
        )

    def test_sitemap_xml_accessible(self, http_session):
        """sitemap.xml должен быть доступен."""
        url = BASE_URL + "/sitemap.xml"
        response = http_session.get(url, timeout=10)
        assert response.status_code == 200, (
            f"sitemap.xml недоступен: статус {response.status_code}"
        )

    def test_404_page_exists(self, http_session):
        """Несуществующий URL должен возвращать 404."""
        url = BASE_URL + "/this-page-does-not-exist-xyz-12345"
        response = http_session.get(url, timeout=10)
        assert response.status_code == 404, (
            f"Ожидался 404, но получен {response.status_code}"
        )

    def test_http_redirects_to_https(self):
        """HTTP должен редиректить на HTTPS."""
        http_url = "http://studia-54.com/"
        response = requests.get(http_url, timeout=10, headers=HEADERS, allow_redirects=True)
        assert response.url.startswith("https://"), (
            f"HTTP не перенаправляет на HTTPS. Финальный URL: {response.url}"
        )

    def test_www_redirects_correctly(self, http_session):
        """www-версия должна редиректить на основной домен."""
        url = "https://www.studia-54.com/"
        response = http_session.get(url, timeout=10, allow_redirects=True)
        assert response.status_code == 200, (
            f"www-версия сайта недоступна: статус {response.status_code}"
        )
