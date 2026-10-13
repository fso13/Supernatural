#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собирает печатный бестиарий в оформлении книги правил.

Формат 163 x 215 мм, две колонки, тёмные полосы колонтитулов, акцидентные
шрифты. Каждая запись начинается с новой страницы.

  python3 scripts/make_bestiary_book.py                     # все 354 записи
  python3 scripts/make_bestiary_book.py --limit 12          # проба
  python3 scripts/make_bestiary_book.py --page a4           # формат A4 вместо дайджеста
"""
import argparse
import html
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_book import CAT_ICON, CAT_ORDER, esc, load, statblock  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site", "bestiary.html")
OUT_FRONT = os.path.join(ROOT, "site", "bestiary-front.html")

CAT_DESC = {
    "Монстр": "Существа, которых охотники встречают чаще всего: от вендиго в лесах "
              "до джиннов в зернохранилищах. У каждого своя повадка, свой ареал и своё правило.",
    "Демон": "Обитатели Ада и те, кто с ними связан. Держат контракты, помнят долги, "
             "соблюдают букву сделки — и почти никогда её дух.",
    "Ангел": "Небесное воинство. Сильнее демонов, равнодушнее людей и убеждены, "
             "что действуют во благо. Чаще всего это хуже всего.",
    "Божество": "Боги, полубоги и то, что древнее их. Питаются верой, славой "
                "или страхом и почти не замечают отдельных людей.",
    "Дух": "То, что осталось после смерти. Призраки, банши, потерянные души — "
           "и те, кто не понял, что уже умер.",
    "Ведьма": "Практикующие. Ковены, одиночки и те, кто продал душу за пару заклинаний.",
    "Левиафан": "Древнее и чужое. Ест людей не от голода, а по привычке, "
                "и считает себя венцом творения.",
    "Иное": "Места, предметы и понятия: Чистилище, Первое Лезвие, Благодать. "
            "Всё, что не существо, но по правилам имеет силу.",
}

CSS = """
@font-face { font-family: "Ruslan"; font-weight: 400; font-style: normal;
             src: url("../assets/fonts/RuslanDisplay-Regular.ttf") format("truetype"); }
@font-face { font-family: "Yeseva"; font-weight: 400; font-style: normal;
             src: url("../assets/fonts/YesevaOne-Regular.ttf") format("truetype"); }

