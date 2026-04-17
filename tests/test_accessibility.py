"""
Тесты доступности (accessibility): alt-тексты, aria-метки, формы, структура.
"""

import pytest
from tests.config import DETAIL_PAGES, GENERIC_ALT_TEXTS, FORM_PAGES
from tests.utils import get_soup

# Страницы с формами берутся из конфига (FORM_PAGES), используются параметрически


class TestAccessibility:
    """Проверка базовых требований веб-доступности (WCAG 2.1)."""

    @pytest.mark.parametrize("path", DETAIL_PAGES)
    def test_images_have_alt_attribute(self, http_session, path):
        """Все теги <img> должны иметь атрибут alt."""
        _, soup = get_soup(http_session, path)
        images = soup.find_all("img")
        missing_alt = [
            img.get("src", "no-src")
            for img in images
            if img.get("alt") is None
        ]
        assert not missing_alt, (
            f"[{path}] {len(missing_alt)} изображений без атрибута alt:\n"
            + "\n".join(f"  - {src}" for src in missing_alt[:10])
        )

    @pytest.mark.parametrize("path", DETAIL_PAGES)
    def test_images_alt_not_empty(self, http_session, path):
        """Alt-текст изображений не должен быть пустым (за исключением декоративных)."""
        _, soup = get_soup(http_session, path)
        images = soup.find_all("img")
        empty_alt = []
        for img in images:
            alt = img.get("alt", None)
            src = img.get("src", "")
            # Пропускаем декоративные изображения (alt="")
            if alt == "":
                continue
            # Alt существует, но содержит только пробелы
            if alt is not None and not alt.strip():
                empty_alt.append(src)
        assert not empty_alt, (
            f"[{path}] {len(empty_alt)} изображений с пустым alt (только пробелы):\n"
            + "\n".join(f"  - {src}" for src in empty_alt[:10])
        )

    @pytest.mark.parametrize("path", DETAIL_PAGES)
    def test_images_alt_not_generic(self, http_session, path):
        """Alt-тексты не должны быть бессмысленными ('img', 'image', 'photo', 'brand')."""
        _, soup = get_soup(http_session, path)
        images = soup.find_all("img")
        generic = [
            (img.get("src", ""), img.get("alt", ""))
            for img in images
            if img.get("alt", "").strip().lower() in GENERIC_ALT_TEXTS
        ]
        assert not generic, (
            f"[{path}] {len(generic)} изображений с недескриптивным alt:\n"
            + "\n".join(f"  - alt='{alt}' ({src})" for src, alt in generic[:10])
        )

    @pytest.mark.parametrize("path", FORM_PAGES)
    def test_form_inputs_have_labels_or_placeholder(self, http_session, path):
        """Поля форм должны иметь label или атрибут placeholder."""
        _, soup = get_soup(http_session, path)
        inputs = soup.find_all("input", type=lambda t: t not in ("hidden", "submit", "button"))
        unlabeled = []
        for inp in inputs:
            input_id = inp.get("id", "")
            has_label = bool(
                input_id and soup.find("label", attrs={"for": input_id})
            )
            has_placeholder = bool(inp.get("placeholder", "").strip())
            has_aria_label = bool(inp.get("aria-label", "").strip())
            if not (has_label or has_placeholder or has_aria_label):
                unlabeled.append(inp.get("name", inp.get("type", "unknown")))
        assert not unlabeled, (
            f"[{path}] Поля форм без label/placeholder/aria-label: {unlabeled}"
        )

    @pytest.mark.parametrize("path", DETAIL_PAGES)
    def test_links_have_text(self, http_session, path):
        """Ссылки не должны быть пустыми (без текста и без title/aria-label)."""
        _, soup = get_soup(http_session, path)
        links = soup.find_all("a")
        empty_links = []
        for link in links:
            text = link.get_text(strip=True)
            title = link.get("title", "").strip()
            aria_label = link.get("aria-label", "").strip()
            has_img = bool(link.find("img"))
            if not (text or title or aria_label or has_img):
                href = link.get("href", "")
                empty_links.append(href)
        assert not empty_links, (
            f"[{path}] {len(empty_links)} пустых ссылок (нет текста/title/aria-label):\n"
            + "\n".join(f"  - href='{h}'" for h in empty_links[:10])
        )

    def test_html_has_lang_attribute(self, http_session):
        """Атрибут lang на теге <html> обязателен для доступности."""
        _, soup = get_soup(http_session, "/")
        html = soup.find("html")
        lang = html.get("lang", "").strip() if html else ""
        assert lang, "Тег <html> не имеет атрибута lang"

    def test_page_has_main_landmark(self, http_session):
        """На странице должен быть элемент <main> или role='main'."""
        _, soup = get_soup(http_session, "/")
        main = soup.find("main") or soup.find(attrs={"role": "main"})
        assert main is not None, (
            "На странице отсутствует элемент <main> или role='main'"
        )

    @pytest.mark.parametrize("path", DETAIL_PAGES)
    def test_headings_hierarchy(self, http_session, path):
        """Иерархия заголовков не должна пропускать уровни (H1→H3 без H2)."""
        _, soup = get_soup(http_session, path)
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        levels = [int(h.name[1]) for h in headings]
        violations = []
        for i in range(1, len(levels)):
            if levels[i] - levels[i - 1] > 1:
                violations.append(
                    f"H{levels[i-1]} → H{levels[i]} (пропуск уровня)"
                )
        assert not violations, (
            f"[{path}] Нарушена иерархия заголовков:\n"
            + "\n".join(f"  - {v}" for v in violations[:5])
        )
