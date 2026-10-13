#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Универсальный конвертер Markdown -> страница сайта (с оглавлением и навигацией).

Использование:
  python3 scripts/md2site.py <src.md> <out.html> --title "..." --subtitle "..." \
      --nav "Дом|index.html,Правила|rules.html" [--css adventure.css] [--home index.html]
"""
import argparse, html, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BLOCK_START = re.compile(
    r"^(?:#{1,6}\s|\s*[-*+]\s|\s*\d+\.\s|\s*>|\s*\||\s*-{3,}\s*$|\s*```)")


def is_block_start(line):
    return bool(BLOCK_START.match(line))


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+?)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def slug(s):
    s = s.lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.U)
    return re.sub(r"\s+", "-", s).strip("-")


def convert(md):
    lines = md.split("\n")
    out, toc = [], []
    i = 0
    while i < len(lines):
        ln = lines[i]
        # блок кода ```
        if ln.strip().startswith("```"):
            lang = ln.strip()[3:].strip()
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1  # закрывающая ```
            cls = ' class="lang-%s"' % lang if lang else ""
            out.append("<pre%s><code>%s</code></pre>"
                       % (cls, html.escape("\n".join(buf), quote=False)))
            continue
        if re.match(r"^\s*-{3,}\s*$", ln):
            out.append("<hr>"); i += 1; continue
        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            lvl, txt = len(m.group(1)), m.group(2).strip()
            sid = slug(txt)
            if lvl in (2, 3):
                toc.append((lvl, txt, sid))
            out.append('<h%d id="%s">%s</h%d>' % (lvl, sid, inline(txt), lvl))
            i += 1; continue
        if ln.lstrip().startswith(">"):
            buf = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                buf.append(lines[i].lstrip()[1:].strip()); i += 1
            body, _ = convert("\n".join(buf))
            out.append("<blockquote>%s</blockquote>" % body)
            continue
        if ln.strip().startswith("|") and i + 1 < len(lines) and \
                re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            head = [c.strip() for c in ln.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            t = ['<table class="md"><thead><tr>'] + \
                ["<th>%s</th>" % inline(c) for c in head] + ["</tr></thead><tbody>"]
            for r in rows:
                t.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>")
            t.append("</tbody></table>")
            out.append("".join(t)); continue
        if re.match(r"^\s*[-*+]\s+", ln) or re.match(r"^\s*\d+\.\s+", ln):
            ordered = bool(re.match(r"^\s*\d+\.\s+", ln))
            items = []
            while i < len(lines) and (re.match(r"^\s*[-*+]\s+", lines[i]) or
                                      re.match(r"^\s*\d+\.\s+", lines[i])):
                items.append(re.sub(r"^\s*(?:[-*+]|\d+\.)\s+", "", lines[i])); i += 1
            tag = "ol" if ordered else "ul"
            out.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % inline(x) for x in items), tag))
            continue
        if not ln.strip():
            i += 1; continue
        buf = []
        while i < len(lines) and lines[i].strip() and not is_block_start(lines[i]):
            buf.append(lines[i]); i += 1
        if buf:
            out.append("<p>%s</p>" % inline(" ".join(buf)))
        else:
            i += 1
    return "\n".join(out), toc


TPL = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<link rel="stylesheet" href="style.css">
<link rel="stylesheet" href="%(css)s">
<link rel="stylesheet" href="../assets/brand.css">
<link rel="icon" type="image/svg+xml" href="../assets/brand/favicon.svg">
</head>
<body>
<header class="topbar">
  <div class="brand">
    <span class="sig sig-trap brandmark" role="img" aria-label="Ловушка дьявола"></span>
    <div>
      <h1 class="wordmark">%(title_short)s <span class="thin">%(title_thin)s</span></h1>
      <p class="tagline">%(subtitle)s</p>
    </div>
  </div>
  <nav class="tabs">%(nav)s</nav>
</header>
<main>
  <div class="adv-wrap">
    <aside class="adv-toc">
      <h4>Содержание</h4>
      %(toc)s
    </aside>
    <article class="prose adv">
%(body)s
    </article>
  </div>
</main>
<div class="salt-divider" aria-hidden="true"></div>
<footer class="adv-foot">
  <div class="brandline"><span class="sig sig-trap"></span><span>Saving people, hunting things</span><span class="sig sig-trap"></span></div>
  Неофициальный фанатский материал. Supernatural — Warner Bros. Television;
  GUMSHOE — Pelgrane Press; Dungeons &amp; Dragons — Wizards of the Coast.
</footer>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("out")
    ap.add_argument("--title", default="")
    ap.add_argument("--title-short", default="")
    ap.add_argument("--title-thin", default="")
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--nav", default="")
    ap.add_argument("--active", default="")
    ap.add_argument("--css", default="adventure.css")
    args = ap.parse_args()

    md = open(args.src, encoding="utf-8").read()
    body, toc = convert(md)
    toc_html = "\n      ".join(
        '<a class="t%d" href="#%s">%s</a>' % (lvl, sid, html.escape(txt))
        for lvl, txt, sid in toc if lvl <= 3)

    nav_html = []
    for part in args.nav.split(","):
        part = part.strip()
        if not part:
            continue
        label, _, href = part.partition("|")
        cls = "tab is-active" if label.strip() == args.active else "tab"
        nav_html.append('<a class="%s" href="%s">%s</a>' % (cls, href, html.escape(label.strip())))

    htmlout = TPL % {
        "title": args.title, "title_short": args.title_short,
        "title_thin": args.title_thin, "subtitle": args.subtitle,
        "nav": "\n    ".join(nav_html), "toc": toc_html, "body": body, "css": args.css,
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    open(args.out, "w", encoding="utf-8").write(htmlout)
    print("%s: %d bytes | %d заголовков" % (args.out, os.path.getsize(args.out), len(toc)))


if __name__ == "__main__":
    main()
