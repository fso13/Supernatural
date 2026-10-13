#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собирает каталог public/ — то, что уезжает на GitHub Pages.

Структура повторяет корень репозитория, поэтому все относительные ссылки
между редакциями (../site/img/, ../assets/) работают без правок.
"""
import os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "public")

DIRS = ["assets", "site", "site-gumshoe", "site-edge"]
FILES = ["index.html", "README.md"]
PDFS = [
    "bestiary-dnd5e.pdf", "statblocks-dnd5e.pdf", "adventure-dnd5e.pdf",
    "quickstart-gumshoe.pdf", "rules-gumshoe.pdf", "sheet-gumshoe.pdf",
    "adventure-gumshoe.pdf",
    "rules-edge.pdf", "adventure-edge.pdf",
]
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

    dl = os.path.join(OUT, "downloads")
    os.makedirs(dl, exist_ok=True)
    missing = []
    for p in PDFS:
        src = os.path.join(ROOT, p)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dl, p))
        else:
            missing.append(p)

    # GitHub Pages не должен прогонять Jekyll
    open(os.path.join(OUT, ".nojekyll"), "w").close()

    size = tree_size(OUT)
    print("public/ собран: %s" % human(size))
    print("  index.html + %s" % ", ".join(DIRS))
    print("  downloads/: %d PDF" % (len(PDFS) - len(missing)))
    if missing:
        print("  !! не найдены:", ", ".join(missing), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
