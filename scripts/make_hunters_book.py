#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собирает печатный бестиарий «Охотников» — карточки GUMSHOE книгой.

Оформление то же, что у книги правил и бестиария D&D: формат A4, две
колонки, тёмные полосы колонтитулов, акцидентные шрифты.

  python3 scripts/make_hunters_book.py            # все 354 записи
  python3 scripts/make_hunters_book.py --limit 12 # проба
"""
import argparse
import glob
import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_bestiary_book import CAT_DESC, CSS, PAGES, TRAP, css_for  # noqa: E402
from make_book import esc  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site-gumshoe", "bestiary.html")
OUT_FRONT = os.path.join(ROOT, "site-gumshoe", "bestiary-front.html")

CAT_ORDER = ["Монстр", "Демон", "Ангел", "Божество", "Дух", "Ведьма", "Левиафан", "Иное"]

EXTRA_CSS = """
/* ── статблок GUMSHOE ──────────────────────────────────────────────────── */
/* вложенные колонки внутри статблока давали пустую половину: карточки
   короче, чем статблоки D&D, и балансировка не сходилась */
.stat { column-count: 1; }
.stat .gsgrid { display: grid; grid-template-columns: 1fr 1.35fr; gap: 4mm; min-width: 0; }
.stat table.pools { width: 100%; border-collapse: collapse;
                    font-family: "Helvetica Neue", Arial, sans-serif; font-size: 7.4pt; }
