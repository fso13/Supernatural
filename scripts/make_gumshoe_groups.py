#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Готовит компактные входные файлы для конвертации бестиария в GUMSHOE."""
import json, glob, os, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
skel = json.load(open(os.path.join(ROOT, "data", "gumshoe", "skeleton.json")))
GROUPS = os.path.join(ROOT, "data", "gumshoe", "groups")
PER = 15


def compact(d):
    s = d.get("dnd") or {}
    return {
        "slug": d["slug"], "name_ru": d["name_ru"], "name_en": d.get("name_en", ""),
        "category": d.get("category"), "kind": d.get("kind"), "threat": d.get("threat"),
        "aka": d.get("aka", []), "seasons": d.get("seasons", []),
        "first_appearance": d.get("first_appearance", ""),
        "summary": d.get("summary", ""),
        "lore": (d.get("lore") or "")[:1400],
        "powers": d.get("powers", []),
        "weaknesses": d.get("weaknesses", []),
        "hunting": d.get("hunting", ""),
        "notable": d.get("notable", []),
        "dnd_type": s.get("type"), "dnd_cr": s.get("cr"),
        "dnd_traits": [t.get("name") for t in (s.get("traits") or []) if isinstance(t, dict)],
        "dnd_actions": [t.get("name") for t in (s.get("actions") or []) if isinstance(t, dict)],
        "skeleton": skel.get(d["slug"]),
    }


def main():
    os.makedirs(GROUPS, exist_ok=True)
    items = []
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "creatures", "*.json"))):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        items.append(compact(d))
    items.sort(key=lambda x: (x["category"] or "", x["name_ru"]))
    n = 0
    for i in range(0, len(items), PER):
        n += 1
        gid = "s%02d" % n
        chunk = items[i:i + PER]
        json.dump({"id": gid, "items": chunk},
                  open(os.path.join(GROUPS, gid + ".json"), "w"), ensure_ascii=False, indent=1)
    print("групп:", n, "записей:", len(items))
    print("первая группа:", [x["slug"] for x in items[:PER]])


if __name__ == "__main__":
    main()
