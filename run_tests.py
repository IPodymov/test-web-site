"""
Главный запускатор тестов с генерацией Markdown и PDF-отчётов.

Использование:
    python run_tests.py
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
import markdown
from jinja2 import Template

# pylint: disable=redefined-outer-name,too-many-locals,broad-exception-caught,import-outside-toplevel

BASE_DIR = Path(__file__).parent
TESTS_DIR = BASE_DIR / "tests"
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

JSON_REPORT = REPORTS_DIR / "results.json"
TARGET_URL = "https://studia-54.com"

CATEGORY_MAP = {
    "test_http_status": ("HTTP-статусы", "critical", "🔴"),
    "test_seo": ("SEO-оптимизация", "high", "🟠"),
    "test_performance": ("Производительность", "high", "🟠"),
    "test_accessibility": ("Доступность (a11y)", "medium", "🟡"),
    "test_links": ("Ссылки", "critical", "🔴"),
    "test_functional": ("Функциональность", "medium", "🟡"),
}

PRIORITY_ORDER = ["critical", "high", "medium", "low"]
PRIORITY_LABELS = {
    "critical": "Критический",
    "high": "Высокий",
    "medium": "Средний",
    "low": "Низкий",
}


def run_tests() -> dict:
    """Запустить pytest и вернуть результаты в виде словаря."""
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(TESTS_DIR),
        "--tb=short",
        "--no-header",
        "-q",
        "--json-report",
        f"--json-report-file={JSON_REPORT}",
        "--json-report-indent=2",
    ]

    print(f"{'='*60}")
    print(f"  Тестирование сайта: {TARGET_URL}")
    print(f"  Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*60}\n")

    start = time.perf_counter()
    subprocess.run(cmd, capture_output=False, cwd=BASE_DIR, check=False)
    elapsed = round(time.perf_counter() - start, 1)

    if not JSON_REPORT.exists():
        print("\n[ERROR] JSON-отчёт pytest не создан. Используем упрощённую генерацию.")
        return {"summary": {}, "tests": [], "duration": elapsed}

    with open(JSON_REPORT, encoding="utf-8") as f:
        data = json.load(f)

    data["duration"] = elapsed
    return data


def build_markdown_report(data: dict) -> None:
    """Сгенерировать финальный отчёт REPORT.md."""
    all_tests = data.get("tests", [])
    passed = [t for t in all_tests if t.get("outcome") == "passed"]
    failed = [t for t in all_tests if t.get("outcome") in ("failed", "error")]
    skipped = [t for t in all_tests if t.get("outcome") == "skipped"]

    total = len(all_tests)
    n_passed = len(passed)
    n_failed = len(failed)
    n_skipped = len(skipped)
    duration = data.get("duration", 0)

    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    score = round((n_passed / total) * 100, 1) if total else 0.0

    lines = [
        "# Отчёт о тестировании сайта Studia 54",
        "",
        f"> **URL:** {TARGET_URL}  ",
        f"> **Дата проверки:** {now}  ",
        f"> **Общее время выполнения:** {duration} сек  ",
        "",
        "---",
        "",
        "## Сводка результатов",
        "",
        "| Метрика | Значение |",
        "|---------|----------|",
        f"| Всего тестов | {total} |",
        f"| ✅ Прошли | {n_passed} |",
        f"| ❌ Упали | {n_failed} |",
        f"| ⚠️ Пропущены | {n_skipped} |",
        f"| 🏆 Оценка качества | **{score}%** |",
        "",
        "---",
        "",
    ]
    report_path = REPORTS_DIR / "REPORT.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n📄 Отчёт MD сохранён: {report_path}")


def build_context(data: dict) -> dict:
    """Подготовка контекста из pytest-json-report для рендеринга HTML/PDF."""
    all_tests = data.get("tests", [])
    passed = [t for t in all_tests if t.get("outcome") == "passed"]
    failed = [t for t in all_tests if t.get("outcome") in ("failed", "error")]
    skipped = [t for t in all_tests if t.get("outcome") == "skipped"]

    total = len(all_tests)
    n_passed = len(passed)
    n_failed = len(failed)
    n_skipped = len(skipped)
    score = round(n_passed / total * 100, 1) if total else 0.0
    duration = data.get("duration", "—")

    cat_stats = {}
    for key, (name, _, _) in CATEGORY_MAP.items():
        matching = [t for t in all_tests if key in t.get("nodeid", "")]
        p = len([t for t in matching if t.get("outcome") == "passed"])
        f = len([t for t in matching if t.get("outcome") in ("failed", "error")])
        total_c = p + f
        pct = round(p / total_c * 100) if total_c else 100
        cat_stats[key] = {"name": name, "passed": p, "failed": f, "pct": pct}

    grouped = {p: [] for p in PRIORITY_ORDER}
    for t in failed:
        nodeid = t.get("nodeid", "")
        call = t.get("call", {}) or {}
        crash = call.get("crash", {}) or {}
        message = crash.get("message", "нет сообщения").strip()

        priority = "low"
        for key, (_, p_level, _) in CATEGORY_MAP.items():
            if key in nodeid:
                priority = p_level
                break

        parts = nodeid.split("::")
        title = (
            parts[-1].replace("test_", "").replace("_", " ").strip().capitalize()
            if parts
            else nodeid
        )

        grouped[priority].append(
            {
                "nodeid": nodeid,
                "title": title,
                "message": message[:800],
                "priority_label": PRIORITY_LABELS.get(priority, priority),
            }
        )

    priority_groups = [
        {"label": PRIORITY_LABELS.get(p, p), "bugs": grouped[p]} for p in PRIORITY_ORDER
    ]

    answers_html = ""
    answers_path = BASE_DIR / "ANSWERS.md"
    if answers_path.exists():
        with open(answers_path, "r", encoding="utf-8") as f:
            answers_html = markdown.markdown(
                f.read(), extensions=["tables", "fenced_code"]
            )

    return {
        "target_url": TARGET_URL,
        "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "duration": duration,
        "score": score,
        "total": total,
        "n_passed": n_passed,
        "n_failed": n_failed,
        "n_skipped": n_skipped,
        "categories": list(cat_stats.values()),
        "bugs": failed,
        "priority_groups": priority_groups,
        "answers_html": answers_html,
    }


def build_pdf_report(data: dict) -> None:
    """Сгенерировать PDF-отчёт через Playwright и Jinja2."""
    pdf_path = REPORTS_DIR / "REPORT.pdf"

    from playwright.sync_api import sync_playwright

    print("📄 Формирование PDF-отчета...")
    try:
        template = Template(PDF_TEMPLATE_HTML)
        html_content = template.render(**build_context(data))

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(html_content, wait_until="networkidle")
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                margin={
                    "top": "15mm",
                    "bottom": "15mm",
                    "left": "15mm",
                    "right": "15mm",
                },
            )
            browser.close()

        print(f"✅ Отчёт в PDF готов: {pdf_path}")
    except Exception as e:
        print(f"[ERROR] Ошибка генерации PDF: {e}")


PDF_TEMPLATE_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>Отчет о тестировании — {{ target_url }}</title>
<style>
/* CSS для PDF-отчета ========================================= */
@page {
    size: A4;
    margin: 20mm;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #333;
    line-height: 1.5;
    font-size: 11pt;
    background: #fff;
    margin: 0;
    padding: 0;
}

h1, h2, h3, h4 {
    margin-top: 2em;
    margin-bottom: 0.5em;
    color: #1a202c;
    page-break-after: avoid;
}

.cover-page {
    height: 90vh; /* Почти полная страница для обложки */
    display: flex;
    flex-direction: column;
    justify-content: center;
    text-align: center;
}

.cover-page h1 {
    font-size: 28pt;
    margin-bottom: 0.2em;
}

.cover-page .subtitle {
    font-size: 16pt;
    color: #718096;
    margin-bottom: 2em;
}

.cover-meta {
    font-size: 12pt;
    background: #f7fafc;
    padding: 2em;
    border-radius: 8px;
    display: inline-block;
    text-align: left;
    margin: 0 auto;
    border: 1px solid #e2e8f0;
}

.cover-meta table {
    width: 100%;
    border-collapse: collapse;
}

.cover-meta th {
    text-align: left;
    padding-right: 1em;
    padding-bottom: 0.5em;
    color: #4a5568;
    font-weight: normal;
}

.cover-meta td {
    padding-bottom: 0.5em;
    font-weight: 500;
}

.score-badge {
    font-size: 24pt;
    font-weight: bold;
    color: #fff;
    background: #38a169;
    padding: 10px 20px;
    border-radius: 8px;
    display: inline-block;
    margin-top: 1em;
}
.score-badge.low { background: #e53e3e; }
.score-badge.medium { background: #d69e2e; }

.page-break {
    page-break-before: always;
}

/* Сводная таблица ========================================= */
table.styled-table {
    width: 100%;
    border-collapse: collapse;
    margin: 1.5em 0;
    font-size: 10pt;
}

table.styled-table th, table.styled-table td {
    border: 1px solid #e2e8f0;
    padding: 10px;
    text-align: left;
}

table.styled-table th {
    background-color: #f7fafc;
    font-weight: bold;
    color: #4a5568;
}

/* БОКС со статистикой ================================================= */
.stats-grid {
    display: flex;
    gap: 15px;
    margin: 2em 0;
}
.stat-box {
    flex: 1;
    background: #f7fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 15px;
    text-align: center;
}
.stat-box .num {
    display: block;
    font-size: 20pt;
    font-weight: bold;
    margin-bottom: 5px;
}
.stat-box.passed .num { color: #38a169; }
.stat-box.failed .num { color: #e53e3e; }
.stat-box.skipped .num { color: #d69e2e; }

/* Ошибки ================================================= */
.bug-card {
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    margin-bottom: 15px;
    page-break-inside: avoid;
}

.bug-header {
    background: #f7fafc;
    padding: 10px 15px;
    border-bottom: 1px solid #e2e8f0;
    font-weight: bold;
    display: flex;
    justify-content: space-between;
}

.bug-title {
    color: #e53e3e;
}

.bug-body {
    padding: 15px;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 9pt;
    background: #fafafa;
    overflow-x: hidden;
    white-space: pre-wrap;
    word-wrap: break-word;
    color: #a0aec0;
}
.bug-body span.error { color: #e53e3e; }

/* Ответы ANSWERS.md ================================================= */
.answers-content pre {
    background: #f7fafc;
    padding: 1em;
    border-radius: 6px;
    overflow-x: hidden;
    white-space: pre-wrap;
    font-size: 9pt;
    border: 1px solid #e2e8f0;
}
.answers-content code {
    background: #f7fafc;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-family: monospace;
    font-size: 90%;
}
.answers-content p, .answers-content li {
    font-size: 11pt;
    line-height: 1.6;
}
</style>
</head>
<body>

    <!-- ОБЛОЖКА -->
    <div class="cover-page">
        <h1>Отчет о тестировании</h1>
        <div class="subtitle">Сайт: {{ target_url }}</div>
        
        <div class="cover-meta">
            <table>
                <tr><th>Дата отчета:</th><td>{{ date }}</td></tr>
                <tr><th>Время выполнения:</th><td>{{ duration }} сек</td></tr>
                <tr><th>Инструменты:</th><td>Python, pytest, Playwright</td></tr>
            </table>
            <br>
            <div style="text-align: center;">
                <div class="score-badge {% if score < 50 %}low{% elif score < 80 %}medium{% endif %}">
                    Quality Score: {{ score }}%
                </div>
            </div>
        </div>
    </div>

    <!-- СВОДКА -->
    <div class="page-break"></div>
    <h2>1. Сводка выполнения</h2>
    
    <div class="stats-grid">
        <div class="stat-box">
            <span class="num" style="color: #4a5568">{{ total }}</span>
            Всего тестов
        </div>
        <div class="stat-box passed">
            <span class="num">{{ n_passed }}</span>
            Успешно
        </div>
        <div class="stat-box failed">
            <span class="num">{{ n_failed }}</span>
            Ошибок
        </div>
        <div class="stat-box skipped">
            <span class="num">{{ n_skipped }}</span>
            Пропущено
        </div>
    </div>

    <h3>Статистика по категориям</h3>
    <table class="styled-table">
        <thead>
            <tr>
                <th>Категория</th>
                <th>Успешно</th>
                <th>Ошибки</th>
                <th>Прогресс</th>
            </tr>
        </thead>
        <tbody>
            {% for cat in categories %}
            <tr>
                <td>{{ cat.name }}</td>
                <td>{{ cat.passed }}</td>
                <td>{{ cat.failed }}</td>
                <td>{{ cat.pct }}%</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <!-- ДЕТАЛИ ОШИБОК -->
    {% if bugs %}
        <div class="page-break"></div>
        <h2>2. Детали ошибок</h2>
        
        {% for group in priority_groups %}
            {% if group.bugs %}
                <h3>{{ group.label }} приоритет</h3>
                {% for bug in group.bugs %}
                    <div class="bug-card">
                        <div class="bug-header">
                            <span class="bug-title">{{ bug.title }}</span>
                            <span style="color:#718096; font-size:9pt; font-weight:normal;">{{ bug.nodeid }}</span>
                        </div>
                        <div class="bug-body">
                            {{ bug.message | e }}
                        </div>
                    </div>
                {% endfor %}
            {% endif %}
        {% endfor %}
    {% endif %}

    <!-- ОТВЕТЫ НА ВОПРОСЫ (ANSWERS.md) -->
    {% if answers_html %}
        <div class="page-break"></div>
        <h2>3. Ответы на вопросы задания</h2>
        <div class="answers-content">
            {{ answers_html | safe }}
        </div>
    {% endif %}

</body>
</html>
"""

if __name__ == "__main__":
    try:
        import pytest_jsonreport  # pylint: disable=unused-import  # noqa: F401
    except ImportError:
        print("Устанавливаю pytest-json-report...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pytest-json-report", "-q"],
            check=True,
        )

    results = run_tests()
    build_markdown_report(results)
    build_pdf_report(results)

    total = len(results.get("tests", []))
    n_failed = len(
        [t for t in results.get("tests", []) if t.get("outcome") in ("failed", "error")]
    )

    print(f"\n{'='*60}")
    print(f"  Итог: {total - n_failed}/{total} тестов прошло")
    print(f"  Отчёты: {REPORTS_DIR}/")
    print(f"{'='*60}")

    sys.exit(0 if n_failed == 0 else 1)
