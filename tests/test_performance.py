"""
Тесты производительности: время ответа страниц.
"""

import time
import pytest
from tests.config import BASE_URL, TARGET_PAGES as PAGES, PERF, CACHE_CHECK_PAGES

FAST_THRESHOLD = PERF["fast"]
SLOW_THRESHOLD = PERF["slow"]


class TestPerformance:
    """Проверка времени ответа сервера."""

    @pytest.mark.parametrize("path", PAGES)
    def test_response_time_acceptable(self, http_session, path):
        """Время ответа не должно превышать 5 секунд."""
        url = BASE_URL + path
        start = time.perf_counter()
        http_session.get(url, timeout=15)
        elapsed = time.perf_counter() - start

        assert elapsed < SLOW_THRESHOLD, (
            f"[{path}] Критически медленный ответ: {elapsed:.2f}с "
            f"(порог: {SLOW_THRESHOLD}с)"
        )

    @pytest.mark.parametrize("path", PAGES)
    def test_response_time_fast(self, http_session, path):
        """Желательно, чтобы время ответа было менее 2 секунд."""
        url = BASE_URL + path
        start = time.perf_counter()
        http_session.get(url, timeout=15)
        elapsed = time.perf_counter() - start

        assert elapsed < FAST_THRESHOLD, (
            f"[{path}] Медленный ответ: {elapsed:.2f}с (рекомендуется < {FAST_THRESHOLD}с)"
        )

    def test_main_page_ttfb(self, http_session):
        """
        Время до первого байта (TTFB) главной страницы не должно превышать 1 секунду.
        Измеряется как время до получения первого чанка ответа.
        """
        url = BASE_URL + "/"
        start = time.perf_counter()
        response = http_session.get(url, timeout=15, stream=True)
        response.raw.read(1)
        ttfb = time.perf_counter() - start

        assert ttfb < 1.0, (
            f"TTFB главной страницы = {ttfb:.2f}с (рекомендуется < 1.0с)"
        )

    def test_content_encoding_gzip(self, http_session):
        """Ответ должен передаваться со сжатием (gzip/br/zstd)."""
        headers = {**http_session.headers, "Accept-Encoding": "gzip, deflate, br"}
        response = http_session.get(BASE_URL + "/", headers=headers, timeout=10)
        encoding = response.headers.get("Content-Encoding", "")
        assert encoding in ("gzip", "br", "zstd", "deflate"), (
            f"Сжатие ответа не используется. Content-Encoding: '{encoding}'"
        )

    @pytest.mark.parametrize("path", CACHE_CHECK_PAGES)
    def test_cache_control_header_present(self, http_session, path):
        """Заголовок Cache-Control должен быть выставлен для статических ресурсов."""
        response = http_session.get(BASE_URL + path, timeout=10)
        cache = response.headers.get("Cache-Control", "")
        assert cache, (
            f"[{path}] Отсутствует заголовок Cache-Control"
        )
