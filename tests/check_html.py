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
  DA — страница удаления аккаунта /delete-account/ (07.09, требование
      Google Play и Apple 5.1.1(v)): путь в приложении, письмо, честный
      перечень «что удаляется / что остаётся», привязка из privacy §12
      и ОТРИЦАТЕЛЬНЫЙ чек на обещания тотального удаления.
  LTD — юрблок SKIPI LTD (опубликован 03.09) на месте.
  G — щели, вскрытые мутациями (№200, 05.09): индексируемость и
      видимость витрины, нижний порог слов, Paddle в privacy, страны
      по всему сайту, вывод множества страниц из rglob, sitemap ↔ файлы.

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
# Точечное разрешение ОДНОЙ ссылки, а не хоста (owner 05.09, сигнал
# легитимности Android): страница Skipi Seafarer в Google Play. Хост
# play.google.com в ALLOWED_HOSTS НЕ добавляется — чужой app-id и любой
# <script src> с этого хоста по-прежнему краснеют по I2.
PLAY_URL = "https://play.google.com/store/apps/details?id=app.skipi.seafarer"
ALLOWED_LINKS = {PLAY_URL}

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
    for attr, url in re.findall(r'(href|src)="(https?://[^"]+)"', html):
        if attr == "href" and url in ALLOWED_LINKS:   # exact-URL, не хост
            continue
        hosts.add(url.split("://", 1)[1].split("/", 1)[0].lower())
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
    # A7 (owner 05.09, сигнал легитимности Android): в <main> одна тихая
    # строка «Skipi Seafarer for Android is on Google Play.» — ссылка на
    # словах «Google Play» ведёт на живую страницу магазина (exact-URL
    # PLAY_URL). Это НЕ .cta (I1 держит ровно три SaaS-входа); издатель
    # не называется. A5 сторожит, чтобы строка осталась короткой.
    play_a = re.search(r'<a\b[^>]*\bhref="%s"[^>]*>Google Play</a>'
                       % re.escape(PLAY_URL), entry_main)
    check(f"A7[{loc}] Play-строка в <main>: <a href=PLAY_URL>Google Play</a> "
          f"без класса cta",
          bool(play_a)
          and not re.search(r'class="[^"]*cta[^"]*"', play_a.group(0)),
          "в <main> нет ссылки «Google Play» на PLAY_URL, или у неё .cta")

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

# ── Группа SUP: страница поддержки (2026-08-17, переписана 05.09) ──
# Прежняя редакция страницы объявляла ВТОРОЙ платёжный канал на домене
# продавца: PayPal-donate на ЛИЧНЫЙ адрес и Patreon-рекуррент, при том
# что продавец — SKIPI LTD. Перед подачей в Paddle канал снят целиком
# (BACKLOG №198, DECISIONS (234)), а SUP2/SUP3 ИНВЕРТИРОВАНЫ: сторож
# страницы сохранён, но теперь он сторожит отсутствие, а не наличие.
PAYPAL_DONATE = (
    "https://www.paypal.com/donate/?business=tymur.rudov%40icloud.com"
    "&no_recurring=0&item_name=Support+Skipi+AI+assistant"
    "&currency_code=USD"
)
PATREON = "https://patreon.com/Capt_Tymur"
support = read("support/index.html")
check("SUP1 support/index.html существует", bool(support))
check("SUP2 PayPal-донат снят: ни donate-URL, ни paypal.me, ни слова "
      "paypal на странице поддержки (инвертирован 05.09)",
      bool(support) and PAYPAL_DONATE not in support
      and "paypal" not in support.lower())
check("SUP3 Patreon снят: ни ссылки, ни упоминания "
      "(инвертирован 05.09)",
      bool(support) and PATREON not in support
      and "patreon" not in support.lower())
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

# ── PAY7: второго платёжного канала нет НИГДЕ на домене продавца ───
# Отрицательная проверка по всему сайту, а не по одной странице:
# ревьюер платёжной платформы смотрит домен целиком. Заменяет прежние
# положительные SUP2/SUP3 (BACKLOG №198).
PAY_BANNED = ("paypal", "patreon", "donate")
pay_hits = {}
for f in HTML_FILES:
    low = read(f).lower()
    found = [w for w in PAY_BANNED if w in low]
    if found:
        pay_hits[f] = found
sm_low = read("sitemap.xml").lower()
sm_found = [w for w in PAY_BANNED if w in sm_low]
if sm_found:
    pay_hits["sitemap.xml"] = sm_found
check("PAY7 второго платёжного канала на сайте нет: ни paypal, ни "
      "patreon, ни donate ни в одном .html, ни в sitemap.xml",
      not pay_hits, f"найдено: {pay_hits}")


# ── Группа PAY: витрина продавца перед подачей в Paddle (№198) ─────
# Ревьюер платёжного комплаенса ищет глазами три вещи: страницу цены,
# страницу возвратов и коммерческий раздел в Terms с merchant of
# record. Проверяем их механически, включая щели, из-за которых сьют
# остался бы зелёным при сломанной работе (§K карточки).
PAY_PAGES = {
    "pricing/index.html": "/pricing/",
    "refunds/index.html": "/refunds/",
}
pricing = read("pricing/index.html")
refunds = read("refunds/index.html")

for page, url in PAY_PAGES.items():
    html = read(page)
    head = html.split(">", 2)[1] + ">" if html else ""
    ok = (bool(html)
          and 'lang="en"' in head
          and canonical_of(html) == f"{SITE}{url}"
          and og_url_of(html) == f"{SITE}{url}"
          and hreflangs_of(html) == {"en": f"{SITE}{url}",
                                     "x-default": f"{SITE}{url}"}
          and "http-equiv=\"refresh\"" not in html)
    check(f"PAY1 {page}: содержательная страница на {url} "
          f"(lang=\"en\", canonical/og:url/hreflang → {url})", ok,
          f"canonical={canonical_of(html)} og:url={og_url_of(html)} "
          f"hreflang={hreflangs_of(html)}")

# сверяем ВИДИМЫЙ текст, а не сырой html: иначе строку вроде
# «Merchant of Record» достаточно оставить в <meta description>, и
# проверка промолчит при пустой странице (поймано на adversarial-
# прогоне 05.09 — мутация тела прошла мимо теста).
pricing_text = strip_text(pricing)
refunds_text = strip_text(refunds)

