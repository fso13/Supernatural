#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собирает книгу правил «Охотники» в стиле правил The Esoterrorists.

Из Markdown делает вёрстку: обложка, титул, оглавление с номерами страниц,
разделы частей, открывалки глав, две колонки, врезки, таблицы.

  python3 scripts/make_gumshoe_book.py            # site-gumshoe/book.html + book-front.html
"""
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from md2site import convert, slug  # noqa: E402

SRC = os.path.join(ROOT, "Охотники — полные правила (GUMSHOE).md")
OUT = os.path.join(ROOT, "site-gumshoe", "book.html")
OUT_FRONT = os.path.join(ROOT, "site-gumshoe", "book-front.html")
BRAND = os.path.join(ROOT, "assets", "brand")


def svg_inline(name):
    """Читает SVG и делает его пригодным для вставки в HTML (цвет — currentColor)."""
    with open(os.path.join(BRAND, name), encoding="utf-8") as fh:
        s = fh.read()
    s = re.sub(r"<\?xml[^>]*\?>", "", s)
    s = re.sub(r"<title>.*?</title>", "", s, flags=re.S)
    s = re.sub(r'\s+role="img"', "", s)
    s = re.sub(r'\s+aria-label="[^"]*"', "", s)
    return re.sub(r"\s+", " ", s).strip()


TRAP = svg_inline("devils-trap.svg")
ROAD_COVER = None
ENO = svg_inline("enochian-band.svg")
IMPALA = svg_inline("impala.svg")
ROAD = svg_inline("road.svg")


ROAD_COVER = None  # заполняется ниже


def svg_colored(svg, color):
    """Подставляет цвет вместо currentColor — для использования как background-image."""
    return svg.replace("currentColor", color)
SALT = svg_inline("salt-line.svg")


# ─────────────────────────────────────────────────────────────────────────────
#  Разбор исходника на части и главы
# ─────────────────────────────────────────────────────────────────────────────

def split_chapters(body):
    """Режет готовый HTML по <h1> на список блоков."""
    chunks = re.split(r'(<h1 id="[^"]*">.*?</h1>)', body)
    blocks, pending = [], None
    for piece in chunks:
        if piece.startswith("<h1 "):
            if pending:
                blocks.append(pending)
            title = re.sub(r"<[^>]+>", "", piece).strip()
            pending = {"title": title, "head": piece, "body": ""}
        elif pending is not None:
            pending["body"] += piece
    if pending:
        blocks.append(pending)
    return blocks


def classify(block):
    t = block["title"]
    if t.startswith("ЧАСТЬ") or t.upper() == "ПРИЛОЖЕНИЯ":
        return "part"
    if t.startswith("Глава"):
        return "chapter"
    if t.startswith("Приложение"):
        return "chapter"
    return "front"


def chapter_bits(title):
    """'Глава 3. Способности' -> ('Глава', '3', 'Способности')."""
    m = re.match(r"^(Глава|Приложение)\s+([0-9А-ЯA-Z]+)\.\s*(.*)$", title)
    if m:
        return m.group(1), m.group(2), m.group(3)
    return "", "", title


def clean_body(html_text):
    """Убирает горизонтальные линейки, превращает цитаты во врезки."""
    html_text = re.sub(r"<hr\s*/?>", '<div class="orn"></div>', html_text)
    html_text = html_text.replace("<blockquote>", '<aside class="sidebar">')
    html_text = html_text.replace("</blockquote>", "</aside>")
    return html_text


# ─────────────────────────────────────────────────────────────────────────────
#  Оформление
# ─────────────────────────────────────────────────────────────────────────────

CSS = """
:root { --red: #8c1420; --red-2: #b7222b; --ink: #131313; --grey: #6a6a6a;
        --rule: #c9c9c9; --tint: #f2f2f2; }

@page { size: A4; margin: 15mm 14mm 16mm; }
@page cover { size: A4; margin: 0; }

* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: "Iowan Old Style", "Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif;
  font-size: 9.6pt; line-height: 1.46; color: var(--ink);
  -webkit-font-smoothing: antialiased;
}
p { margin: 0 0 4.4pt; text-align: justify; hyphens: auto; }

