#!/usr/bin/env python3
"""Собирает страницы-презентации по типам профиля: /seafarer/, /crewing/, /chartering/.

Слово владельца 28.11.2026 (дело № 298): таблетки главной объясняют, как пользоваться Skipi с каждым
типом профиля; в конце — создать профиль или войти. Вёрстка — та же, что у /story/ (assets/journey.css).
Запуск: python3 scripts/build_profile_pages.py — перезаписывает три index.html.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCOUNT = "https://account.skipi.app"

PAGES = {
    "seafarer": {
        "title": "Skipi for seafarers — documents, sea service, CV and jobs",
        "description": "How a seafarer uses Skipi: certificates with expiry dates, sea service, CV, document packages for crewing, jobs and port notes. Free for seafarers.",
        "kicker": "Skipi for seafarers",
        "h1": "Your sea career in&nbsp;one&nbsp;place.",
        "lead": "Documents, sea service, CV and jobs — on your phone, on desktop and in the browser.",
        "scenes": [
            ("documents", "Documents", ["Every certificate, with its expiry date.",
                                        "Add a photo or a PDF — Skipi reads it and files it. You see what expires and what is missing."]),
            ("experience", "Sea service and CV", ["Record your contracts once.",
                                                  "Skipi builds your CV and puts together document packages you can send to crewing."]),
            ("jobs", "Jobs and ports", ["Browse vacancies and apply.",
                                        "Read port notes left by other seafarers and add your own."]),
        ],
        "finale": ("Free for seafarers.", "On your phone, on desktop and in the browser — one account."),
    },
    "crewing": {
        "title": "Skipi for crewing — vacancies, candidates and their documents",
        "description": "How a crewing team uses Skipi: vacancies seafarers see, replies with documents attached, candidates kept in one flow. 14-day trial.",
        "kicker": "Skipi for crewing",
        "h1": "From vacancy to&nbsp;a&nbsp;signed&nbsp;crew.",
        "lead": "Vacancies, replies and candidates' documents in one flow instead of mailboxes and spreadsheets.",
        "scenes": [
            ("vacancies", "Vacancies", ["Publish a vacancy once.",
                                        "Seafarers see it in the Skipi jobs feed and reply from their profile."]),
            ("candidates", "Candidates", ["A reply arrives with the seafarer's documents and sea service.",
                                          "Compare it with what the vacancy requires."]),
            ("flow", "Crew flow", ["Every candidate has a stage.",
                                   "The team sees who is waiting, who is cleared and what is still missing."]),
        ],
        "finale": ("Start with a 14-day trial.", "The crewing workplace is being moved into the single Skipi app."),
    },
    "chartering": {
        "title": "Skipi for chartering — cargoes, tonnage and negotiations",
        "description": "How a chartering desk uses Skipi: cargoes and open tonnage, matching, negotiations step by step, letters from your own mail. 14-day trial.",
        "kicker": "Skipi for chartering",
        "h1": "Cargo, tonnage and the&nbsp;deal between them.",
        "lead": "Keep cargoes, open vessels and negotiations in one workplace instead of scattered mail threads.",
        "scenes": [
            ("cargo", "Cargoes and tonnage", ["Enter a cargo or an open position once.",
                                              "Skipi keeps the ports, dates and terms together."]),
            ("matching", "Matching", ["Put a vessel against a cargo.",
                                      "Follow each pair from request to negotiation, step by step."]),
            ("mail", "Letters", ["Skipi prepares the letter; you send it from your own mail.",
                                 "Your records stay in your account."]),
        ],
        "finale": ("Start with a 14-day trial.", "Then a subscription. The chartering workplace arrives in the Skipi app with its next release."),
    },
}

LEGAL = '''<footer class="legal-foot">
    <p class="legal-line">
        SKIPI LTD &middot; Registered in England and Wales &middot; Company No. 17433479<br>
        Registered office: Office 20748, 182-184 High Street North, East Ham, London, United Kingdom, E6 2JA<br>
        Tymur Rudov &mdash; Founder &amp; Director &middot; <a href="mailto:info@skipi.app">info@skipi.app</a> &middot; <a href="tel:+442034320682">+44 20 3432 0682</a>
    </p>
</footer>'''


def page(slug, p):
    url = f"https://skipi.app/{slug}/"
    register = f"{ACCOUNT}/register?profile={slug}"
    # вход с указанием типа: вошедшему с другим типом профиля сайт объяснит это, а не откроет чужой профиль
    login = f"{ACCOUNT}/login?profile={slug}"
    ids = [s[0] for s in p["scenes"]] + ["start"]
    scenes = []
    for n, (sid, name, lines) in enumerate(p["scenes"]):
        body = "\n".join(f'            <p class="line reveal">{line}</p>' for line in lines)
        scenes.append(f'''    <section class="scene" id="{sid}" aria-label="{name}">
        <div class="scene-inner">
            <p class="kicker reveal">{n + 1} of {len(p["scenes"])}</p>
            <h2 class="reveal">{name}</h2>
            <div class="horizon reveal" aria-hidden="true"></div>
{body}
        </div>
        <a class="hint" href="#{ids[n + 1]}" aria-label="Next">↓</a>
    </section>
''')
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{p["title"]}</title>
    <meta name="description" content="{p["description"]}">
    <meta name="author" content="Skipi">
    <meta name="theme-color" content="#ffffff">
    <meta property="og:title" content="{p["kicker"]}">
    <meta property="og:description" content="{p["lead"]}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{url}">
    <meta property="og:site_name" content="Skipi">
    <meta name="twitter:card" content="summary">
    <link rel="canonical" href="{url}">
    <link rel="alternate" hreflang="en" href="{url}">
    <link rel="alternate" hreflang="x-default" href="{url}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/assets/journey.css">
</head>
<body class="story-page">

<header class="voyage-bar">
    <a class="brand" href="/">Skipi<span class="dot">.</span></a>
    <a class="cta cta-bar" href="{login}">Log in <span class="arr">→</span></a>
</header>

<main>
    <section class="scene" id="prologue" aria-label="{p["kicker"]}">
        <div class="scene-inner">
            <p class="kicker reveal">{p["kicker"]}</p>
            <h1 class="reveal">{p["h1"]}</h1>
            <p class="line reveal">{p["lead"]}</p>
        </div>
        <a class="hint" href="#{ids[0]}" aria-label="Next">↓</a>
    </section>

{"".join(s + chr(10) for s in scenes)}    <section class="scene" id="start" aria-label="Start">
        <div class="scene-inner">
            <p class="kicker reveal">Start</p>
            <h2 class="reveal">{p["finale"][0]}</h2>
            <p class="line reveal">{p["finale"][1]}</p>
            <a class="cta cta-big reveal" href="{register}">Create a profile <span class="arr">→</span></a>
            <p class="reveal"><a class="quiet" href="{login}">I already have an account — log in</a></p>
            <p class="reveal"><a class="quiet" href="/">Back home</a></p>
        </div>
    </section>
</main>

{LEGAL}

<script src="/assets/journey.js" defer></script>
</body>
</html>
'''


if __name__ == "__main__":
    for slug, p in PAGES.items():
        out = ROOT / slug / "index.html"
        out.parent.mkdir(exist_ok=True)
        out.write_text(page(slug, p), encoding="utf-8")
        print(out.relative_to(ROOT))
