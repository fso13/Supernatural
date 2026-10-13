#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fetch + condense wiki wikitext for every curated bestiary entry."""
import json, os, re, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from entries import ENTRIES

API = "https://supernatural.fandom.com/api.php"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

def api(params, tries=4):
    params = dict(params); params["format"] = "json"
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params),
                                 headers={"User-Agent": UA})
    for a in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print("retry", a, e, file=sys.stderr); time.sleep(2 + 3 * a)
    return {}

# ---------- wikitext cleaning ----------
def strip_templates(s):
    out, i, n = [], 0, len(s)
    depth = 0
    while i < n:
        if s.startswith("{{", i):
            depth += 1; i += 2; continue
        if s.startswith("}}", i):
            depth = max(0, depth - 1); i += 2; continue
        if depth == 0:
            out.append(s[i])
        i += 1
    return "".join(out)

def strip_tables(s):
    return re.sub(r"\{\|.*?\|\}", "", s, flags=re.S)

RE_CLEAN = [
    (re.compile(r"<ref[^>/]*/>"), ""),
    (re.compile(r"<ref.*?</ref>", re.S), ""),
    (re.compile(r"<gallery.*?</gallery>", re.S), ""),
    (re.compile(r"<[^>]{1,120}>"), ""),
    (re.compile(r"\{\|.*?\|\}", re.S), ""),
    (re.compile(r"\[\[Category:[^\]]*\]\]"), ""),
    (re.compile(r"\[\[([^\]|]*)\|([^\]]*)\]\]"), r"\2"),
    (re.compile(r"\[\[([^\]]*)\]\]"), r"\1"),
    (re.compile(r"\[https?://\S+\s+([^\]]*)\]"), r"\1"),
    (re.compile(r"\[https?://\S+\]"), ""),
    (re.compile(r"'{2,5}"), ""),
    (re.compile(r"^[#*:;]+", re.M), ""),
    (re.compile(r"__[A-Z]+__"), ""),
    (re.compile(r"[ \t]{2,}"), " "),
    (re.compile(r"\n{3,}"), "\n\n"),
]

def clean(s):
    s = strip_templates(s)
    for rx, rep in RE_CLEAN:
        s = rx.sub(rep, s)
    return s.strip()

def parse_infobox(raw):
    """Pull the first {{Infobox-like template}} params."""
    m = re.search(r"\{\{\s*([A-Za-z][A-Za-z0-9 _\-/]*)", raw)
    if not m:
        return {}
    start = m.start()
    depth, i = 0, start
    while i < len(raw):
        if raw.startswith("{{", i):
            depth += 1; i += 2; continue
        if raw.startswith("}}", i):
            depth -= 1; i += 2
            if depth == 0:
                break
            continue
        i += 1
    body = raw[start:i]
    info = {"_template": m.group(1).strip()}
    for pm in re.finditer(r"\n\s*\|\s*([^=\n|]{1,40}?)\s*=\s*(.*?)(?=\n\s*\||\Z)", body, re.S):
        k = pm.group(1).strip().lower()
        v = clean(pm.group(2))
        v = re.sub(r"\s*\n\s*", " ", v).strip()
        if v and len(v) < 400:
            info[k] = v
    return info

def split_sections(raw):
    parts = re.split(r"\n\s*(={2,4})\s*([^=\n]+?)\s*\1\s*\n", raw)
    intro = parts[0]
    subs = []
    i = 1
    while i + 2 < len(parts) + 1 and i + 2 <= len(parts):
        subs.append((parts[i + 1].strip(), parts[i + 2]))
        i += 3
    return clean(intro), [(n, clean(b)) for n, b in subs]