# 05.09-II (три SKU): пины стали фразами, а не словами — «$10» и «per
# seat» оставались зелёными при «Assistant — $5» рядом с «Broker — $10».
# 06.09 (живой каталог Paddle): цена всех трёх позиций = $11.45/мес,
# налог ВКЛЮЧЁН, слово «seat» из названий убрано владельцем (зарезервировано
# под будущий групповой тариф), а платная позиция ассистента называется в
# каталоге «Skipi Seafarer — Premium», не «Skipi Assistant». Paddle требует
# совпадения витрины с каталогом — поэтому имена SKU пинятся тоже.
# Merchant of record в обеих формах: §7 плана вводит строчную в подписи о
# биллинге, раздел «Who you buy from» держит прописную; уронить любую —
# красный. «free tier» — обещание бесплатного уровня с дневным лимитом
# (владелец: платный = без лимита).
PRICING_MUST = ("$11.45 per month", "Skipi Seafarer", "Premium",
                "Skipi Crewing", "Skipi Broker",
                "14-day free trial", "merchant of record",
                "Merchant of Record", "Paddle", "Cancel anytime",
                "free tier")
missing = [t for t in PRICING_MUST if t not in pricing_text]
check("PAY2 /pricing/ (видимый текст): $11.45 per month, три имени SKU как "
      "в каталоге Paddle (Seafarer/Premium, Crewing, Broker), триал, "
      "merchant of record (обе формы), Paddle, Cancel anytime, free tier "
      f"{PRICING_MUST}",
      bool(pricing) and not missing, f"нет: {missing}")

REFUNDS_MUST = ("14 days", "full refund", "Paddle", "info@skipi.app")
missing = [t for t in REFUNDS_MUST if t not in refunds_text]
check("PAY3 /refunds/ (видимый текст): срок, полный возврат, Paddle, "
      f"адрес {REFUNDS_MUST}",
      bool(refunds) and not missing, f"нет: {missing}")

terms = read("terms.html")
TERMS_MUST = ("Merchant of Record", "Paddle.com", "refund", "renew",
              "cancel", "VAT")
missing = [t for t in TERMS_MUST if t not in strip_text(terms)]
nums = [int(n) for n in re.findall(r"<h2>(\d+)\.", terms)]
numbering_ok = nums == list(range(1, len(nums) + 1)) and len(nums) == 22
check("PAY4 terms.html: коммерческий блок есть "
      f"{TERMS_MUST} и разделы идут подряд 1..22 без пропусков и "
      f"дублей (факт {nums})",
      bool(terms) and not missing and numbering_ok,
      f"нет: {missing}; нумерация: {nums}")

in_sitemap = [u for u in PAY_PAGES.values()
              if f"<loc>{SITE}{u}</loc>" not in sitemap]
not_linked = [u for u in PAY_PAGES.values()
              for f in ("index.html", "en/index.html")
              if f'href="{u}"' not in read(f)]
check("PAY5 /pricing/ и /refunds/: обе в sitemap.xml и обе слинкованы "
      "из футера входной страницы (root и en)",
      not in_sitemap and not not_linked,
      f"нет в sitemap: {in_sitemap}; не слинковано: {sorted(set(not_linked))}")

# витрина и инвесторская страница не должны называть разные цены за
# одно и то же место — расхождение ловится механически, не глазами
invest = read("invest/index.html")
# 06.09: цена дробная ($11.45) — регэксп читает и копейки, иначе «$11.45»
# схлопывалось бы в «11» и пин прошёл бы при любой копеечной подмене.
PRICE = "11.45"
PRICE_RE = re.compile(r"(?:Broker|Crewing)[^.<]{0,80}?\$(\d+(?:\.\d+)?)")
pricing_prices = set(PRICE_RE.findall(pricing))
invest_prices = set(PRICE_RE.findall(invest))
check("PAY6 цена Broker/Crewing на /pricing/ и в /invest/ совпадает "
      f"(обе ${PRICE}; факт pricing={sorted(pricing_prices)} "
      f"invest={sorted(invest_prices)})",
      pricing_prices == {PRICE} and invest_prices == {PRICE})

check("PAY8 /support/ — настоящая поддержка: info@skipi.app + ссылки "
      "на /pricing/ и /refunds/",
      bool(support) and "info@skipi.app" in support
      and 'href="/pricing/"' in support
      and 'href="/refunds/"' in support)

# /invest/ стоит в выдаче и спорит с витриной: объявляет четвёртую цену
# «PRO ($5/mo)», которую нельзя купить, и рядом печатает «Paying: 0 ·
# Revenue: $0». Страница остаётся доступной по прямой ссылке для
# инвесторов — из индекса и sitemap она убрана (§F карточки №198).
invest_robots = re.search(r'<meta name="robots" content="([^"]+)"', invest)
invest_robots = invest_robots.group(1).replace(" ", "").lower() \
    if invest_robots else ""
check("PAY9 /invest/ вне индексации: noindex в <meta robots> и нет "
      f"в sitemap.xml (факт robots=\"{invest_robots}\")",
      "noindex" in invest_robots
      and f"<loc>{SITE}/invest/</loc>" not in sitemap)

# Строка приоритетных рынков перечисляла страны поимённо, включая
# Россию, в одном документе с обязательством не нарушать санкции —
# для платёжного андеррайтинга самая дорогая строка на сайте.
# OWNER 05.09: «приоритетный рынок не Россия. Если можно, я бы
# воздержался от этого» → перечисление убрано целиком, юридическая
# функция абзаца сохранена. Тест сторожит, чтобы список не вернулся.
# Georgia в privacy §9 — это НЕ целевой рынок, а раскрытие места
# фактической обработки данных, и оно обязано остаться.
COUNTRY_LIST = ("Russia", "Ukraine", "India", "Philippines",
                "Indonesia", "Sri Lanka")
country_hits = {}
for page in ("terms.html", "privacy.html"):
    found = [c for c in COUNTRY_LIST if c in read(page)]
    if found:
        country_hits[page] = found
check("PAY10 terms.html и privacy.html: приоритетные рынки без "
      f"перечисления стран и без слова Russia {COUNTRY_LIST}",
      not country_hits, f"найдено: {country_hits}")

