#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Добирает изображения для записей без картинки через поиск в пространстве файлов вики."""
import json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://supernatural.fandom.com/api.php"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
BAD = re.compile(r"(logo|icon|symbol|flag|background|placeholder|noimage|no_image|"
                 r"template|wanted|noncanon|improvement|stub|spoiler|redlink|"
                 r"\.svg$|\.ogg$|\.webm$|\.mp4$|\.pdf$|\.ico$|\.gif$)", re.I)


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


def search_files(query, limit=12):
    d = api({"action": "query", "list": "search", "srsearch": query,
             "srnamespace": "6", "srlimit": str(limit)})
    return [h["title"] for h in d.get("query", {}).get("search", [])]


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
    idx = {c["slug"]: c for c in json.load(open(os.path.join(ROOT, "data/raw/index.json")))}
    tasks = json.load(open(os.path.join(ROOT, "data/raw/image_tasks.json")))
    have = {t["slug"] for t in tasks}
    missing = [s for s in idx if s not in have]
    print("записей без картинки:", len(missing))

    queries = {}
    for slug in missing:
        c = idx[slug]
        for q in [c["wiki"], c.get("ru", ""), c["wiki"] + " character"]:
            if not q:
                continue
            hits = [h for h in search_files(q) if not BAD.search(h[5:])]
            if hits:
                queries[slug] = hits[:5]
                break
        time.sleep(0.12)

    allfiles = [f for v in queries.values() for f in v]
    print("кандидатов найдено:", len(allfiles), "для", len(queries), "записей")
    urlmap = resolve(sorted(set(allfiles)))

    def key(f):
        return f if f.lower().startswith("file:") else "File:" + f

    added = []
    for slug, files in queries.items():
        for f in files:
            info = urlmap.get(key(f))
            if not info:
                continue
            tasks.append({"slug": slug, "file": f[5:] if f.lower().startswith("file:") else f,
                          "url": info["url"], "w": info.get("w"), "h": info.get("h"),
                          "mime": info.get("mime")})
            added.append((slug, f))
            break

    json.dump(tasks, open(os.path.join(ROOT, "data", "raw", "image_tasks.json"), "w"),
              ensure_ascii=False, indent=1)
    print("добавлено задач:", len(added))
    for s, f in added:
        print("  %-26s %s" % (s, f))


if __name__ == "__main__":
    main()
