#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Догружает вики-выжимки для дополненных/изменённых записей и обновляет index.json + группы."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_wiki as FW
from entries import ENTRIES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORCE = {"first-blade", "angel-tablet", "demon-tablet", "book-of-the-damned",
         "alpha-vampire", "first-vampire", "alpha-shapeshifter", "lenore",
         "benny-lafitte", "boris", "kate-werewolf", "madison-mclaughlin",
         "garth-fitzgerald", "tasha-werewolf", "lydia-crawford", "zachariah",
         "hael", "muriel", "ephraim", "benjamin", "barthamus", "abraxas",
         "drexel", "gavin-macleod"}

idx_path = os.path.join(ROOT, "data", "raw", "index.json")
index = json.load(open(idx_path))
by_slug = {c["slug"]: c for c in index}
wiki_dir = os.path.join(ROOT, "data", "raw", "wiki")
new = []

for slug, wtitle, cat, runame in ENTRIES:
    exists = os.path.exists(os.path.join(wiki_dir, slug + ".txt"))
    if exists and slug not in FORCE:
        if slug in by_slug:
            by_slug[slug]["ru"] = runame
            by_slug[slug]["cat"] = cat
        continue
    d = FW.api({"action": "parse", "page": wtitle, "prop": "wikitext", "redirects": "1"})
    if "error" in d or "parse" not in d:
        print("  !! missing", slug, wtitle); continue
    p = d["parse"]
    cond, info = FW.condense(p["wikitext"]["*"])
    with open(os.path.join(wiki_dir, slug + ".txt"), "w") as f:
        f.write("### WIKI: %s | RU: %s | КАТЕГОРИЯ: %s\n\n%s\n" % (p["title"], runame, cat, cond))
    rec = {"slug": slug, "wiki": p["title"], "cat": cat, "ru": runame,
           "chars": len(cond), "raw_chars": len(p["wikitext"]["*"]),
           "path": "data/raw/wiki/%s.txt" % slug, "info": info}
    by_slug[slug] = rec
    new.append(rec)
    print("  %-24s %-38s -> %5d" % (slug, p["title"], len(cond)))
    time.sleep(0.1)

order = {e[0]: i for i, e in enumerate(ENTRIES)}
merged = sorted(by_slug.values(), key=lambda c: order.get(c["slug"], 9999))
json.dump(merged, open(idx_path, "w"), ensure_ascii=False, indent=1)
print("index:", len(merged), "new/updated:", len(new))

# группы только для новых
GROUP = 10
gdir = os.path.join(ROOT, "data", "groups")
existing = sorted(os.listdir(gdir))
nxt = max(int(f[1:3]) for f in existing) + 1
made = []
for i in range(0, len(new), GROUP):
    chunk = new[i:i + GROUP]
    gid = "g%02d" % nxt
    nxt += 1
    json.dump({"id": gid, "items": [{"slug": c["slug"], "ru": c["ru"], "wiki": c["wiki"],
                                     "cat": c["cat"], "path": os.path.join(ROOT, c["path"])}
                                    for c in chunk]},
              open(os.path.join(gdir, gid + ".json"), "w"), ensure_ascii=False, indent=1)
    made.append((gid, [c["slug"] for c in chunk]))
for gid, slugs in made:
    print(gid, slugs)
