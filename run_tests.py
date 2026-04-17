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
        template_str = (BASE_DIR / "templates" / "pdf_template.html").read_text(encoding="utf-8")
        css_str = (BASE_DIR / "templates" / "pdf_style.css").read_text(encoding="utf-8")
        template = Template(template_str)
        context = build_context(data)
        context["pdf_style"] = css_str
        html_content = template.render(**context)

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



if __name__ == "__main__":
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