:root { --red: #8c1420; --red-2: #b7222b; --ink: #111; --grey: #6a6a6a;
        --rule: #bdbdbd; --tint: #eceae5; }

@page { size: @@PAGE_W@@mm @@PAGE_H@@mm; margin: 13mm 13mm 15mm; }
@page cover { size: @@PAGE_W@@mm @@PAGE_H@@mm; margin: 0; }

* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body { font-family: "Iowan Old Style", "Palatino Linotype", Palatino, "Book Antiqua",
                     Georgia, serif;
       font-size: 8.4pt; line-height: 1.36; color: var(--ink);
       -webkit-font-smoothing: antialiased; }
p { margin: 0 0 3.4pt; text-align: justify; hyphens: auto; }
h1, h2, h3, h4 { margin: 0; }

/* ── обложка ───────────────────────────────────────────────────────────── */
.cover { page: cover; position: relative; width: @@PAGE_W@@mm; height: @@PAGE_H@@mm; margin: 0;
         overflow: hidden; break-after: page; background: #0a0a0c; }
.cover .art { position: absolute; inset: 0;
  background: url("../assets/brand/bestiary-cover.jpg") center / 100% 100% no-repeat; }
.cover .shade { position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(6,6,8,.92) 0%, rgba(6,6,8,.35) 34%,
              rgba(6,6,8,.30) 62%, rgba(6,6,8,.94) 100%); }
.cover .in { position: absolute; inset: 0; z-index: 2; padding: 16mm 13mm 12mm;
             display: flex; flex-direction: column; align-items: center; text-align: center; }
.cover .brush { position: relative; width: 100%; padding: 8mm 4mm; margin-bottom: 5mm; }
.cover .brush::before { content: ""; position: absolute; inset: -1mm -2mm;
  background: url("../assets/brand/brush.svg") center / 100% 100% no-repeat; }
.cover .brush h1 { position: relative; font-family: "Ruslan", serif; font-weight: 400;
  font-size: 33pt; line-height: 1; color: #fff; letter-spacing: .06em; margin: 0; }
.cover .sub { font-family: "Yeseva", serif; font-size: 9.4pt; color: #f0ebe1;
              letter-spacing: .05em; margin-top: 1mm; }
.cover .tag { margin-top: auto; font-size: 9pt; font-style: italic; color: #ddd6c9;
              max-width: 120mm; }
.cover .sys { font-family: "Yeseva", serif; font-size: 7.6pt; letter-spacing: .28em;
              text-transform: uppercase; color: #e8bb63; margin-top: 3mm; }
.cover .cnt { font-family: "Yeseva", serif; font-size: 7.4pt; letter-spacing: .16em;
              text-transform: uppercase; color: #bdb5a6; margin-top: 6mm; }

/* ── титул ─────────────────────────────────────────────────────────────── */
.titlepage { break-after: page; padding-top: 22mm; text-align: center; }
.titlepage .trap { width: 20mm; height: 20mm; color: var(--red-2); margin: 0 auto 6mm; }
.titlepage h1 { font-family: "Ruslan", serif; font-weight: 400; font-size: 30pt;
                letter-spacing: .04em; margin: 0 0 3mm; line-height: 1; }
.titlepage .sub { font-size: 11.5pt; font-style: italic; color: #333; margin-bottom: 2.4mm; }
.titlepage .sys { font-family: "Yeseva", serif; font-size: 8pt; letter-spacing: .3em;
                  text-transform: uppercase; color: var(--red); margin-bottom: 14mm; }
.titlepage .rule { width: 34mm; height: 1px; background: var(--rule); margin: 0 auto 14mm; }
.colophon { font-size: 8.4pt; color: #444; line-height: 1.55; max-width: 112mm; margin: 0 auto; }
.colophon b { color: var(--ink); }
.colophon .credits { margin-top: 9mm; font-size: 7.8pt; color: var(--grey); }

/* ── иллюстрация на всю страницу ───────────────────────────────────────── */
.plate { break-after: page; height: @@BODY_H@@mm; display: flex; align-items: center;
         justify-content: center; }
.plate img { max-width: 100%; max-height: 100%; object-fit: contain; }

/* ── оглавление ────────────────────────────────────────────────────────── */
.toc { break-after: page; }
.toc h2 { font-family: "Ruslan", serif; font-weight: 400; font-size: 19pt;
          letter-spacing: .05em; margin: 0 0 1.6mm; text-align: center; }
.toc .rule { height: 2.4px; background: var(--ink); width: 26mm; margin: 0 auto 6mm; }
.toc .cat { font-family: "Yeseva", serif; font-size: 9.6pt; color: var(--red);
            border-bottom: 1px solid #444; padding-bottom: .8mm; margin: 4.5mm 0 2mm;
            break-after: avoid; }
.toc .cat:first-of-type { margin-top: 0; }
.toc .cat span { color: var(--grey); font-size: 8pt; }
.toc .cols { column-count: 2; column-gap: 9mm; }
.tocline { display: flex; align-items: baseline; font-size: 7.9pt; margin-bottom: 1.1mm;
           break-inside: avoid; }
.tocline .t { flex: 0 1 auto; }
.tocline .d { flex: 1 1 auto; border-bottom: 1px dotted #b0b0b0; margin: 0 1.4mm .7mm;
              min-width: 2.5mm; }
.tocline .p { flex: 0 0 auto; font-variant-numeric: tabular-nums; color: #333; }

/* ── раздел категории ──────────────────────────────────────────────────── */
.catpage { break-before: page; break-after: page; height: @@BODY_H@@mm; position: relative;
           display: flex; flex-direction: column; justify-content: center;
           align-items: center; text-align: center; }
.catpage .brush { position: relative; width: 100%; padding: 7mm 3mm; margin-bottom: 6mm; }
.catpage .brush::before { content: ""; position: absolute; inset: -1mm -2mm;
  background: url("../assets/brand/brush.svg") center / 100% 100% no-repeat; }
.catpage .brush h2 { position: relative; font-family: "Ruslan", serif; font-weight: 400;
  font-size: 25pt; color: #fff; letter-spacing: .05em; margin: 0; }
.catpage .brush .k { position: relative; font-family: "Yeseva", serif; font-size: 7pt;
  letter-spacing: .3em; text-transform: uppercase; color: #d8d2c6; }
.catpage p { max-width: 120mm; font-size: 9pt; color: #333; text-align: center; }
.catpage .cnt { font-family: "Yeseva", serif; font-size: 7.6pt; letter-spacing: .18em;
                text-transform: uppercase; color: var(--grey); margin-top: 5mm; }

/* ── запись ────────────────────────────────────────────────────────────── */
.entry { break-before: auto; }
.entry + .entry { margin-top: 5mm; padding-top: 3mm; border-top: 1.2px solid var(--line, #bdbdbd); }
.eh { break-inside: avoid; break-after: avoid;
      display: flex; align-items: baseline; gap: 3.4mm; margin-bottom: 1.4mm;
      padding-bottom: 2mm; border-bottom: 2.4px solid var(--ink); }
.eh .num { font-family: "Ruslan", serif; font-size: 26pt; line-height: .84;
           color: var(--red); flex: 0 0 auto; }
.eh h2 { font-family: "Ruslan", serif; font-weight: 400; font-size: 15pt;
         line-height: 1.06; letter-spacing: .02em; }
.eh .en { font-family: "Yeseva", serif; font-size: 7pt; letter-spacing: .12em;
          text-transform: uppercase; color: var(--grey); margin: .8mm 0 0; }
.aka { font-size: 7.6pt; color: var(--grey); font-style: italic; margin: 1.4mm 0 2.4mm; }

.pic { margin: 0 0 3mm; break-inside: avoid; }
/* без object-fit: Chrome иначе пересобирает картинку и кладёт её без сжатия */
.pic img { width: 100%; height: auto; max-height: @@PIC_H@@mm; display: block;
           border: .8pt solid #2a2a2a; }
.pic .cap { font-family: "Yeseva", serif; font-size: 5.8pt; letter-spacing: .1em;
            text-transform: uppercase; color: var(--grey); margin-top: .8mm; }

/* ── статблок ──────────────────────────────────────────────────────────── */
.stat { break-inside: avoid; border: 1.2px solid #1c1c1c; background: #f4f2ee;
        padding: 2.8mm 3.4mm; margin: 0 0 3.4mm;
        column-count: 2; column-gap: 6mm; column-rule: .4pt solid #cfcbc2; }
.stat h3 { font-family: "Ruslan", serif; font-weight: 400; font-size: 12pt;
           color: var(--red); margin-bottom: .8mm; column-span: all; }
.stat .sub { font-size: 7.6pt; font-style: italic; color: #444; margin: 0 0 1.6mm; }
.stat .ruler { height: 2px; background: var(--red); margin: 0 0 2mm; }
.stat p { font-size: 7.6pt; margin: 0 0 1.2mm; text-align: left; }
.stat .abil { display: grid; grid-template-columns: repeat(6, 1fr); gap: 1mm;
              margin: 1.6mm 0; text-align: center; max-width: 120mm; }
.stat .abil > div { font-family: "Yeseva", serif; font-size: 6pt;
                    letter-spacing: .06em; color: #333; }
.stat .abil b { display: block; font-family: "Ruslan", serif; font-size: 11pt;
                color: var(--ink); line-height: 1.1; }
.stat .abil span { font-size: 5.6pt; display: block; }
.stat h4 { font-family: "Yeseva", serif; font-size: 8pt; color: var(--red);
           margin: 2mm 0 .8mm; }
.stat ul { margin: 0 0 1mm; padding-left: 4mm; }
.stat li { font-size: 7.4pt; margin-bottom: .6mm; }

/* ── текст записи ──────────────────────────────────────────────────────── */
.flow { column-count: 2; column-gap: 7mm; column-fill: auto;
        column-rule: .4pt solid var(--rule); }
.flow .lead { font-size: 9pt; font-style: italic; color: #222; }
.flow h3 { break-after: avoid; font-family: "Yeseva", serif; font-weight: 400;
           font-size: 9.4pt; margin: 3.6mm 0 1.4mm; padding-top: 1.2mm;
           border-top: 1.2px solid var(--ink); color: var(--ink); }
.flow h3:first-child { margin-top: 0; }
.flow h4 { break-after: avoid; font-family: "Yeseva", serif; font-weight: 400;
           font-size: 8.6pt; margin: 2.8mm 0 1mm; color: var(--red); }
.flow ul { margin: 0 0 3pt; padding-left: 4.4mm; }
.flow li { margin-bottom: .8mm; text-align: left; }
.flow strong { color: #000; }

table.meta { width: 100%; border-collapse: collapse; margin: 2.4mm 0;
             font-family: "Helvetica Neue", Arial, sans-serif; font-size: 7.2pt; }
table.meta th { background: #e2dfd8; color: #111; text-align: left; font-weight: 700;
                padding: 1.2mm 1.4mm; border-top: .8pt solid #333;
                border-bottom: .8pt solid #333; }
table.meta td { padding: 1mm 1.4mm; border-bottom: .4pt solid #cfcfcf; vertical-align: top; }
table.meta td:first-child { color: #555; width: 40%; }
table.meta tr { break-inside: avoid; }
"""


def build_front(items, toc_pages=None, page="digest"):
    cats = {}
    for d in items:
        cats.setdefault(d.get("category", "Иное"), []).append(d)

    toc = []
    for cat in CAT_ORDER:
        if cat not in cats:
            continue
        toc.append('<div class="cat">%s %s <span>(%d)</span></div>'
                   % (CAT_ICON.get(cat, ""), esc(cat), len(cats[cat])))
        rows = []
        for i, d in enumerate(cats[cat], 1):
            pg = ""
            if toc_pages:
                pg = toc_pages.get(d["slug"], "")
            rows.append('<div class="tocline"><span class="t">%d. %s</span>'
                        '<span class="d"></span><span class="p">%s</span></div>'
                        % (i, esc(d["name_ru"]), pg))
        toc.append('<div class="cols">%s</div>' % "".join(rows))

    return """<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8">
<title>Бестиарий «Сверхъестественного» — D&D 5e</title>
<style>%(css)s</style></head><body>

<section class="cover">
  <div class="art"></div>
  <div class="shade"></div>
  <div class="in">
    <div class="brush"><h1>Бестиарий</h1>
      <div class="sub">Сверхъестественного</div></div>
    <div class="tag">Все существа сериала: лор, силы, слабости и способ убийства —
      с адаптацией под правила пятой редакции.</div>
    <div class="sys">Dungeons &amp; Dragons 5e</div>
    <div class="cnt">%(n)d записи · %(imgs)d иллюстраций</div>
  </div>
</section>

<section class="titlepage">
  <div class="trap">%(trap)s</div>
  <h1>БЕСТИАРИЙ</h1>
  <div class="sub">Все существа сериала «Сверхъестественное»</div>
  <div class="sys">Dungeons &amp; Dragons 5e</div>
  <div class="rule"></div>
  <div class="colophon">
    <p style="text-align:center"><b>%(n)d записи.</b> Виды, Альфы, архангелы, Принцы Ада,
    Рыцари Ада, Всадники Апокалипсиса, боги пантеонов и ключевые именные сущности.
    У каждой — лор, силы, слабости, способ убийства и полный статблок пятой редакции.</p>
    <div class="credits">
      <p style="text-align:center">Собрано по <b>Supernatural Wiki</b>.<br>
      «Сверхъестественное» — Warner Bros. Television.<br>
      <b>Dungeons &amp; Dragons</b> — Wizards of the Coast.</p>
      <p style="text-align:center">Неофициальный фанатский материал для домашних игр.
      Не для продажи.</p>
    </div>
  </div>
</section>

<section class="toc">
  <h2>Содержание</h2>
  <div class="rule"></div>
  %(toc)s
</section>

</body></html>
""" % {"css": css_for(page), "n": len(items),
       "imgs": sum(1 for d in items if d.get("_img")),
       "trap": TRAP, "toc": "".join(toc)}


TRAP = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none" '
        'stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
        'stroke-linejoin="round"><circle cx="50" cy="50" r="47.2"/>'
        '<circle cx="50" cy="50" r="42.4" stroke-width="0.9" opacity=".75"/>'
        '<path d="M50,14 L28.84,79.12 L84.24,38.88 L15.76,38.88 L71.16,79.12 Z"/>'
        '<g fill="currentColor" stroke="none"><circle cx="50" cy="14" r="1.7"/>'
        '<circle cx="15.76" cy="38.88" r="1.7"/><circle cx="28.84" cy="79.12" r="1.7"/>'
        '<circle cx="71.16" cy="79.12" r="1.7"/><circle cx="84.24" cy="38.88" r="1.7"/>'
        '</g></svg>')


def entry_html(d, num):
    L = ['<section class="entry" id="%s">' % esc(d["slug"])]
    L.append('<div class="eh"><span class="num">%d</span><div><h2>%s</h2>'
             '<p class="en">%s · %s · CR %s · опасность %s/5</p></div></div>'
             % (num, esc(d["name_ru"]), esc(d.get("name_en", "")),
                esc(d.get("category", "")),
                esc((d.get("dnd") or {}).get("cr", "—")), esc(d.get("threat", "—"))))
    if d.get("aka"):
        L.append('<p class="aka">Также известно как: %s</p>' % esc("; ".join(d["aka"])))
    L.append('<aside class="stat">%s</aside>' % statblock(d))
    L.append('<div class="flow">')
    if d.get("_img"):
        L.append('<figure class="pic"><img src="%s" alt="%s">'
                 '<div class="cap">Кадр из сериала · Supernatural Wiki</div></figure>'
                 % (esc(d["_img"]), esc(d["name_ru"])))
    if d.get("summary"):
        L.append('<p class="lead">%s</p>' % esc(d["summary"]))
    for par in (d.get("lore") or "").split("\n\n"):
        if par.strip():
            L.append("<p>%s</p>" % esc(par.strip()))
    if d.get("powers"):
        L.append("<h3>Силы и способности</h3><ul>")
        L += ["<li>%s</li>" % esc(x) for x in d["powers"]]
        L.append("</ul>")
    if d.get("weaknesses"):
        L.append("<h3>Слабости</h3><ul>")
        L += ["<li>%s</li>" % esc(x) for x in d["weaknesses"]]
        L.append("</ul>")
    if d.get("hunting"):
        L.append("<h3>Как его убить</h3><p>%s</p>" % esc(d["hunting"]))
    if d.get("notable"):
        L.append("<h3>Известные особи</h3><ul>")
        L += ["<li>%s</li>" % esc(x) for x in d["notable"]]
        L.append("</ul>")
    if (d.get("dnd") or {}).get("tactics"):
        L.append("<h4>Тактика</h4><p>%s</p>" % esc(d["dnd"]["tactics"]))
    if (d.get("dnd") or {}).get("ecology"):
        L.append("<h4>Экология</h4><p>%s</p>" % esc(d["dnd"]["ecology"]))
    if d.get("dnd_notes"):
        L.append("<h4>Заметки мастеру</h4><p>%s</p>" % esc(d["dnd_notes"]))
    meta = [("Первое появление", d.get("first_appearance")),
            ("Сезоны", ", ".join(str(x) for x in d.get("seasons", []))),
            ("Тип в D&D", (d.get("dnd") or {}).get("type")),
            ("Класс опасности", "CR %s" % (d.get("dnd") or {}).get("cr", "—")),
            ("Опасность в сериале", "%s/5" % d.get("threat", "—"))]
    meta = [(k, v) for k, v in meta if v]
    if meta:
        L.append('<table class="meta"><thead><tr><th>Карточка</th><th></th></tr></thead><tbody>')
        for k, v in meta:
            L.append("<tr><td>%s</td><td>%s</td></tr>" % (esc(k), esc(v)))
        L.append("</tbody></table>")
    L.append("</div>")
    L.append("</section>")
    return "\n".join(L)


PAGES = {
    "digest": dict(w=163, h=215, body=187, pic=52, cover="../assets/brand/bestiary-cover.jpg"),
    "a4":     dict(w=210, h=297, body=269, pic=52, cover="../assets/brand/bestiary-cover.jpg"),
}


def css_for(page):
    c = PAGES[page]
    return (CSS.replace("@@PAGE_W@@", str(c["w"])).replace("@@PAGE_H@@", str(c["h"]))
               .replace("@@BODY_H@@", str(c["body"])).replace("@@PIC_H@@", str(c["pic"])))


def build(limit=None, page="digest", toc_pages=None):
    items = load()
    if limit:
        items = items[:limit]
    cats = {}
    for d in items:
        cats.setdefault(d.get("category", "Иное"), []).append(d)

    body = []
    for cat in CAT_ORDER:
        group = cats.get(cat)
        if not group:
            continue
        body.append('<section class="catpage"><div class="brush">'
                    '<div class="k">Раздел</div><h2>%s</h2></div>'
                    '<p>%s</p><div class="cnt">%d %s</div></section>'
                    % (esc(cat), esc(CAT_DESC.get(cat, "")), len(group),
                       "запись" if len(group) % 10 == 1 and len(group) != 11 else "записей"))
        for i, d in enumerate(group, 1):
            body.append(entry_html(d, i))

    inner = '<div class="flow-root">%s</div>' % "".join(body)
    doc = """<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><title>Бестиарий — D&D 5e</title>
<style>%(css)s</style></head><body>
%(inner)s
</body></html>""" % {"css": css_for(page), "inner": inner}

    open(OUT, "w", encoding="utf-8").write(doc)
    open(OUT_FRONT, "w", encoding="utf-8").write(build_front(items, toc_pages, page))
    print("бестиарий: %s (%.1f МБ, %d записей)"
          % (os.path.relpath(OUT, ROOT), len(doc) / 1e6, len(items)))
    print("обложка+титул+оглавление: %s" % os.path.relpath(OUT_FRONT, ROOT))
    return items


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--page", choices=["digest", "a4"], default="digest")
    a = ap.parse_args()
    build(a.limit, a.page)
