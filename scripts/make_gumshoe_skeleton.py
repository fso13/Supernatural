#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Считает числовой скелет GUMSHOE для каждой записи бестиария.

Формулы — детерминированное преобразование статблока D&D 5e в пулы GUMSHOE.
Документируются в rules.html, чтобы ведущий понимал, откуда числа.
"""
import json, glob, os, re, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "gumshoe", "skeleton.json")

CR_NUM = {"0": 0, "1/8": 0.125, "1/4": 0.25, "1/2": 0.5}


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
    """Средний урон из строки вида '19 (2d10 + 8) колющего'."""
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
    m = re.search(r"\b(\d{1,3})\b", s)
    return int(m.group(1)) if m else 0


def build(d):
    s = d.get("dnd") or {}
    cr = cr_val(s.get("cr", 0))
    hp = avg_dice(s.get("hp", "")) or 10
    ac = avg_dice(s.get("ac", "")) or 12
    ab = s.get("abilities") or {}
    threat = int(d.get("threat") or 1)
    kind = d.get("kind", "creature")
    typ = (s.get("type") or "").lower()

    # --- пулы общих способностей ---
    athletics = clamp(round(cr / 2) + 2, 2, 20)
    fight = clamp(round(cr / 2) + 3, 3, 24)
    health = clamp(round(hp / 7) + 2, 3, 45)
    alertness = clamp(round(cr / 3) + 3, 3, 14)

    abilities = {"Атлетика": athletics, "Бой": fight, "Здоровье": health,
                 "Бдительность": alertness}

    # ловкие/скрытные получают Скрытность
    dex = int(ab.get("dex") or 10)
    intl = int(ab.get("int") or 10)
    cha = int(ab.get("cha") or 10)
    if dex >= 13 or typ in ("фея", "аберрация"):
        abilities["Скрытность"] = clamp(round(cr / 3) + 3, 3, 16)
    if typ in ("исчадие", "демон", "дьявол"):
        abilities["Подготовка"] = clamp(round(cr / 3) + 3, 3, 14)
    if intl >= 15:
        abilities["Воля"] = clamp(round(cr / 3) + 4, 4, 16)
    if cha >= 15 or d.get("category") in ("Ангел", "Божество"):
        abilities["Репутация"] = clamp(round(cr / 3) + 3, 3, 14)
    # стрельба только у тех, кто бьёт издалека
    acts = " ".join((a.get("text") or "") for a in (s.get("actions") or [])
                    if isinstance(a, dict))
    if re.search(r"(дальн|дальность|метател|выстрел|конус|линией|снаряд)", acts, re.I):
        abilities["Стрельба"] = clamp(round(cr / 2) + 3, 3, 20)

    # --- порог попадания ---
    ht = clamp(3 + round((ac - 12) / 4), 3, 6)
    if kind == "being" and cr >= 20:
        ht = clamp(ht, 5, 6)

    # --- урон ---
    best = 0
    for a in (s.get("actions") or []):
        if isinstance(a, dict):
            best = max(best, avg_dice(a.get("text", "")))
    dmg_mod = clamp(round(best / 6) - 1, 0, 4)

    # --- потеря Стабильности ---
    base = threat
    mult = 1.35 if typ in ("аберрация", "нежить", "исчадие", "демон", "дьявол") else 1.0
    test_loss = clamp(round(base * mult), 0, 7)
    wit_loss = clamp(round(base * mult) + 2, 0, 8)
    if kind in ("place", "artifact", "lore"):
        test_loss, wit_loss = 0, clamp(threat - 1, 0, 4)
    if d.get("category") == "Монстр" and threat <= 2:
        test_loss, wit_loss = 0, max(0, wit_loss - 3)

    armor = "—"
    res = (s.get("damage_resistances") or "").lower()
    if "немагическ" in res:
        armor = "−1 против обычного оружия"

    return {
        "slug": d["slug"], "name_ru": d["name_ru"], "name_en": d.get("name_en", ""),
        "category": d.get("category"), "kind": kind, "threat": threat,
        "abilities": abilities,
        "hit_threshold": ht,
        "damage_mod": dmg_mod,
        "stability": {"test": test_loss, "witnessed": wit_loss},
        "armor": armor,
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
    print("Health:", dict(collections.Counter(
        min(6, v["abilities"]["Здоровье"] // 5) * 5 for v in out.values())))
    print("Hit Threshold:", dict(collections.Counter(v["hit_threshold"] for v in out.values())))
    print("Stability test:", dict(collections.Counter(v["stability"]["test"] for v in out.values())))


if __name__ == "__main__":
    main()
