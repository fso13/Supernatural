#!/usr/bin/env python3
"""Classify harvested pages: species/type vs. named individual character."""
import json, time, urllib.parse, urllib.request, sys

API = "https://supernatural.fandom.com/api.php"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

def api(params):
    params = dict(params); params["format"] = "json"
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params),
                                 headers={"User-Agent": UA})
    for a in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print("retry", a, e, file=sys.stderr); time.sleep(2 + 3 * a)
    return {}

pages = json.load(open("data/raw/pages.json"))
titles = pages["pages"]
info = {}
B = 50
for i in range(0, len(titles), B):
    chunk = titles[i:i + B]
    d = api({"action": "query", "titles": "|".join(chunk), "prop": "categories|info",
             "cllimit": "max", "redirects": "1"})
    q = d.get("query", {})
    for p in q.get("pages", {}).values():
        t = p.get("title")
        if not t:
            continue
        cats = [c["title"] for c in p.get("categories", [])]
        info[t] = {"cats": cats, "len": p.get("length", 0)}
    # handle clcontinue
    cont = d.get("continue", {}).get("clcontinue")
    while cont:
        d = api({"action": "query", "titles": "|".join(chunk), "prop": "categories",
                 "cllimit": "max", "clcontinue": cont})
        q = d.get("query", {})
        for p in q.get("pages", {}).values():
            t = p.get("title")
            if t and t in info:
                info[t]["cats"] += [c["title"] for c in p.get("categories", [])]
        cont = d.get("continue", {}).get("clcontinue")
    print(i, len(info), file=sys.stderr)
    time.sleep(0.2)

json.dump(info, open("data/raw/pageinfo.json", "w"), ensure_ascii=False, indent=1)

CHAR = {"Category:Characters", "Category:Humans", "Category:Deceased", "Category:Main Characters",
        "Category:Winchesters", "Category:Male Characters", "Category:Female Characters",
        "Category:Recurring Characters", "Category:Minor Characters", "Category:Vessels",
        "Category:Season 1 Characters"}
SPECIES = {"Category:Creatures", "Category:Monster", "Category:Types of Creatures",
           "Category:Higher Beings", "Category:Deities", "Category:Demigods",
           "Category:Personifications", "Category:Species Unknown", "Category:Species"}

species, individuals = [], []
for t, v in info.items():
    cs = set(v["cats"])
    is_char = bool(cs & CHAR)
    is_spec = bool(cs & SPECIES)
    (individuals if is_char and not is_spec else species).append((t, v["len"], is_char))
species.sort(key=lambda x: -x[1])
individuals.sort(key=lambda x: -x[1])
open("data/raw/species.txt", "w").write("\n".join(t for t, _, _ in species))
open("data/raw/individuals.txt", "w").write("\n".join(t for t, _, _ in individuals))
print("species:", len(species), "individuals:", len(individuals))
