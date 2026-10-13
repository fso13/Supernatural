#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Оптимизирует изображения бестиария: ограничивает ширину и пережимает в JPEG/WebP."""
import json, os, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMGDIR = os.path.join(ROOT, "site", "img")
MAXW = 900
state_path = os.path.join(ROOT, "data", "raw", "images.json")
state = json.load(open(state_path))


def optimize(path, slug):
    before = os.path.getsize(path)
    try:
        im = Image.open(path)
    except Exception as e:
        return None, "не открылось: %s" % e
    animated = getattr(im, "is_animated", False)
    im.load()
    w, h = im.size
    changed = False
    if w > MAXW:
        nh = max(1, round(h * MAXW / w))
        im = im.resize((MAXW, nh), Image.LANCZOS)
        w, h = MAXW, nh
        changed = True
    # непрозрачные картинки переводим в JPEG — так в разы легче
    has_alpha = im.mode in ("RGBA", "LA", "P")
    ext = os.path.splitext(path)[1].lower()
    if animated:
        im.save(path, save_all=True, format="WEBP", quality=78, method=4)
        newpath = path
    elif has_alpha and ext == ".png":
        im.save(path, format="PNG", optimize=True)
        newpath = path
    else:
        rgb = im.convert("RGB")
        newpath = os.path.join(IMGDIR, slug + ".jpg")
        rgb.save(newpath, format="JPEG", quality=84, optimize=True, progressive=True)
        if newpath != path and os.path.exists(path):
            os.remove(path)
        changed = True
    after = os.path.getsize(newpath)
    return (newpath, before, after, w, h, changed), None


def main():
    total_before = total_after = 0
    rows = []
    for slug, rec in list(state.items()):
        local = rec.get("local")
        if not local:
            continue
        p = os.path.join(ROOT, "site", local)
        if not os.path.exists(p):
            continue
        res, err = optimize(p, slug)
        if err:
            print("  !! %s: %s" % (slug, err)); continue
        newpath, before, after, w, h, changed = res
        total_before += before
        total_after += after
        rec["local"] = "img/" + os.path.basename(newpath)
        rec["w"], rec["h"] = w, h
        rec["bytes"] = after
        if changed:
            rows.append((before - after, slug, before, after))
    json.dump(state, open(state_path, "w"), ensure_ascii=False, indent=1)
    rows.sort(reverse=True)
    print("сжато файлов: %d" % len(rows))
    for d, slug, b, a in rows[:10]:
        print("  %-24s %6.0f КБ -> %5.0f КБ" % (slug, b / 1024, a / 1024))
    print("итого: %.1f МБ -> %.1f МБ" % (total_before / 1e6, total_after / 1e6))


if __name__ == "__main__":
    main()
