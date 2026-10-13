#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собирает печатную версию бестиария (site/book.html) для экспорта в PDF."""
import json, glob, os, html, collections, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site", "book.html")

INLINE_TRAP = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" role="img" aria-label="Ловушка дьявола"> <title>Ловушка дьявола</title> <circle cx="50" cy="50" r="47.2" stroke-width="2.2"/> <circle cx="50" cy="50" r="42.4" stroke-width="0.9" opacity=".75"/> <path d="M50,14 L28.84,79.12 L84.24,38.88 L15.76,38.88 L71.16,79.12 Z" stroke-width="2"/> <path d="M50,6.8 L50,4 M38.82,8.27 L38.09,5.57 M28.4,12.59 L27,10.16 M19.45,19.45 L17.47,17.47 M12.59,28.4 L10.16,27 M8.27,38.82 L5.57,38.09 M6.8,50 L4,50 M8.27,61.18 L5.57,61.91 M12.59,71.6 L10.16,73 M19.45,80.55 L17.47,82.53 M28.4,87.41 L27,89.84 M38.82,91.73 L38.09,94.43 M50,93.2 L50,96 M61.18,91.73 L61.91,94.43 M71.6,87.41 L73,89.84 M80.55,80.55 L82.53,82.53 M87.41,71.6 L89.84,73 M91.73,61.18 L94.43,61.91 M93.2,50 L96,50 M91.73,38.82 L94.43,38.09 M87.41,28.4 L89.84,27 M80.55,19.45 L82.53,17.47 M71.6,12.59 L73,10.16 M61.18,8.27 L61.91,5.57" stroke-width="0.9" opacity=".55"/> <g fill="currentColor" stroke="none"><circle cx="50" cy="14" r="1.7"/><circle cx="15.76" cy="38.88" r="1.7"/><circle cx="28.84" cy="79.12" r="1.7"/><circle cx="71.16" cy="79.12" r="1.7"/><circle cx="84.24" cy="38.88" r="1.7"/></g> </svg>'''

CAT_ORDER = ["Монстр", "Демон", "Ангел", "Божество", "Дух", "Ведьма", "Левиафан", "Иное"]
CAT_ICON = {"Монстр": "🐾", "Демон": "😈", "Ангел": "😇", "Божество": "⚡",
            "Дух": "👻", "Ведьма": "🕯", "Левиафан": "🐍", "Иное": "🌀"}
ABIL = [("str", "СИЛ"), ("dex", "ЛОВ"), ("con", "ТЕЛ"),
        ("int", "ИНТ"), ("wis", "МДР"), ("cha", "ХАР")]


def esc(s):
    return html.escape(str(s if s is not None else ""))


def load():
    imgs = {}
    p = os.path.join(ROOT, "data", "raw", "images.json")
    if os.path.exists(p):
        for slug, rec in json.load(open(p)).items():
            if rec.get("local") and os.path.exists(os.path.join(ROOT, "site", rec["local"])):
                imgs[slug] = rec
    items = []
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "creatures", "*.json"))):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        r = imgs.get(d["slug"])
        if r:
            d["_img"] = r["local"]
        items.append(d)
    items.sort(key=lambda d: (CAT_ORDER.index(d["category"]) if d.get("category") in CAT_ORDER else 99,
                              d.get("name_ru", "")))
    return items


