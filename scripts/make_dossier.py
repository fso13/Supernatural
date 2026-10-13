#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собирает «Досье охотника» — лист персонажа для «Охотников».

Оформление повторяет «Досье агента» из «Эзотеррористов»: мазок кистью
с названием игры, две колонки, способности строками «название — рейтинг |
запас», дорожки Здоровья и Стабильности, блок напоминаний внизу.

  python3 scripts/make_dossier.py          # -> site-gumshoe/dossier.html
"""
import html
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site-gumshoe", "dossier.html")

INVESTIGATIVE = [
    ("Академические", 5, ["Антропология", "Археология", "Архивы", "Баллистика", "Демонология",
                          "История", "Криптозоология", "Медицина", "Оккультизм", "Теология",
                          "Химия", "Языки"]),
    ("Межличностные", 4, ["Допрос", "Запугивание", "Лесть", "Ложь", "Проницательность",
                          "Репутация", "Уличное чутьё"]),
    ("Технические", 4, ["Взлом", "Наружное наблюдение", "Осмотр места", "Слежка",
                        "Фотосъёмка", "Эксплуатация"]),
]

GENERAL = ["Атлетика", "Бдительность", "Бой", "Вера", "Вождение", "Здоровье", "Первая помощь",
           "Подготовка", "Связи", "Скрытность", "Стабильность", "Стрельба", "Воля"]


def ability_row(name, extra=False):
    cls = "ab extra" if extra else "ab"
    return ('<div class="%s"><span class="nm">%s</span>'
            '<span class="rt"></span><span class="bar"></span><span class="pl"></span></div>'
            % (cls, html.escape(name)))


def track(high, low):
    hi = " ".join(str(i) for i in range(high, 0, -1))
    lo = " ".join(("0" if i == 0 else str(i)) for i in range(0, low - 1, -1))
    return '<div class="trk"><div class="nums">%s</div><div class="nums">%s</div></div>' % (hi, lo)


def build():
    left = ['<h2 class="sect">Расследовательские<br>способности</h2>']
    for title, blanks, names in INVESTIGATIVE:
        left.append('<div class="hd"><span class="g">%s</span>'
                    '<span class="c1">рейтинг</span><span class="c2">запас</span></div>' % title)
        left += [ability_row(n) for n in names]
        left += [ability_row("", extra=True) for _ in range(blanks)]

    gen = ['<h2 class="sect sub">Общие способности</h2>',
           '<div class="hd gen"><span class="g"></span>'
           '<span class="c1">рейтинг</span><span class="c2">запас</span></div>']
    gen += [ability_row(n) for n in GENERAL]

    right = f'''
    <div class="two">
      <div class="fld"><label>Имя</label><span class="ln"></span></div>
      <div class="fld"><label>Игрок</label><span class="ln"></span></div>
    </div>
    <div class="fld"><label>Драйв</label><span class="ln"></span>
      <div class="hintline">Долг · Месть · Искупление · Знание · Защита · Азарт</div></div>
    <div class="fld"><label>Легенда</label><span class="ln"></span>
      <div class="hintline">кем представляешься в морге, в участке, на пороге дома</div></div>
    <div class="fld"><label>Источники стабильности</label><span class="ln"></span>
      <span class="ln"></span>
      <div class="hintline">только люди. Разговор с ними возвращает Стабильность</div></div>

    <div class="combat">
      <div class="crow"><label>Защита</label><span class="box"></span></div>
      <div class="wcol">
        <div class="wh"><span>Оружие</span><span>модификатор</span></div>
        <div class="wr"><span class="ln"></span><span class="ln short"></span></div>
        <div class="wr"><span class="ln"></span><span class="ln short"></span></div>
      </div>
    </div>
    <div class="hintline under">Безоружный −2 · нож −1 · пистолет +0 · дробовик в упор +2</div>

    <div class="tracks">
      <div class="trkblk"><label>Здоровье</label>{track(12, -12)}
        <div class="hintline">на 0 — тяжёлое ранение, на −5 — мёртв</div></div>
      <div class="trkblk"><label>Стабильность</label>{track(12, -12)}
        <div class="hintline">на 0 — срыв и шрам. Сном не восстанавливается</div></div>
    </div>

    <div class="trkblk">
      <label>Убеждённость</label>
      <div class="boxes">{"".join('<span class="bx"></span>' for _ in range(10))}</div>
      <div class="hintline">не растёт никогда. На 0 охотник уходит из дела</div>
    </div>

    <div class="general">{"".join(gen)}</div>

    <div class="tail">
    <div class="scars">
      <label>Шрамы</label>
      <div class="scarrow"><span>1</span><span class="ln"></span></div>
      <div class="scarrow"><span>2</span><span class="ln"></span></div>
      <div class="scarrow"><span>3</span><span class="ln"></span></div>
      <div class="hintline">третий шрам — уход из дела</div>
    </div>

    <div class="exp">
      <label>Опыт и рост</label>
      <div class="exrow"><span>Свободных ОО</span><span class="ln"></span></div>
      <div class="exrow"><span>Узлы архетипа</span><span class="ln"></span></div>
      <div class="hintline">узел — 3 ОО · +1 к общей — 1 ОО · +1 к расследовательской — 2 ОО</div>
    </div>
    </div>
    '''

    doc = f'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Досье охотника — «Охотники» на GUMSHOE</title>
<link rel="icon" type="image/svg+xml" href="../assets/brand/favicon.svg">
<style>
@font-face {{ font-family: "Ruslan"; font-weight: 400; font-style: normal;
             src: url("../assets/fonts/RuslanDisplay-Regular.ttf") format("truetype"); }}
@font-face {{ font-family: "Yeseva"; font-weight: 400; font-style: normal;
             src: url("../assets/fonts/YesevaOne-Regular.ttf") format("truetype"); }}

@page {{ size: A4; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: #fff;
  font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
  color: #111; -webkit-font-smoothing: antialiased; }}

.sheet {{ width: 210mm; height: 297mm; padding: 11mm 12mm 9mm; position: relative;
          overflow: hidden; }}

/* ── шапка: мазок кистью ───────────────────────────────────────────────── */
.banner {{ position: relative; height: 30mm; margin: 0 -2mm 6mm; }}
.banner::before {{ content: ""; position: absolute; inset: 0;
  background: url("../assets/brand/brush.svg") center / 100% 100% no-repeat; }}
.banner .in {{ position: absolute; inset: 0; display: flex; align-items: center;
               justify-content: space-between; padding: 0 9mm; }}
.banner .who {{ color: #fff; text-align: left; line-height: 1.15; padding-top: 1mm; }}
.banner .who b {{ display: block; font-family: "Ruslan", serif; font-weight: 400;
                  font-size: 10.5pt; letter-spacing: .2em; }}
.banner .who i {{ display: block; font-family: "Yeseva", serif; font-style: normal;
                  font-size: 6.4pt; letter-spacing: .3em; text-transform: uppercase; opacity: .95; }}
.banner h1 {{ font-family: "Ruslan", serif; font-weight: 400; color: #fff;
              font-size: 27pt; letter-spacing: .07em; margin: 0; line-height: 1; }}

/* ── две колонки ───────────────────────────────────────────────────────── */
.cols {{ display: grid; grid-template-columns: 72mm 1fr; gap: 8mm; }}
.col-left, .col-right {{ min-width: 0; }}

.sect {{ font-family: "Yeseva", serif; font-weight: 400; font-size: 11pt;
         text-align: center; margin: 0 0 3mm; line-height: 1.16;
         border-bottom: 1.2px solid #111; padding-bottom: 1.4mm; }}
.sect.sub {{ font-size: 9.6pt; margin: 4mm 0 2.4mm; }}

.hd {{ display: grid; grid-template-columns: 1fr 18mm 1.6mm 18mm; align-items: baseline;
       margin: 4mm 0 1.2mm; }}
.hd.gen {{ margin-top: 0; }}
.hd .g {{ font-weight: 700; font-size: 8.8pt; }}
.hd .c1, .hd .c2 {{ font-family: "Yeseva", serif; font-size: 6.2pt; letter-spacing: .12em;
                    text-transform: uppercase; text-align: right; color: #333; }}
.hd .c2 {{ grid-column: 4; }}

.ab {{ display: grid; grid-template-columns: 1fr 18mm 1.6mm 18mm; align-items: center;
       height: 4.4mm; }}
.ab .nm {{ font-size: 8.8pt; white-space: nowrap; overflow: hidden; }}
.ab .rt {{ border-bottom: 1px dashed #555; height: 0; margin-top: 2.6mm; }}
.ab .bar {{ border-left: 1.2px solid #333; height: 4mm; }}
.ab .pl {{ border-bottom: 1px solid #333; height: 0; margin-top: 2.6mm; }}
.ab.extra .nm {{ font-size: 1pt; }}

/* ── правая колонка ────────────────────────────────────────────────────── */
.two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4mm; }}
.fld {{ margin-bottom: 2.2mm; min-width: 0; }}
.fld label {{ display: block; font-family: "Yeseva", serif; font-size: 6.4pt;
              letter-spacing: .18em; text-transform: uppercase; color: #222; margin-bottom: .5mm; }}
.fld .ln {{ display: block; border-bottom: 1px solid #333; height: 4.8mm; }}
.hintline {{ font-size: 6.2pt; color: #6a6a6a; margin-top: .6mm; font-style: italic; }}
.under {{ margin: .6mm 0 2.4mm; }}

.combat {{ display: grid; grid-template-columns: 30mm 1fr; gap: 6mm; align-items: start;
           min-width: 0; }}
.crow {{ display: flex; align-items: center; gap: 2.5mm; }}
.crow label {{ font-family: "Yeseva", serif; font-size: 7.6pt; }}
.crow .box {{ width: 13mm; height: 6mm; border: 1.2px solid #333; }}
.wcol {{ min-width: 0; }}
.wh {{ display: grid; grid-template-columns: 1fr 20mm; font-family: "Yeseva", serif;
       font-size: 6.2pt; letter-spacing: .12em; text-transform: uppercase; color: #333; }}
.wh span:last-child {{ text-align: right; }}
.wr {{ display: grid; grid-template-columns: 1fr 20mm; gap: 2mm; }}
.wr .ln {{ border-bottom: 1px solid #333; height: 4.6mm; }}

.tracks {{ display: grid; grid-template-columns: 1fr 1fr; gap: 5mm; min-width: 0; }}
.trkblk {{ margin-bottom: 2.6mm; min-width: 0; }}
.trkblk > label {{ display: block; font-family: "Yeseva", serif; font-size: 7.6pt;
                   margin-bottom: .8mm; }}
.trk .nums {{ font-size: 6pt; letter-spacing: 0; color: #222;
              font-variant-numeric: tabular-nums; white-space: nowrap; }}
.trk .nums + .nums {{ color: #555; }}

.boxes {{ display: grid; grid-template-columns: repeat(10, 1fr); gap: 1.4mm; }}
.boxes .bx {{ height: 5mm; border: 1.2px solid #333; }}

.general .hd {{ grid-template-columns: 1fr 14mm 1.6mm 14mm; }}
.general .ab {{ grid-template-columns: 1fr 14mm 1.6mm 14mm; height: 4.2mm; }}

.tail {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6mm; margin-top: 3mm;
         min-width: 0; }}
.scars, .exp {{ min-width: 0; }}
.scars > label, .exp > label {{ display: block; font-family: "Yeseva", serif; font-size: 7.2pt;
                  letter-spacing: .14em; text-transform: uppercase; margin-bottom: 1.2mm; }}
.scarrow {{ display: grid; grid-template-columns: 5mm 1fr; align-items: end; gap: 2mm;
            margin-bottom: 1.4mm; }}
.scarrow span:first-child {{ font-family: "Yeseva", serif; font-size: 7pt; color: #444; }}
.scarrow .ln {{ border-bottom: 1px solid #333; height: 4.4mm; }}
.exrow {{ display: grid; grid-template-columns: 32mm 1fr; align-items: end; gap: 2mm;
          margin-bottom: 1.4mm; }}
.exrow span:first-child {{ font-size: 8pt; }}
.exrow .ln {{ border-bottom: 1px solid #333; height: 4.4mm; }}

/* ── напоминания внизу ─────────────────────────────────────────────────── */
.notes {{ position: absolute; left: 12mm; right: 12mm; bottom: 6mm;
          border-top: 1.2px solid #111; padding-top: 2mm;
          font-family: "Yeseva", serif; font-size: 6pt; line-height: 1.5;
          letter-spacing: .01em; text-align: left; color: #222; }}
.notes b {{ font-family: "Yeseva", serif; }}
.notes .sep {{ color: #888; }}

/* ── экран ─────────────────────────────────────────────────────────────── */
.screenbar {{ position: fixed; top: 0; left: 0; right: 0; z-index: 9;
  background: #14121a; color: #e8e2d8; padding: 9px 16px; display: flex; gap: 14px;
  align-items: center; font-family: "Yeseva", serif; font-size: 12px; }}
.screenbar a {{ color: #4fb3c7; text-decoration: none; }}
.screenbar button {{ background: #4fb3c7; color: #06222a; border: 0; border-radius: 7px;
  padding: 6px 14px; font: inherit; font-weight: 700; cursor: pointer; }}
@media print {{ .screenbar {{ display: none !important; }}
  body {{ padding: 0 !important; }}
  .sheet {{ box-shadow: none !important; margin: 0 !important; }} }}
@media screen {{ body {{ background: #2a2733; padding: 52px 0 40px; }}
  .sheet {{ margin: 0 auto; background: #fff; box-shadow: 0 12px 50px rgba(0,0,0,.55); }} }}
</style>
</head>
<body>

<div class="screenbar">
  <span>Досье охотника · «Охотники» на GUMSHOE</span>
  <button onclick="window.print()">🖨 Печать</button>
  <a href="sheet.html">Заполняемый лист в браузере →</a>
  <a href="rules.html">Правила →</a>
</div>

<div class="sheet">

  <header class="banner">
    <div class="in">
      <div class="who"><b>ОХОТНИКИ</b><i>досье охотника</i></div>
      <h1>Охотники</h1>
    </div>
  </header>

  <div class="cols">
    <div class="col-left">{"".join(left)}</div>
    <div class="col-right">{right}</div>
  </div>

  <div class="notes">
    <b>РАССЛЕДОВАТЕЛЬСКИЕ СПОСОБНОСТИ:</b> 18 очков на старте, от 1 до 4 в способность,
    не меньше восьми разных. Расследование не бросают кубик — есть способность и подходящая
    сцена, значит есть улика; очко даёт дополнительную правду.
    <span class="sep">•</span>
    <b>Единица в «Языках»</b> — один дополнительный язык.
    <span class="sep">•</span>
    <b>ОБЩИЕ СПОСОБНОСТИ:</b> 50 очков, от 1 до 12. Бесплатно: <b>Здоровье 4</b>,
    <b>Стабильность 4</b>, <b>Бдительность 2</b>.
    <span class="sep">•</span>
    <b>Проверка:</b> 1к6 плюс потраченные очки против Сл. Обычная Сл — 4, трудная — 5,
    почти невозможная — 6. Потраченные очки уходят даже при провале.
    <span class="sep">•</span>
    <b>ПРАВИЛО ТВАРИ:</b> пока слабость существа не установлена, любая атака наносит
    ровно 1 урона. Оружие по правилу: +2 и тварь смертна.
    <span class="sep">•</span>
    <b>Стабильность:</b> разговор с Источником возвращает 1к6, признание вслух — 1к3
    (раз за дело), ночь не в деле — 1. Сном и выпивкой — нельзя.
  </div>

</div>
</body>
</html>
'''

    open(OUT, "w", encoding="utf-8").write(doc)
    print("досье: %s (%.1f КБ)" % (os.path.relpath(OUT, ROOT), len(doc) / 1024))
    return doc


if __name__ == "__main__":
    build()
