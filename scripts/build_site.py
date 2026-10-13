#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merge data/creatures/*.json into site/data.js and report quality issues."""
import json, glob, os, re, sys, datetime, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRE = os.path.join(ROOT, "data", "creatures")
OUT = os.path.join(ROOT, "site", "data.js")

REQ = ["slug", "name_ru", "name_en", "category", "kind", "threat", "summary",
       "lore", "powers", "weaknesses", "hunting", "dnd", "dnd_notes"]
CR_XP = {"0": 10, "1/8": 25, "1/4": 50, "1/2": 100, "1": 200, "2": 450, "3": 700, "4": 1100,
         "5": 1800, "6": 2300, "7": 2900, "8": 3900, "9": 5000, "10": 5900, "11": 7200,
         "12": 8400, "13": 10000, "14": 11500, "15": 13000, "16": 15000, "17": 18000,
         "18": 20000, "19": 22000, "20": 25000, "21": 33000, "22": 41000, "23": 50000,
         "24": 62000, "25": 75000, "26": 90000, "27": 105000, "28": 120000, "29": 135000,
         "30": 155000}

CATS = ["Монстр", "Демон", "Ангел", "Божество", "Дух", "Ведьма", "Левиафан", "Иное"]
KINDS = ["creature", "being", "place", "artifact", "lore"]

def main():
    idx = json.load(open(os.path.join(ROOT, "data", "raw", "index.json")))
    by_slug = {c["slug"]: c for c in idx}
    images = {}
    ipath = os.path.join(ROOT, "data", "raw", "images.json")
    if os.path.exists(ipath):
        raw = json.load(open(ipath))
        for slug, rec in raw.items():
            local = rec.get("local")
            if not local:
                continue
            if not os.path.exists(os.path.join(ROOT, "site", local)):
                continue
            images[slug] = {"src": local, "w": rec.get("w"), "h": rec.get("h"),
                            "file": rec.get("file")}
    items, problems, missing = [], [], []

    for slug, meta in by_slug.items():
        p = os.path.join(CRE, slug + ".json")
        if not os.path.exists(p):
            missing.append(slug); continue
        try:
            d = json.load(open(p))
        except Exception as e:
            problems.append("%s: невалидный JSON (%s)" % (slug, e)); continue
        errs = []
        for k in REQ:
            if k not in d or d[k] in (None, "", [], {}):
                errs.append("пустое поле %s" % k)
        if d.get("category") not in CATS:
            errs.append("category=%r" % d.get("category"))
        if d.get("kind") not in KINDS:
            errs.append("kind=%r" % d.get("kind"))
        s = d.get("dnd") or {}
        if not isinstance(s.get("abilities"), dict) or len(s.get("abilities") or {}) != 6:
            errs.append("abilities != 6 ключей")
        cr = str(s.get("cr", "")).strip()
        if cr not in CR_XP:
            errs.append("cr=%r вне таблицы" % cr)
        elif s.get("xp") and int(s["xp"]) != CR_XP[cr]:
            errs.append("xp %s != табличного %s для CR %s" % (s.get("xp"), CR_XP[cr], cr))
        for k in ("traits", "actions", "bonus_actions", "reactions",
                  "legendary_actions", "lair_actions"):
            if k in s and not isinstance(s[k], list):
                errs.append("dnd.%s не список" % k)
        if errs:
            problems.append("%s: %s" % (slug, "; ".join(errs)))
        # нормализация
        d.setdefault("aka", []); d.setdefault("seasons", [])
        d.setdefault("first_appearance", ""); d.setdefault("notable", [])
        # короткий тип 5e для бейджа на карточке
        t = str((d.get("dnd") or {}).get("type", "") or "").strip()
        t = re.split(r"\s*\(", t)[0].strip()
        if t in ("—", "-", "?"):
            t = ""
        if len(t) > 28:
            t = re.split(r"\s+или\s+", t)[0].strip()
        d["dnd"]["type_short"] = t
        d["wiki"] = meta.get("wiki", "")
        d["_cat_declared"] = meta.get("cat", "")
        im = images.get(slug)
        if im:
            d["image"] = im["src"]
            d["image_w"] = im.get("w")
            d["image_h"] = im.get("h")
            d["image_file"] = im.get("file")
        items.append(d)

    items.sort(key=lambda d: (CATS.index(d["category"]) if d["category"] in CATS else 99,
                              d["name_ru"]))
    build = {"date": datetime.date.today().isoformat(), "count": len(items),
             "with_image": len([d for d in items if d.get("image")])}
    js = "/* Автоматически сгенерировано scripts/build_site.py — не редактировать вручную. */\n"
    js += "window.BUILD = %s;\n" % json.dumps(build, ensure_ascii=False)
    js += "window.BESTIARY = %s;\n" % json.dumps(items, ensure_ascii=False, indent=1)
    with open(OUT, "w") as f:
        f.write(js)

    print("собрано записей: %d (с изображением: %d), отсутствуют: %d, проблем: %d"
          % (len(items), build["with_image"], len(missing), len(problems)))
    if missing:
        print("НЕТ ФАЙЛОВ:", ", ".join(missing))
    if problems:
        print("--- проблемы ---")
        for p in problems[:80]:
            print(" ", p)
    # статистика
    c = collections.Counter(d["category"] for d in items)
    print("по категориям:", dict(c))
    k = collections.Counter(d["kind"] for d in items)
    print("по kind:", dict(k))

if __name__ == "__main__":
    main()