# Оба юрдокумента содержательно изменены 05.09 (коммерческие разделы
# в terms, Paddle в privacy §8, строка рынков в обоих). Протухшая
# строка «Last updated» на политике — заметный дефект для платёжного
# ревью, поэтому дата закреплена тестом, а не памятью.
LAST_UPDATED = "Last updated: September 5, 2026"
stale = [f for f in ("terms.html", "privacy.html")
         if LAST_UPDATED not in read(f)]
check(f"PAY11 terms.html и privacy.html: строка даты обновлена "
      f"(«{LAST_UPDATED}»)", not stale, f"протухло: {stale}")

# Витрина называла Skipi Assistant просто «free» и не упоминала PRO,
# тогда как PRO продавался тем же PayPal-флоу (флот: paid_price_usd=5
# при enabled=true, webapp/pro.py), а /invest/ печатал «PRO ($5/mo)».
# Платный продукт, названный бесплатным, — ровно то расхождение
# витрины и продукта, которое ищет платёжный андеррайтинг. Первая
# редакция PAY12 (05.09-I) держала на /pricing/ оговорку «not on sale
# while we move to Paddle».
# OWNER 05.09 (DECISIONS (258)): «PRO снимается совсем» → упоминания
# сняты с /pricing/ и /invest/ (включая JSON-LD), а PAY12 ИНВЕРТИРОВАН
# И ГЛОБАЛЕН: слово «PRO» (отдельное слово, регистр учитывается —
# «pro», «PropertyValue» не считаются) = 0 вхождений в ПОЛНОМ html
# каждого файла сайта, не только в видимом тексте: JSON-LD /invest/
# читают роботы.
PRO_WORD = re.compile(r"\bPRO\b")
pro_hits = {f: len(PRO_WORD.findall(read(f))) for f in HTML_FILES}
pro_hits = {f: n for f, n in pro_hits.items() if n}
check("PAY12 слова «PRO» нет ни в одном html сайта (полный html, включая "
      "JSON-LD; owner 05.09 — «PRO снимается совсем»)",
      not pro_hits, f"найдено: {pro_hits}")

# 05.09-II (три SKU): Skipi Assistant стал платной подпиской ($10/мес без
# дневного лимита), а страница называла его «free» и в lede/meta/og писала
# «free for seafarers». Платный продукт, названный бесплатным, — то самое
# расхождение витрины и продукта, которое ищет платёжный андеррайтинг
# (см. PAY12). Негатив по ПОЛНОМУ html (meta/og мимо strip_text), допустимые
# контексты — ЛИТЕРАЛЬНЫЙ кортеж (не регэксп: «free» после любого слова
# прошёл бы), регистр не учитывается. Код — аудит Супервайзора
# AUDIT-2026-09-05-pricing-three-skus-prep.md §C3.
FREE_OK = ("Seafarer &mdash; free",     # абзац Plans: «Skipi Seafarer &mdash; free.»
           "Seafarer app is free",      # lede/meta/og после правки C1
           "free tier", "free trial")
html = read("pricing/index.html")
rest = re.sub(r"<style\b.*?</style>", " ", html, flags=re.S | re.I)
for ok in FREE_OK:
    rest = re.sub(re.escape(ok), " ", rest, flags=re.I)
stray = [re.sub(r"\s+", " ", rest[max(0, m.start()-35):m.end()+12])
         for m in re.finditer(r"\bfree\b", rest, re.I)]
check("PAY13 /pricing/: «free» только у Seafarer и в free tier/free trial "
      f"(кортеж {FREE_OK}; полный html)", not stray, f"лишнее: {stray}")

# 05.09-II (три SKU): PAY6 читает цену только в хвосте «Broker|Crewing …
# $N» — «Skipi Assistant &mdash; $5 per month» проходил мимо (аудит §C4,
# MUT5). Глобальный пин: любая сумма `$N` в видимом тексте /pricing/ равна
# 10 и хотя бы одна есть (пустое множество — тоже красный).
pricing_amounts = set(re.findall(r"\$(\d+(?:\.\d+)?)", pricing_text))
check("PAY14 /pricing/ (видимый текст): все суммы $N на странице = только "
      f"${PRICE}, у всех трёх SKU (факт {sorted(pricing_amounts)})",
      pricing_amounts == {PRICE}, f"суммы: {sorted(pricing_amounts)}")

# ── PAY15 (06.09): налог ВКЛЮЧЁН в цену, и страница это говорит ───
# Аккаунт Paddle настроен на «Price includes tax»: покупатель платит ровно
# опубликованную сумму. Прежняя редакция витрины и terms §12 обещали
# обратное («shown excluding VAT … added at checkout») — это прямая
# неправда о налоге в платёжных документах, самый дорогой класс
# расхождения для андеррайтинга. Негатив — по ВИДИМОМУ тексту обоих
# документов, позитив — фраза о включённом налоге на каждом из них.
TAX_BANNED = ("excluding VAT", "exclude VAT", "excludes VAT",
              "added at checkout", "excluding tax", "plus VAT")
# Позитив требуется от двух документов, которые обязаны объяснить налог;
# НЕГАТИВ — по ВСЕМУ сайту: аудит Супервайзора 06.09 показал, что та же
# ложь, вставленная в /refunds/, оставляла сьют зелёным, пока денилист
# смотрел ровно две страницы.
TAX_MUST = "include VAT and sales tax"
TAX_PAGES = ("pricing/index.html", "terms.html")
tax_bad = {}
for page in HTML_FILES:
    hits = [b for b in TAX_BANNED
            if b.lower() in strip_text(read(page)).lower()]
    if hits:
        tax_bad[page] = hits
tax_silent = [page for page in TAX_PAGES
              if TAX_MUST not in strip_text(read(page))]
check(f"PAY15 цена ВКЛЮЧАЕТ налог: фраза «{TAX_MUST}» есть на {TAX_PAGES}, "
      f"а обещания «налог сверху» нет НИ НА ОДНОЙ странице {TAX_BANNED}",
      not tax_bad and not tax_silent,
      f"обещает налог сверху: {tax_bad}; молчит о включённом: {tax_silent}")

