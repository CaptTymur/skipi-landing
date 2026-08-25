#!/usr/bin/env python3
"""HTML-проверки лендинга skipi.app (stdlib-only, без сети).

Волна «redesign v2 — journey» (owner, 05.08). Вердикт владельца по v1:
«слишком много всего», «пользователь должен путешествовать по сайту,
а не читать». Новая структура: сайт = путешествие из сцен.

Скелет (FigJam-борд владельца):
  1. Вход (index):
     root/en/ru — развилка трёх ролей ПРЯМО в hero (№135, owner 14.08):
       моряк → assistant, крюинг → /app/crewing, брокер → /app/broker;
     hi/id — одиночная «Начать пользоваться» → https://assistant.skipi.app;
     везде «Что такое Skipi» → /story/ (путешествие-объяснение).
  2. Путешествие /story/ — полноэкранные главы:
     prologue → assistant (identity-канон) → apps → contours → start
  3. Все пути сходятся в assistant.skipi.app.

Группы проверок:
  A — вход: два действия, локали, лёгкость (бюджет слов).
  S — story: сцены-главы, identity-канон, apps, contours, финальный CTA.
  I — инварианты: все .cta → assistant, светлая тема, никаких новых
      внешних CDN, downloads не сломан, sitemap.

Принцип «МАЛО на экране» проверяется механически: бюджет слов на
вход и на каждую сцену.

Запуск:  python3 tests/check_html.py   (exit 0 = все PASS)
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ASSISTANT = "https://assistant.skipi.app"

# Язык по умолчанию = АНГЛИЙСКИЙ (owner-решение 05.08, задача №92):
# корень / и /story/ — EN; русский полноценно живёт на /ru/ и /ru/story/;
# /en/ остаётся зеркалом корня с canonical на корень.

# локаль -> (входная, story, ссылка на story, lang-атрибут)
LOCALES = {
    "root": ("index.html", "story/index.html", "/story/", "en"),
    "en":   ("en/index.html", "en/story/index.html", "/en/story/", "en"),
    "ru":   ("ru/index.html", "ru/story/index.html", "/ru/story/", "ru"),
    "hi":   ("hi/index.html", "hi/story/index.html", "/hi/story/", "hi"),
    "id":   ("id/index.html", "id/story/index.html", "/id/story/", "id"),
}

START_LABEL = {
    "root": "Start using",
    "en":   "Start using",
    "ru":   "Начать пользоваться",
    "hi":   "उपयोग शुरू",
    "id":   "Mulai gunakan",
}
# Развилка в hero (№135, owner-уточнение 14.08, вторая итерация):
# одна фраза-приглашение «Start using Skipi as:» (лид-строка) + три
# равноправные роль-кнопки прямо в hero (перенос секции .paths,
# не дубль). hi/id/tl — не участвуют.
FORK_LOCALES = ("root", "en", "ru")
FORK_HREFS = (ASSISTANT,
              f"{ASSISTANT}/app/crewing",
              f"{ASSISTANT}/app/broker")
FORK_LEAD = {
    "root": "Start using Skipi as",
    "en":   "Start using Skipi as",
    "ru":   "Начните использовать Skipi как",
}
# лейблы ролей проверяются как точный текст ссылки (">…<"), иначе
# «Seafarer» ложно совпадает с kicker «United Seafarers»
FORK_ROLES = {
    "root": ("Seafarer", "Crewing manager", "Broker"),
    "en":   ("Seafarer", "Crewing manager", "Broker"),
    "ru":   ("Моряк", "Крюинг-менеджер", "Брокер"),
}
# I1 (owner-решение 14.08): допустимые href для .cta — РОВНО эти три
# SaaS-входа, не «любая ссылка».
CTA_ALLOWED = set(FORK_HREFS)

WHATIS_LABEL = {
    "root": "What is Skipi",
    "en":   "What is Skipi",
    "ru":   "Что такое Skipi",
    "hi":   "Skipi क्या है",
    "id":   "Apa itu Skipi",
}

# identity-канон ассистента (DECISIONS 2026-08-05 (10)):
# специализированный ИИ под судоходство, создан капитаном Тимуром
# Рудовым на основе коллективного опыта моряков. hi/id — подход репо
# (смешанный текст, EN-термины).
IDENTITY = {
    "root": ("purpose-built for shipping", "Tymur Rudov",
             "collective experience of seafarers"),
    "ru":   ("заточенный под судоходство", "Тимуром Рудовым",
             "коллективного опыта моряков"),
    "en":   ("purpose-built for shipping", "Tymur Rudov",
             "collective experience of seafarers"),
    "hi":   ("purpose-built", "Tymur Rudov"),
    "id":   ("khusus untuk pelayaran", "Tymur Rudov"),
}

APPS = ("Seafarer", "Crewing", "Broker")

CONTOURS = {
    "root": ("seafarer", "crewing", "broker"),
    "ru":   ("моряк", "крюинг", "брокер"),
    "en":   ("seafarer", "crewing", "broker"),
    "hi":   ("seafarer", "crewing", "broker"),
    "id":   ("pelaut", "crewing", "broker"),
}

SCENES = ("prologue", "assistant", "apps", "contours", "start")

# бюджеты слов: сдержанность как механический инвариант
ENTRY_WORD_BUDGET = 40   # <main> входной страницы
SCENE_WORD_BUDGET = 60   # каждая сцена story

# разрешённые внешние хосты (href/src). Новых CDN не появляется.
ALLOWED_HOSTS = {
    "assistant.skipi.app",
    "skipi.app",
    "fonts.googleapis.com",
    "fonts.gstatic.com",
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


def strip_text(html: str) -> str:
    """Видимый текст: без script/style/тегов/entities."""
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style\b.*?</style>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    html = re.sub(r"&[a-z#0-9]+;", " ", html)
    return html


def word_count(html: str) -> int:
    return len([w for w in strip_text(html).split()
                if any(ch.isalnum() for ch in w)])


def section_of(html: str, sec_id: str) -> str:
    """Фрагмент <section ... id="sec_id" ...> до </section>."""
    m = re.search(r'<section\b[^>]*\bid="%s"' % re.escape(sec_id), html)
    if not m:
        return ""
    return html[m.start():].split("</section>", 1)[0]


def main_of(html: str) -> str:
    m = re.search(r"<main\b[^>]*>", html)
    if not m:
        return ""
    return html[m.end():].split("</main>", 1)[0]


def external_hosts(html: str):
    hosts = set()
    for m in re.finditer(r'(?:href|src)="(https?://[^"/]+)', html):
        hosts.add(m.group(1).split("://", 1)[1].lower())
    return hosts


for loc, (entry_rel, story_rel, story_href, lang) in LOCALES.items():
    entry = read(entry_rel)
    story = read(story_rel)

    # ── Группа A: вход ──────────────────────────────────────────────
    check(f"A1[{loc}] входная существует: {entry_rel}", bool(entry))
    check(f"A2[{loc}] lang=\"{lang}\"",
          f'lang="{lang}"' in entry.split(">", 2)[1] + ">"
          if entry else False,
          "нет lang в <html>")
    entry_main = main_of(entry)
    # действие 1: на fork-локалях — роль-кнопка моряка (точный текст
    # ссылки), на остальных — прежняя одиночная CTA (№135, owner 14.08)
    if loc in FORK_LOCALES:
        act1_label = FORK_ROLES[loc][0]
        act1_ok = (f'href="{ASSISTANT}"' in entry_main
                   and f">{act1_label}<" in entry_main)
    else:
        act1_label = START_LABEL[loc]
        act1_ok = (f'href="{ASSISTANT}"' in entry_main
                   and act1_label in entry_main)
    check(f"A3[{loc}] действие 1: «{act1_label}» → assistant", act1_ok)
    check(f"A4[{loc}] действие 2: «{WHATIS_LABEL[loc]}» → {story_href}",
          f'href="{story_href}"' in entry_main
          and WHATIS_LABEL[loc] in entry_main)
    wc = word_count(entry_main)
    check(f"A5[{loc}] вход лёгкий: <main> ≤ {ENTRY_WORD_BUDGET} слов "
          f"(факт {wc})", 0 < wc <= ENTRY_WORD_BUDGET)
    check(f"A6[{loc}] вход подключает journey.css",
          "/assets/journey.css" in entry)

    # ── Группа S: путешествие ──────────────────────────────────────
    check(f"S1[{loc}] story существует: {story_rel}", bool(story))
    for sc in SCENES:
        sec = section_of(story, sc)
        okwc = word_count(sec)
        check(f"S2[{loc}] сцена «{sc}»: есть и ≤ {SCENE_WORD_BUDGET} "
              f"слов (факт {okwc})",
              bool(sec) and 0 < okwc <= SCENE_WORD_BUDGET)

    asec = section_of(story, "assistant")
    check(f"S3[{loc}] глава ИИ-помощник: identity-канон {IDENTITY[loc]}",
          bool(asec) and all(s in asec for s in IDENTITY[loc]))

    psec = section_of(story, "apps")
    check(f"S4[{loc}] глава Приложения: Seafarer/Crewing/Broker "
          f"+ /downloads",
          bool(psec) and all(a in psec for a in APPS)
          and 'href="/downloads' in psec)

    csec = section_of(story, "contours")
    check(f"S5[{loc}] глава Контуры: три роли {CONTOURS[loc]}",
          bool(csec) and all(c in csec.lower() for c in CONTOURS[loc]))

    ssec = section_of(story, "start")
    check(f"S6[{loc}] финал: «{START_LABEL[loc]}» → assistant",
          bool(ssec) and f'href="{ASSISTANT}"' in ssec
          and START_LABEL[loc] in ssec)

    check(f"S7[{loc}] из любой точки шаг «начать»: постоянная "
          f"cta-ссылка в шапке story",
          bool(story) and f'href="{ASSISTANT}"' in
          (story.split("</header>", 1)[0] if "</header>" in story else ""))

    # ── Группа I (по-локально): CTA и внешние хосты ────────────────
    for rel, html in ((entry_rel, entry), (story_rel, story)):
        ctas = re.findall(r'<a\b[^>]*class="[^"]*cta[^"]*"[^>]*>', html)
        hrefs = [m.group(1) for c in ctas
                 for m in [re.search(r'href="([^"]+)"', c)] if m]
        cta_ok = (bool(ctas) and len(hrefs) == len(ctas)
                  and all(h in CTA_ALLOWED for h in hrefs))
        check(f"I1[{loc}] {rel}: каждый .cta → один из трёх SaaS-входов "
              f"(assistant / app/crewing / app/broker; {len(ctas)} шт.)",
              cta_ok)
        bad = external_hosts(html) - ALLOWED_HOSTS
        check(f"I2[{loc}] {rel}: без новых внешних CDN",
              bool(html) and not bad, f"лишние хосты: {sorted(bad)}")

# ── Группа P: развилка в HERO (№135; owner-уточнение 14.08) ───────
# Owner (вторая итерация, дословно): «стильная развилка start using
# skipi as: seafarer, crewing manager, broker». Форма: лид-строка
# + три равноправные роли → входы в SaaS: моряк → assistant,
# крюинг-менеджер и брокер → веб-кабинеты.
# Локали: корень + en + ru; hi/id/tl не участвуют.
for loc in FORK_LOCALES:
    page = LOCALES[loc][0]
    html = read(page)
    hero = main_of(html)
    ok = (all(f'href="{u}"' in hero for u in FORK_HREFS)
          and FORK_LEAD[loc] in hero
          and all(f">{r}<" in hero for r in FORK_ROLES[loc]))
    check(f"P1[{loc}] {page}: hero-развилка — лид «{FORK_LEAD[loc]}» "
          f"+ 3 роли → 3 SaaS-входа "
          f"(assistant / app/crewing / app/broker)", ok)
    check(f"P2[{loc}] {page}: отдельной секции .paths ниже hero нет "
          f"(перенос, не дубль)", bool(html) and 'class="paths"' not in html)

# ── Группа L: язык по умолчанию = EN (задача №92) ──────────────────
SITE = "https://skipi.app"


def canonical_of(html: str) -> str:
    m = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    return m.group(1) if m else ""


def og_url_of(html: str) -> str:
    m = re.search(r'<meta property="og:url" content="([^"]+)"', html)
    return m.group(1) if m else ""


def hreflangs_of(html: str) -> dict:
    return dict(re.findall(
        r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', html))


root = read("index.html")
root_story = read("story/index.html")
en = read("en/index.html")
en_story = read("en/story/index.html")
ru = read("ru/index.html")
ru_story = read("ru/story/index.html")

check("L1 корень = EN: canonical и og:url корня — https://skipi.app/",
      canonical_of(root) == f"{SITE}/" and og_url_of(root) == f"{SITE}/",
      f"canonical={canonical_of(root)} og:url={og_url_of(root)}")

hl = hreflangs_of(root)
check("L2 hreflang корня: en → корень, ru → /ru/, x-default → корень",
      hl.get("en") == f"{SITE}/" and hl.get("ru") == f"{SITE}/ru/"
      and hl.get("x-default") == f"{SITE}/", f"факт: {hl}")

check("L3 /story/ = EN: canonical/og:url → /story/, hreflang en → /story/, "
      "ru → /ru/story/, x-default → /story/",
      canonical_of(root_story) == f"{SITE}/story/"
      and og_url_of(root_story) == f"{SITE}/story/"
      and hreflangs_of(root_story).get("en") == f"{SITE}/story/"
      and hreflangs_of(root_story).get("ru") == f"{SITE}/ru/story/"
      and hreflangs_of(root_story).get("x-default") == f"{SITE}/story/")

check("L4 /en/ — зеркало корня: canonical → корень, /en/story/ → /story/",
      canonical_of(en) == f"{SITE}/"
      and canonical_of(en_story) == f"{SITE}/story/",
      f"факт: {canonical_of(en)}, {canonical_of(en_story)}")

check("L5 /ru/ самодостаточен: canonical /ru/ и /ru/story/, "
      "hreflang ru → /ru/ и /ru/story/",
      canonical_of(ru) == f"{SITE}/ru/"
      and canonical_of(ru_story) == f"{SITE}/ru/story/"
      and hreflangs_of(ru).get("ru") == f"{SITE}/ru/"
      and hreflangs_of(ru_story).get("ru") == f"{SITE}/ru/story/")

# единый языковой футер: EN/RU/TL/HI/ID доступны с каждой входной локали
LANG_FOOTER = {"en": "/", "ru": "/ru/", "tl": "/tl/",
               "hi": "/hi/", "id": "/id/"}
for page in ("index.html", "en/index.html", "ru/index.html",
             "hi/index.html", "id/index.html", "tl/index.html"):
    html = read(page)
    missing = [f'{code} → {href}' for code, href in LANG_FOOTER.items()
               if f'href="{href}" lang="{code}"' not in html]
    check(f"L6 {page}: футер-переключатель EN/RU/TL/HI/ID "
          f"(EN → корень, RU → /ru/)", bool(html) and not missing,
          f"нет: {missing}")

# hi/id/tl: hreflang мигрирован на новую раскладку (en → корень, ru → /ru/)
for page in ("hi/index.html", "id/index.html", "tl/index.html"):
    hlp = hreflangs_of(read(page))
    check(f"L7 {page}: hreflang en → корень, ru → /ru/, x-default → корень",
          hlp.get("en") == f"{SITE}/" and hlp.get("ru") == f"{SITE}/ru/"
          and hlp.get("x-default") == f"{SITE}/", f"факт: {hlp}")
for page in ("hi/story/index.html", "id/story/index.html",
             "en/story/index.html", "ru/story/index.html"):
    hlp = hreflangs_of(read(page))
    check(f"L8 {page}: hreflang en → /story/, ru → /ru/story/, "
          f"x-default → /story/",
          hlp.get("en") == f"{SITE}/story/"
          and hlp.get("ru") == f"{SITE}/ru/story/"
          and hlp.get("x-default") == f"{SITE}/story/", f"факт: {hlp}")

# ── Группа I (глобально) ───────────────────────────────────────────
css = read("assets/journey.css")
check("I3 светлая тема: journey.css задаёт color-scheme: light + белый фон",
      "color-scheme: light" in css and "#ffffff" in css)
check("I4 тёмная тема не задана по умолчанию: в journey.css нет "
      "prefers-color-scheme: dark",
      bool(css) and "prefers-color-scheme: dark" not in css)

downloads = read("downloads/index.html")
check("I5 downloads жив и не тронут этой волной",
      bool(downloads) and "Seafarer" in downloads)

sitemap = read("sitemap.xml")
check("I6 sitemap: все пять story-URL",
      all(f"https://skipi.app{h}" in sitemap
          for h in ("/story/", "/en/story/", "/ru/story/",
                    "/hi/story/", "/id/story/")))

# ── Группа SUP: страница поддержки проекта (2026-08-17) ────────────
PAYPAL_DONATE = (
    "https://www.paypal.com/donate/?business=tymur.rudov%40icloud.com"
    "&no_recurring=0&item_name=Support+Skipi+AI+assistant"
    "&currency_code=USD"
)
PATREON = "https://patreon.com/Capt_Tymur"
support = read("support/index.html")
check("SUP1 support/index.html существует", bool(support))
check("SUP2 PayPal: официальный donate-URL (не paypal.me)",
      PAYPAL_DONATE in support and "paypal.me" not in support.lower())
check("SUP3 Patreon: https://patreon.com/Capt_Tymur",
      PATREON in support)
forbidden = ("USDT", "Bybit", "IBAN", "SWIFT")
hit = [w for w in forbidden if w.lower() in support.lower()]
check("SUP4 нет USDT/Bybit/IBAN/SWIFT",
      bool(support) and not hit, f"запрещённые слова: {hit}")
check("SUP5 sitemap: https://skipi.app/support/",
      "https://skipi.app/support/" in sitemap)
check("SUP6 светлая тема + accent #007a86 + Inter",
      bool(support)
      and "color-scheme: light" in support
      and "#007a86" in support
      and "Inter" in support)
for page, label in (("index.html", "Support"),
                    ("en/index.html", "Support"),
                    ("ru/index.html", "Поддержка"),
                    ("hi/index.html", "Support"),
                    ("id/index.html", "Support")):
    html = read(page)
    check(f"SUP7 {page}: футер quiet-ссылка «{label}» → /support/",
          f'href="/support/"' in html and label in html)

# ── Группа AG: agent-readable поверхность (owner, 2026-08-25) ─────
agent_page = read("for-agents/index.html")
llms = read("llms.txt")
site_summary_raw = read("site-summary.json")
try:
    site_summary = json.loads(site_summary_raw)
except (TypeError, json.JSONDecodeError):
    site_summary = {}

check("AG1 for-agents/index.html существует и canonical → /for-agents/",
      bool(agent_page)
      and '<link rel="canonical" href="https://skipi.app/for-agents/">'
      in agent_page)
check("AG2 /for-agents/ видимо связан с главной страницей",
      'href="/for-agents/"' in root and ">For agents<" in root)
check("AG3 /for-agents/ указывает на обе локальные machine-readable поверхности",
      'href="/llms.txt"' in agent_page
      and 'href="/site-summary.json"' in agent_page)
check("AG4 /for-agents/ связывает продукт с отдельным skipi.info",
      'href="https://skipi.info/"' in agent_page
      and 'href="https://skipi.info/llms.txt"' in agent_page)

required_llms_urls = (
    "https://skipi.app/",
    "https://skipi.app/for-agents/",
    "https://skipi.app/site-summary.json",
    "https://skipi.info/",
    "https://skipi.info/llms.txt",
)
check("AG5 llms.txt содержит canonical product/discovery routes",
      llms.startswith("# Skipi\n")
      and all(url in llms for url in required_llms_urls))

check("AG6 site-summary.json валиден и self-identifies",
      site_summary.get("schema_version") == "1.0"
      and site_summary.get("name") == "Skipi"
      and site_summary.get("canonical_url") == "https://skipi.app/")
machine = site_summary.get("machine_readable", {})
related = site_summary.get("related_sites", [])
check("AG7 structured summary связывает llms/sitemap и skipi.info",
      machine.get("llms_txt") == "https://skipi.app/llms.txt"
      and machine.get("sitemap") == "https://skipi.app/sitemap.xml"
      and bool(related)
      and related[0].get("canonical_url") == "https://skipi.info/"
      and related[0].get("llms_txt") == "https://skipi.info/llms.txt")

agent_surface = "\n".join((agent_page, llms, site_summary_raw)).lower()
unsupported = ("real-time", "guaranteed", "public api", "/api/", "api key")
hits = [claim for claim in unsupported if claim in agent_surface]
check("AG8 нет неподтверждённых real-time/API/guarantee claims",
      bool(agent_page) and bool(llms) and bool(site_summary_raw) and not hits,
      f"сомнительные claims: {hits}")
check("AG9 sitemap содержит /for-agents/",
      "https://skipi.app/for-agents/" in sitemap)

passed = sum(1 for _, ok in results if ok)
total = len(results)
print(f"\n{passed}/{total} checks passed")
sys.exit(0 if passed == total else 1)
