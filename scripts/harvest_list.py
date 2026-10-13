#!/usr/bin/env python3
"""Harvest the list of creature pages from the Supernatural Wiki via MediaWiki API."""
import json, time, urllib.parse, urllib.request, os, sys

API = "https://supernatural.fandom.com/api.php"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

def api(params):
    params = dict(params)
    params["format"] = "json"
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print("  retry", attempt, e, file=sys.stderr)
            time.sleep(2 + attempt * 3)
    return {}

def cat_members(cat):
    out, cont = [], None
    while True:
        p = {"action": "query", "list": "categorymembers", "cmtitle": cat,
             "cmlimit": "500", "cmnamespace": "0|14"}
        if cont:
            p["cmcontinue"] = cont
        d = api(p)
        out += d.get("query", {}).get("categorymembers", [])
        cont = d.get("continue", {}).get("cmcontinue")
        if not cont:
            break
        time.sleep(0.3)
    return out

ROOT_CATS = [
    "Category:Creatures",
    "Category:Monster",
    "Category:Types of Creatures",
    "Category:Higher Beings",
    "Category:Deities",
    "Category:Demigods",
    "Category:Personifications",
    "Category:Species Unknown",
]

# Categories whose members are *individuals* worth having in a bestiary
EXPAND = [
    "Category:Demons", "Category:Angels", "Category:Archangel", "Category:High-tier Angels",
    "Category:Vampires", "Category:Werewolves", "Category:Ghosts", "Category:Ghost",
    "Category:Witches", "Category:Leviathans", "Category:Reaper", "Category:Hellhounds",
    "Category:Knights of Hell", "Category:Princes of Hell", "Category:White-eyed Demons",
    "Category:Four Horsemen", "Category:Horseman", "Category:Primordial Entities",
    "Category:Shapeshifter", "Category:Tricksters", "Category:Fairies", "Category:Ghouls",
    "Category:Wendigo", "Category:Zanna", "Category:Rugaru", "Category:Nephilim",
    "Category:Prophet", "Category:Prophets", "Category:Dragons", "Category:Gorgons",
    "Category:Wraiths", "Category:Constructs", "Category:One-Episode Species",
    "Category:Supernatural Animals", "Category:Animals", "Category:Hybrid",
    "Category:Alpha", "Category:Siren", "Category:Banshee", "Category:Nachzehrer",
    "Category:Pishtaco", "Category:Pontianaks", "Category:Marids", "Category:Muscas",
    "Category:Kohonta", "Category:Loup-Garou", "Category:Rabid", "Category:Shamans",
    "Category:Familiar", "Category:Dreamwalkers", "Category:Mandragora",
    "Category:Akrida", "Category:Book Creatures", "Category:Comic Book Monsters",
    "Category:Gorilla Wolves", "Category:Cherubim", "Category:Changelings",
    "Category:Arachne", "Category:Amazons", "Category:Jefferson Starship",
    "Category:Strongest of Species",
]

def main():
    species, individuals = {}, {}
    seen_cats = set()

    def harvest(cat, depth=0):
        if cat in seen_cats or depth > 2:
            return
        seen_cats.add(cat)
        for m in cat_members(cat):
            title = m["title"]
            if m["ns"] == 0:
                # Heuristic: single-word/species-ish titles vs. person names
                individuals.setdefault(title, cat)
            else:
                if title.startswith("Category:"):
                    sub = title
                    if depth < 1 or sub in EXPAND:
                        harvest(sub, depth + 1)
        time.sleep(0.25)

    for c in ROOT_CATS:
        print("root", c)
        harvest(c, 0)
    for c in EXPAND:
        print("expand", c)
        harvest(c, 0)

    # individuals collected from expanded cats
    all_pages = sorted(set(individuals))
    os.makedirs("data/raw", exist_ok=True)
    with open("data/raw/pages.txt", "w") as f:
        f.write("\n".join(all_pages))
    with open("data/raw/pages.json", "w") as f:
        json.dump({"pages": all_pages, "source": individuals, "cats": sorted(seen_cats)}, f,
                  ensure_ascii=False, indent=1)
    print("total pages:", len(all_pages), "cats:", len(seen_cats))

if __name__ == "__main__":
    main()