def statblock(d):
    s = d.get("dnd") or {}
    L = ['<div class="sb">']
    L.append("<h3>%s</h3>" % esc(d["name_ru"]))
    sub = ", ".join(x for x in [s.get("size"), s.get("type"), s.get("alignment")] if x)
    L.append('<p class="sub">%s</p>' % esc(sub))
    L.append('<div class="ruler"></div>')
    for label, key in [("Класс доспеха", "ac"), ("Хиты", "hp"), ("Скорость", "speed")]:
        if s.get(key):
            L.append("<p><b>%s</b> %s</p>" % (label, esc(s[key])))
    a = s.get("abilities") or {}
    L.append('<div class="abil">')
    for k, n in ABIL:
        v = a.get(k)
        if v is None:
            L.append("<div></div>"); continue
        v = int(v)
        L.append("<div><b>%d</b><span>%s %s%d</span></div>" % (v, n, "+" if v >= 10 else "", (v - 10) // 2))
    L.append("</div>")
    for label, key in [("Спасброски", "saves"), ("Навыки", "skills"),
                       ("Уязвимость к урону", "damage_vulnerabilities"),
                       ("Сопротивление урону", "damage_resistances"),
                       ("Иммунитет к урону", "damage_immunities"),
                       ("Иммунитет к состояниям", "condition_immunities"),
                       ("Чувства", "senses"), ("Языки", "languages")]:
        if s.get(key):
            L.append("<p><b>%s</b> %s</p>" % (label, esc(s[key])))
    if s.get("pb"):
        L.append("<p><b>Бонус мастерства</b> +%s</p>" % esc(s["pb"]))
    if s.get("cr"):
        xp = " (%s опыта)" % format(int(s["xp"]), ",").replace(",", " ") if s.get("xp") else ""
        L.append("<p><b>Уровень опасности</b> %s%s</p>" % (esc(s["cr"]), xp))
    for title, key in [("Особенности", "traits"), ("Действия", "actions"),
                       ("Бонусные действия", "bonus_actions"), ("Реакции", "reactions"),
                       ("Легендарные действия", "legendary_actions"),
                       ("Действия в логове", "lair_actions")]:
        arr = s.get(key) or []
        if not arr:
            continue
        L.append('<h4>%s</h4>' % title)
        for e in arr:
            if isinstance(e, str):
                L.append("<p>%s</p>" % esc(e))
            else:
                L.append("<p><i>%s.</i> %s</p>" % (esc(e.get("name", "")), esc(e.get("text", ""))))
    L.append("</div>")
    return "\n".join(L)


def entry(d, num):
    L = ['<section class="entry" id="%s">' % esc(d["slug"])]
    L.append('<header class="eh"><span class="num">%d</span><h2>%s</h2>' % (num, esc(d["name_ru"])))
    L.append('<p class="en">%s · %s · CR %s · опасность %s/5</p></header>' %
             (esc(d.get("name_en", "")), esc(d.get("category", "")),
              esc((d.get("dnd") or {}).get("cr", "—")), esc(d.get("threat", "—"))))
    if d.get("aka"):
        L.append('<p class="aka">Также известно как: %s</p>' % esc("; ".join(d["aka"])))
    L.append('<div class="cols">')
    L.append('<div class="left">')
    if d.get("_img"):
        L.append('<figure class="pic"><img src="%s" alt="%s"></figure>'
                 % (esc(d["_img"]), esc(d["name_ru"])))
    L.append("<p class='lead'>%s</p>" % esc(d.get("summary", "")))
    for par in (d.get("lore") or "").split("\n\n"):
        if par.strip():
            L.append("<p>%s</p>" % esc(par.strip()))
    if d.get("powers"):
        L.append("<h4>Силы и способности</h4><ul>")
        L += ["<li>%s</li>" % esc(x) for x in d["powers"]]
        L.append("</ul>")
    if d.get("weaknesses"):
        L.append("<h4>Слабости</h4><ul>")
        L += ["<li>%s</li>" % esc(x) for x in d["weaknesses"]]
        L.append("</ul>")
    if d.get("hunting"):
        L.append("<h4>Как его убить</h4><p>%s</p>" % esc(d["hunting"]))
    if d.get("notable"):
        L.append("<h4>Известные особи</h4><ul>")
        L += ["<li>%s</li>" % esc(x) for x in d["notable"]]
        L.append("</ul>")
    meta = [("Первое появление", d.get("first_appearance")),
            ("Сезоны", ", ".join(str(x) for x in d.get("seasons", []))),
            ("Тип в D&D", (d.get("dnd") or {}).get("type")),
            ("Класс опасности", "CR %s" % (d.get("dnd") or {}).get("cr", "—"))]
    meta = [(k, v) for k, v in meta if v]
    if meta:
        L.append('<table class="meta">')
        for k, v in meta:
            L.append("<tr><td>%s</td><td>%s</td></tr>" % (esc(k), esc(v)))
        L.append("</table>")
    L.append("</div>")
    L.append('<div class="right">%s' % statblock(d))
    if (d.get("dnd") or {}).get("tactics"):
        L.append("<h4>Тактика</h4><p>%s</p>" % esc(d["dnd"]["tactics"]))
    if (d.get("dnd") or {}).get("ecology"):
        L.append("<h4>Экология</h4><p>%s</p>" % esc(d["dnd"]["ecology"]))
    if d.get("dnd_notes"):
        L.append("<h4>Заметки мастеру</h4><p>%s</p>" % esc(d["dnd_notes"]))
    L.append("</div></div></section>")
    return "\n".join(L)


CSS = """
@page { size: A4; margin: 11mm 11mm 12mm; }
* { box-sizing: border-box; }
body { margin:0; font-family: Georgia, "Times New Roman", serif; color:#1c1710;
       background:#fff; font-size:8.7pt; line-height:1.33; }
h1,h2,h3,h4 { margin:0; }
.cover { height: 262mm; display:flex; flex-direction:column; justify-content:center;
         align-items:center; text-align:center; page-break-after: always; }
.cover .mark { width:34mm; height:34mm; color:#b7222b; margin:0 auto 8mm; }
.cover .mark svg { width:100%; height:100%; display:block; }
.cover h1 { font-size:30pt; line-height:1.15; letter-spacing:.5px; }
.cover h1 small { display:block; font-size:15pt; font-weight:400; font-style:italic; color:#6a5f4e; margin-top:3mm; }
.cover .sub { margin-top:8mm; font-size:11pt; color:#5a5142; max-width:120mm; }
.cover .stats { margin-top:12mm; font-size:9.5pt; color:#7a7060; }
.cover .rule { width:60mm; height:2px; background:#b7222b; margin:7mm 0; }
.toc { page-break-after: always; }
.toc h2 { font-size:17pt; border-bottom:2px solid #b7222b; padding-bottom:2mm; margin-bottom:4mm; }
.toc h3 { font-size:11pt; margin:4mm 0 1.5mm; color:#b7222b; }
.toc ol { margin:0; padding-left:6mm; columns:2; column-gap:10mm; font-size:9pt; }
.toc li { margin-bottom:0.6mm; break-inside:avoid; }
.catpage { page-break-before: always; padding-top:70mm; text-align:center; }
.catpage .ic { font-size:40pt; }
.catpage h2 { font-size:26pt; margin-top:4mm; }
.catpage p { color:#6a5f4e; margin-top:3mm; }
.entry { padding-top:5mm; margin-top:4mm; border-top:1px solid #e0d6bd; }
.entry:first-of-type { border-top:none; }
.eh { border-bottom:2px solid #b7222b; padding-bottom:1.4mm; margin-bottom:3mm;
      break-after:avoid; page-break-after:avoid; }
.eh h2 { font-size:16.5pt; display:inline; }
.eh .num { display:inline-block; min-width:9mm; color:#b7222b; font-size:12pt; }
.en { font-size:9pt; color:#6a5f4e; font-style:italic; margin-top:1mm; }
.aka { font-size:8.6pt; color:#6a5f4e; margin:1.5mm 0 0; }
.cols { display:flex; gap:6mm; align-items:flex-start; }
.left { flex:1.06; } .right { flex:.94; }
.pic { margin:0 0 2.5mm; }
.pic img { width:100%; max-height:52mm; object-fit:cover; border-radius:3px; border:1px solid #cbbf9f; }
.lead { font-size:9.6pt; font-weight:600; }
h4 { font-size:8.4pt; text-transform:uppercase; letter-spacing:.8px; color:#8a6a20;
     margin:2.6mm 0 .9mm; border-bottom:1px solid #ddd0b0; padding-bottom:.6mm; }
p { margin:0 0 1.5mm; }
ul { margin:0 0 1.5mm; padding-left:4.2mm; }
li { margin-bottom:.4mm; }
.meta { width:100%; border-collapse:collapse; font-size:7.9pt; margin-top:1.5mm; }
.meta td { border-bottom:1px dotted #ccc; padding:.8mm 0; vertical-align:top; }
.meta td:first-child { color:#7a7060; width:38%; }
.sb { background:#f7f2e6; border:1px solid #b9a887; border-radius:3px;
      padding:2.8mm 3.2mm; font-size:8.1pt; }
.sb h3 { font-size:12.6pt; color:#7a1420; font-variant:small-caps; }
.sb .sub { font-style:italic; font-size:8.6pt; color:#4a3d2c; margin-bottom:1.5mm; }
.ruler { height:2px; background:#7a1420; clip-path:polygon(0 40%,100% 0,100% 60%,0 100%);
         margin:1.5mm 0; }
.abil { display:flex; justify-content:space-between; text-align:center; margin:1.1mm 0; font-size:7.7pt; }
.abil b { display:block; font-size:10pt; color:#7a1420; }
.sb h4 { font-size:8.6pt; text-transform:none; letter-spacing:0; color:#7a1420;
         border-bottom:1px solid #b9a887; margin:2.5mm 0 1mm; }
.sb p { margin:0 0 1mm; }
.foot { text-align:center; color:#8a8070; font-size:8.5pt; padding-top:8mm; }
"""


def main():
    items = load()
    cre = [d for d in items if d.get("kind") in ("creature", "being")]
    app = [d for d in items if d.get("kind") in ("place", "artifact", "lore")]
    today = datetime.date.today().strftime("%d.%m.%Y")
    with_img = sum(1 for d in items if d.get("_img"))

    L = ["<!DOCTYPE html><html lang='ru'><head><meta charset='utf-8'>",
         "<title>Бестиарий «Сверхъестественного» — D&amp;D 5e</title>",
         "<style>%s</style></head><body>" % CSS]

    L.append('<div class="cover"><div class="mark">' + INLINE_TRAP + '</div>'
             '<h1>Бестиарий<br>«Сверхъестественного»<small>Supernatural &middot; Dungeons &amp; Dragons 5e</small></h1>'
             '<div class="rule"></div>'
             '<p class="sub">Все существа сериала с адаптацией под правила пятой редакции: '
             'лор, силы, слабости, способ охоты и полные статблоки.</p>'
             '<p class="stats">%d записей &middot; %d существ и высших сущностей &middot; '
             '%d локаций, артефактов и понятий &middot; %d иллюстраций<br>сборка %s</p></div>'
             % (len(items), len(cre), len(app), with_img, today))

    # оглавление
    by_cat = collections.defaultdict(list)
    for d in cre:
        by_cat[d.get("category", "Иное")].append(d)
    L.append('<div class="toc"><h2>Содержание</h2>')
    n = 0
    for cat in CAT_ORDER:
        arr = sorted(by_cat.get(cat, []), key=lambda x: x["name_ru"])
        if not arr:
            continue
        L.append("<h3>%s %s (%d)</h3><ol>" % (CAT_ICON.get(cat, ""), cat, len(arr)))
        for d in arr:
            n += 1
            d["_n"] = n
            L.append('<li><a href="#%s">%s</a> — CR %s</li>'
                     % (esc(d["slug"]), esc(d["name_ru"]), esc((d.get("dnd") or {}).get("cr", "—"))))
        L.append("</ol>")
    if app:
        L.append("<h3>📦 Приложение: мир, артефакты и понятия (%d)</h3><ol>" % len(app))
        for i, d in enumerate(sorted(app, key=lambda x: x["name_ru"]), 1):
            d["_n"] = i
            L.append('<li><a href="#%s">%s</a></li>' % (esc(d["slug"]), esc(d["name_ru"])))
        L.append("</ol>")
    L.append("</div>")

    for cat in CAT_ORDER:
        arr = sorted(by_cat.get(cat, []), key=lambda x: x["name_ru"])
        if not arr:
            continue
        L.append('<div class="catpage"><div class="ic">%s</div><h2>%s</h2>'
                 "<p>%d записей</p></div>" % (CAT_ICON.get(cat, ""), cat, len(arr)))
        L += [entry(d, d["_n"]) for d in arr]

    if app:
        L.append('<div class="catpage"><div class="ic">📦</div><h2>Приложение</h2>'
                 "<p>Локации, артефакты, организации и понятия — %d записей</p></div>" % len(app))
        L += [entry(d, d["_n"]) for d in sorted(app, key=lambda x: x["name_ru"])]

    L.append('<div class="foot">Неофициальный фанатский материал. Supernatural — Warner Bros. Television; '
             "Dungeons &amp; Dragons — Wizards of the Coast. Факты собраны по Supernatural Wiki.</div>")
    L.append("</body></html>")
    open(OUT, "w").write("\n".join(L))
    print("book:", OUT, os.path.getsize(OUT), "bytes |", len(items), "записей", with_img, "иллюстраций")


if __name__ == "__main__":
    main()
