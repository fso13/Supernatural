#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собирает сайт-бестиарий под «The Edge!»: site-edge/data.js + отчёт о качестве."""
import json, glob, os, re, datetime, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "edge")
OUT = os.path.join(ROOT, "site-edge", "data.js")

CATS = ["Монстр", "Демон", "Ангел", "Божество", "Дух", "Ведьма", "Левиафан", "Иное"]
KINDS = ["creature", "being", "place", "artifact", "lore"]
ATTRS = ["Тело", "Ловкость", "Разум", "Воля"]

SKILLS = {
    "Рукопашное оружие", "Двуручное оружие", "Оружие и щит", "Двойное оружие",
    "Стрельба", "Безоружный бой", "Лёгкая броня", "Тяжёлая броня",
    "Дипломатия", "Запугивание", "Обман", "Выступление", "Проницательность",
    "Этикет", "Торговля", "Право и обычай",
    "История", "Природа", "Религия", "Магические знания", "Анализ", "Ремесло",
    "Алхимия", "Медицина", "Подделка",
    "Атлетика", "Акробатика", "Скрытность", "Внимание", "Выживание", "Взлом",
    "Верховая езда",
    "Огнестрел", "Вождение", "Техника", "Уличное чутьё",
}
REQ = ["slug", "name_ru", "name_en", "category", "kind", "threat", "ugroza",
       "look", "special", "weakness", "learn", "notes"]

# D&D-термины, которых не должно быть в тексте карточки.
# Проверяем по границам слов: «похитил», «хитин» и «инициатива у него» — обычный русский.
BANNED = [
    r"спасброс\w*",
    r"\bкд\b",
    r"\bхит(?:ы|ов|а|ам|ами|е)?\b",
    r"\bпреимущество\s+на\b",
    r"\bс\s+преимуществом\b",
    r"\bпомеха\s+на\b",
    r"\bбросок\s+инициативы\b",
    r"\bинициатива\s+в\s+бою\b",
    r"\bd20\b", r"\bd8\b", r"\bd12\b",
]


def main():
    skel = json.load(open(os.path.join(SRC, "skeleton.json")))
    imgs = {}
    ip = os.path.join(ROOT, "data", "raw", "images.json")
    if os.path.exists(ip):
        for slug, rec in json.load(open(ip)).items():
            if rec.get("local") and os.path.exists(os.path.join(ROOT, "site", rec["local"])):
                imgs[slug] = rec["local"]

    lore = {}
    for f in glob.glob(os.path.join(ROOT, "data", "creatures", "*.json")):
        try:
            c = json.load(open(f))
        except Exception:
            continue
        lore[c["slug"]] = {
            "summary": c.get("summary", ""), "lore": c.get("lore", ""),
            "powers": c.get("powers", []), "weaknesses": c.get("weaknesses", []),
            "notable": c.get("notable", []), "aka": c.get("aka", []),
            "seasons": c.get("seasons", []),
            "first_appearance": c.get("first_appearance", ""),
        }

    items, problems, missing = [], [], []
    for slug in skel:
        p = os.path.join(SRC, slug + ".json")
        if not os.path.exists(p):
            missing.append(slug); continue
        try:
            d = json.load(open(p))
        except Exception as e:
            problems.append("%s: невалидный JSON (%s)" % (slug, e)); continue
        errs = []
        for k in REQ:
            if k not in d or d[k] in (None, "", [], {}):
                if k == "stress" and d.get("stress") is None:
                    continue
                errs.append("пустое %s" % k)
        if d.get("category") not in CATS:
            errs.append("category=%r" % d.get("category"))
        if d.get("kind") not in KINDS:
            errs.append("kind=%r" % d.get("kind"))
        sp = d.get("special") or []
        if not isinstance(sp, list) or not (1 <= len(sp) <= 2):
            errs.append("special: %d (нужно 1–2)" % (len(sp) if isinstance(sp, list) else -1))
        lr = d.get("learn") or []
        if not isinstance(lr, list) or not (2 <= len(lr) <= 3):
            errs.append("learn: %d (нужно 2–3)" % (len(lr) if isinstance(lr, list) else -1))
        else:
            for c in lr:
                if (c or {}).get("skill") not in SKILLS:
                    errs.append("навык %r вне списка" % (c or {}).get("skill"))
                if (c or {}).get("attr") not in ATTRS:
                    errs.append("атрибут %r" % (c or {}).get("attr"))
                if not isinstance((c or {}).get("cch"), int) or not (7 <= c["cch"] <= 18):
                    errs.append("ЧЦ %r" % (c or {}).get("cch"))
        # числа сверяем со скелетом
        sk = skel[slug]
        for k in ("ugroza", "attrs", "wounds", "stress", "armor", "defense", "weapon"):
            if d.get(k) != sk.get(k):
                errs.append("%s != скелет" % k)
        blob = " ".join(str(d.get(x, "")) for x in ("look", "notes", "weakness")).lower()
        for b in BANNED:
            m = re.search(b, blob)
            if m:
                errs.append("D&D-термин %r" % m.group(0))
        if errs:
            problems.append("%s: %s" % (slug, "; ".join(errs)))
        d["image"] = imgs.get(slug)
        d["_wounds"] = int(d.get("wounds") or 0)
        d["_def"] = int(d.get("defense") or 0)
        d["_threat"] = int(d.get("threat") or 1)
        d["_seasons"] = [int(x) for x in (lore.get(slug, {}).get("seasons") or [])
                         if str(x).isdigit()]
        d.update(lore.get(slug, {}))
        d["_skills"] = " ".join((c or {}).get("skill", "") for c in (d.get("learn") or []))
        items.append(d)

    items.sort(key=lambda d: (CATS.index(d["category"]) if d.get("category") in CATS else 99,
                              d["name_ru"]))
    build = {"date": datetime.date.today().isoformat(), "count": len(items),
             "with_image": sum(1 for d in items if d.get("image"))}
    js = "/* Автоматически сгенерировано scripts/build_edge_site.py */\n"
    js += "window.BUILD = %s;\n" % json.dumps(build, ensure_ascii=False)
    js += "window.BESTIARY = %s;\n" % json.dumps(items, ensure_ascii=False, indent=1)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write(js)

    print("собрано: %d, отсутствуют: %d, проблем: %d" % (len(items), len(missing), len(problems)))
    if missing:
        print("НЕТ ФАЙЛОВ:", ", ".join(missing[:40]))
    for p in problems[:40]:
        print("  !", p)
    print("по категориям:", dict(collections.Counter(d["category"] for d in items)))


if __name__ == "__main__":
    main()