# ── PAY16 (06.09): слова «seat» на сайте нет НИГДЕ ───────────────
# OWNER 06.09: «место» снято из названий и текстов — сегодня продаётся
# соло-подписка одному человеку, а слово «место» зарезервировано под
# будущий групповой тариф с оплатой по числу людей. Пока такого тарифа
# нет, «per seat» на витрине = обещание несуществующей модели продажи и
# расхождение с каталогом Paddle. Негатив по ПОЛНОМУ html всех страниц
# (meta/og/JSON-LD мимо strip_text), как PAY12.
SEAT_RE = re.compile(r"\bseats?\b", re.I)
seat_hits = {f: len(SEAT_RE.findall(read(f))) for f in HTML_FILES}
seat_hits = {f: n for f, n in seat_hits.items() if n}
check("PAY16 слова «seat/seats» нет ни в одном html сайта (owner 06.09: "
      "продаётся соло-подписка, «место» зарезервировано под будущий "
      "групповой тариф)", not seat_hits, f"найдено: {seat_hits}")

# ── PAY17 (06.09): одна цена на ВСЁМ сайте, а не только на витрине ─
# Paddle верифицирует продавца сверкой сайта с каталогом, и цену печатает
# не только /pricing/: «$10/mo» жил ещё в /invest/ (включая JSON-LD, его
# читают роботы) и на /for-companies/. PAY6 сверял только две страницы и
# только хвост «Broker|Crewing … $N».
# Первая редакция этой проверки читала только «$N + месяц» и пропускала
# три подмены (аудит Супервайзора 06.09): «USD 10 per month» (сумма без
# знака), «€11.45» (чужая валюта при верной цифре) и «$120 per year»
# (другой период — годовых позиций в каталоге Paddle нет). Теперь
# разбирается ЛЮБАЯ пара «сумма + период»: валюта обязана быть долларом,
# сумма — каталожной, период — месячным.
PRICE_TOKEN = re.compile(
    r"(?P<pre>[$\u20ac\u00a3]|\bUSD\b|\bEUR\b|\bGBP\b)?\s{0,2}"
    r"(?P<amt>\d+(?:[.,]\d{1,2})?)\s{0,2}"
    r"(?P<post>[$\u20ac\u00a3]|\bUSD\b|\bEUR\b|\bGBP\b"
    r"|dollars?|euros?|pounds?)?\s{0,2}"
    r"(?P<per>/\s?(?:mo|month|yr|year)\b|per\s(?:month|year|seat|user|person)"
    r"|a\s(?:month|year)\b|monthly|annually|yearly)", re.I)
MONTHLY_PER = re.compile(r"(?:/\s?mo|/\s?month|per\smonth|a\smonth|monthly)",
                         re.I)
money_bad, money_seen = {}, 0
for f in HTML_FILES:
    for m in PRICE_TOKEN.finditer(strip_text(read(f))):
        money_seen += 1
        cur = (m.group("pre") or m.group("post") or "").upper()
        amt = m.group("amt").replace(",", ".")
        why = []
        if cur not in ("$", "USD", "DOLLAR", "DOLLARS"):
            why.append(f"валюта «{cur or '---'}»")
        if amt != PRICE:
            why.append(f"сумма {amt}")
        if not MONTHLY_PER.fullmatch(m.group("per").strip()):
            why.append(f"период «{m.group('per').strip()}»")
        if why:
            money_bad.setdefault(f, []).append(
                f"{' '.join(m.group(0).split())} -> {', '.join(why)}")
check(f"PAY17 любая пара «сумма + период» в любом html сайта = ${PRICE} в "
      f"долларах и за МЕСЯЦ (найдено пар: {money_seen}; ловит «USD 10 per "
      "month» без знака, «€11.45», «$120 per year» и JSON-LD)",
      not money_bad and money_seen > 0, f"чужие цены: {money_bad}")

# ── PAY18 (06.09): имя SKU стоит РЯДОМ со своей ценой ────────────
# PAY2 держит имена и цену по отдельности, и этого мало: подмена имени
# в заголовке плана оставляла сьют зелёным (имя жило в другой строке,
# слово «Premium» — в lede). Сверка идёт по ЗАГОЛОВКАМ планов (<strong>),
# а не по всей странице: иначе достаточно одной lede-строки «Crewing и
# Broker по $11.45», и абзац плана мог бы остаться вовсе без цены.
SKU_NAMES = ("Skipi Assistant Premium", "Skipi Crewing", "Skipi Broker")
heads = [re.sub(r"\s+", " ", strip_text(h))
         for h in re.findall(r"<strong>(.*?)</strong>", pricing, re.S)]
unpriced = [n for n in SKU_NAMES
            if not any(n in h and f"${PRICE}" in h for h in heads)]
check(f"PAY18 /pricing/: каждое имя плана {SKU_NAMES} стоит в заголовке "
      f"своего плана вместе с ценой ${PRICE}",
      not unpriced, f"без цены рядом: {unpriced}")

# ── PAY19 (06.09): платный план НЕ назван именем приложения ───────
# Строка «Skipi Seafarer — Premium. $11.45 per month» прямо под строкой
# «Skipi Seafarer — free. The desktop and mobile app» читается как платный
# тир САМОГО приложения, продаваемый мимо покупок App Store — Guideline
# 3.1.1, ровно тот реджект, который дом прошёл четыре раза. Apple письменно
# отвечено, что платных функций в приложении нет; покупается безлимит
# ассистента в веб-кабинете, поэтому платный план называется «Skipi
# Assistant — Premium» (это имя пережило три ревью на этой же странице).
# Путь ревьюера до /pricing/ установлен: первый экран → Register →
# assistant.skipi.app → skipi.app → цены, поэтому проверка глобальная:
# (а) «Premium» не стоит вплотную к «Seafarer» ни в одном html,
# (б) ни один заголовок плана со словом «Seafarer» не несёт цены
# (бесплатная строка «Skipi Seafarer — free» цены не содержит и проходит).
def _dash_norm(t: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"&[mn]dash;", "\u2014", t))


APP_TIER_RE = re.compile(
    r"Seafarer[\s\u2013\u2014.,:;-]{0,4}Premium"
    r"|Premium[\s\u2013\u2014.,:;-]{0,4}Seafarer", re.I)
tier_hits = {f: APP_TIER_RE.findall(_dash_norm(read(f))) for f in HTML_FILES}
tier_hits = {f: h for f, h in tier_hits.items() if h}
priced_app = [re.sub(r"\s+", " ", strip_text(h))
              for h in re.findall(r"<strong>(.*?)</strong>", pricing, re.S)
              if "Seafarer" in h and "$" in h]