.stat table.pools td { padding: .7mm 0; border-bottom: .4pt solid #dcd8cf; }
.stat table.pools td:last-child { text-align: right; font-weight: 700; width: 12mm;
                                  font-variant-numeric: tabular-nums; }
.stat .gscombat p { font-size: 7.5pt; margin: 0 0 1.4mm; }
.stat .gscombat b { font-family: "Yeseva", serif; font-weight: 400; color: #111; }
.stat h4.gsh { font-family: "Yeseva", serif; font-size: 8pt; color: var(--red);
               margin: 2mm 0 .8mm; }
.stat ul.cl { margin: 0; padding-left: 4mm; }
.stat ul.cl li { font-size: 7.4pt; margin-bottom: .7mm; }
.stat ul.cl b { color: var(--red); }
.stat .spend { font-family: "Yeseva", serif; font-size: 6.2pt; color: #555;
               border: .6pt solid #999; border-radius: 1mm; padding: 0 .8mm; margin-left: .6mm; }

.core { border-left: 2.4px solid var(--red); background: #f4f2ee; padding: 1.8mm 2.4mm;
        margin: 2.4mm 0; break-inside: avoid; }
.core b { display: block; font-family: "Yeseva", serif; font-size: 8pt; color: var(--red);
          margin-bottom: .6mm; }
.core p { font-size: 7.8pt; margin: 0; text-align: left; }
"""


def load():
    """Карточки GUMSHOE + картинки, как в книге D&D."""
    imgs = {}
    p = os.path.join(ROOT, "data", "raw", "images.json")
    if os.path.exists(p):
        for slug, rec in json.load(open(p)).items():
            if rec.get("local") and os.path.exists(os.path.join(ROOT, "site", rec["local"])):
                imgs[slug] = rec["local"]
    items = []
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "gumshoe", "*.json"))):
        if os.path.basename(f) in ("skeleton.json",):
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if "slug" not in d:
            continue
        if d["slug"] in imgs:
            # книга лежит в site-gumshoe/, картинки — в site/img/
            d["_img"] = "../site/" + imgs[d["slug"]]
        items.append(d)
    items.sort(key=lambda d: (CAT_ORDER.index(d["category"]) if d.get("category") in CAT_ORDER else 99,
                              d.get("name_ru", "")))
    return items


def statblock(d):
    ab = d.get("abilities") or {}
    pools = "".join("<tr><td>%s</td><td>%s</td></tr>" % (esc(k), esc(v))
                    for k, v in ab.items())
    st = d.get("stability") or {}
    combat = []
    if d.get("hit_threshold") is not None:
        combat.append("<p><b>Порог попадания</b> %s</p>" % esc(d["hit_threshold"]))
    if d.get("damage"):
        combat.append("<p><b>Урон</b> %s</p>" % esc(d["damage"]))
    if d.get("armor"):
        combat.append("<p><b>Броня</b> %s</p>" % esc(d["armor"]))
    if st:
        combat.append("<p><b>Стабильность</b> проверка %s · при виде %s</p>"
                      % (esc(st.get("test", "—")), esc(st.get("witnessed", "—"))))

    sp = ""
    if d.get("special"):
        sp = "<h4 class='gsh'>Особое</h4><ul class='cl'>"
        for x in d["special"]:
            sp += "<li><b>%s.</b> %s</li>" % (esc(x.get("name", "")), esc(x.get("text", "")))
        sp += "</ul>"

    # название уже стоит в шапке записи — в статблоке не повторяем
    return ('<div class="gsgrid"><table class="pools">%s</table>'
            '<div class="gscombat">%s</div></div>%s'
            % (pools, "".join(combat), sp))


def entry_html(d, num):
    L = ['<section class="entry" id="%s">' % esc(d["slug"])]
    L.append('<div class="eh"><span class="num">%d</span><div><h2>%s</h2>'
             '<p class="en">%s · %s · угроза %s/5</p></div></div>'
             % (num, esc(d["name_ru"]), esc(d.get("name_en", "")),
                esc(d.get("category", "")), esc(d.get("threat", "—"))))
    L.append('<aside class="stat">%s</aside>' % statblock(d))

    L.append('<div class="flow">')
    if d.get("_img"):
        L.append('<figure class="pic"><img src="%s" alt="%s">'
                 '<div class="cap">Кадр из сериала · Supernatural Wiki</div></figure>'
                 % (esc(d["_img"]), esc(d["name_ru"])))
    if d.get("horror"):
        L.append('<p class="lead">%s</p>' % esc(d["horror"]))

    if d.get("clues"):
        L.append("<h3>Улики</h3><ul class='cl'>")
        for c in d["clues"]:
            badge = ('<span class="spend">трата %s</span>' % esc(c["spend"])) if c.get("spend") else ""
            L.append("<li><b>%s.</b>%s %s</li>" % (esc(c.get("ability", "")), badge,
                                                   esc(c.get("text", ""))))
        L.append("</ul>")
    if d.get("core_clue"):
        L.append('<div class="core"><b>Ядро дела</b><p>%s</p></div>' % esc(d["core_clue"]))
    if d.get("rule"):
        L.append("<h3>Правило твари</h3><p>%s</p>" % esc(d["rule"]))
    if d.get("notes"):
        L.append("<h3>Заметки ведущему</h3><p>%s</p>" % esc(d["notes"]))

    meta = [("Оригинал", d.get("name_en")),
            ("Категория", d.get("category")),
            ("Тип", d.get("kind")),
            ("Угроза", "%s/5" % d.get("threat", "—"))]
    meta = [(k, v) for k, v in meta if v]
    if meta:
        L.append('<table class="meta"><thead><tr><th>Карточка</th><th></th></tr></thead><tbody>')
        for k, v in meta:
            L.append("<tr><td>%s</td><td>%s</td></tr>" % (esc(k), esc(v)))
        L.append("</tbody></table>")
    L.append("</div></section>")
    return "\n".join(L)


def build_front(items, toc_pages=None, page="a4"):
    cats = {}
    for d in items:
        cats.setdefault(d.get("category", "Иное"), []).append(d)
    toc = []
    for cat in CAT_ORDER:
        if cat not in cats:
            continue
        toc.append('<div class="cat">%s <span>(%d)</span></div>' % (esc(cat), len(cats[cat])))
        rows = []
        for i, d in enumerate(cats[cat], 1):
            pg = (toc_pages or {}).get(d["slug"], "")
            rows.append('<div class="tocline"><span class="t">%d. %s</span>'
                        '<span class="d"></span><span class="p">%s</span></div>'
                        % (i, esc(d["name_ru"]), pg))
        toc.append('<div class="cols">%s</div>' % "".join(rows))

    return """<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8">
<title>Бестиарий охотника — GUMSHOE</title>
<style>%(css)s</style></head><body>

<section class="cover">
  <div class="art"></div>
  <div class="shade"></div>
  <div class="in">
    <div class="brush"><h1>Бестиарий</h1>
      <div class="sub">охотника</div></div>
    <div class="tag">Все существа сериала: что видят сыщики, что они узнают
      и чем это убивается — под систему GUMSHOE.</div>
    <div class="sys">Охотники · GUMSHOE</div>
    <div class="cnt">%(n)d записи · %(imgs)d иллюстраций</div>
  </div>
</section>

<section class="titlepage">
  <div class="trap">%(trap)s</div>
  <h1>БЕСТИАРИЙ</h1>
  <div class="sub">Все существа сериала «Сверхъестественное»</div>
  <div class="sys">Охотники · GUMSHOE</div>
  <div class="rule"></div>
  <div class="colophon">
    <p style="text-align:center"><b>%(n)d записи.</b> У каждой — пулы способностей,
    Порог попадания, урон, потеря Стабильности, особые свойства, улики с указанием
    способности и Сл, ядро дела, правило твари и заметки ведущему.</p>
    <div class="credits">
      <p style="text-align:center">Собрано по <b>Supernatural Wiki</b>.<br>
      «Сверхъестественное» — Warner Bros. Television.<br>
      <b>GUMSHOE</b> — Pelgrane Press, автор системы Робин Д. Лоуз.</p>
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
""" % {"css": css_for(page) + EXTRA_CSS, "n": len(items),
       "imgs": sum(1 for d in items if d.get("_img")),
       "trap": TRAP, "toc": "".join(toc)}


def build(limit=None, page="a4", toc_pages=None):
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
                    '<p>%s</p><div class="cnt">%d записей</div></section>'
                    % (esc(cat), esc(CAT_DESC.get(cat, "")), len(group)))
        for i, d in enumerate(group, 1):
            body.append(entry_html(d, i))

    doc = """<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><title>Бестиарий охотника</title>
<style>%(css)s</style></head><body>
%(inner)s
</body></html>""" % {"css": css_for(page) + EXTRA_CSS, "inner": "".join(body)}

    open(OUT, "w", encoding="utf-8").write(doc)
    open(OUT_FRONT, "w", encoding="utf-8").write(build_front(items, toc_pages, page))
    print("бестиарий: %s (%.1f МБ, %d записей)"
          % (os.path.relpath(OUT, ROOT), len(doc) / 1e6, len(items)))
    return items


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--page", choices=list(PAGES), default="a4")
    a = ap.parse_args()
    build(a.limit, a.page)