WANT = [
    ("powers and abilities", "СИЛЫ И СПОСОБНОСТИ"),
    ("abilities", "СИЛЫ И СПОСОБНОСТИ"),
    ("powers", "СИЛЫ И СПОСОБНОСТИ"),
    ("weaknesses", "СЛАБОСТИ"),
    ("weakness", "СЛАБОСТИ"),
    ("characteristics", "ХАРАКТЕРИСТИКИ"),
    ("biology", "БИОЛОГИЯ"),
    ("physiology", "ФИЗИОЛОГИЯ"),
    ("behaviour", "ПОВЕДЕНИЕ"),
    ("behavior", "ПОВЕДЕНИЕ"),
    ("history", "ИСТОРИЯ"),
    ("overview", "ОБЗОР"),
    ("background", "ПРЕДЫСТОРИЯ"),
    ("lore", "ЛОР"),
    ("appearances", "ПОЯВЛЕНИЯ"),
    ("known vampires", "ИЗВЕСТНЫЕ ОСОБИ"),
    ("known werewolves", "ИЗВЕСТНЫЕ ОСОБИ"),
    ("known demons", "ИЗВЕСТНЫЕ ОСОБИ"),
    ("known ghosts", "ИЗВЕСТНЫЕ ОСОБИ"),
    ("known", "ИЗВЕСТНЫЕ ОСОБИ"),
]

def condense(raw, limit=4600):
    info = parse_infobox(raw)
    intro, subs = split_sections(raw)
    blocks = []
    if intro:
        blocks.append(("[ОПИСАНИЕ]", intro))
    used = set()
    for key, label in WANT:
        for idx, (name, body) in enumerate(subs):
            if idx in used:
                continue
            if name.strip().lower() == key and body:
                used.add(idx)
                blocks.append(("[%s]" % label, body))
    # a little history if nothing else
    if not any(b[0] in ("[ИСТОРИЯ]", "[ОБЗОР]", "[ПРЕДЫСТОРИЯ]") for b in blocks):
        for idx, (name, body) in enumerate(subs):
            if idx in used or not body:
                continue
            if len(body) > 300:
                blocks.append(("[ИСТОРИЯ]", body)); used.add(idx); break
    total = sum(len(b[1]) for b in blocks)
    budget = max(350, limit // max(1, len(blocks)))
    out = []
    if info:
        keys = ["name", "category", "status", "season", "family", "title/alias", "aliases",
                "actor", "powers", "weaknesses", "species", "occupation", "affiliation",
                "portrayed by", "gender", "died", "killed by", "cause of death"]
        lines = []
        for k in keys:
            if k in info:
                lines.append("%s: %s" % (k, info[k]))
        if lines:
            out.append("[ИНФОБОКС]\n" + "\n".join(lines))
    for label, body in blocks:
        if len(body) > budget:
            body = body[:budget].rsplit(" ", 1)[0] + " …"
        out.append(label + "\n" + body)
    txt = "\n\n".join(out)
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    return txt.strip(), info

def main():
    os.makedirs("data/raw/wiki", exist_ok=True)
    index, missing = [], []
    for n, (slug, wtitle, cat, runame) in enumerate(ENTRIES, 1):
        d = api({"action": "parse", "page": wtitle, "prop": "wikitext", "redirects": "1"})
        if "error" in d or "parse" not in d:
            missing.append((slug, wtitle)); print("  !! missing", slug, wtitle)
            continue
        p = d["parse"]
        raw = p["wikitext"]["*"]
        cond, info = condense(raw)
        if not cond:
            missing.append((slug, wtitle)); print("  !! empty", slug)
            continue
        path = "data/raw/wiki/%s.txt" % slug
        with open(path, "w") as f:
            f.write("### WIKI: %s | RU: %s | КАТЕГОРИЯ: %s\n\n%s\n" % (p["title"], runame, cat, cond))
        index.append({"slug": slug, "wiki": p["title"], "cat": cat, "ru": runame,
                      "chars": len(cond), "raw_chars": len(raw), "path": path, "info": info})
        print("%3d %-30s %-42s %6d -> %5d" % (n, slug, p["title"], len(raw), len(cond)))
        time.sleep(0.1)
    json.dump(index, open("data/raw/index.json", "w"), ensure_ascii=False, indent=1)
    print("done:", len(index), "missing:", missing)

if __name__ == "__main__":
    main()
