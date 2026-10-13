#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собирает компактную печатную шпаргалку мастера: только статблоки (site/statblocks.html)."""
import json, glob, os, html, collections, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site", "statblocks.html")
INLINE_TRAP = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" role="img" aria-label="Ловушка дьявола"> <title>Ловушка дьявола</title> <circle cx="50" cy="50" r="47.2" stroke-width="2.2"/> <circle cx="50" cy="50" r="42.4" stroke-width="0.9" opacity=".75"/> <path d="M50,14 L28.84,79.12 L84.24,38.88 L15.76,38.88 L71.16,79.12 Z" stroke-width="2"/> <path d="M50,6.8 L50,4 M38.82,8.27 L38.09,5.57 M28.4,12.59 L27,10.16 M19.45,19.45 L17.47,17.47 M12.59,28.4 L10.16,27 M8.27,38.82 L5.57,38.09 M6.8,50 L4,50 M8.27,61.18 L5.57,61.91 M12.59,71.6 L10.16,73 M19.45,80.55 L17.47,82.53 M28.4,87.41 L27,89.84 M38.82,91.73 L38.09,94.43 M50,93.2 L50,96 M61.18,91.73 L61.91,94.43 M71.6,87.41 L73,89.84 M80.55,80.55 L82.53,82.53 M87.41,71.6 L89.84,73 M91.73,61.18 L94.43,61.91 M93.2,50 L96,50 M91.73,38.82 L94.43,38.09 M87.41,28.4 L89.84,27 M80.55,19.45 L82.53,17.47 M71.6,12.59 L73,10.16 M61.18,8.27 L61.91,5.57" stroke-width="0.9" opacity=".55"/> <g fill="currentColor" stroke="none"><circle cx="50" cy="14" r="1.7"/><circle cx="15.76" cy="38.88" r="1.7"/><circle cx="28.84" cy="79.12" r="1.7"/><circle cx="71.16" cy="79.12" r="1.7"/><circle cx="84.24" cy="38.88" r="1.7"/></g> </svg>'''

CAT_ORDER = ["Монстр", "Демон", "Ангел", "Божество", "Дух", "Ведьма", "Левиафан", "Иное"]
ABIL = [("str", "СИЛ"), ("dex", "ЛОВ"), ("con", "ТЕЛ"),
        ("int", "ИНТ"), ("wis", "МДР"), ("cha", "ХАР")]


def esc(s):
    return html.escape(str(s if s is not None else ""))


def statblock(d):
    s = d.get("dnd") or {}
    L = ['<div class="sb">']
    L.append("<h3>%s</h3>" % esc(d["name_ru"]))
    sub = ", ".join(x for x in [s.get("size"), s.get("type"), s.get("alignment")] if x)
    L.append('<p class="sub">%s <span class="cr">CR %s</span></p>' % (esc(sub), esc(s.get("cr", "—"))))
    L.append('<div class="ruler"></div>')
    for label, key in [("КД", "ac"), ("Хиты", "hp"), ("Скорость", "speed")]:
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
                       ("Сопротивление", "damage_resistances"),
                       ("Иммунитет", "damage_immunities"),
                       ("Иммунитет к состояниям", "condition_immunities"),
                       ("Чувства", "senses"), ("Языки", "languages")]:
        if s.get(key):
            L.append("<p><b>%s</b> %s</p>" % (label, esc(s[key])))
    xp = " (%s опыта)" % format(int(s["xp"]), ",").replace(",", " ") if s.get("xp") else ""
    L.append("<p><b>БМ</b> +%s · <b>Опасность</b> %s%s</p>" % (esc(s.get("pb", "—")), esc(s.get("cr", "—")), xp))
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
    if s.get("tactics"):
        L.append('<h4>Тактика</h4><p>%s</p>' % esc(s["tactics"]))
    L.append("</div>")
    return "\n".join(L)


