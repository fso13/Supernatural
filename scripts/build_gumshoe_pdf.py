#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собирает PDF книги правил «Охотники».

  1. верстает книгу (make_gumshoe_book.py)
  2. печатает тело книги                       -> interior.pdf
  3. читает interior.pdf и находит страницы глав
  4. печатает слой колонтитулов, по странице   -> overlay.pdf
  5. накладывает колонтитулы
  6. печатает обложку, титул и оглавление с номерами страниц
  7. склеивает и ставит закладки               -> rules-gumshoe.pdf

Нужен запущенный локальный сервер:  bash scripts/serve.sh
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bookkit as bk  # noqa: E402

ROOT = bk.ROOT
SITE = os.path.join(ROOT, "site-gumshoe")
TMP = bk.setup_tmp("gumshoe-book")
OUTPUT = os.path.join(ROOT, "downloads", "rules-gumshoe.pdf")


def book_structure():
    """Список разделов в порядке книги: (kind, label, поисковая строка)."""
    import make_gumshoe_book as mgb
    md = open(mgb.SRC, encoding="utf-8").read()
    body, _ = mgb.convert(md)
    items = []
    for b in mgb.split_chapters(body):
        kind = mgb.classify(b)
        if kind == "front":
            items.append(("chapter", "Введение. Что это за игра", "чтоэтозаигра"))
        elif kind == "part":
            if b["title"].upper() == "ПРИЛОЖЕНИЯ":
                items.append(("part", "ПРИЛОЖЕНИЯ. Справочник хранителя", "справочникхранителя"))
            else:
                name = re.sub(r"^ЧАСТЬ\s+\w+\.\s*", "", b["title"])
                items.append(("part", b["title"], "часть" + name))
        else:
            what, num, name = mgb.chapter_bits(b["title"])
            items.append(("chapter", b["title"],
                          ("глава" if what == "Глава" else "приложение") + num + name))
    return items


def main():
    print("· верстаю книгу")
    subprocess.check_call([sys.executable, os.path.join(ROOT, "scripts", "make_gumshoe_book.py")],
                          stdout=subprocess.DEVNULL)
    items = book_structure()

    print("· печатаю тело книги — это несколько минут")
    interior = bk.render("/site-gumshoe/book.html", os.path.join(TMP, "interior.pdf"), 300000)

    print("· ищу страницы разделов")
    pages, n_pages = bk.locate(interior, items)
    print("  страниц в теле: %d · найденных разделов: %d/%d"
          % (n_pages, sum(1 for v in pages if v), len(items)))

    heads, current = [], ""
    for i in range(n_pages):
        for (_k, label, _n), pg in zip(items, pages):
            if pg == i + 1:
                current = label
        heads.append(current)

    print("· печатаю колонтитулы")
    bk.build_overlay(n_pages, heads, os.path.join(SITE, "book-overlay.html"),
                     title="Охотники", tail="GUMSHOE")
    overlay = bk.render("/site-gumshoe/book-overlay.html",
                        os.path.join(TMP, "overlay.pdf"), 60000)
    body = bk.stamp(interior, overlay, os.path.join(TMP, "interior-foot.pdf"))

    print("· верстаю обложку и оглавление с номерами страниц")
    import make_gumshoe_book as mgb
    toc = [(kind, label, "", pg or "") for (kind, label, _n), pg in zip(items, pages)]
    open(os.path.join(SITE, "book-front.html"), "w", encoding="utf-8").write(
        mgb.build_front(toc, True))
    front = bk.render("/site-gumshoe/book-front.html", os.path.join(TMP, "front.pdf"), 60000)
    p = bk.pypdf()
    front_pages = len(p.PdfReader(front).pages)

    print("· склеиваю и ставлю закладки")
    outline = [(label, front_pages + pg - 1)
               for (_k, label, _n), pg in zip(items, pages) if pg]
    bk.assemble(front, body, OUTPUT, outline)

    total = len(p.PdfReader(OUTPUT).pages)
    print("\nготово: %s" % os.path.relpath(OUTPUT, ROOT))
    print("  %d страниц (вступление %d + книга %d) · %.1f МБ · закладок %d"
          % (total, front_pages, n_pages, os.path.getsize(OUTPUT) / 1e6, len(outline)))


if __name__ == "__main__":
    main()
