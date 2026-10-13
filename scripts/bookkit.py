#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Общие кирпичи для сборки книг в PDF.

Печать через headless Chrome, поиск страниц разделов, слой колонтитулов,
склейка с закладками. Используется сборщиками книг правил и бестиария.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
BASE = os.environ.get("BASE", "http://127.0.0.1:8770")


def pypdf():
    """pypdf из окружения или из scripts/_vendor, с автоустановкой."""
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
    """Печатает страницу в PDF через headless Chrome."""
    if not os.access(CHROME, os.X_OK):
        raise SystemExit("Не найден Chrome: %s" % CHROME)
    profile = tempfile.mkdtemp(prefix="bkpdf_")
    try:
        proc = subprocess.Popen(
            [CHROME, "--headless", "--disable-gpu", "--no-sandbox",
             "--user-data-dir=" + profile, "--no-first-run", "--no-pdf-header-footer",
             "--virtual-time-budget=%d" % budget, "--print-to-pdf=" + out, BASE + url],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            proc.wait(timeout=3600)
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


def locate(pdf_path, items):
    """Номер страницы (с 1) для каждого раздела. items: [(key, label, needle)]."""
    p = pypdf()
    reader = p.PdfReader(pdf_path)
    pages = [norm(pg.extract_text() or "") for pg in reader.pages]
    found = []
    for _key, _label, needle in items:
        n = norm(needle)
        page = None
        if n:
            for i, text in enumerate(pages):
                if n in text:
                    page = i + 1
                    break
        found.append(page)
    return found, len(reader.pages)


def _inline(name, cls):
    """SVG как элемент, а не фон: иначе Chrome растеризует его на каждой странице."""
    import re
    src = open(os.path.join(ROOT, "assets", "brand", name), encoding="utf-8").read()
    src = re.sub(r"<\?xml[^>]*\?>", "", src)
    src = re.sub(r"<title>.*?</title>", "", src, flags=re.S)
    src = re.sub(r'\s+role="img"', '', src)
    src = re.sub(r'\s+aria-label="[^"]*"', "", src)
    src = src.replace("<svg ", '<svg class="%s" preserveAspectRatio="none" ' % cls, 1)
    return re.sub(r"\s+", " ", src).strip()


OVERLAY_TPL = """<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><style>
@font-face { font-family: "Ruslan"; font-weight: 400; font-style: normal;
             src: url("@@ASSETS@@fonts/RuslanDisplay-Regular.ttf") format("truetype"); }
@font-face { font-family: "Yeseva"; font-weight: 400; font-style: normal;
             src: url("@@ASSETS@@fonts/YesevaOne-Regular.ttf") format("truetype"); }
@page { size: @@PW@@mm @@PH@@mm; margin: 0; }
html, body { margin: 0; padding: 0; }
.ov { width: @@PW@@mm; height: @@PH@@mm; position: relative; break-after: page; }
.ov.last { break-after: auto; }

.rh, .rf {
  position: absolute; left: 11mm; right: 11mm;
  display: flex; align-items: center; justify-content: space-between;
}
.rh { top: 4mm; height: 8.4mm; padding: 0 2.4mm; }
.rf { bottom: 5mm; height: 6.6mm; padding: 0 2.4mm; }
.rh .band, .rf .band { position: absolute; inset: 0; width: 100%; height: 100%; }
.rh > *, .rf > * { position: relative; z-index: 1; }

.rh .pn {
  font-family: "Ruslan", serif; font-size: 8.6pt; line-height: 1; color: #fff;
  background: #1a1a1a; padding: .9mm 1.8mm .5mm; min-width: 7mm; text-align: center;
}
.rh .ttl {
  font-family: "Ruslan", serif; font-size: 8.8pt; line-height: 1; color: #fff;
  letter-spacing: .3em; padding-left: .3em; white-space: nowrap;
}
.rh .wv { width: 30mm; height: 5.4mm; color: #fff; opacity: .8; }
.rh .wv svg { width: 100%; height: 100%; display: block; }
.rf { font-family: "Yeseva", serif; font-size: 6.2pt; letter-spacing: .14em;
      text-transform: uppercase; color: #fff; }
.rf .ch { max-width: 110mm; overflow: hidden; white-space: nowrap; }
.rf .gu { letter-spacing: .22em; opacity: .85; }
</style></head><body>
@@ROWS@@
</body></html>"""


BAND = _inline("grunge.svg", "band")
WAVE = _inline("wave.svg", "band")


def build_overlay(page_count, heads, path, title="Охотники", tail="GUMSHOE",
                  page_w=163, page_h=215, assets="../assets/"):
    """Слой колонтитулов: тёмная полоса с номером, названием и волной."""
    rows = []
    for i in range(page_count):
        head = (heads[i] if i < len(heads) else "")
        head = head.replace("&", "&amp;").replace("<", "&lt;")
        rows.append(
            '<div class="ov%s">'
            '<div class="rh"><span class="pn">%d</span>'
            '<span class="ttl">%s</span><span class="wv"></span></div>'
            '<div class="rf"><span class="ch">%s</span>'
            '<span class="gu">%s</span></div>'
            '</div>' % (" last" if i == page_count - 1 else "", i + 1,
                        title.replace("&", "&amp;"), head,
                        tail.replace("&", "&amp;")))
    doc = (OVERLAY_TPL.replace("@@ROWS@@", "\n".join(rows))
           .replace("@@PW@@", str(page_w)).replace("@@PH@@", str(page_h))
           .replace("@@ASSETS@@", assets))
    open(path, "w", encoding="utf-8").write(doc)
    return path


def stamp(body_pdf, overlay_pdf, out_pdf):
    """Накладывает колонтитулы на страницы книги.

    После merge_page pypdf оставляет поток страницы распакованным — на глаз
    это 140 КБ на страницу вместо 12. Сжимаем обратно, иначе книга, а с ней
    и слой колонтитулов, раздувается втрое.
    """
    p = pypdf()
    base = p.PdfReader(body_pdf)
    over = p.PdfReader(overlay_pdf)
    writer = p.PdfWriter()
    for i, page in enumerate(base.pages):
        if i < len(over.pages):
            page.merge_page(over.pages[i])
        writer.add_page(page)
        # сжимать можно только страницу, уже добавленную в writer
        try:
            writer.pages[-1].compress_content_streams()
        except Exception as exc:
            print("  не удалось сжать страницу %d: %s" % (i + 1, exc))
    with open(out_pdf, "wb") as fh:
        writer.write(fh)
    return out_pdf


def assemble(front_pdf, body_pdf, out_pdf, outline=None):
    """Склеивает вступление с телом и ставит закладки."""
    p = pypdf()
    writer = p.PdfWriter()
    for page in p.PdfReader(front_pdf).pages:
        writer.add_page(page)
    for page in p.PdfReader(body_pdf).pages:
        writer.add_page(page)
    for label, page_index in (outline or []):
        writer.add_outline_item(label, page_index)
    with open(out_pdf, "wb") as fh:
        writer.write(fh)
    return out_pdf


def setup_tmp(name):
    tmp = os.path.join(tempfile.gettempdir(), name)
    os.makedirs(tmp, exist_ok=True)
    return tmp
