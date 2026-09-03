#!/usr/bin/env python3
"""HTML-проверки лендинга skipi.app (stdlib-only, без сети).

Волна «redesign v2 — journey» (owner, 05.08). Вердикт владельца по v1:
«слишком много всего», «пользователь должен путешествовать по сайту,
а не читать». Новая структура: сайт = путешествие из сцен.

Сайт англоязычный (owner 03.09: «это убери с сайта совсем. пока только
английский язык»). Переключателя языков нет; прежние языковые адреса
(/ru/, /tl/, /hi/, /id/ и их /story/) живут как заглушки-редиректы на
английскую версию — ссылки из внешнего мира не ломаются.

Второе owner-решение 03.09 — «английский на главный адрес»: английский
контент /en/for-companies/ и /en/presentation/ переехал на /for-companies/
и /presentation/ (русские версии этих двух страниц заменены английскими,
текст остался в истории git), а /en/-двойники стали заглушками-переходами
на верхний уровень. Зеркало /en/ и /en/story/ (canonical на корень)
сохраняется как было.

Скелет (FigJam-борд владельца):
  1. Вход (index): root/en — развилка трёх ролей ПРЯМО в hero (№135,
     owner 14.08): моряк → assistant, крюинг → /app/crewing,
     брокер → /app/broker; «What is Skipi» → /story/.
  2. Путешествие /story/ — полноэкранные главы:
     prologue → assistant (identity-канон) → apps → contours → start
  3. Все пути сходятся в assistant.skipi.app.

Группы проверок:
  A — вход: два действия, лёгкость (бюджет слов).
  S — story: сцены-главы, identity-канон, apps, contours, финальный CTA.
  I — инварианты: все .cta → assistant, светлая тема, никаких новых
      внешних CDN, downloads не сломан, sitemap.
  R — прежние языковые адреса редиректят на английский.
  X — англоязычность: переключателя нет, неанглийских hreflang нет,
      русских страниц не осталось.
  DL — страница загрузок и её заглушка англоязычные.
  LTD — юрблок SKIPI LTD (опубликован 03.09) на месте.

Принцип «МАЛО на экране» проверяется механически: бюджет слов на
вход и на каждую сцену.

Запуск:  python3 tests/check_html.py   (exit 0 = все PASS)
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ASSISTANT = "https://assistant.skipi.app"

# Язык сайта = АНГЛИЙСКИЙ и только он (owner-решение 03.09).
# Живой контент: корень / и /story/ (+ зеркало /en/ и /en/story/).
# Неанглийские адреса — заглушки-редиректы, они проверяются группой R.

# локаль -> (входная, story, ссылка на story, lang-атрибут)
LOCALES = {
    "root": ("index.html", "story/index.html", "/story/", "en"),
    "en":   ("en/index.html", "en/story/index.html", "/en/story/", "en"),
}

START_LABEL = {
    "root": "Start using",
    "en":   "Start using",
}
# Развилка в hero (№135, owner-уточнение 14.08, вторая итерация):
# одна фраза-приглашение «Start using Skipi as:» (лид-строка) + три
# равноправные роль-кнопки прямо в hero (перенос секции .paths,
# не дубль). hi/id/tl — не участвуют.
FORK_LOCALES = ("root", "en")
FORK_HREFS = (ASSISTANT,
              f"{ASSISTANT}/app/crewing",
              f"{ASSISTANT}/app/broker")
FORK_LEAD = {
    "root": "Start using Skipi as",
    "en":   "Start using Skipi as",
}
# лейблы ролей проверяются как точный текст ссылки (">…<"), иначе
# «Seafarer» ложно совпадает с kicker «United Seafarers»
FORK_ROLES = {
    "root": ("Seafarer", "Crewing manager", "Broker"),
    "en":   ("Seafarer", "Crewing manager", "Broker"),
}
# I1 (owner-решение 14.08): допустимые href для .cta — РОВНО эти три
# SaaS-входа, не «любая ссылка».
CTA_ALLOWED = set(FORK_HREFS)

WHATIS_LABEL = {
    "root": "What is Skipi",
    "en":   "What is Skipi",
}

# identity-канон ассистента (DECISIONS 2026-08-05 (10)):
# специализированный ИИ под судоходство, создан капитаном Тимуром
# Рудовым на основе коллективного опыта моряков.
IDENTITY = {
    "root": ("purpose-built for shipping", "Tymur Rudov",
             "collective experience of seafarers"),
    "en":   ("purpose-built for shipping", "Tymur Rudov",
             "collective experience of seafarers"),
}

APPS = ("Seafarer", "Crewing", "Broker")

CONTOURS = {
    "root": ("seafarer", "crewing", "broker"),
    "en":   ("seafarer", "crewing", "broker"),
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
# Локали: корень + en (сайт англоязычный, owner 03.09).
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

# ── Группа L: единственный язык сайта = EN (owner 03.09) ───────────
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

check("L1 корень = EN: canonical и og:url корня — https://skipi.app/",
      canonical_of(root) == f"{SITE}/" and og_url_of(root) == f"{SITE}/",
      f"canonical={canonical_of(root)} og:url={og_url_of(root)}")

hl = hreflangs_of(root)
check("L2 hreflang корня: только en → корень и x-default → корень",
      hl == {"en": f"{SITE}/", "x-default": f"{SITE}/"}, f"факт: {hl}")

check("L3 /story/ = EN: canonical/og:url → /story/, hreflang только "
      "en → /story/ и x-default → /story/",
      canonical_of(root_story) == f"{SITE}/story/"
      and og_url_of(root_story) == f"{SITE}/story/"
      and hreflangs_of(root_story) == {"en": f"{SITE}/story/",
                                       "x-default": f"{SITE}/story/"},
      f"факт: {hreflangs_of(root_story)}")

check("L4 /en/ — зеркало корня: canonical → корень, /en/story/ → /story/",
      canonical_of(en) == f"{SITE}/"
      and canonical_of(en_story) == f"{SITE}/story/",
      f"факт: {canonical_of(en)}, {canonical_of(en_story)}")

check("L5 /en/story/ — зеркало: hreflang только en и x-default → /story/",
      hreflangs_of(en_story) == {"en": f"{SITE}/story/",
                                 "x-default": f"{SITE}/story/"},
      f"факт: {hreflangs_of(en_story)}")


# ── Группа R: прежние языковые адреса → редирект на английский ─────
# owner 03.09: неанглийские страницы не удаляем, а перенаправляем —
# внешние ссылки и поисковая выдача не ломаются.
REDIRECTS = {
    # прежние языковые адреса → английская версия (owner 03.09, решение 1)
    "ru/index.html": "/",
    "tl/index.html": "/",
    "hi/index.html": "/",
    "id/index.html": "/",
    "ru/story/index.html": "/story/",
    "hi/story/index.html": "/story/",
    "id/story/index.html": "/story/",
    # английский переехал на главный адрес (owner 03.09, решение 2):
    # /en/-двойники этих двух страниц теперь ведут на верхний уровень
    "en/for-companies/index.html": "/for-companies/",
    "en/presentation/index.html": "/presentation/",
}
for page, target in REDIRECTS.items():
    html = read(page)
    ok = (bool(html)
          and f'content="0; url={target}"' in html
          and f'<link rel="canonical" href="{SITE}{target}">' in html
          and f'href="{target}"' in html          # видимая ссылка
          and 'lang="en"' in html.split(">", 2)[1] + ">")
    check(f"R1 {page}: meta-refresh + canonical + видимая ссылка → "
          f"{target}, lang=\"en\"", ok)

# зеркало корня /en/ и /en/story/ остаётся содержательным (canonical
# на корень) — редиректами его не трогали
EN_MIRROR = ("en/index.html", "en/story/index.html")
check("R2 зеркало /en/ и /en/story/ живое, не заглушка",
      all(k not in REDIRECTS and "http-equiv=\"refresh\"" not in read(k)
          for k in EN_MIRROR))

# ── Группа T: английский на главном адресе (owner 03.09, решение 2) ─
TOP_LEVEL_EN = {
    "for-companies/index.html": ("/for-companies/", "Intelligence for companies"),
    "presentation/index.html":  ("/presentation/", "How Skipi works"),
}
for page, (url, title_part) in TOP_LEVEL_EN.items():
    html = read(page)
    head = html.split(">", 2)[1] + ">" if html else ""
    ok = (bool(html)
          and 'lang="en"' in head
          and f'<title>' in html and title_part in html
          and f'<link rel="canonical" href="{SITE}{url}">' in html
          and "http-equiv=\"refresh\"" not in html)   # это контент, не заглушка
    check(f"T1 {page}: англоязычная содержательная страница на главном "
          f"адресе (lang=\"en\", canonical → {url})", ok)
    check(f"T2 {page}: внутри нет ссылок на /en/-двойники "
          f"(английский теперь верхний уровень)",
          bool(html) and "/en/" not in html,
          "остались /en/-ссылки")
    check(f"T3 sitemap: {url} есть, /en{url} нет",
          f"<loc>{SITE}{url}</loc>" in read("sitemap.xml")
          and f"<loc>{SITE}/en{url}</loc>" not in read("sitemap.xml"))


# ── Группа X: сайт англоязычный (owner 03.09) ──────────────────────
HTML_FILES = sorted(pp.relative_to(ROOT).as_posix()
                    for pp in ROOT.rglob("*.html")
                    if ".git" not in pp.parts)
check("X0 обход страниц непустой", len(HTML_FILES) > 10,
      f"найдено {len(HTML_FILES)}")

# Хвост закрыт owner-решением 03.09 «английский на главный адрес»:
# /for-companies/ и /presentation/ теперь сами английские, исключений
# из этой проверки больше нет — ни одной страницы с переключателем.
switcher = [f for f in HTML_FILES
            if 'class="langs"' in read(f) or 'lang-link' in read(f)
            or 'lang-switch' in read(f)]
check("X1 переключателя языков нет ни на одной странице (без исключений)",
      not switcher, f"остался на: {switcher}")

NON_EN = ("ru", "tl", "hi", "id")
bad_hl = {f: [c for c in hreflangs_of(read(f)) if c in NON_EN]
          for f in HTML_FILES}
bad_hl = {f: v for f, v in bad_hl.items() if v}
check("X2 hreflang-альтернатив неанглийских версий нет "
      "(только en / x-default)", not bad_hl, f"факт: {bad_hl}")

CYRILLIC = set(range(0x0400, 0x0460)) | {0x0451, 0x0401}
ru_pages = sorted(f for f in HTML_FILES
                  if '<html lang="ru"' in read(f)
                  or any(ord(ch) in CYRILLIC for ch in read(f)))
check("X4 русских страниц не осталось: ни <html lang=\"ru\">, "
      "ни кириллицы ни в одном HTML (owner 03.09 — «пока только "
      "английский язык»)", not ru_pages, f"осталось: {ru_pages}")

check("X3 мёртвых стилей переключателя нет ни в одном CSS "
      "(.langs / .lang-switch / .lang-link)",
      not [c for c in ("assets/journey.css", "assets/localized-home.css")
           if any(t in read(c)
                  for t in (".langs", ".lang-switch", ".lang-link"))])

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
check("I6 sitemap: английские story-URL на месте",
      all(f"<loc>https://skipi.app{h}</loc>" in sitemap
          for h in ("/", "/story/", "/en/story/")))
check("I7 sitemap: ни неанглийских адресов, ни /en/-двойников "
      "переехавших страниц",
      not [h for h in ("/ru/", "/tl/", "/hi/", "/id/", "/ru/story/",
                       "/hi/story/", "/id/story/",
                       "/en/for-companies/", "/en/presentation/")
           if f"<loc>https://skipi.app{h}</loc>" in sitemap])

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
                    ("en/index.html", "Support")):
    html = read(page)
    check(f"SUP7 {page}: футер quiet-ссылка «{label}» → /support/",
          f'href="/support/"' in html and label in html)

# ── Группа DL: страница загрузок англоязычная (owner 03.09) ────────
# /downloads была последней русской страницей сайта; переведена целиком
# (видимый текст, заголовки, мета, подписи кнопок, тексты писем-заявок).
# Ссылки, версии и пути к артефактам при переводе не менялись.
dl = read("downloads/index.html")
check("DL1 downloads/index.html: англоязычная страница "
      "(lang=\"en\", английский <title>, ноль кириллицы)",
      bool(dl)
      and '<html lang="en">' in dl
      and "<title>Download Skipi</title>" in dl
      and not any(ord(ch) in CYRILLIC for ch in dl))

check("DL2 downloads: ссылки на артефакты релизов живы "
      "(github releases + Google Play)",
      bool(dl)
      and dl.count("https://github.com/CaptTymur/") >= 10
      and "https://play.google.com/store/apps/details?id=app.skipi.seafarer" in dl)

dl_stub = read("download.html")
check("DL3 download.html: англоязычная заглушка-переход на /downloads "
      "(meta refresh + canonical + видимая ссылка, lang=\"en\")",
      bool(dl_stub)
      and '<html lang="en">' in dl_stub
      and 'content="0; url=/downloads"' in dl_stub
      and f'<link rel="canonical" href="{SITE}/downloads">' in dl_stub
      and '<a href="/downloads">' in dl_stub
      and not any(ord(ch) in CYRILLIC for ch in dl_stub))


# ── Группа LTD: корпоративный юрблок SKIPI LTD (опубликован 03.09) ─
# Обязательные по закону сведения UK-компании. Волна «только английский»
# не имеет права их повредить, поэтому инвариант зафиксирован тестом.
# Страницы-редиректы (группа R) юрблока не несут — это заглушки.
# /en/for-companies/ и /en/presentation/ ушли отсюда в REDIRECTS
# (owner 03.09, решение 2) — юрблок теперь на верхнеуровневой паре.
LTD_PAGES = (
    "index.html", "en/index.html", "story/index.html", "en/story/index.html",
    "downloads/index.html", "support/index.html", "invest/index.html",
    "for-companies/index.html", "presentation/index.html",
    "terms.html", "privacy.html",
)
LTD_STRINGS = ("SKIPI LTD", "England and Wales", "17433479",
               "182-184 High Street North", "E6 2JA", "info@skipi.app")
for page in LTD_PAGES:
    html = read(page)
    missing = [t for t in LTD_STRINGS if t not in html]
    check(f"LTD1 {page}: юрблок SKIPI LTD полный "
          f"(название, England and Wales, No. 17433479, office, контакт)",
          bool(html) and not missing, f"нет: {missing}")

for page in REDIRECTS:
    check(f"LTD2 {page}: заглушка-редирект без юрблока (ожидаемо)",
          "17433479" not in read(page))


passed = sum(1 for _, ok in results if ok)
total = len(results)
print(f"\n{passed}/{total} checks passed")
sys.exit(0 if passed == total else 1)
