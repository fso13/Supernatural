#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собирает единый Markdown-компендиум бестиария (для печати и VTT)."""
import json, os, glob, collections, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_MD = os.path.join(ROOT, "Бестиарий Supernatural — D&D 5e.md")
OUT_SB = os.path.join(ROOT, "Статблоки D&D 5e.md")

CAT_ORDER = ["Монстр", "Демон", "Ангел", "Божество", "Дух", "Ведьма", "Левиафан", "Иное"]
CAT_ICON = {"Монстр": "🐾", "Демон": "😈", "Ангел": "😇", "Божество": "⚡",
            "Дух": "👻", "Ведьма": "🕯️", "Левиафан": "🐍", "Иное": "🌀"}
ABIL = [("str", "СИЛ"), ("dex", "ЛОВ"), ("con", "ТЕЛ"),
        ("int", "ИНТ"), ("wis", "МДР"), ("cha", "ХАР")]


def load():
    items = []
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "creatures", "*.json"))):
        try:
            items.append(json.load(open(p)))
        except Exception:
            pass
    ipath = os.path.join(ROOT, "data", "raw", "images.json")
    imgs = json.load(open(ipath)) if os.path.exists(ipath) else {}
    for d in items:
        rec = imgs.get(d.get("slug")) or {}
        local = rec.get("local")
        if local and os.path.exists(os.path.join(ROOT, "site", local)):
            d["image"] = "site/" + local
    items.sort(key=lambda d: (CAT_ORDER.index(d["category"]) if d.get("category") in CAT_ORDER else 99,
                              d.get("name_ru", "")))
    return items


def lvl_str(v):
    return "—"


def statblock_md(d):
    s = d.get("dnd") or {}
    L = []
    L.append("#### %s" % d["name_ru"])
    L.append("*%s*" % ", ".join(x for x in [s.get("size"), s.get("type"), s.get("alignment")] if x))
    L.append("")
    L.append("---")
    for label, key in [("**Класс доспеха**", "ac"), ("**Хиты**", "hp"), ("**Скорость**", "speed")]:
        if s.get(key):
            L.append("- %s %s" % (label, s[key]))
    L.append("")
    a = s.get("abilities") or {}
    L.append("| " + " | ".join(n for _, n in ABIL) + " |")
    L.append("|" + "---|" * 6)
    L.append("| " + " | ".join(str(a.get(k, "—")) for k, _ in ABIL) + " |")
    L.append("")
    for label, key in [("Спасброски", "saves"), ("Навыки", "skills"),
                       ("Уязвимость к урону", "damage_vulnerabilities"),
                       ("Сопротивление урону", "damage_resistances"),
                       ("Иммунитет к урону", "damage_immunities"),
                       ("Иммунитет к состояниям", "condition_immunities"),
                       ("Чувства", "senses"), ("Языки", "languages")]:
        if s.get(key):
            L.append("- **%s** %s" % (label, s[key]))
    if s.get("pb"):
        L.append("- **Бонус мастерства** +%s" % s["pb"])
    if s.get("cr"):
        xp = (" (%s опыта)" % format(int(s["xp"]), ",").replace(",", " ")) if s.get("xp") else ""
        L.append("- **Уровень опасности** %s%s" % (s["cr"], xp))
    L.append("")
    for title, key in [("Особенности", "traits"), ("Действия", "actions"),
                       ("Бонусные действия", "bonus_actions"), ("Реакции", "reactions"),
                       ("Легендарные действия", "legendary_actions"),
                       ("Действия в логове", "lair_actions")]:
        arr = s.get(key) or []
        if not arr:
            continue
        L.append("***%s***" % title)
        for e in arr:
            if isinstance(e, str):
                L.append("- %s" % e)
            else:
                L.append("- ***%s.*** %s" % (e.get("name", ""), e.get("text", "")))
        L.append("")
    if s.get("tactics"):
        L.append("**Тактика.** %s" % s["tactics"])
        L.append("")
    if s.get("ecology"):
        L.append("**Экология.** %s" % s["ecology"])
        L.append("")
    return "\n".join(L)