/* ── обложка ───────────────────────────────────────────────────────────── */
.cover {
  page: cover; position: relative; width: 210mm; height: 297mm;
  margin: 0; overflow: hidden;
  background: #0a0a0c; color: #f2ece2; break-after: page;
}
.cover::before {
  content: ""; position: absolute; inset: 0;
  background:
    radial-gradient(closest-side, rgba(183,34,43,.30), rgba(183,34,43,0) 100%)
      no-repeat 50% 88% / 200mm 150mm,
    radial-gradient(closest-side, rgba(160,26,36,.20), rgba(183,34,43,0) 100%)
      no-repeat 50% 6% / 150mm 120mm;
}
.cover::after {
  content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 110mm;
  background: url("data:image/svg+xml;utf8,ROADURI") center bottom / 100% auto no-repeat;
  opacity: .9;
}
.cover .inner { position: relative; z-index: 3; height: 100%; padding: 24mm 18mm 18mm;
                display: flex; flex-direction: column; align-items: center; text-align: center;
                justify-content: space-between; }
.cover .grp { display: flex; flex-direction: column; align-items: center; width: 100%; }
.cover .trap { width: 82mm; height: 82mm; color: #b7222b; opacity: .9; margin-bottom: 4mm; }
.cover .eno { width: 62mm; height: 5mm; color: #d8b26a; opacity: .7; margin-bottom: 8mm; }
.cover h1 {
  font-family: "Helvetica Neue", "Arial Narrow", Arial, sans-serif;
  font-weight: 700; font-size: 52pt; letter-spacing: .09em; line-height: 1;
  margin: 0; color: #fff;
}
.cover .sub {
  font-size: 13.5pt; font-style: italic; margin-top: 7mm; color: #e8e0d2; max-width: 120mm;
}
.cover .sys {
  font-family: "Helvetica Neue", Arial, sans-serif; font-size: 9pt; letter-spacing: .34em;
  text-transform: uppercase; color: #d8b26a; margin-top: 9mm;
}
.cover .salt { width: 100mm; height: 5mm; color: #d8b26a; opacity: .6; margin: 12mm 0 0; }
.cover .bottom { width: 100%; }
.cover .impala { width: 96mm; height: 26mm; color: #cfc7ba; opacity: .75; margin: 0 auto 6mm; }
.cover .strap {
  font-family: "Helvetica Neue", Arial, sans-serif; font-size: 8.6pt; letter-spacing: .26em;
  text-transform: uppercase; color: #f2ece2; opacity: .85;
}
.cover .tag { font-size: 10pt; font-style: italic; color: #b9b0a2; margin-top: 3mm; }

/* ── титул ─────────────────────────────────────────────────────────────── */
.titlepage { break-after: page; padding-top: 34mm; text-align: center; }
.titlepage .trap { width: 26mm; height: 26mm; color: var(--red-2); margin: 0 auto 8mm; }
.titlepage h1 {
  font-family: "Helvetica Neue", Arial, sans-serif; font-weight: 700;
  font-size: 30pt; letter-spacing: .08em; margin: 0 0 4mm; color: var(--ink);
}
.titlepage .sub { font-size: 13pt; font-style: italic; color: #333; margin-bottom: 3mm; }
.titlepage .sys {
  font-family: "Helvetica Neue", Arial, sans-serif; font-size: 8.4pt; letter-spacing: .3em;
  text-transform: uppercase; color: var(--red); margin-bottom: 22mm;
}
.titlepage .rule { width: 40mm; height: 1px; background: var(--rule); margin: 0 auto 22mm; }
.colophon { font-size: 9pt; color: #444; line-height: 1.6; max-width: 120mm; margin: 0 auto; }
.colophon b { color: var(--ink); }
.colophon .credits { margin-top: 12mm; font-size: 8.4pt; color: var(--grey); }

/* ── оглавление ────────────────────────────────────────────────────────── */
.toc { break-after: page; }
.toc h2 {
  font-family: "Helvetica Neue", Arial, sans-serif; font-size: 15pt; letter-spacing: .16em;
  text-transform: uppercase; margin: 0 0 2mm; color: var(--ink);
}
.toc .rule { height: 2px; background: var(--red); width: 28mm; margin-bottom: 8mm; }
.toc .cols { column-count: 2; column-gap: 11mm; }
.tocline { display: flex; align-items: baseline; font-size: 9.4pt; margin-bottom: 1.7mm; }
.tocline .t { flex: 0 1 auto; }
.tocline .d { flex: 1 1 auto; border-bottom: 1px dotted #b6b6b6; margin: 0 2mm 0.9mm; min-width: 4mm; }
.tocline .p { flex: 0 0 auto; font-variant-numeric: tabular-nums; color: #444; }
.tocline.part { font-family: "Helvetica Neue", Arial, sans-serif; font-weight: 700;
                font-size: 9.6pt; text-transform: uppercase; letter-spacing: .1em;
                margin: 4.5mm 0 2.2mm; color: var(--red); break-after: avoid; }
.tocline.part .d { border-bottom-style: solid; border-bottom-color: var(--red); }
.tocline.part:first-child { margin-top: 0; }

/* ── раздел части ──────────────────────────────────────────────────────── */
.partpage {
  break-before: page; break-after: page; height: 250mm;
  display: flex; flex-direction: column; justify-content: center; align-items: center;
  text-align: center;
}
.partpage .trap { width: 30mm; height: 30mm; color: var(--red-2); opacity: .85; margin-bottom: 10mm; }
.partpage .kicker {
  font-family: "Helvetica Neue", Arial, sans-serif; font-size: 8.4pt; letter-spacing: .34em;
  text-transform: uppercase; color: var(--grey); margin-bottom: 5mm;
}
.partpage h1 {
  font-family: "Helvetica Neue", Arial, sans-serif; font-weight: 700; font-size: 24pt;
  letter-spacing: .06em; margin: 0; color: var(--ink); max-width: 150mm;
}
.partpage .rule { width: 46mm; height: 2px; background: var(--red); margin: 9mm 0; }
.partpage .eno { width: 50mm; height: 4.4mm; color: var(--red-2); opacity: .4; }

/* ── открывалка главы ──────────────────────────────────────────────────── */
.chapter { break-inside: auto; }
.partpage + .flow, .flow + .flow, .flow + .partpage { break-before: page; }
.ch-open {
  break-inside: avoid; break-after: avoid;
  margin: 0 0 4.6mm; padding-top: 1mm; border-bottom: 2px solid var(--red); padding-bottom: 3.4mm;
}
.chapter + .chapter .ch-open { margin-top: 7mm; }
.ch-open .kick {
  font-family: "Helvetica Neue", Arial, sans-serif; font-size: 8pt; letter-spacing: .32em;
  text-transform: uppercase; color: var(--grey); margin-bottom: 1.5mm;
}
.ch-open .row { display: flex; align-items: baseline; gap: 5mm; }
.ch-open .num {
  font-family: "Helvetica Neue", Arial, sans-serif; font-weight: 700; font-size: 38pt;
  line-height: .84; color: var(--red); flex: 0 0 auto; letter-spacing: .01em;
  font-variant-numeric: lining-nums tabular-nums;
}
.ch-open h1 {
  font-family: "Helvetica Neue", Arial, sans-serif; font-weight: 700; font-size: 19pt;
  line-height: 1.1; margin: 0; color: var(--ink); letter-spacing: .01em;
}

/* ── текст в две колонки ───────────────────────────────────────────────── */
.flow { column-count: 2; column-gap: 8mm; column-fill: auto; }
.flow:first-of-type { break-before: avoid; }
.flow > .chapter:first-child .ch-open { margin-top: 0; }
.flow h2 {
  break-after: avoid; font-family: "Helvetica Neue", Arial, sans-serif; font-weight: 700;
  font-size: 11.4pt; margin: 6mm 0 2mm; padding-top: 1.6mm; border-top: 1px solid var(--rule);
  color: var(--ink);
}
.flow h2:first-child { margin-top: 0; }
.flow h3 {
  break-after: avoid; font-family: "Helvetica Neue", Arial, sans-serif; font-weight: 700;
  font-size: 9.7pt; margin: 4.4mm 0 1.6mm; color: var(--red);
}
.flow h4 {
  break-after: avoid; font-family: "Helvetica Neue", Arial, sans-serif; font-weight: 700;
  font-size: 9.1pt; margin: 3.6mm 0 1.2mm; color: #333; letter-spacing: .02em;
}
.flow h5, .flow h6 { break-after: avoid; font-size: 9.1pt; margin: 3mm 0 1mm; }

ul, ol { margin: 0 0 4pt; padding-left: 5.4mm; }
li { margin-bottom: 1.1mm; text-align: left; }
strong { color: #000; }
code {
  font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 8.4pt;
  background: var(--tint); padding: 0 .7mm; border-radius: 1mm;
}
a { color: var(--red); text-decoration: none; }

/* ── врезки ────────────────────────────────────────────────────────────── */
.sidebar {
  break-inside: avoid; margin: 3.6mm 0; padding: 2.6mm 3.4mm 2.2mm;
  background: var(--tint); border-left: 2.6px solid var(--red);
  font-family: "Helvetica Neue", Arial, sans-serif; font-size: 8.5pt; line-height: 1.42;
}
.sidebar p { text-align: left; margin: 0 0 2.2mm; }
.sidebar p:last-child { margin-bottom: 0; }
.sidebar strong { color: var(--red); }
.sidebar em { font-style: italic; }

/* ── таблицы ───────────────────────────────────────────────────────────── */
table.md {
  width: 100%; border-collapse: collapse; margin: 3mm 0 4mm;
  font-family: "Helvetica Neue", Arial, sans-serif; font-size: 8.1pt; line-height: 1.3;
  break-inside: auto;
}
table.md thead { display: table-header-group; }
table.md th {
  background: #232323; color: #fff; text-align: left; font-weight: 700;
  padding: 1.5mm 1.7mm; border: none; letter-spacing: .02em;
}
table.md td {
  padding: 1.3mm 1.7mm; border-bottom: .5px solid var(--rule); vertical-align: top;
}
table.md tbody tr:nth-child(even) td { background: #f7f7f7; }
table.md tr { break-inside: avoid; }
table.md strong { color: var(--red); }

pre {
  break-inside: avoid; background: var(--tint); border-left: 2px solid var(--rule);
  padding: 2.4mm 3mm; font-size: 8pt; margin: 3mm 0; overflow-wrap: anywhere;
}
pre code { background: none; padding: 0; font-size: 8pt; }

.orn {
  width: 14mm; height: 1.6px; background: var(--rule);
  margin: 4.5mm auto; break-after: avoid;
}

/* ── подвал врезки-финала ──────────────────────────────────────────────── */
.endnote { margin-top: 6mm; font-size: 8.4pt; color: var(--grey); font-style: italic; }
.endnote p { text-align: left; }
"""


def build_front(toc_entries, toc_pages_known):
    """Обложка + титул + оглавление."""
    toc_rows = []
    for kind, label, num, page in toc_entries:
        pg = page if toc_pages_known else ""
        cls = "tocline part" if kind == "part" else "tocline"
        toc_rows.append(
            '<div class="%s"><span class="t">%s</span>'
            '<span class="d"></span><span class="p">%s</span></div>'
            % (cls, html.escape(label), pg)
        )

    return """<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8">
<title>Охотники — полные правила (GUMSHOE)</title>
<style>%(css)s</style></head><body>

<section class="cover">
  <div class="inner">
    <div class="grp">
      <div class="trap">%(trap)s</div>
      <div class="eno">%(eno)s</div>
    </div>
    <div class="grp">
      <h1>ОХОТНИКИ</h1>
      <div class="sub">Ролевая игра по «Сверхъестественному»</div>
      <div class="sys">на системе GUMSHOE</div>
      <div class="salt">%(salt)s</div>
    </div>
    <div class="grp bottom">
      <div class="impala">%(impala)s</div>
      <div class="strap">Полные правила · для игрока и хранителя</div>
      <div class="tag">Спасать людей. Охотиться на нечисть. Семейный бизнес.</div>
    </div>
  </div>
</section>

<section class="titlepage">
  <div class="trap">%(trap)s</div>
  <h1>ОХОТНИКИ</h1>
  <div class="sub">Ролевая игра по «Сверхъестественному»</div>
  <div class="sys">на системе GUMSHOE</div>
  <div class="rule"></div>
  <div class="colophon">
    <p style="text-align:center"><b>Полные правила.</b> Тринадцать глав, четыре приложения,
    двести шестнадцать таблиц: ядро системы, создание охотника, расследование, бой,
    Стабильность и Убеждённость, обряды и экзорцизм, глава хранителя.</p>
    <div class="credits">
      <p style="text-align:center">Система <b>GUMSHOE</b> придумана Робином Д. Лоузом.<br>
      Опубликована Pelgrane Press. Оригинальные игры системы —
      <b>The Esoterrorists</b> и <b>Trail of Cthulhu</b>.</p>
      <p style="text-align:center">«Сверхъестественное» — Warner Bros. Television.<br>
      Неофициальный фанатский материал для домашних игр. Не для продажи.</p>
      <p style="text-align:center">Первое издание · Бестиарий на 354 существа,
      архетипы и приключение «Спящие» — на сайте проекта.</p>
    </div>
  </div>
</section>

<section class="toc">
  <h2>Содержание</h2>
  <div class="rule"></div>
  <div class="cols">
    %(toc)s
  </div>
</section>

</body></html>
""" % {"css": CSS.replace("ROADURI", _cover_road()), "trap": TRAP, "eno": ENO,
       "salt": SALT, "impala": IMPALA, "toc": "\n    ".join(toc_rows)}


def _cover_road():
    """Дорога для обложки: цвет прописан, линии толще — иначе не видно в печати."""
    r = svg_colored(ROAD, "#b7222b").replace('stroke-width="2"', 'stroke-width="5"')
    r = r.replace('stroke-width="1"', 'stroke-width="3"')
    return _data_uri(r)


def _data_uri(svg):
    from urllib.parse import quote
    return "data:image/svg+xml;charset=utf-8," + quote(svg, safe="")


def build_interior(blocks, page_map=None):
    """Введение, затем на каждую часть — свой поток в две колонки."""
    def chapter_html(b):
        kind = classify(b)
        body = clean_body(b["body"])
        if kind == "front":
            return ('<section class="chapter">'
                    '<div class="ch-open"><div class="kick">Введение</div>'
                    '<div class="row"><h1>Что это за игра</h1></div></div>%s</section>' % body)
        what, num, name = chapter_bits(b["title"])
        return ('<section class="chapter" id="%s">'
                '<div class="ch-open"><div class="kick">%s</div>'
                '<div class="row"><div class="num">%s</div><h1>%s</h1></div></div>%s</section>'
                % (slug(b["title"]), html.escape(what), html.escape(num),
                   html.escape(name), body))

    def part_html(b):
        kicker = "Часть" if b["title"].startswith("ЧАСТЬ") else "Приложения"
        name = ("Справочник хранителя" if b["title"].upper() == "ПРИЛОЖЕНИЯ"
                else re.sub(r"^ЧАСТЬ\s+\w+\.\s*", "", b["title"]))
        return ('<section class="partpage"><div class="trap">%s</div>'
                '<div class="kicker">%s</div><h1>%s</h1>'
                '<div class="rule"></div><div class="eno">%s</div></section>'
                % (TRAP, kicker, html.escape(name), ENO))

    groups, cur = [], []
    for b in blocks:
        if classify(b) == "part":
            if cur:
                groups.append(("flow", cur))
                cur = []
            groups.append(("part", b))
        else:
            cur.append(b)
    if cur:
        groups.append(("flow", cur))

    out = []
    for kind, payload in groups:
        if kind == "part":
            out.append(part_html(payload))
        else:
            out.append('<div class="flow">%s</div>'
                       % "\n".join(chapter_html(b) for b in payload))
    return "\n".join(out)


def build_interior_doc(inner):
    return """<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8">
<title>Охотники — правила</title>
<style>%(css)s</style></head><body>
%(inner)s
</body></html>
""" % {"css": CSS, "inner": inner}


def main():
    md = open(SRC, encoding="utf-8").read()
    body, _ = convert(md)
    blocks = split_chapters(body)

    # оглавление
    toc = []
    for b in blocks:
        kind = classify(b)
        if kind == "front":
            toc.append(("chapter", "Введение. Что это за игра", "", ""))
        elif kind == "part":
            name = re.sub(r"^ЧАСТЬ\s+\w+\.\s*", "", b["title"])
            name = ("ПРИЛОЖЕНИЯ. Справочник хранителя"
                    if b["title"].upper() == "ПРИЛОЖЕНИЯ" else b["title"])
            toc.append(("part", name, "", ""))
        else:
            toc.append(("chapter", b["title"], "", ""))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT_FRONT, "w", encoding="utf-8").write(build_front(toc, False))
    open(OUT, "w", encoding="utf-8").write(build_interior_doc(build_interior(blocks, None)))

    print("обложка+титул+оглавление: %s" % os.path.relpath(OUT_FRONT, ROOT))
    print("книга: %s" % os.path.relpath(OUT, ROOT))
    print("разделов: %d, из них в оглавлении: %d" % (len(blocks), len(toc)))
    for kind, label, _n, _p in toc:
        print("   %-9s %s" % (kind, label))
    return toc


if __name__ == "__main__":
    main()