check("PAY19 платный план не назван именем мобильного приложения: "
      "«Seafarer» вплотную к «Premium» нет ни в одном html сайта, и ни "
      "один заголовок плана с «Seafarer» не несёт цены (App Store 3.1.1)",
      not tier_hits and not priced_app,
      f"тир приложения: {tier_hits}; платный заголовок: {priced_app}")

# ── PAY20 (06.09): триал не обещает списания по окончании ─────────
# terms §13 обещал «If the trial is not cancelled before it ends, the paid
# subscription begins and the first payment is taken», тогда как в каталоге
# Paddle лежат три ПРОСТЫЕ recurring-подписки без триала: карты у продавца
# в момент триала нет, списать физически нечего. /pricing/ и /refunds/ при
# этом говорили обратное — два взаимоисключающих обещания на одном сайте,
# и худшее стояло в юридическом документе (андеррайтинг Paddle + UK-правила
# автопродления + прямой вред покупателю). Проверка: рядом со словом
# «trial» (окно ±240 символов видимого текста) не должно быть обещания
# списания. Денилист ЛИТЕРАЛЬНЫЙ: «you are not charged» и «you are never
# charged» подстроку «you are charged» не содержат и проверку проходят.
CHARGE_NEAR_TRIAL = ("payment is taken", "first payment", "will be charged",
                     "you are charged", "we charge you", "card is charged",
                     "converts to a paid", "automatically converts",
                     "not cancelled before it ends",
                     "not cancelled before the end",
                     "unless you cancel before")
trial_bad = {}
for f in HTML_FILES:
    low = re.sub(r"\s+", " ", strip_text(read(f))).lower()
    for m in re.finditer(r"\btrials?\b", low):
        win = low[max(0, m.start() - 240):m.end() + 240]
        hits = [b for b in CHARGE_NEAR_TRIAL if b in win]
        if hits:
            trial_bad.setdefault(f, set()).update(hits)
trial_bad = {f: sorted(h) for f, h in trial_bad.items()}
check("PAY20 ни одна страница не обещает списание по окончании триала "
      f"(окно ±240 симв. вокруг «trial», денилист {CHARGE_NEAR_TRIAL}): "
      "триал даёт Skipi при регистрации, платная подписка начинается "
      "только с покупкой",
      not trial_bad, f"обещает списание: {trial_bad}")

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


# ── Группа DA: страница удаления аккаунта (07.09) ─────────────────
# Google Play (support.google.com/googleplay/android-developer/answer/13327111)
# требует в декларации Data safety веб-URL, где пользователь может запросить
# удаление аккаунта, и чтобы путь был «prominently featured and easily
# discoverable» и называл приложение так, как оно называется в сторе.
# Apple 5.1.1(v) требует того же изнутри приложения — путь в 0.4.190:
# Settings → «Skipi account» → «Delete account…».
# Главный инвариант группы — DA5: страница НЕ обещает удаление «везде».
# Журналы мозга ассистента на проде удаление аккаунта не затрагивает
# (skipi-ops RISKS №232b, открыт), поэтому обещание тотальности здесь —
# не стилистика, а неправда в документе, который читает регулятор стора.
DEL_PAGE = "delete-account/index.html"
DEL_URL = "/delete-account/"
delp = read(DEL_PAGE)
delp_head = delp.split(">", 2)[1] + ">" if delp else ""
delp_text = re.sub(r"\s+", " ", strip_text(delp))

check(f"DA1 {DEL_PAGE}: содержательная страница на {DEL_URL} "
      f"(lang=\"en\", <title>, canonical/og:url/hreflang → {DEL_URL}, "
      "не заглушка-редирект)",
      bool(delp)
      and 'lang="en"' in delp_head
      and re.search(r"<title>[^<]{5,}</title>", delp) is not None
      and canonical_of(delp) == f"{SITE}{DEL_URL}"
      and og_url_of(delp) == f"{SITE}{DEL_URL}"
      and hreflangs_of(delp) == {"en": f"{SITE}{DEL_URL}",
                                 "x-default": f"{SITE}{DEL_URL}"}
      and 'http-equiv="refresh"' not in delp,
      f"canonical={canonical_of(delp)} og:url={og_url_of(delp)} "
      f"hreflang={hreflangs_of(delp)}")

# DA2: Google требует назвать приложение ИМЕНЕМ ИЗ ЛИСТИНГА. Проверяем по
# ВИДИМОМУ тексту (в <meta> имя ревьюер не увидит), плюс остальные
# поверхности одного аккаунта.
DEL_SURFACES = ("Skipi Seafarer", "Skipi Assistant", "Skipi Crewing",
                "Skipi Broker")
missing_surface = [n for n in DEL_SURFACES if n not in delp_text]
check("DA2 страница удаления называет приложение именем из листинга "
      f"«Skipi Seafarer» и остальные поверхности одного аккаунта "
      f"{DEL_SURFACES} — в ВИДИМОМ тексте",
      not missing_surface, f"нет в видимом тексте: {missing_surface}")

# DA3: канал запроса = mailto с готовой темой. Отдельно href (кликабельно)
# и отдельно тема письма в видимом тексте (её человек перепишет руками,
# если почтовик не откроется).
DEL_SUBJECT = "Delete my Skipi account"
check("DA3 рабочий mailto:info@skipi.app на странице (href) и тема письма "
      f"«{DEL_SUBJECT}» в видимом тексте",
      'href="mailto:info@skipi.app' in delp and DEL_SUBJECT in delp_text,
      f"mailto-href={'есть' if 'href=\"mailto:info@skipi.app' in delp else 'нет'}; "
      f"тема={'есть' if DEL_SUBJECT in delp_text else 'нет'}")

# DA4: путь внутри приложения — ТОЧНЫЙ, как он записан в заметках ревьюеру
# ASC (skipi-ops DECISIONS 2026-09-07 (372)) и как он выглядит в 0.4.190.
# Сверка по видимому тексту со схлопнутыми пробелами: &rarr;/&ldquo;/&hellip;
# в strip_text становятся пробелами, поэтому пин — три метки подряд.
DEL_PATH_RE = re.compile(r"Settings\s+Skipi account\s+Delete account", re.I)
check("DA4 путь удаления В ПРИЛОЖЕНИИ указан точно: «Settings → Skipi "
      "account → Delete account…» (видимый текст, метки подряд)",
      bool(DEL_PATH_RE.search(delp_text)),
      f"видимый текст: {delp_text[:200]}")

