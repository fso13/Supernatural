#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Split the bestiary into work groups for parallel generation."""
import json, math, os

idx = json.load(open("data/raw/index.json"))
ROOT = "/Users/rudenkodmitry/Documents/Личное/сверхестественное"
GROUP = 10
groups = []
for i in range(0, len(idx), GROUP):
    chunk = idx[i:i + GROUP]
    groups.append({
        "id": "g%02d" % (len(groups) + 1),
        "items": [{"slug": c["slug"], "ru": c["ru"], "wiki": c["wiki"],
                   "cat": c["cat"], "path": os.path.join(ROOT, c["path"])} for c in chunk],
    })
os.makedirs("data/groups", exist_ok=True)
for g in groups:
    json.dump(g, open("data/groups/%s.json" % g["id"], "w"), ensure_ascii=False, indent=1)
print("groups:", len(groups), "entries:", len(idx))
for g in groups[:3]:
    print(g["id"], [x["slug"] for x in g["items"]])
