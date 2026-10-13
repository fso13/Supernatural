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
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
BASE = os.environ.get("BASE", "http://127.0.0.1:8770")
SITE = os.path.join(ROOT, "site-gumshoe")
OUTPUT = os.path.join(ROOT, "rules-gumshoe.pdf")
TMP = os.path.join(tempfile.gettempdir(), "gumshoe-book")


def pypdf():
    try:
        import pypdf
        return pypdf
    except ImportError:
        pass
    vendor = os.path.join(ROOT, "scripts", "_vendor")
    if vendor not in sys.path:
        sys.path.insert(0, vendor)
    try:
        import pypdf
        return pypdf
    except ImportError:
        print("  ставлю pypdf в scripts/_vendor")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet",
                               "--target", vendor, "pypdf"])
        sys.path.insert(0, vendor)
        import pypdf
        return pypdf


def render(url, out, budget=180000):
    profile = tempfile.mkdtemp(prefix="gpdf_")
    try:
        proc = subprocess.Popen(
            [CHROME, "--headless", "--disable-gpu", "--no-sandbox",
             "--user-data-dir=" + profile, "--no-first-run", "--no-pdf-header-footer",
             "--virtual-time-budget=%d" % budget, "--print-to-pdf=" + out, BASE + url],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            proc.wait(timeout=900)
        except subprocess.TimeoutExpired:
            proc.kill()
            raise SystemExit("Chrome не успел напечатать %s" % url)
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    if not os.path.exists(out):
        raise SystemExit("Chrome не создал %s" % out)
    return out


def norm(s):
    return re.sub(r"[^0-9a-zа-яё]", "", s.lower())


# ─────────────────────────────────────────────────────────────────────────────

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
            items.append(("chapter", b["title"], ("глава" if what == "Глава" else "приложение")
                          + num + name))
    return items


def locate(pdf_path, items):
    """Номер страницы (с 1) для каждого раздела."""
    p = pypdf()
    reader = p.PdfReader(pdf_path)
    pages = [norm(pg.extract_text() or "") for pg in reader.pages]
    found = []
    for kind, label, needle in items:
        n = norm(needle)
        page = None
        for i, text in enumerate(pages):
            if n and n in text:
                page = i + 1
                break
        found.append(page)
    return found, len(reader.pages)


def build_overlay(page_count, heads, path):
    """Слой колонтитулов: тёмная полоса с номером, названием и волной."""
    rows = []
    for i in range(page_count):
        head = (heads[i] if i < len(heads) else "")
        head = head.replace("&", "&amp;").replace("<", "&lt;")
        rows.append(
            '<div class="ov%s">'
            '<div class="rh"><span class="pn">%d</span>'
            '<span class="ttl">Охотники</span><span class="wv"></span></div>'
            '<div class="rf"><span class="ch">%s</span>'
            '<span class="gu">GUMSHOE</span></div>'
            '</div>' % (" last" if i == page_count - 1 else "", i + 1, head))

    doc = """<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><style>
@font-face { font-family: "Ruslan"; font-weight: 400; font-style: normal;
             src: url("../assets/fonts/RuslanDisplay-Regular.ttf") format("truetype"); }
@font-face { font-family: "Yeseva"; font-weight: 400; font-style: normal;
             src: url("../assets/fonts/YesevaOne-Regular.ttf") format("truetype"); }
@page { size: 163mm 215mm; margin: 0; }
html, body { margin: 0; padding: 0; }
.ov { width: 163mm; height: 215mm; position: relative; break-after: page; }
.ov.last { break-after: auto; }

.rh, .rf {
  position: absolute; left: 11mm; right: 11mm;
  display: flex; align-items: center; justify-content: space-between;
}
.rh { top: 4mm; height: 8.4mm; padding: 0 2.4mm; }
.rf { bottom: 5mm; height: 6.6mm; padding: 0 2.4mm; }
.rh::before, .rf::before {
  content: ""; position: absolute; inset: 0;
  background: url("../assets/brand/grunge.svg") center / 100% 100% no-repeat;
}
.rh > *, .rf > * { position: relative; z-index: 1; }

.rh .pn {
  font-family: "Ruslan", serif; font-size: 8.6pt; line-height: 1; color: #fff;
  background: #1a1a1a; padding: .9mm 1.8mm .5mm; min-width: 7mm; text-align: center;
}
.rh .ttl {
  font-family: "Ruslan", serif; font-size: 8.8pt; line-height: 1; color: #fff; letter-spacing: .3em;
  padding-left: .3em; white-space: nowrap;
}
.rh .wv {
  width: 30mm; height: 5.4mm; background-color: #fff; opacity: .8;
  -webkit-mask: url("../assets/brand/wave.svg") center / contain no-repeat;
  mask: url("../assets/brand/wave.svg") center / contain no-repeat;
}
.rf { font-family: "Yeseva", serif; font-size: 6.2pt; letter-spacing: .14em;
      text-transform: uppercase; color: #fff; }
.rf .ch { max-width: 110mm; overflow: hidden; white-space: nowrap; }
.rf .gu { letter-spacing: .22em; opacity: .85; }
</style></head><body>
@@ROWS@@
</body></html>"""
    open(path, "w", encoding="utf-8").write(doc.replace("@@ROWS@@", "\n".join(rows)))
    return path


def main():
    os.makedirs(TMP, exist_ok=True)
    if not os.access(CHROME, os.X_OK):
        raise SystemExit("Не найден Chrome: %s" % CHROME)

    print("· верстаю книгу")
    subprocess.check_call([sys.executable, os.path.join(ROOT, "scripts", "make_gumshoe_book.py")],
                          stdout=subprocess.DEVNULL)
    items = book_structure()

    print("· печатаю тело книги — это несколько минут")
    interior = render("/site-gumshoe/book.html", os.path.join(TMP, "interior.pdf"), 300000)

    print("· ищу страницы разделов")
    pages, n_pages = locate(interior, items)
    hit = sum(1 for v in pages if v)
    print("  страниц в теле: %d · найденных разделов: %d/%d" % (n_pages, hit, len(items)))
    for (kind, label, _), pg in zip(items, pages):
        print("     %-46s %s" % (label[:44], pg or "—"))

    heads, current = [], ""
    for i in range(n_pages):
        for (_k, label, _n), pg in zip(items, pages):
            if pg == i + 1:
                current = label
        heads.append(current)

    print("· печатаю колонтитулы")
    build_overlay(n_pages, heads, os.path.join(SITE, "book-overlay.html"))
    overlay = render("/site-gumshoe/book-overlay.html", os.path.join(TMP, "overlay.pdf"), 60000)

    p = pypdf()
    base = p.PdfReader(interior)
    over = p.PdfReader(overlay)
    stitched = p.PdfWriter()
    for i, page in enumerate(base.pages):
        if i < len(over.pages):
            page.merge_page(over.pages[i])
        stitched.add_page(page)
    body_pdf = os.path.join(TMP, "interior-foot.pdf")
    with open(body_pdf, "wb") as fh:
        stitched.write(fh)

    print("· верстаю обложку и оглавление с номерами страниц")
    import make_gumshoe_book as mgb
    toc = [(kind, label, "", pg or "") for (kind, label, _n), pg in zip(items, pages)]
    open(os.path.join(SITE, "book-front.html"), "w", encoding="utf-8").write(
        mgb.build_front(toc, True))
    front = render("/site-gumshoe/book-front.html", os.path.join(TMP, "front.pdf"), 60000)
    front_pages = len(p.PdfReader(front).pages)

    print("· склеиваю и ставлю закладки")
    final = p.PdfWriter()
    for page in p.PdfReader(front).pages:
        final.add_page(page)
    for page in p.PdfReader(body_pdf).pages:
        final.add_page(page)
    for (kind, label, _n), pg in zip(items, pages):
        if pg:
            final.add_outline_item(label, front_pages + pg - 1)
    with open(OUTPUT, "wb") as fh:
        final.write(fh)

    total = len(p.PdfReader(OUTPUT).pages)
    print("\nготово: %s" % os.path.relpath(OUTPUT, ROOT))
    print("  %d страниц (вступление %d + книга %d) · %.1f МБ · закладок %d"
          % (total, front_pages, n_pages, os.path.getsize(OUTPUT) / 1e6,
             sum(1 for v in pages if v)))


if __name__ == "__main__":
    main()
