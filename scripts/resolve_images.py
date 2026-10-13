#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Шаг 1/2: ранжирует кандидатов-изображений для каждой записи и резолвит их в URL CDN."""
import json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://supernatural.fandom.com/api.php"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

BAD = re.compile(
    r"(site-?logo|wiki-?background|favicon|placeholder|noimage|no_image|"
    r"question|disambig|stub|redlink|supernatural_?wiki|fandom|advert|button|"
    r"template|wanted|noncanon|improvement|spoiler|barnstar|"
    r"\.svg$|\.ogg$|\.webm$|\.mp4$|\.pdf$|\.ico$)", re.I)
BAD_STRICT = re.compile(r"(icon|symbol|logo|flag|135px|100px)", re.I)


def api(params, tries=4):
    params = dict(params); params["format"] = "json"
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params),
                                 headers={"User-Agent": UA, "Accept": "application/json"})
    for a in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print("   retry", a, e, file=sys.stderr); time.sleep(2 + 3 * a)
    return {}


def page_images(title):
    d = api({"action": "query", "titles": title, "prop": "images", "imlimit": "200"})
    out = []
    for p in d.get("query", {}).get("pages", {}).values():
        out += [im["title"] for im in p.get("images", [])]
    return out


def candidates_for(c):
    """Возвращает ранжированный список имён файлов-кандидатов."""
    out = []
    img = ((c.get("info") or {}).get("image") or "").strip()
    if img and not BAD.search(img):
        out.append(img)
    page = c.get("wiki") or ""
    others = [n[5:] if n.lower().startswith("file:") else n for n in page_images(page)]
    key = re.sub(r"[^a-z0-9]", "", page.lower())
    scored = []
    for n in others:
        if BAD.search(n) or BAD_STRICT.search(n):
            continue
        if n in out:
            continue
        nk = re.sub(r"[^a-z0-9]", "", n.lower())
        score = 0
        if key and key[:8] and key[:8] in nk:
            score += 100
        if len(key) > 4 and key[:5] in nk:
            score += 30
        if n.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
            score += 5
        if n.lower().endswith(".gif"):
            score -= 20          # анимированный гиф хуже для карточки
        scored.append((-score, len(n), n))
    scored.sort()
    out += [n for _, _, n in scored]
    return out


def resolve(files, width=700):
    out = {}
    files = [f if f.lower().startswith("file:") else "File:" + f for f in files]
    for i in range(0, len(files), 40):
        d = api({"action": "query", "titles": "|".join(files[i:i + 40]), "prop": "imageinfo",
                 "iiprop": "url|size|mime", "iiurlwidth": str(width)})
        for p in d.get("query", {}).get("pages", {}).values():
            ii = (p.get("imageinfo") or [{}])[0]
            url = ii.get("thumburl") or ii.get("url")
            if url:
                out[p["title"]] = {"url": url, "w": ii.get("thumbwidth") or ii.get("width"),
                                   "h": ii.get("thumbheight") or ii.get("height"),
                                   "mime": ii.get("mime", "")}
        time.sleep(0.15)
    return out


def main():
    idx = json.load(open(os.path.join(ROOT, "data", "raw", "index.json")))
    cands = {c["slug"]: candidates_for(c) for c in idx}
    print("кандидатов собрано, записей с хотя бы одним: %d" %
          sum(1 for v in cands.values() if v))

    allfiles = sorted({f for v in cands.values() for f in v[:6]})
    print("резолвим до 6 кандидатов на запись, всего файлов:", len(allfiles))
    urlmap = resolve(allfiles)
    print("URL получено:", len(urlmap))

    def key(f):
        return f if f.lower().startswith("file:") else "File:" + f

    tasks, noimg = [], []
    for c in idx:
        slug = c["slug"]
        chosen = None
        for f in cands[slug][:6]:
            if key(f) in urlmap:
                chosen = (f, urlmap[key(f)])
                break
        if not chosen:
            noimg.append(slug)
            continue
        f, info = chosen
        tasks.append({"slug": slug, "file": f, "url": info["url"],
                      "w": info.get("w"), "h": info.get("h"), "mime": info.get("mime")})
    json.dump(tasks, open(os.path.join(ROOT, "data", "raw", "image_tasks.json"), "w"),
              ensure_ascii=False, indent=1)
    json.dump(noimg, open(os.path.join(ROOT, "data", "raw", "no_image.json"), "w"),
              ensure_ascii=False, indent=1)
    print("задач на скачивание: %d, без изображения: %d" % (len(tasks), len(noimg)))
    print("без изображения:", ", ".join(noimg[:40]))


if __name__ == "__main__":
    main()
