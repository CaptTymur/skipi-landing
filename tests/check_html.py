#!/usr/bin/env python3
"""HTML-проверки лендинга skipi.app (stdlib-only, без сети).

Волна «редизайн по Figma-борду» (owner, 05.08): skipi.app = входная
страница с двумя действиями; «Что такое Skipi» ведёт на ОТДЕЛЬНУЮ
страницу «Разделы» (/sections/) с тремя разделами: ИИ-помощник
(identity-канон DECISIONS 2026-08-05 (10)), Приложения, Контуры.
Каждый экран несёт короткий путь «Начать пользоваться» →
https://assistant.skipi.app (принцип борда).

Группа E — инварианты предыдущей волны (диктовка №375, commit 8087680):
входной hero с двумя кнопками на корне+en+ru+hi+id. НЕ ослаблять.

Группа N — новая структура (failing-first): до реализации страницы
«Разделы» отсутствуют → RED; после реализации все проверки GREEN.

Запуск:  python3 tests/check_html.py   (exit 0 = все PASS)
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ASSISTANT = 'href="https://assistant.skipi.app"'

# локаль -> (входная страница, страница «Разделы», путь-ссылка на «Разделы»)
LOCALES = {
    "root": ("index.html", "sections/index.html", "/sections/"),
    "en":   ("en/index.html", "en/sections/index.html", "/en/sections/"),
    "ru":   ("ru/index.html", "ru/sections/index.html", "/ru/sections/"),
    "hi":   ("hi/index.html", "hi/sections/index.html", "/hi/sections/"),
    "id":   ("id/index.html", "id/sections/index.html", "/id/sections/"),
}

# локальные подписи кнопок входного hero (существующая волна — не трогать)
START_LABEL = {
    "root": "Начать пользоваться",
    "en":   "Start using Skipi",
    "ru":   "Начать пользоваться",
    "hi":   "उपयोग शुरू",
    "id":   "Mulai gunakan",
}
WHATIS_LABEL = {
    "root": "Узнать, что это такое",
    "en":   "What is Skipi",
    "ru":   "Узнать, что это такое",
    "hi":   "Skipi क्या है",
    "id":   "Apa itu Skipi",
}

# identity-канон ассистента (DECISIONS 2026-08-05 (10)) — обязательные
# подстроки раздела «ИИ-помощник». Полные локали — свой язык; hi/id — по
# подходу репо (смешанный текст, EN-термины).
IDENTITY = {
    "root": ("заточенный под судоходство", "Тимуром Рудовым",
             "коллективного опыта моряков"),
    "ru":   ("заточенный под судоходство", "Тимуром Рудовым",
             "коллективного опыта моряков"),
    "en":   ("purpose-built for shipping", "Tymur Rudov",
             "collective experience of seafarers"),
    "hi":   ("purpose-built for shipping", "Tymur Rudov"),
    "id":   ("purpose-built for shipping", "Tymur Rudov"),
}

APPS = ("Skipi Seafarer", "Skipi Crewing", "Skipi Broker")

# три контура экосистемы (роли вокруг одного слоя данных)
CONTOURS = {
    "root": ("Моряк", "Крюинг", "Брокер"),
    "ru":   ("Моряк", "Крюинг", "Брокер"),
    "en":   ("Seafarer", "Crewing", "Broker"),
    "hi":   ("Seafarer", "Crewing", "Broker"),
    "id":   ("Seafarer", "Crewing", "Broker"),
}

results = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, bool(ok)))
    mark = "PASS" if ok else "FAIL"
    line = f"[{mark}] {name}"
    if not ok and detail:
        line += f" — {detail}"
    print(line)


def read(rel: str) -> str:
    p = ROOT / rel
    if not p.is_file():
        return ""
    return p.read_text(encoding="utf-8")


def section_of(html: str, sec_id: str) -> str:
    """Фрагмент от id=... до ближайшего </section>."""
    marker = f'id="{sec_id}"'
    if marker not in html:
        return ""
    return html.split(marker, 1)[1].split("</section>", 1)[0]


for loc, (entry_rel, sections_rel, sections_href) in LOCALES.items():
    entry = read(entry_rel)

    # ── Группа E: инварианты входного hero (волна 8087680) ──────────
    check(f"E1[{loc}] входная: ссылка на assistant.skipi.app",
          ASSISTANT in entry, entry_rel)
    check(f"E2[{loc}] входная: hero-entry блок на месте",
          "hero-entry" in entry, entry_rel)
    check(f"E3[{loc}] входная: кнопка «{START_LABEL[loc]}»",
          START_LABEL[loc] in entry, entry_rel)
    check(f"E4[{loc}] входная: кнопка «{WHATIS_LABEL[loc]}»",
          WHATIS_LABEL[loc] in entry, entry_rel)

    # ── Группа N: страница «Разделы» (failing-first) ────────────────
    # HTML-блок hero-entry (маркер с '">' отсекает упоминание в CSS)
    hero_entry = entry.split('hero-entry">', 1)[-1].split("</div>", 1)[0]
    check(f"N1[{loc}] входная: «Что такое Skipi» ведёт на {sections_href} "
          f"(отдельная страница, не якорь)",
          f'href="{sections_href}"' in hero_entry,
          "кнопка ещё ведёт на якорь")

    sections = read(sections_rel)
    check(f"N2[{loc}] страница «Разделы» существует: {sections_rel}",
          bool(sections), "файла нет")

    assistant_sec = section_of(sections, "assistant")
    check(f"N3[{loc}] razdel ИИ-помощник (id=\"assistant\") с CTA "
          f"на assistant.skipi.app",
          bool(assistant_sec) and ASSISTANT in assistant_sec)

    ident_ok = bool(assistant_sec) and all(
        s in assistant_sec for s in IDENTITY[loc])
    check(f"N4[{loc}] identity-канон ассистента дословно по смыслу",
          ident_ok, f"нет подстрок {IDENTITY[loc]}")

    apps_sec = section_of(sections, "apps")
    apps_ok = bool(apps_sec) and all(a in apps_sec for a in APPS) \
        and "/downloads" in apps_sec
    check(f"N5[{loc}] razdel Приложения (id=\"apps\"): Seafarer/Crewing/"
          f"Broker + /downloads", apps_ok)

    cont_sec = section_of(sections, "contours")
    cont_ok = bool(cont_sec) and all(c in cont_sec for c in CONTOURS[loc])
    check(f"N6[{loc}] razdel Контуры (id=\"contours\"): три контура "
          f"{CONTOURS[loc]}", cont_ok)

    check(f"N7[{loc}] «Разделы»: кнопка «Начать пользоваться» → "
          f"assistant.skipi.app",
          START_LABEL[loc] in sections and ASSISTANT in sections)

    light_ok = ("--bg:" in sections and "#ffffff" in sections) or \
        "/assets/localized-home.css" in sections
    check(f"N8[{loc}] «Разделы»: светлая тема по умолчанию (канон)",
          light_ok)

passed = sum(1 for _, ok in results if ok)
total = len(results)
print(f"\n{passed}/{total} checks passed")
sys.exit(0 if passed == total else 1)
