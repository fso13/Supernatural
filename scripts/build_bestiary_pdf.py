#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собирает PDF бестиария в оформлении книги правил.

  python3 scripts/build_bestiary_pdf.py            # все записи
  python3 scripts/build_bestiary_pdf.py --limit 12 # проба
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bookkit as bk  # noqa: E402

ROOT = bk.ROOT
SITE = os.path.join(ROOT, "site")
TMP = bk.setup_tmp("bestiary-book")
OUTPUT = os.path.join(ROOT, "downloads", "bestiary-dnd5e.pdf")

PAGE = "a4"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default=OUTPUT)
    a = ap.parse_args()

    print("· верстаю бестиарий")
    import make_bestiary_book as mbb
    items = mbb.build(a.limit, PAGE)
    page = mbb.PAGES[PAGE]

    # список разделов для оглавления и закладок
    sections = []
    cats = {}
    for d in items:
        cats.setdefault(d.get("category", "Иное"), []).append(d)
    for cat in mbb.CAT_ORDER:
        group = cats.get(cat)
        if not group:
            continue
        sections.append(("cat:" + cat, cat, cat))
        for i, d in enumerate(group, 1):
            sections.append(("ch:" + d["slug"], "%d. %s" % (i, d["name_ru"]),
                             "%d%s" % (i, d["name_ru"])))

    print("· печатаю тело — это долго, записей %d" % len(items))
    interior = bk.render("/site/bestiary.html",
                         os.path.join(TMP, "interior.pdf"), 3600000)

    print("· ищу страницы разделов")
    pages, n_pages = bk.locate(interior, sections)
    print("  страниц в теле: %d · найдено разделов: %d/%d"
          % (n_pages, sum(1 for v in pages if v), len(sections)))

    heads, current = [], ""
    for i in range(n_pages):
        for (_k, label, _n), pg in zip(sections, pages):
            if pg == i + 1:
                current = label
        heads.append(current)

    print("· печатаю колонтитулы")
    bk.build_overlay(n_pages, heads, os.path.join(SITE, "bestiary-overlay.html"),
                     title="Бестиарий", tail="D&D 5e",
                     page_w=page["w"], page_h=page["h"])
    overlay = bk.render("/site/bestiary-overlay.html",
                        os.path.join(TMP, "overlay.pdf"), 120000)
    body = bk.stamp(interior, overlay, os.path.join(TMP, "interior-foot.pdf"))

    print("· верстаю обложку и оглавление")
    toc = {}
    for (key, _label, _n), pg in zip(sections, pages):
        if key.startswith("ch:") and pg:
            toc[key[3:]] = pg
    mbb.build(a.limit, PAGE, toc)
    front = bk.render("/site/bestiary-front.html", os.path.join(TMP, "front.pdf"), 90000)

    p = bk.pypdf()
    front_pages = len(p.PdfReader(front).pages)

    print("· склеиваю и ставлю закладки")
    outline = [(label, front_pages + pg - 1)
               for (_k, label, _n), pg in zip(sections, pages) if pg]
    bk.assemble(front, body, a.out, outline)

    total = len(p.PdfReader(a.out).pages)
    print("\nготово: %s" % os.path.relpath(a.out, ROOT))
    print("  %d страниц (вступление %d + бестиарий %d) · %.1f МБ · закладок %d"
          % (total, front_pages, n_pages, os.path.getsize(a.out) / 1e6, len(outline)))


if __name__ == "__main__":
    main()