def full_md(d, n):
    L = []
    L.append('<a id="%s"></a>' % d["slug"])
    L.append("### %d. %s" % (n, d["name_ru"]))
    L.append("")
    L.append("**%s** · %s · CR %s · опасность в сериале %s/5" %
             (d.get("name_en", ""), d.get("category", ""),
              (d.get("dnd") or {}).get("cr", "—"), d.get("threat", "—")))
    if d.get("aka"):
        L.append("")
        L.append("*Также известно как:* %s" % "; ".join(d["aka"]))
    if d.get("first_appearance"):
        L.append("")
        L.append("*Первое появление:* %s" % d["first_appearance"])
    if d.get("seasons"):
        L.append("")
        L.append("*Сезоны:* %s" % ", ".join(str(x) for x in d["seasons"]))
    L.append("")
    L.append(d.get("summary", ""))
    L.append("")
    if d.get("image"):
        L.append('![%s](%s)' % (d["name_ru"], d["image"]))
        L.append("")
    L.append("**Описание**")
    L.append("")
    L.append(d.get("lore", ""))
    L.append("")
    if d.get("powers"):
        L.append("**Силы и способности**")
        L.append("")
        for p in d["powers"]:
            L.append("- %s" % p)
        L.append("")
    if d.get("weaknesses"):
        L.append("**Слабости**")
        L.append("")
        for p in d["weaknesses"]:
            L.append("- %s" % p)
        L.append("")
    if d.get("hunting"):
        L.append("**Как его убить.** %s" % d["hunting"])
        L.append("")
    if d.get("notable"):
        L.append("**Известные особи:** %s" % "; ".join(d["notable"]))
        L.append("")
    L.append(statblock_md(d))
    if d.get("dnd_notes"):
        L.append("")
        L.append("> **Заметки мастеру.** %s" % d["dnd_notes"])
    L.append("")
    L.append("[↑ к содержанию](#содержание)")
    L.append("")
    L.append("---")
    L.append("")
    return "\n".join(L)


def main():
    items = load()
    creatures = [d for d in items if d.get("kind") in ("creature", "being")]
    appendix = [d for d in items if d.get("kind") in ("place", "artifact", "lore")]
    today = datetime.date.today().isoformat()

    # ---- заголовок ----
    L = ["# Бестиарий «Сверхъестественного» — Dungeons & Dragons 5e", "",
         "Полный бестиарий существ сериала *Supernatural* (The CW, 2005–2020) "
         "с адаптацией каждого существа под правила D&D 5e.", "",
         "Сборка: %s · записей: %d (существ и высших сущностей: %d, "
         "локаций/артефактов/понятий: %d)" % (today, len(items), len(creatures), len(appendix)),
         "", "---", "", '<a id="содержание"></a>', "## Содержание", ""]

    by_cat = collections.defaultdict(list)
    for d in creatures:
        by_cat[d.get("category", "Иное")].append(d)

    n = 0
    for cat in CAT_ORDER:
        arr = by_cat.get(cat, [])
        if not arr:
            continue
        L.append("- %s **%s** (%d)" % (CAT_ICON.get(cat, ""), cat, len(arr)))
        for d in sorted(arr, key=lambda x: x["name_ru"]):
            n += 1
            d["_n"] = n
            L.append("  - [%s](#%s) — CR %s" %
                     (d["name_ru"], d["slug"], (d.get("dnd") or {}).get("cr", "—")))
    if appendix:
        L.append("- 📦 **Приложение: мир, артефакты и понятия** (%d)" % len(appendix))
    L += ["", "---", ""]

    # ---- разделы ----
    for cat in CAT_ORDER:
        arr = by_cat.get(cat, [])
        if not arr:
            continue
        L.append("## %s %s" % (CAT_ICON.get(cat, ""), cat))
        L.append("")
        for d in sorted(arr, key=lambda x: x["name_ru"]):
            L.append(full_md(d, d["_n"]))

    if appendix:
        L.append("## 📦 Приложение: мир, артефакты и понятия")
        L.append("")
        for i, d in enumerate(sorted(appendix, key=lambda x: x["name_ru"]), 1):
            L.append(full_md(d, i))

    L += ["---", "",
          "*Supernatural* — торговая марка Warner Bros. Television. "
          "*Dungeons & Dragons* — Wizards of the Coast. "
          "Неофициальный фанатский материал; факты собраны по материалам Supernatural Wiki, "
          "игровая механика — оригинальная адаптация.", ""]

    with open(OUT_MD, "w") as f:
        f.write("\n".join(L))

    # ---- только статблоки ----
    S = ["# Статблоки D&D 5e — бестиарий «Сверхъестественного»", "",
         "Компактная выжимка: только игровая механика, без лора. Сборка %s." % today, "", "---", ""]
    for cat in CAT_ORDER:
        arr = by_cat.get(cat, [])
        if not arr:
            continue
        S.append("## %s" % cat)
        S.append("")
        for d in sorted(arr, key=lambda x: x["name_ru"]):
            S.append(statblock_md(d))
            S.append("")
            S.append("---")
            S.append("")
    with open(OUT_SB, "w") as f:
        f.write("\n".join(S))

    print("compendium:", OUT_MD, os.path.getsize(OUT_MD), "bytes")
    print("statblocks:", OUT_SB, os.path.getsize(OUT_SB), "bytes")


if __name__ == "__main__":
    main()
