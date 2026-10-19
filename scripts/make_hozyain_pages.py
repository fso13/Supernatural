#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собирает страницы приключения «Хозяин Леса» для трёх редакций сайта.

Исходники лежат в hozyain-lesa/. Конвертер md2site ожидает пути к картинкам
относительно выходной страницы, поэтому префикс подставляется по месту.

  python3 scripts/make_hozyain_pages.py
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "hozyain-lesa")

NAV_D = ("Бестиарий|index.html,Приключение|adventure.html,"
         "Хозяин Леса|adventure-hozyain.html,GUMSHOE →|../site-gumshoe/index.html")
NAV_G = ("Быстрый старт|quickstart.html,Правила|rules.html,Лист персонажа|sheet.html,"
         "Приключение|adventure.html,← Бестиарий|index.html,Все редакции|../index.html")
NAV_E = ("← Бестиарий|index.html,Правила|rules.html,"
         "Приключение|adventure.html,Все редакции|../index.html")

DL_D = ("«Хозяин Леса», PDF|../downloads/adventure-hozyain-dnd5.pdf;"
        "Бестиарий D&D — 728 страниц, PDF|../downloads/bestiary-dnd5e.pdf")
DL_G = ("«Хозяин Леса», PDF|../downloads/adventure-hozyain-gumshoe.pdf;"
        "«Охотники» — правила, PDF|../downloads/rules-gumshoe.pdf;"
        "Бестиарий охотника, PDF|../downloads/bestiary-gumshoe.pdf")
DL_GE = ("«Хозяин Леса»: две серии, PDF|../downloads/adventure-hozyain-dve-serii.pdf;"
         "«Охотники» — правила, PDF|../downloads/rules-gumshoe.pdf;"
         "Быстрый старт, PDF|../downloads/quickstart-gumshoe.pdf")
DL_E = ("«Хозяин Леса», PDF|../downloads/adventure-hozyain-edge.pdf;"
        "Правила «The Edge!», PDF|../downloads/rules-edge.pdf")

# куда ведут перекрёстные ссылки из каждой версии
LINKS_BASE = {
    "00-syuzhet.md": None,                     # канон на сайт не выложен
    "hozyain-lesa-supernatural.md": None,      # версия Cortex не публикуется
}
LINKS_BY_PAGE = {
    "site/": {"hozyain-lesa-dnd5.md": "adventure-hozyain.html",
              "hozyain-lesa-gumshoe.md": "../site-gumshoe/adventure-hozyain.html",
              "hozyain-lesa-edge.md": "../site-edge/adventure-hozyain.html",
              "hozyain-lesa-dve-serii.md": "../site-gumshoe/adventure-hozyain-dve-serii.html"},
    "site-gumshoe/": {"hozyain-lesa-gumshoe.md": "adventure-hozyain.html",
                      "hozyain-lesa-dve-serii-gumshoe.md": "adventure-hozyain-dve-serii.html",
                      "hozyain-lesa-dnd5.md": "../site/adventure-hozyain.html",
                      "hozyain-lesa-edge.md": "../site-edge/adventure-hozyain.html"},
    "site-edge/": {"hozyain-lesa-edge.md": "adventure-hozyain.html",
                   "hozyain-lesa-dnd5.md": "../site/adventure-hozyain.html",
                   "hozyain-lesa-gumshoe.md": "../site-gumshoe/adventure-hozyain.html"},
}

# (исходник, выходная страница, префикс картинок, title, short, thin, subtitle, nav, active, dl)
PAGES = [
    ("hozyain-lesa-dnd5.md", "site/adventure-hozyain.html", "img/",
     "Хозяин Леса — приключение D&D 5e", "Хозяин Леса", "хоррор в Чёрном Бору · D&D 5e",
     "Деревня, трактир, часовня из живых деревьев и выбор: убить или освободить",
     NAV_D, "Хозяин Леса", DL_D),
    ("hozyain-lesa-gumshoe.md", "site-gumshoe/adventure-hozyain.html", "../site/img/",
     "Хозяин Леса — приключение GUMSHOE | Охотники", "Хозяин Леса", "дело в Чёрном Бору · GUMSHOE",
     "Национальный парк Блэкпайн, языческий бог леса и нож-якорь: улики, Стабильность и правило твари",
     NAV_G, "Приключение", DL_G),
    ("hozyain-lesa-dve-serii-gumshoe.md", "site-gumshoe/adventure-hozyain-dve-serii.html", "../site/img/",
     "Хозяин Леса: две серии — GUMSHOE | Охотники", "Хозяин Леса", "две серии · GUMSHOE",
     "То же дело, разложенное на две сессии: клиффхэнгер между ними и цена во второй",
     NAV_G, "Приключение", DL_GE),
    ("hozyain-lesa-edge.md", "site-edge/adventure-hozyain.html", "../site/img/",
     "Хозяин Леса — приключение The Edge!", "Хозяин Леса", "хоррор в Чёрном Бору · The Edge!",
     "ЧЦ, раны и стресс: светлый и тёмный кубик против Хозяина Леса",
     NAV_E, "Приключение", DL_E),
]


def prepare(src_name, prefix, out_path):
    """Префикс картинок и перекрёстные ссылки под выходную страницу."""
    p = os.path.join(SRC, src_name)
    if not os.path.exists(p):
        return None
    s = open(p, encoding="utf-8").read()
    s = s.replace("../site/img/", "\x00IMG\x00").replace("\x00IMG\x00", prefix)

    folder = os.path.dirname(out_path).rstrip("/") + "/"
    mapping = dict(LINKS_BASE)
    mapping.update(LINKS_BY_PAGE.get(folder, {}))

    def repl(m):
        label, target = m.group(1), m.group(2)
        name = os.path.basename(target)
        dest = mapping.get(name)
        if dest is None:
            return "*%s*" % label      # публиковать нечего — оставляем текстом
        return "[%s](%s)" % (label, dest)

    s = re.sub(r"\[([^\]]+)\]\((?:[^)]*/)?([A-Za-z0-9._-]+\.md)\)", repl, s)
    return s


def main():
    made = 0
    for src_name, out, prefix, title, short, thin, sub, nav, act, dl in PAGES:
        text = prepare(src_name, prefix, out)
        if text is None:
            print("  пропуск (нет файла): %s" % src_name)
            continue
        tmp = os.path.join("/tmp", "hl_" + src_name)
        open(tmp, "w", encoding="utf-8").write(text)
        cmd = [sys.executable, os.path.join(ROOT, "scripts", "md2site.py"), tmp,
               os.path.join(ROOT, out), "--title", title, "--title-short", short,
               "--title-thin", thin, "--subtitle", sub, "--nav", nav,
               "--active", act, "--dl", dl]
        r = subprocess.run(cmd, capture_output=True, text=True)
        print("  " + (r.stdout.strip() or r.stderr.strip()[:200]))
        made += 1
    print("страниц собрано: %d" % made)


if __name__ == "__main__":
    main()
