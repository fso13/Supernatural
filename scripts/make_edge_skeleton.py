#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Числовой скелет бестиария под систему «The Edge!» (только d6).

Формулы — детерминированное преобразование статблока D&D 5e в термины «The Edge!»:
четыре атрибута, раны, стресс, ЧЦ защиты, бонус оружия, нарративная угроза.
Документируются на странице правил, чтобы хранитель понимал, откуда числа.
"""
import json, glob, os, re, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "edge", "skeleton.json")

CR_NUM = {"0": 0, "1/8": 0.125, "1/4": 0.25, "1/2": 0.5}
THREAT_WORD = {1: "низкая", 2: "средняя", 3: "высокая", 4: "очень высокая", 5: "смертельная"}


def cr_val(cr):
    s = str(cr).strip()
    if s in CR_NUM:
        return CR_NUM[s]
    try:
        return float(s)
    except ValueError:
        return 0.0


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def avg_dice(s):
    if not s:
        return 0
    m = re.search(r"(\d+)\s*\((\d+)d(\d+)\s*([+-]\s*\d+)?\)", s)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)d(\d+)\s*([+-]\s*\d+)?", s)
    if m:
        n, d, mod = int(m.group(1)), int(m.group(2)), m.group(3)
        mod = int(mod.replace(" ", "")) if mod else 0
        return round(n * (d + 1) / 2) + mod
    m = re.search(r"\b(\d{1,4})\b", s)
    return int(m.group(1)) if m else 0


def mod(score):
    return (int(score or 10) - 10) // 2


def attr_from(score):
    """D&D-характеристика -> атрибут «The Edge!» (0…8)."""
    return clamp(round(mod(score) / 1.5) + 2, 0, 8)


def attack_entries(actions, dmg_bonus):
    """Собирает оружие/атаки из действий D&D в формат «The Edge!»."""
    out, seen = [], set()
    for a in actions or []:
        if not isinstance(a, dict):
            continue
        name = (a.get("name") or "").strip()
        text = a.get("text") or ""
        if not name or name.lower().startswith("мультиатака"):
            continue
        if re.search(r"(мультиатака|multiattack)", name, re.I):
            continue
        avg = avg_dice(text)
        if avg <= 0 and not re.search(r"(урон|потеря|спасбросок)", text, re.I):
            continue
        low = name.lower()
        if re.search(r"(дальн|дальность 30|дальность 60|дальность 120|выстрел|снаряд|луч|конус|линией)", text, re.I):
            dist = "Даль"
        else:
            dist = "Рукопашная"
        bonus = clamp(round(avg / 7), 0, 5) if avg else 0
        key = (name.lower(), dist)
        if key in seen:
            continue
        seen.add(key)
        out.append({"name": name, "bonus": bonus, "dist": dist})
        if len(out) >= 3:
            break
    if not out:
        out = [{"name": "Атака", "bonus": dmg_bonus, "dist": "Рукопашная"}]
    return out


def build(d):
    s = d.get("dnd") or {}
    cr = cr_val(s.get("cr", 0))
    hp = avg_dice(s.get("hp", "")) or 10
    ac = avg_dice(s.get("ac", "")) or 12
    ab = s.get("abilities") or {}
    threat = int(d.get("threat") or 1)
    kind = d.get("kind", "creature")

    body = attr_from(ab.get("str", 10))
    dex = attr_from(ab.get("dex", 10))
    mind = attr_from(ab.get("int", 10))
    will = attr_from(round((int(ab.get("wis", 10)) + int(ab.get("cha", 10))) / 2))

    # доспех: из КД, поверх ловкости
    armor = clamp(round((ac - 12) / 2), 0, 5)
    defense = 8 + dex + armor

    # раны: база человека 6 + Тело, плюс за уровень опасности
    wounds = clamp(6 + body + round(cr / 2), 3, 40)
    # стресс: воля; у бессознательных тварей не используется
    if mind == 0 and threat <= 2:
        stress = None
    else:
        stress = clamp(6 + will, 3, 24)

    # урон основной атаки
    best = 0
    for a in (s.get("actions") or []):
        if isinstance(a, dict):
            best = max(best, avg_dice(a.get("text", "")))
    dmg_bonus = clamp(round(best / 7), 0, 5)

    return {
        "slug": d["slug"], "name_ru": d["name_ru"], "name_en": d.get("name_en", ""),
        "category": d.get("category"), "kind": kind, "threat": threat,
        "ugroza": THREAT_WORD.get(threat, "средняя"),
        "attrs": {"Тело": body, "Ловкость": dex, "Разум": mind, "Воля": will},
        "wounds": wounds,
        "stress": stress,
        "armor": armor,
        "defense": defense,
        "weapon": attack_entries(s.get("actions"), dmg_bonus),
        "_source": {"cr": s.get("cr"), "hp": hp, "ac": ac, "type": s.get("type")},
    }


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "creatures", "*.json"))):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        out[d["slug"]] = build(d)
    json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
    import collections
    print("скелетов:", len(out))
    print("Раны:", dict(sorted(collections.Counter(
        min(8, v["wounds"] // 4) * 4 for v in out.values()).items())))
    print("ЧЦ защиты:", dict(sorted(collections.Counter(v["defense"] for v in out.values()).items())))
    print("Угроза:", dict(collections.Counter(v["ugroza"] for v in out.values())))


if __name__ == "__main__":
    main()
