#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собирает сайт-бестиарий под GUMSHOE: site-gumshoe/data.js + отчёт о качестве."""
import json, glob, os, re, datetime, collections, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "gumshoe")
OUT = os.path.join(ROOT, "site-gumshoe", "data.js")

CATS = ["Монстр", "Демон", "Ангел", "Божество", "Дух", "Ведьма", "Левиафан", "Иное"]
KINDS = ["creature", "being", "place", "artifact", "lore"]

INVESTIGATIVE = {
    "Антропология", "Археология", "Архивы", "История", "Оккультизм", "Демонология",
    "Теология", "Медицина", "Языки", "Криптозоология", "Химия", "Баллистика",
    "Допрос", "Запугивание", "Лесть", "Ложь", "Проницательность", "Уличное чутьё",
    "Репутация", "Осмотр места", "Взлом", "Слежка", "Наружное наблюдение",
    "Эксплуатация", "Фотосъёмка",
}
GENERAL = {
    "Атлетика", "Бой", "Стрельба", "Здоровье", "Стабильность", "Бдительность",
    "Скрытность", "Вождение", "Подготовка", "Связи", "Воля", "Вера",
    # Репутация в этом варианте работает и как общий пул (имя и связи),
    # и как расследовательская способность (что можно вытянуть через знакомых)
    "Репутация",
}
REQ = ["slug", "name_ru", "name_en", "category", "kind", "threat", "horror",
       "abilities", "hit_threshold", "damage", "stability", "special", "clues",
       "core_clue", "rule", "notes"]


def main():
    skel = json.load(open(os.path.join(SRC, "skeleton.json")))
    imgs = {}
    ip = os.path.join(ROOT, "data", "raw", "images.json")
    if os.path.exists(ip):
        for slug, rec in json.load(open(ip)).items():
            if rec.get("local") and os.path.exists(os.path.join(ROOT, "site", rec["local"])):
                imgs[slug] = rec["local"]

    # лор и факты берём из D&D-карточек, чтобы карточка GUMSHOE была самодостаточной
    lore = {}
    for f in glob.glob(os.path.join(ROOT, "data", "creatures", "*.json")):
        try:
            c = json.load(open(f))
        except Exception:
            continue
        lore[c["slug"]] = {
            "summary": c.get("summary", ""), "lore": c.get("lore", ""),
            "powers": c.get("powers", []), "weaknesses": c.get("weaknesses", []),
            "hunting": c.get("hunting", ""), "notable": c.get("notable", []),
            "aka": c.get("aka", []), "seasons": c.get("seasons", []),
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
                errs.append("пустое %s" % k)
        if d.get("category") not in CATS:
            errs.append("category=%r" % d.get("category"))
        if d.get("kind") not in KINDS:
            errs.append("kind=%r" % d.get("kind"))
        if not isinstance(d.get("abilities"), dict) or not d.get("abilities"):
            errs.append("abilities пуст")
        else:
            for k, v in d["abilities"].items():
                if k not in GENERAL:
                    errs.append("неизвестная общая способность %r" % k)
                if not isinstance(v, int) or not (1 <= v <= 60):
                    errs.append("%s=%r вне 1..60" % (k, v))
        for c in (d.get("clues") or []):
            a = (c or {}).get("ability")
            if a not in INVESTIGATIVE:
                errs.append("улика с неизвестной способностью %r" % a)
        if not isinstance(d.get("special"), list) or len(d.get("special") or []) < 1:
            errs.append("special пуст")
        st = d.get("stability") or {}
        if not isinstance(st, dict) or "test" not in st or "witnessed" not in st:
            errs.append("stability без test/witnessed")
        # числа должны совпадать со скелетом
        sk = skel[slug]
        if d.get("hit_threshold") != sk["hit_threshold"]:
            errs.append("hit_threshold %s != скелет %s" % (d.get("hit_threshold"), sk["hit_threshold"]))
        if (d.get("stability") or {}) != sk["stability"]:
            errs.append("stability %s != скелет %s" % (d.get("stability"), sk["stability"]))
        if errs:
            problems.append("%s: %s" % (slug, "; ".join(errs)))
        d["image"] = imgs.get(slug)
        d["_stability"] = int((d.get("stability") or {}).get("test") or 0)
        d["_health"] = int((d.get("abilities") or {}).get("Здоровье") or 0)
        d["_inv"] = sorted({(c or {}).get("ability") for c in (d.get("clues") or [])
                            if (c or {}).get("ability")})
        d["_search_extra"] = " ".join(d["_inv"])
        d.update(lore.get(slug, {}))
        items.append(d)

    items.sort(key=lambda d: (CATS.index(d["category"]) if d.get("category") in CATS else 99,
                              d["name_ru"]))
    build = {"date": datetime.date.today().isoformat(), "count": len(items),
             "with_image": sum(1 for d in items if d.get("image"))}
    js = "/* Автоматически сгенерировано scripts/build_gumshoe_site.py */\n"
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
    print("по kind:", dict(collections.Counter(d["kind"] for d in items)))


if __name__ == "__main__":
    main()
