"""
Фикстуры pytest для тестирования сайта studia-54.com.

Константы → tests/config.py
Вспомогательные функции → tests/utils.py
"""

import pytest
import requests
from bs4 import BeautifulSoup

from tests.config import REQUEST_HEADERS
from tests.utils import get_soup  # re-export для обратной совместимости

# pylint: disable=redefined-outer-name



@pytest.fixture(scope="session")
def http_session() -> requests.Session:
    """Переиспользуемая HTTP-сессия на всю тестовую сессию."""
    session = requests.Session()
    session.headers.update(REQUEST_HEADERS)
    yield session
    session.close()


@pytest.fixture(scope="session")
def home_page(http_session: requests.Session) -> tuple[requests.Response, BeautifulSoup]:
    """Главная страница — кешированный (response, soup) на всю сессию."""
    return get_soup(http_session, "/")