CSS = """
@page { size: A4; margin: 10mm; }
body { margin:0; font-family: Georgia, serif; color:#1c1710; background:#fff;
       font-size:8pt; line-height:1.3; }
h1 { font-size:22pt; text-align:center; margin:0 0 2mm; }
.cover { text-align:center; padding-top:80mm; page-break-after:always; }
.cover .mark { width:30mm; height:30mm; color:#b7222b; margin:0 auto 6mm; }
.cover .mark svg { width:100%; height:100%; display:block; }
.cover p { color:#6a5f4e; font-size:10pt; }
.cols { column-count:2; column-gap:7mm; }
.sb { break-inside:avoid; page-break-inside:avoid; border:1px solid #b9a887; background:#faf6ec;
      border-radius:3px; padding:2.6mm 3mm; margin:0 0 4mm; }
.sb h3 { font-size:11.4pt; color:#7a1420; font-variant:small-caps; margin:0; }
.sb .sub { font-style:italic; font-size:7.6pt; color:#4a3d2c; margin:0 0 1mm; }
.sb .cr { float:right; font-style:normal; font-weight:700; color:#7a1420; }
.ruler { height:2px; background:#7a1420; margin:1mm 0; }
.abil { display:flex; justify-content:space-between; text-align:center; font-size:7.2pt; margin:1mm 0; }
.abil b { display:block; font-size:9pt; color:#7a1420; }
.sb h4 { font-size:8pt; color:#7a1420; border-bottom:1px solid #d8c9a8; margin:1.8mm 0 .7mm; }
.sb p { margin:0 0 .8mm; }
h2.cat { font-size:13pt; color:#b7222b; border-bottom:2px solid #b7222b;
         margin:0 0 3mm; page-break-after:avoid; }
.sec { page-break-before:always; }
"""


def main():
    imgs = {}
    ip = os.path.join(ROOT, "data", "raw", "images.json")
    if os.path.exists(ip):
        for slug, rec in json.load(open(ip)).items():
            if rec.get("local") and os.path.exists(os.path.join(ROOT, "site", rec["local"])):
                imgs[slug] = rec["local"]
    items = []
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "creatures", "*.json"))):
        try:
            items.append(json.load(open(f)))
        except Exception:
            pass
    cre = [d for d in items if d.get("kind") in ("creature", "being")]
    app = [d for d in items if d.get("kind") in ("place", "artifact", "lore")]
    by_cat = collections.defaultdict(list)
    for d in cre:
        by_cat[d.get("category", "Иное")].append(d)
    today = datetime.date.today().strftime("%d.%m.%Y")

    L = ["<!DOCTYPE html><html lang='ru'><head><meta charset='utf-8'>",
         "<title>Статблоки D&amp;D 5e — бестиарий «Сверхъестественного»</title>",
         "<style>%s</style></head><body>" % CSS]
    L.append('<div class="cover"><div class="mark">' + INLINE_TRAP + '</div>'
             "<h1>Статблоки D&amp;D 5e</h1>"
             "<p>Бестиарий «Сверхъестественного» · шпаргалка мастера<br>"
             "%d существ · %d записей приложения · сборка %s</p></div>" % (len(cre), len(app), today))

    first = True
    for cat in CAT_ORDER:
        arr = sorted(by_cat.get(cat, []), key=lambda x: x["name_ru"])
        if not arr:
            continue
        L.append('<div class="sec"><h2 class="cat">%s (%d)</h2><div class="cols">' % (cat, len(arr)))
        L += [statblock(d) for d in arr]
        L.append("</div></div>")
        first = False
    if app:
        L.append('<div class="sec"><h2 class="cat">Приложение: мир, артефакты, понятия (%d)</h2>'
                 '<div class="cols">' % len(app))
        L += [statblock(d) for d in sorted(app, key=lambda x: x["name_ru"])]
        L.append("</div></div>")
    L.append("</body></html>")
    open(OUT, "w").write("\n".join(L))
    print("statblocks.html:", os.path.getsize(OUT), "bytes |", len(cre) + len(app), "статблоков")


if __name__ == "__main__":
    main()
