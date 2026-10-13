#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собирает каталог public/ — то, что уезжает на GitHub Pages.

Структура повторяет корень репозитория, поэтому все относительные ссылки
между редакциями (../site/img/, ../assets/) работают без правок.
"""
import os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "public")

DIRS = ["assets", "downloads", "site", "site-gumshoe", "site-edge"]
FILES = ["index.html", "README.md"]
# PDF лежат в downloads/ в корне репозитория — копируются в артефакт как есть,
# поэтому ссылки вида downloads/x.pdf работают и локально, и на Pages
# site/book.html и site/statblocks.html — тяжёлые печатные страницы D&D (5,4 МБ);
# в книге D&D они не нужны, там те же материалы лежат в downloads/
SKIP = shutil.ignore_patterns("__pycache__", ".DS_Store", "*.pyc", "book-overlay.html")
SKIP_SITE = shutil.ignore_patterns("__pycache__", ".DS_Store", "*.pyc",
                                   "book.html", "statblocks.html", "book-overlay.html")


def human(n):
    for u in ("Б", "КБ", "МБ", "ГБ"):
        if n < 1024:
            return "%.1f %s" % (n, u)
        n /= 1024
    return "%.1f ТБ" % n


def tree_size(path):
    total = 0
    for base, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(base, f))
            except OSError:
                pass
    return total


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    for d in DIRS:
        src = os.path.join(ROOT, d)
        if not os.path.isdir(src):
            print("  !! нет каталога:", d, file=sys.stderr)
            continue
        shutil.copytree(src, os.path.join(OUT, d),
                        ignore=SKIP_SITE if d == "site" else SKIP)

    for f in FILES:
        src = os.path.join(ROOT, f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(OUT, f))

    # GitHub Pages не должен прогонять Jekyll
    open(os.path.join(OUT, ".nojekyll"), "w").close()

    size = tree_size(OUT)
    print("public/ собран: %s" % human(size))
    print("  index.html + %s" % ", ".join(DIRS))
    pdfs = sorted(f for f in os.listdir(os.path.join(OUT, "downloads")) if f.endswith(".pdf")) \
        if os.path.isdir(os.path.join(OUT, "downloads")) else []
    print("  downloads/: %d PDF" % len(pdfs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