# DA5 — ОТРИЦАТЕЛЬНЫЙ ЧЕК, главный в группе. Обещание тотальности запрещено
# на ЛЮБОЙ странице, которая говорит про удаление аккаунта; множество таких
# страниц ВЫВОДИТСЯ из rglob (урок G6: жёсткий кортеж молчит о новой
# странице), а не перечисляется. Смотрим ПОЛНЫЙ html: meta/og проходят мимо
# strip_text, а обещание в description видно в выдаче.
TOTALITY_BANNED = ("completely", "permanently", "forever", "everywhere",
                   "all systems", "all our systems", "every system",
                   "all copies", "without a trace", "no trace",
                   "erased from all", "wiped from",
                   # 07.09: дрилл M17 показал побег — та же ложь, собранная
                   # синонимами, ни одного слова из списка выше. Добавлены
                   # ровно продемонстрированные идиомы; проверено, что ни одна
                   # из 26 страниц сайта их сегодня не содержит.
                   "not a single byte", "anywhere on our",
                   "any place we operate", "nothing of yours",
                   "nothing is left", "nothing remains", "no copies",
                   "leaves nothing", "for good",
                   "полностью", "навсегда", "без следа")
DELETE_PAGES = [f for f in HTML_FILES
                if re.search(r"delete\w*\W{1,40}account|account\W{1,40}delet",
                             re.sub(r"\s+", " ", strip_text(read(f))), re.I)]
totality_hits = {}
for f in DELETE_PAGES:
    low = read(f).lower()
    hits = [w for w in TOTALITY_BANNED if w in low]
    if hits:
        totality_hits[f] = hits
check("DA5 ни одна страница про удаление аккаунта не обещает удаление "
      f"«везде» (денилист {TOTALITY_BANNED}; страницы выведены из rglob: "
      f"{DELETE_PAGES}): журналы мозга ассистента удаление НЕ затрагивает "
      "(RISKS №232b)",
      bool(DELETE_PAGES) and not totality_hits, f"обещает: {totality_hits}")

# DA6: адрес в sitemap.xml — Google находит страницу не только по ссылке
# из Play Console. (G6a держит то же для всех содержательных страниц;
# здесь — именной пин, чтобы удаление строки читалось как «сломали
# удаление аккаунта», а не как «сломали общий инвариант».)
check(f"DA6 sitemap.xml содержит {SITE}{DEL_URL}",
      f"<loc>{SITE}{DEL_URL}</loc>" in sitemap)

# DA7: якорная ссылка из §12 privacy — дословное требование Google для
# случая, когда путь удаления объясняется в политике: «the data deletion
# section should be highlighted and reasonably prominent (for example,
# through an anchor link)». Пин — именно §12, а не «где-нибудь в файле».
privacy_html = read("privacy.html")
m12 = re.search(r"<h2>12\..*?(?=<h2>13\.)", privacy_html, flags=re.S)
sec12 = m12.group(0) if m12 else ""
check("DA7 privacy.html §12: якорная ссылка на страницу удаления "
      f"(href=\"{DEL_URL}\" внутри секции «Your Choices and Rights»)",
      bool(sec12) and f'href="{DEL_URL}"' in sec12,
      "секция 12 не найдена" if not sec12 else "ссылки в §12 нет")

# DA8: честность — положительная половина DA5. Страница обязана НАЗВАТЬ то,
# что переживает удаление: платёжные записи (GDPR 17(3)(b), обезличиваются)
# и служебные журналы сервиса (RISKS №232b). Без этого блока страница
# формально «не врёт», но умалчивает — а именно умолчание и разбирают
# в споре с пользователем.
DEL_KEPT_MUST = ("What is kept", "Payment records", "Working logs")
kept_missing = [t for t in DEL_KEPT_MUST if t not in delp_text]
check("DA8 страница честно перечисляет, что ОСТАЁТСЯ после удаления: "
      f"{DEL_KEPT_MUST} (платёжные записи — GDPR 17(3)(b); служебные "
      "журналы — RISKS №232b)",
      not kept_missing, f"нет в видимом тексте: {kept_missing}")

# DA9: страница статическая — ни JS, ни форм, ни сторонних ресурсов
# (карточка 07.09: «без JS, без форм с отправкой, без сторонних скриптов»).
del_ext = external_hosts(delp) - ALLOWED_HOSTS
check("DA9 страница удаления статическая: нет <script>, нет <form>, "
      "нет внешних хостов сверх разрешённых",
      bool(delp) and "<script" not in delp.lower()
      and "<form" not in delp.lower() and not del_ext,
      f"внешние хосты: {del_ext}")

# DA10 (07.09) — СРОКИ ХРАНЕНИЯ. Форма Data safety, в которую менеджер
# вписывает этот URL, дословно требует, чтобы по ссылке содержалась
# информация «о том, данные каких типов будут удалены или сохранены, И О
# СРОКАХ ХРАНЕНИЯ». Без срока у сохраняемой категории ссылка не выполняет
# требование, под которое её вписывают, — то есть это блокер декларации,
# а не стилистика. Проверка не читает сам срок (число или критерий —
# решение автора), она держит СТРУКТУРУ: у каждого пункта «что остаётся»
# есть явная строка «How long:». Счёт по верхнеуровневым <li><strong> —
# вложенные подпункты попадают в кусок своего родителя, поэтому пункт,
# у которого срок стоит только в подпункте, всё равно засчитывается.
m_kept = re.search(r"<h2>What is kept, and why</h2>(.*?)<h2>", delp, flags=re.S)
kept_block = m_kept.group(1) if m_kept else ""
kept_chunks = kept_block.split("<li><strong>")[1:]
kept_no_term = [re.sub(r"\s+", " ", strip_text(c.split("</strong>")[0]))[:40]
                for c in kept_chunks if "How long:" not in c]
check("DA10 у КАЖДОЙ сохраняемой категории на странице удаления назван срок "
      "хранения или критерий («How long:») — дословное требование формы "
      f"Data safety (пунктов «что остаётся»: {len(kept_chunks)})",
      bool(kept_block) and len(kept_chunks) >= 5 and not kept_no_term,
      f"без срока: {kept_no_term}" if kept_block else "раздел «What is kept» не найден")

