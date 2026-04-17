"""
SEO-тесты: title, meta description, H1, Open Graph, canonical, lang.
"""

import pytest
from tests.config import DETAIL_PAGES, SEO
from tests.utils import get_soup

MIN_TITLE_LENGTH = SEO["title_min"]
MAX_TITLE_LENGTH = SEO["title_max"]
MIN_DESCRIPTION_LENGTH = SEO["description_min"]
MAX_DESCRIPTION_LENGTH = SEO["description_max"]


class TestSEO:
    """Проверка SEO-оптимизации страниц."""

    @pytest.mark.parametrize("path", DETAIL_PAGES)
    def test_title_exists_and_not_empty(self, http_session, path):
        """Тег <title> должен присутствовать и не быть пустым."""
        _, soup = get_soup(http_session, path)
        title_tag = soup.find("title")
        assert title_tag is not None, f"[{path}] Отсутствует тег <title>"
        assert title_tag.get_text(strip=True), f"[{path}] Тег <title> пустой"

    @pytest.mark.parametrize("path", DETAIL_PAGES)
    def test_title_length(self, http_session, path):
        """Длина <title> должна быть в диапазоне 10–70 символов."""
        _, soup = get_soup(http_session, path)
        title_tag = soup.find("title")
        if title_tag is None:
            pytest.skip("Тег <title> отсутствует — проверяется отдельным тестом")
        text = title_tag.get_text(strip=True)
        length = len(text)
        assert MIN_TITLE_LENGTH <= length <= MAX_TITLE_LENGTH, (
            f"[{path}] Длина title = {length} символов "
            f"(норма: {MIN_TITLE_LENGTH}–{MAX_TITLE_LENGTH}): «{text}»"
        )

    @pytest.mark.parametrize("path", DETAIL_PAGES)
    def test_meta_description_exists(self, http_session, path):
        """Meta description должен присутствовать."""
        _, soup = get_soup(http_session, path)
        desc = soup.find("meta", attrs={"name": "description"})
        assert desc is not None, f"[{path}] Отсутствует <meta name='description'>"
        content = desc.get("content", "").strip()
        assert content, f"[{path}] Meta description пустой"

    @pytest.mark.parametrize("path", DETAIL_PAGES)
    def test_meta_description_length(self, http_session, path):
        """Длина meta description должна быть 50–160 символов."""
        _, soup = get_soup(http_session, path)
        desc = soup.find("meta", attrs={"name": "description"})
        if not desc:
            pytest.skip("Meta description отсутствует — проверяется отдельным тестом")
        content = desc.get("content", "").strip()
        length = len(content)
        assert MIN_DESCRIPTION_LENGTH <= length <= MAX_DESCRIPTION_LENGTH, (
            f"[{path}] Длина meta description = {length} символов "
            f"(норма: {MIN_DESCRIPTION_LENGTH}–{MAX_DESCRIPTION_LENGTH})"
        )

    @pytest.mark.parametrize("path", DETAIL_PAGES)
    def test_single_h1_tag(self, http_session, path):
        """На каждой странице должен быть ровно один тег H1."""
        _, soup = get_soup(http_session, path)
        h1_tags = soup.find_all("h1")
        assert len(h1_tags) == 1, (
            f"[{path}] Найдено {len(h1_tags)} тегов H1 (норма: 1)"
        )

    @pytest.mark.parametrize("path", DETAIL_PAGES)
    def test_h1_not_empty(self, http_session, path):
        """H1 не должен быть пустым."""
        _, soup = get_soup(http_session, path)
        h1_tags = soup.find_all("h1")
        for h1 in h1_tags:
            text = h1.get_text(strip=True)
            assert text, f"[{path}] Тег H1 пустой или содержит только пробелы"

    @pytest.mark.parametrize("path", DETAIL_PAGES)
    def test_og_title_exists(self, http_session, path):
        """Open Graph: og:title должен присутствовать."""
        _, soup = get_soup(http_session, path)
        og_title = soup.find("meta", property="og:title")
        assert og_title is not None, f"[{path}] Отсутствует <meta property='og:title'>"
        assert og_title.get("content", "").strip(), (
            f"[{path}] og:title пустой"
        )

    @pytest.mark.parametrize("path", DETAIL_PAGES)
    def test_og_description_exists(self, http_session, path):
        """Open Graph: og:description должен присутствовать."""
        _, soup = get_soup(http_session, path)
        og_desc = soup.find("meta", property="og:description")
        assert og_desc is not None, (
            f"[{path}] Отсутствует <meta property='og:description'>"
        )
        assert og_desc.get("content", "").strip(), (
            f"[{path}] og:description пустой"
        )

    @pytest.mark.parametrize("path", DETAIL_PAGES)
    def test_og_image_exists(self, http_session, path):
        """Open Graph: og:image должен присутствовать."""
        _, soup = get_soup(http_session, path)
        og_image = soup.find("meta", property="og:image")
        assert og_image is not None, (
            f"[{path}] Отсутствует <meta property='og:image'>"
        )
        assert og_image.get("content", "").strip(), (
            f"[{path}] og:image пустой"
        )

    @pytest.mark.parametrize("path", DETAIL_PAGES)
    def test_canonical_link_exists(self, http_session, path):
        """Canonical-ссылка должна присутствовать и не быть пустой."""
        _, soup = get_soup(http_session, path)
        canonical = soup.find("link", rel=lambda v: v and "canonical" in v)
        assert canonical is not None, f"[{path}] Отсутствует <link rel='canonical'>"
        assert canonical.get("href", "").strip(), (
            f"[{path}] Canonical href пустой"
        )

    def test_html_lang_attribute(self, http_session):
        """Тег <html> должен иметь атрибут lang."""
        _, soup = get_soup(http_session, "/")
        html_tag = soup.find("html")
        lang = html_tag.get("lang", "") if html_tag else ""
        assert lang.strip(), "Тег <html> не имеет атрибута lang"

    def test_viewport_meta_tag(self, http_session):
        """Meta viewport должен быть задан (важно для мобильных устройств)."""
        _, soup = get_soup(http_session, "/")
        viewport = soup.find("meta", attrs={"name": "viewport"})
        assert viewport is not None, "Отсутствует <meta name='viewport'>"
        content = viewport.get("content", "")
        assert "width=device-width" in content, (
            f"Meta viewport не содержит 'width=device-width': {content}"
        )

    @pytest.mark.parametrize("path", DETAIL_PAGES)
    def test_no_duplicate_meta_description(self, http_session, path):
        """Meta description не должен дублироваться."""
        _, soup = get_soup(http_session, path)
        descs = soup.find_all("meta", attrs={"name": "description"})
        assert len(descs) <= 1, (
            f"[{path}] Найдено {len(descs)} тегов meta description (допустимо: 1)"
        )
