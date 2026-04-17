"""
Функциональные тесты: формы, контент, навигация, мобильная адаптация.
"""

import pytest
from tests.config import BASE_URL
from tests.utils import get_soup


class TestFunctional:
    """Проверка функциональности и корректности контента."""

    # ---- Формы ----------------------------------------------------------------

    def test_contact_form_has_name_field(self, http_session):
        """Форма обратной связи должна содержать поле имени."""
        _, soup = get_soup(http_session, "/contacts")
        inputs = soup.find_all("input")
        placeholders = [i.get("placeholder", "").lower() for i in inputs]
        has_name = any(
            kw in p for p in placeholders for kw in ("имя", "name", "ваше")
        )
        assert has_name, (
            "На странице /contacts не найдено поле имени в форме"
        )

    def test_contact_form_has_phone_field(self, http_session):
        """Форма обратной связи должна содержать поле телефона."""
        _, soup = get_soup(http_session, "/contacts")
        phone_inputs = soup.find_all("input", type="tel") + soup.find_all(
            "input",
            attrs={"placeholder": lambda p: p and ("тел" in p.lower() or "phone" in p.lower())},
        )
        assert phone_inputs, (
            "На странице /contacts не найдено поле телефона (type='tel')"
        )

    def test_form_has_submit_button(self, http_session):
        """Форма должна иметь кнопку отправки."""
        _, soup = get_soup(http_session, "/contacts")
        submit = (
            soup.find("button", type="submit")
            or soup.find("input", type="submit")
            or soup.find("button", string=lambda t: t and "отправ" in t.lower())
        )
        assert submit is not None, (
            "На странице /contacts не найдена кнопка отправки формы"
        )

    def test_form_has_privacy_policy_link(self, http_session):
        """Форма должна содержать ссылку на политику конфиденциальности."""
        _, soup = get_soup(http_session, "/contacts")
        policy_links = [
            a for a in soup.find_all("a", href=True)
            if "policy" in a["href"].lower() or "конфиденциальност" in a.get_text().lower()
        ]
        assert policy_links, (
            "На странице /contacts не найдена ссылка на политику конфиденциальности"
        )

    # ---- Контент --------------------------------------------------------------

    def test_main_page_has_portfolio_section(self, http_session):
        """Главная страница должна содержать секцию портфолио."""
        _, soup = get_soup(http_session, "/")
        text = soup.get_text(separator=" ").lower()
        assert "портфолио" in text, (
            "На главной странице не найдено слово 'портфолио'"
        )

    def test_about_page_mentions_team(self, http_session):
        """Страница «О нас» должна упоминать команду."""
        _, soup = get_soup(http_session, "/about")
        text = soup.get_text(separator=" ").lower()
        assert "команда" in text or "специалист" in text, (
            "На странице /about не упоминается команда/специалисты"
        )

    def test_contacts_page_has_phone_number(self, http_session):
        """На странице контактов должен быть номер телефона."""
        _, soup = get_soup(http_session, "/contacts")
        phone_links = soup.find_all("a", href=lambda h: h and h.startswith("tel:"))
        assert phone_links, (
            "На странице /contacts не найдены ссылки с номером телефона (href='tel:...')"
        )

    def test_contacts_page_has_email(self, http_session):
        """На странице контактов должен быть email."""
        _, soup = get_soup(http_session, "/contacts")
        email_links = soup.find_all("a", href=lambda h: h and h.startswith("mailto:"))
        assert email_links, (
            "На странице /contacts не найдены email-ссылки (href='mailto:...')"
        )

    # ---- Навигация ------------------------------------------------------------

    def test_header_has_navigation(self, http_session):
        """В шапке сайта должна быть навигация."""
        _, soup = get_soup(http_session, "/")
        nav = soup.find("nav") or soup.find(attrs={"role": "navigation"})
        assert nav is not None, (
            "На главной странице не найден элемент <nav>"
        )

    def test_footer_has_navigation_links(self, http_session):
        """Подвал сайта должен содержать навигационные ссылки."""
        _, soup = get_soup(http_session, "/")
        footer = soup.find("footer")
        if footer is None:
            pytest.skip("Тег <footer> не найден")
        links = footer.find_all("a", href=True)
        assert len(links) >= 5, (
            f"В footer найдено только {len(links)} ссылок (ожидается ≥ 5)"
        )

    def test_logo_links_to_homepage(self, http_session):
        """Логотип в шапке должен вести на главную страницу."""
        _, soup = get_soup(http_session, "/about")
        logo_links = soup.find_all(
            "a",
            href=lambda h: h in ("/", BASE_URL + "/", BASE_URL),
        )
        assert logo_links, (
            "Логотип не ссылается на главную страницу"
        )

    # ---- Безопасность (базовые заголовки) --------------------------------------

    def test_x_content_type_options_header(self, http_session):
        """Заголовок X-Content-Type-Options: nosniff должен быть выставлен."""
        response = http_session.get(BASE_URL + "/", timeout=10)
        header = response.headers.get("X-Content-Type-Options", "")
        assert "nosniff" in header.lower(), (
            f"Отсутствует или неверный X-Content-Type-Options: '{header}'"
        )

    def test_x_frame_options_header(self, http_session):
        """X-Frame-Options должен быть выставлен (защита от clickjacking)."""
        response = http_session.get(BASE_URL + "/", timeout=10)
        xfo = response.headers.get("X-Frame-Options", "")
        csp = response.headers.get("Content-Security-Policy", "")
        has_xfo = xfo.upper() in ("DENY", "SAMEORIGIN")
        has_csp_frame = "frame-ancestors" in csp.lower()
        assert has_xfo or has_csp_frame, (
            f"Отсутствует защита от clickjacking: "
            f"X-Frame-Options='{xfo}', CSP='{csp[:80]}'"
        )

    def test_strict_transport_security_header(self, http_session):
        """HSTS заголовок должен присутствовать (принудительный HTTPS)."""
        response = http_session.get(BASE_URL + "/", timeout=10)
        hsts = response.headers.get("Strict-Transport-Security", "")
        assert hsts, (
            "Отсутствует заголовок Strict-Transport-Security (HSTS)"
        )