# DA11 (07.09) — ДВЕ НЕПРАВДЫ, снятые по аудиту 07.09
# (skipi-supervisor/audits/AUDIT-2026-09-07-play-datasafety-account-declaration.md).
# Обе были правдоподобны и обе опровергаются кодом, поэтому держим их
# исправленное состояние пином, а не памятью:
#  (а) «Anything already delivered … is in their hands» перекладывало на
#      получателя то, что физически лежит у НАС: crewing_bundles/<uid> ключуется
#      ИЗВЛЕКАТЕЛЕМ, и распакованный плейнтекстовый CV моряка остаётся на нашем
#      сервере под каталогом агентства (webapp/crewing_inbox.delete_user_bundles,
#      skipi-ops DECISIONS (383), RISKS №233b);
#  (б) «переписки удаляются» в одном разделе против «журналы ассистента не
#      затрагиваются» в другом читалось как два взаимоисключающих утверждения;
#      правда — ВТОРАЯ КОПИЯ тех же вопросов и ответов в журналах (RISKS №232b).
# Каждая половина ищется В СВОЁМ разделе, а не «где-нибудь на странице»:
# первая редакция искала «on our server» по всей странице и ловила его на
# соседней фразе списка «что удаляется» («files kept for your account on our
# serverS») — то есть мутация, вернувшая ложь «в его руках», оставляла чек
# зелёным. Проверка, которую нельзя провалить мутацией, ничего не проверяет.
m_del = re.search(r"<h2>What is deleted</h2>(.*?)<h2>", delp, flags=re.S)
deleted_block = re.sub(r"\s+", " ", strip_text(m_del.group(1) if m_del else ""))
kept_flat = re.sub(r"\s+", " ", strip_text(kept_block))
honesty_missing = []
if not re.search(r"working folder on our server", kept_flat, re.I):
    honesty_missing.append(
        "(а) в разделе «что остаётся» не сказано, что распакованная копия "
        "лежит в рабочем каталоге получателя НА НАШЕМ СЕРВЕРЕ")
if not re.search(r"second copy", deleted_block, re.I):
    honesty_missing.append(
        "(б) в разделе «что удаляется» не сказано, что у вопросов и ответов "
        "есть ВТОРАЯ КОПИЯ в журналах сервиса")
check("DA11 обе неправды, снятые аудитом 07.09, не вернулись: страница "
      "говорит, что копия отправленного остаётся НА НАШЕМ СЕРВЕРЕ у "
      "получателя, и что вопросы/ответы имеют ВТОРУЮ КОПИЮ в журналах "
      "сервиса (RISKS №232b, №233b)",
      not honesty_missing, "; ".join(honesty_missing))


# ── Группа G: щели сьюта, вскрытые мутациями (BACKLOG №200; аудиты 05.09) ─
# Каждая проверка заведена под одну конкретную мутацию, на которой сьют
# оставался зелёным (M36, M37, M38, M40, M29, M41a/M41b, M42). Критерий
# узости — «ровно одна красная»: названная мутация красит только свою
# проверку, не соседнюю.

# G1 (M36): обратное к PAY9 состояние было запинено только для /invest/ —
# noindex,nofollow на витрине прошёл бы молча.
def robots_of(html: str) -> str:
    m = re.search(r'<meta\b[^>]*\bname="robots"[^>]*>', html, flags=re.I)
    c = re.search(r'\bcontent="([^"]*)"', m.group(0), flags=re.I) if m else None
    return c.group(1).replace(" ", "").lower() if c else ""


robots_bad = {p: robots_of(read(p)) for p in PAY_PAGES}
robots_bad = {p: v for p, v in robots_bad.items()
              if "noindex" in v or "nofollow" in v}
check("G1 /pricing/ и /refunds/ индексируемы: <meta robots> отсутствует "
      "или без noindex/nofollow", not robots_bad, f"факт: {robots_bad}")

# G2 (M37): strip_text читает DOM, а не рендер — <body style="display:none">
# оставлял PAY2/PAY3 зелёными. Это ДЕНИЛИСТ известных способов спрятать
# страницу целиком, а НЕ доказательство видимости: смотрим только
# открывающие теги <body>/<main> и наличие <template> на PAY_PAGES.
HIDE_DENYLIST = ("display:none", "visibility:hidden", "height:0", "opacity:0")


def hidden_by(html: str) -> list:
    hits = []
    for tag in re.findall(r"<(?:body|main)\b[^>]*>", html, flags=re.I):
        flat = re.sub(r"\s+", "", tag).lower()   # 'display: none' → 'display:none'
        hits += [t for t in HIDE_DENYLIST
                 if re.search(re.escape(t) + r"(?![.\d])", flat)]  # opacity:0.9 — не 0
        if re.search(r"\shidden(?=[\s>/=])", tag, flags=re.I):     # атрибут, не класс
            hits.append("hidden")
    if re.search(r"<template\b", html, flags=re.I):
        hits.append("<template>")
    return hits


hide_hits = {p: hidden_by(read(p)) for p in PAY_PAGES}
hide_hits = {p: h for p, h in hide_hits.items() if h}
check("G2 /pricing/ и /refunds/ не спрятаны целиком — ДЕНИЛИСТ на "
      "<body>/<main>: display:none, visibility:hidden, height:0, opacity:0, "
      "атрибут hidden, <template> (денилист, не доказательство видимости)",
      not hide_hits, f"факт: {hide_hits}")

# G3 (M38): нижнего порога содержательности не было — <head> + строка-суп
# с ключевыми словами + юрфутер проходили PAY1+PAY2+LTD1. Порог ТОЛЬКО для
# PAY_PAGES (у входных — ВЕРХНИЙ бюджет A5). Замеры word_count всей
# страницы 05.09: /pricing/ = 423 (436 до снятия PRO), /refunds/ = 322,
# минимальный суп ≈ 30 слов; 150 — с запасом в обе стороны.
PAY_WORD_FLOOR = 150
pay_wc = {p: word_count(read(p)) for p in PAY_PAGES}
thin = {p: n for p, n in pay_wc.items() if n < PAY_WORD_FLOOR}
check(f"G3 /pricing/ и /refunds/ содержательны: ≥ {PAY_WORD_FLOOR} слов "
      f"видимого текста (факт "
      f"{' '.join(f'{PAY_PAGES[p]}={n}' for p, n in pay_wc.items())})",
      not thin, f"мало слов: {thin}")

