"""
Тесты битых ссылок: проверка всех внутренних ссылок на главной странице.
"""

import pytest
import requests
from tests.config import BASE_URL
from tests.utils import get_soup, collect_internal_links


class TestLinks:
    """Проверка внутренних ссылок сайта."""

    @pytest.fixture(scope="class")
    def internal_links(self, http_session):
        """Собрать все внутренние ссылки главной страницы."""
        _, soup = get_soup(http_session, "/")
        return collect_internal_links(soup, BASE_URL)

    def test_collected_links_not_empty(self, internal_links):
        """Должны быть найдены внутренние ссылки на главной странице."""
        assert len(internal_links) > 0, "Ни одной внутренней ссылки не найдено"

    def test_internal_links_not_broken(self, http_session, internal_links):
        """Все внутренние ссылки должны возвращать HTTP 200."""
        broken = []
        for url in internal_links:
            try:
                response = http_session.get(url, timeout=15, allow_redirects=True)
                if response.status_code not in (200, 301, 302):
                    broken.append((url, response.status_code))
            except requests.RequestException as exc:
                broken.append((url, str(exc)))

        assert not broken, (
            f"Найдено {len(broken)} битых ссылок:\n"
            + "\n".join(f"  - [{status}] {url}" for url, status in broken)
        )

    def test_no_hash_only_links(self, http_session):
        """Ссылки вида href='#' без якоря — потенциальные ошибки."""
        _, soup = get_soup(http_session, "/")
        hash_links = [
            a.get("href")
            for a in soup.find_all("a", href=True)
            if a["href"].strip() == "#"
        ]
        assert not hash_links, (
            f"Найдено {len(hash_links)} ссылок href='#' (пустые якоря)"
        )

    def test_no_javascript_void_links(self, http_session):
        """Ссылки href='javascript:void(0)' считаются признаком плохих практик."""
        _, soup = get_soup(http_session, "/")
        js_links = [
            a.get("href")
            for a in soup.find_all("a", href=True)
            if "javascript:void" in a["href"].lower()
        ]
        assert not js_links, (
            f"Найдено {len(js_links)} ссылок с javascript:void(0)"
        )

    def test_external_links_open_in_new_tab_have_rel_noopener(self, http_session):
        """
        Внешние ссылки с target='_blank' должны иметь rel='noopener noreferrer'
        (защита от tab-napping).
        """
        _, soup = get_soup(http_session, "/")
        violations = []
        for a in soup.find_all("a", href=True, target="_blank"):
            rel = a.get("rel", [])
            if isinstance(rel, str):
                rel = rel.split()
            if "noopener" not in rel:
                violations.append(a.get("href", ""))
        assert not violations, (
            f"{len(violations)} внешних ссылок target='_blank' без rel='noopener':\n"
            + "\n".join(f"  - {href}" for href in violations[:10])
        )
