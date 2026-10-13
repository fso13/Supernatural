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
    # врезка, начинающаяся с «**Что-то.**» — с заголовком по центру
    html_text = re.sub(
        r'<aside class="sidebar"><p><strong>([^<]{2,70}?)\.</strong>',
        lambda m: '<aside class="sidebar headed"><p><strong>%s.</strong>' % m.group(1),
        html_text)
    return html_text


# ─────────────────────────────────────────────────────────────────────────────
#  Оформление
# ─────────────────────────────────────────────────────────────────────────────

CSS = """
@font-face { font-family: "Ruslan"; font-weight: 400; font-style: normal;
             src: url("../assets/fonts/RuslanDisplay-Regular.ttf") format("truetype"); }
@font-face { font-family: "Yeseva"; font-weight: 400; font-style: normal;
             src: url("../assets/fonts/YesevaOne-Regular.ttf") format("truetype"); }

:root { --red: #8c1420; --red-2: #b7222b; --ink: #111; --grey: #6a6a6a;
        --rule: #bdbdbd; --tint: #eceae5; --band: #1a1a1a; }

@page { size: 163mm 215mm; margin: 13mm 13mm 15mm; }
@page cover { size: 163mm 215mm; margin: 0; }

* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: "Iowan Old Style", "Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif;
  font-size: 8.6pt; line-height: 1.37; color: var(--ink);
  -webkit-font-smoothing: antialiased;
}
p { margin: 0 0 3.6pt; text-align: justify; hyphens: auto; }

/* ── обложка ───────────────────────────────────────────────────────────── */
.cover {
  page: cover; position: relative; width: 163mm; height: 215mm;
  margin: 0; overflow: hidden; break-after: page;
  background: #0a0a0c url("../assets/brand/cover.jpg") center / 100% 100% no-repeat;
}

/* ── титул ─────────────────────────────────────────────────────────────── */
.titlepage { break-after: page; padding-top: 22mm; text-align: center; }
.titlepage .trap { width: 20mm; height: 20mm; color: var(--red-2); margin: 0 auto 6mm; }
.titlepage h1 {
  font-family: "Ruslan", serif; font-weight: 400; font-size: 30pt;
  letter-spacing: .04em; margin: 0 0 3mm; color: var(--ink); line-height: 1;
}
.titlepage .sub { font-size: 11.5pt; font-style: italic; color: #333; margin-bottom: 2.4mm; }
.titlepage .sys {
  font-family: "Yeseva", serif; font-size: 8pt; letter-spacing: .3em;
  text-transform: uppercase; color: var(--red); margin-bottom: 16mm;
}
.titlepage .rule { width: 34mm; height: 1px; background: var(--rule); margin: 0 auto 16mm; }
.colophon { font-size: 8.4pt; color: #444; line-height: 1.55; max-width: 112mm; margin: 0 auto; }
.colophon b { color: var(--ink); }
.colophon .credits { margin-top: 9mm; font-size: 7.8pt; color: var(--grey); }

/* ── оглавление ────────────────────────────────────────────────────────── */
.toc { break-after: page; }
.toc h2 {
  font-family: "Ruslan", serif; font-weight: 400; font-size: 19pt; letter-spacing: .05em;
  margin: 0 0 1.6mm; color: var(--ink); text-align: center;
}
.toc .rule { height: 2.4px; background: var(--ink); width: 26mm; margin: 0 auto 7mm; }
.toc .cols { column-count: 2; column-gap: 9mm; }
.tocline { display: flex; align-items: baseline; font-size: 9pt; margin-bottom: 2.3mm; }
.tocline .t { flex: 0 1 auto; }
.tocline .d { flex: 1 1 auto; border-bottom: 1px dotted #a8a8a8; margin: 0 1.6mm 0.8mm; min-width: 3mm; }
.tocline .p { flex: 0 0 auto; font-variant-numeric: tabular-nums; color: #333; }
.tocline.part {
  font-family: "Yeseva", serif; font-size: 8.8pt; letter-spacing: .04em;
  margin: 6mm 0 3mm; color: var(--ink); break-after: avoid;
}
.tocline.part .d { border-bottom: 1px solid #444; }
.tocline.part:first-child { margin-top: 0; }

/* ── раздел части ──────────────────────────────────────────────────────── */
.partpage {
  break-before: page; break-after: page; height: 187mm;
  display: flex; flex-direction: column; justify-content: center; align-items: center;
  text-align: center;
}
.partpage .trap { width: 24mm; height: 24mm; color: var(--red-2); opacity: .9; margin-bottom: 8mm; }
.partpage .kicker {
  font-family: "Yeseva", serif; font-size: 8pt; letter-spacing: .32em;
  text-transform: uppercase; color: var(--grey); margin-bottom: 4mm;
}
.partpage h1 {
  font-family: "Ruslan", serif; font-weight: 400; font-size: 27pt;
  letter-spacing: .03em; margin: 0; color: var(--ink); max-width: 120mm; line-height: 1.06;
}
.partpage .rule { width: 40mm; height: 2.4px; background: var(--ink); margin: 7mm 0; }
.partpage .eno { width: 42mm; height: 3.6mm; color: var(--red-2); opacity: .45; }

/* ── открывалка главы ──────────────────────────────────────────────────── */
.chapter { break-inside: auto; }
.ch-open {
  break-inside: avoid; break-after: avoid;
  margin: 0 0 4mm; padding-bottom: 2.6mm; border-bottom: 2.4px solid var(--ink);
}
.chapter + .chapter .ch-open { margin-top: 6mm; }
.ch-open .kick {
  font-family: "Yeseva", serif; font-size: 7.2pt; letter-spacing: .3em;
  text-transform: uppercase; color: var(--red); margin-bottom: 1.2mm;
}
.ch-open .row { display: flex; align-items: baseline; gap: 3.6mm; }
.ch-open .num {
  font-family: "Ruslan", serif; font-size: 30pt; line-height: .82;
  color: var(--red); flex: 0 0 auto; letter-spacing: .01em;
}
.ch-open h1 {
  font-family: "Ruslan", serif; font-weight: 400; font-size: 15.5pt;
  line-height: 1.1; margin: 0; color: var(--ink); letter-spacing: .03em;
}

/* ── текст в две колонки ───────────────────────────────────────────────── */
.flow {
  column-count: 2; column-gap: 7mm; column-fill: auto;
  column-rule: .4pt solid var(--rule);
}
.partpage + .flow, .flow + .flow, .flow + .partpage { break-before: page; }
.flow:first-of-type { break-before: avoid; }
.flow h2 {
  break-after: avoid; font-family: "Yeseva", serif; font-weight: 400;
  font-size: 10.4pt; margin: 5mm 0 1.8mm; padding-top: 1.4mm;
  border-top: 1.4px solid var(--ink); color: var(--ink); line-height: 1.16;
}
.flow h2:first-child { margin-top: 0; }
.flow h3 {
  break-after: avoid; font-family: "Yeseva", serif; font-weight: 400;
  font-size: 9.2pt; margin: 3.8mm 0 1.4mm; color: var(--red); line-height: 1.2;
}
.flow h4 {
  break-after: avoid; font-family: "Yeseva", serif; font-weight: 400;
  font-size: 8.6pt; margin: 3mm 0 1mm; color: #2a2a2a;
}
.flow h5, .flow h6 { break-after: avoid; font-size: 8.6pt; margin: 2.6mm 0 1mm; }

ul, ol { margin: 0 0 3.4pt; padding-left: 4.6mm; }
li { margin-bottom: .9mm; text-align: left; }
strong { color: #000; }
code {
  font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 7.6pt;
  background: var(--tint); padding: 0 .6mm;
}
a { color: var(--red); text-decoration: none; }

/* ── врезки ────────────────────────────────────────────────────────────── */
.sidebar {
  break-inside: avoid; margin: 3mm 0; padding: 2.4mm 2.8mm 2mm;
  background: var(--tint); border: .8pt solid #2a2a2a;
  font-family: "Helvetica Neue", Arial, sans-serif; font-size: 7.9pt; line-height: 1.38;
}
.sidebar p { text-align: left; margin: 0 0 1.8mm; }
.sidebar p:last-child { margin-bottom: 0; }
.sidebar strong { color: #000; }
.sidebar.headed > p:first-child > strong:first-child {
  display: block; text-align: center; font-family: "Yeseva", serif; font-weight: 400;
  font-size: 9pt; color: var(--ink); margin: 0 0 1.6mm; letter-spacing: .01em;
}

/* ── таблицы ───────────────────────────────────────────────────────────── */
table.md {
  width: 100%; border-collapse: collapse; margin: 2.6mm 0 3.4mm;
  font-family: "Helvetica Neue", Arial, sans-serif; font-size: 7.5pt; line-height: 1.28;
}
table.md thead { display: table-header-group; }
table.md th {
  background: #e2dfd8; color: #111; text-align: left; font-weight: 700;
  padding: 1.3mm 1.5mm; border-top: .8pt solid #333; border-bottom: .8pt solid #333;
}
table.md td { padding: 1.1mm 1.5mm; border-bottom: .4pt solid #cfcfcf; vertical-align: top; }
table.md tbody tr:nth-child(even) td { background: #f6f5f2; }
table.md tr { break-inside: avoid; }
table.md strong { color: var(--red); }

pre {
  break-inside: avoid; background: var(--tint); border-left: 1.6px solid var(--rule);
  padding: 2mm 2.4mm; font-size: 7.4pt; margin: 2.6mm 0; overflow-wrap: anywhere;
}
pre code { background: none; padding: 0; font-size: 7.4pt; }
.orn { width: 12mm; height: 1.4px; background: var(--rule); margin: 3.6mm auto; break-after: avoid; }
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

<section class="cover"></section>

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