# G4 (M40): ту же претензию — Paddle как Merchant of Record — в terms
# сторожит PAY4; абзац privacy §8 не сторожил никто.
privacy_text = strip_text(read("privacy.html"))
check("G4 privacy.html (видимый текст): Paddle назван Merchant of Record "
      "(§8; та же претензия, что PAY4 держит в terms)",
      "Paddle" in privacy_text
      and "merchant of record" in privacy_text.lower())

# G5 (M29): PAY10 привязан к двум документам — «Russia» на /for-companies/
# прошла бы. Тот же COUNTRY_LIST, но по всему сайту, как PAY7.
country_hits_all = {}
for f in HTML_FILES:
    found = [c for c in COUNTRY_LIST if c in read(f)]
    if found:
        country_hits_all[f] = found
check(f"G5 ни один html сайта не называет страны {COUNTRY_LIST} "
      "(глобально по rglob, как PAY7; PAY10 держит только terms/privacy)",
      not country_hits_all, f"найдено: {country_hits_all}")

# G6 (M41a/M41b): LTD_PAGES, PAY_PAGES, REDIRECTS — жёсткие кортежи; новая
# англоязычная страница выходила без юрблока, без canonical и вне sitemap
# молча. Множество содержательных страниц ВЫВОДИТСЯ из rglob минус явные
# исключения, а не перечисляется: REDIRECTS (заглушки), download.html
# (заглушка DL3) и google0dd040fd25f43a16.html (подтверждение Search
# Console — удалять нельзя; canonical и юрблока не несёт).
# G6a — canonical (ПРИСУТСТВИЕ, не равенство своему URL: зеркала /en/* по
# L4/L5 указывают на корень) + адрес в sitemap.xml (исключение — явный
# список, не robots: /invest/ по PAY9). og:url и hreflang НЕ требуются —
# их нет у части легитимных страниц.
# G6b — юрблок: цикл LTD1 ниже обходит CONTENT_PAGES сверх именованного
# LTD_PAGES (отдельной строки нет намеренно — она дублировала бы LTD1).
NON_CONTENT = ("download.html", "google0dd040fd25f43a16.html")
CONTENT_PAGES = [f for f in HTML_FILES
                 if f not in REDIRECTS and f not in NON_CONTENT]
SITEMAP_EXEMPT = ("invest/index.html",)   # /invest/ — намеренно вне sitemap


def sitemap_locs_of(rel: str) -> tuple:
    """Допустимые <loc> файла. x/index.html → /x/ И /x: sitemap держит
    /downloads без слэша, и DL3 пинит именно этот адрес."""
    if rel == "index.html":
        return (f"{SITE}/",)
    if rel.endswith("/index.html"):
        d = rel[:-len("/index.html")]
        return (f"{SITE}/{d}/", f"{SITE}/{d}")
    return (f"{SITE}/{rel}",)


no_canonical = [f for f in CONTENT_PAGES
                if not re.search(r'<link\b[^>]*\brel="canonical"', read(f))]
not_in_sitemap = [f for f in CONTENT_PAGES if f not in SITEMAP_EXEMPT
                  and not any(f"<loc>{u}</loc>" in sitemap
                              for u in sitemap_locs_of(f))]
check(f"G6a все {len(CONTENT_PAGES)} содержательных страниц (rglob минус "
      f"REDIRECTS и {NON_CONTENT}): есть <link rel=\"canonical\"> и адрес "
      "в sitemap.xml (кроме /invest/)",
      bool(CONTENT_PAGES) and not no_canonical and not not_in_sitemap,
      f"без canonical: {no_canonical}; нет в sitemap: {not_in_sitemap}")


# G7 (M42): соответствие sitemap ↔ файлы не проверялось ни в одну сторону —
# несуществующий URL в sitemap проходил. Каждый <loc> → существующий файл:
# «/» → index.html; «/x/» → x/index.html; «/x.html» → x.html;
# «/x» без слэша и без .html → x/index.html (так в sitemap живёт /downloads).
def file_of_loc(loc: str):
    if not loc.startswith(f"{SITE}/"):
        return None                       # чужой хост — тоже дефект
    path = loc[len(SITE):]
    if path == "/":
        return "index.html"
    if path.endswith(".html"):
        return path.lstrip("/")
    return path.strip("/") + "/index.html"


sm_locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", sitemap)
ghost = {}
for loc in sm_locs:
    rel = file_of_loc(loc)
    if rel is None or not (ROOT / rel).is_file():
        ghost[loc] = rel
check(f"G7 sitemap.xml: каждый из {len(sm_locs)} <loc> ведёт на "
      "существующий файл (/ → index.html; /x/ и /x → x/index.html; "
      "/x.html → x.html)",
      bool(sm_locs) and not ghost, f"нет файла: {ghost}")


# ── Группа LTD: корпоративный юрблок SKIPI LTD (опубликован 03.09) ─
# Обязательные по закону сведения UK-компании. Волна «только английский»
# не имеет права их повредить, поэтому инвариант зафиксирован тестом.
# Страницы-редиректы (группа R) юрблока не несут — это заглушки.
# /en/for-companies/ и /en/presentation/ ушли отсюда в REDIRECTS
# (owner 03.09, решение 2) — юрблок теперь на верхнеуровневой паре.
# 05.09: список был хардкодом из 11 страниц — новые страницы вышли бы
# без юрблока, а тест смолчал бы. Добавлены /pricing/, /refunds/ и
# ip-notice.html (юрблока не имел вовсе, контакт вёл на чужой домен).
# 05.09-II (№200, G6b): механизм починен. LTD_PAGES остаётся именованным
# МИНИМУМОМ — пином существования каждой из 14 страниц (удалённая
# страница краснеет; ip-notice.html иначе не сторожит никто), а цикл LTD1
# сверх него обходит все CONTENT_PAGES, выведенные из rglob (группа G):
# новая страница без юрблока краснеет сама, без правки списка.
LTD_PAGES = (
    "index.html", "en/index.html", "story/index.html", "en/story/index.html",
    "downloads/index.html", "support/index.html", "invest/index.html",
    "for-companies/index.html", "presentation/index.html",
    "pricing/index.html", "refunds/index.html",
    "terms.html", "privacy.html", "ip-notice.html",
)
LTD_STRINGS = ("SKIPI LTD", "England and Wales", "17433479",
               "182-184 High Street North", "E6 2JA", "info@skipi.app")
for page in LTD_PAGES + tuple(p for p in CONTENT_PAGES
                              if p not in LTD_PAGES):   # G6b
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
