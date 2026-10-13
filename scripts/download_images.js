#!/usr/bin/env node
/**
 * Качает изображения через живую сессию headless Chrome (CDP):
 * CDN Fandom отдаёт картинки только браузеру, прошедшему Cloudflare-челлендж.
 *
 * Запуск: node scripts/download_images.js <debugPort> [from] [to]
 *   from/to — индексы в списке ещё не скачанных задач (для батчей).
 */
"use strict";
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const PORT = process.argv[2] || "9333";
const FROM = parseInt(process.argv[3] || "0", 10);
const TO = parseInt(process.argv[4] || "100000", 10);
const ALL = JSON.parse(fs.readFileSync(path.join(ROOT, "data/raw/image_tasks.json"), "utf8"));
const OUTDIR = path.join(ROOT, "site", "img");
const STATE = path.join(ROOT, "data/raw/images.json");
fs.mkdirSync(OUTDIR, { recursive: true });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const EXT = { "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
              "image/gif": ".gif", "image/avif": ".avif" };

const CHECK_EXPR = `({ct: document.contentType, href: location.href,
  imgs: document.images.length,
  w: (document.querySelector('img')||{}).naturalWidth || 0,
  src: (document.querySelector('img')||{}).src || ''})`;

const FETCH_EXPR = `(async () => {
  try {
    const r = await fetch(location.href, {credentials:'include'});
    const b = await r.blob();
    if (!/^image\\//.test(b.type)) return {ok:false, err:'not image: '+b.type};
    const d = await new Promise(res => { const fr = new FileReader(); fr.onload=()=>res(fr.result); fr.readAsDataURL(b); });
    return {ok:true, type:b.type, data:d};
  } catch (e) { return {ok:false, err:'fetch: '+String(e)}; }
})()`;

const CANVAS_EXPR = `(async () => {
  const img = document.querySelector('img');
  if (!img) return {ok:false, err:'no <img>'};
  for (let i=0;i<30 && !(img.complete && img.naturalWidth>0);i++) await new Promise(r=>setTimeout(r,300));
  if (!img.naturalWidth) return {ok:false, err:'image not loaded'};
  try {
    const c=document.createElement('canvas'); c.width=img.naturalWidth; c.height=img.naturalHeight;
    c.getContext('2d').drawImage(img,0,0);
    return {ok:true, type:'image/png', data:c.toDataURL('image/png')};
  } catch(e){ return {ok:false, err:'canvas: '+String(e)}; }
})()`;

class CDP {
  constructor(ws) { this.ws = ws; this.id = 0; this.pend = new Map(); }
  static async connect(port) {
    for (let i = 0; i < 40; i++) {
      try {
        const r = await fetch(`http://127.0.0.1:${port}/json/list`);
        const list = await r.json();
        const page = list.find((t) => t.type === "page") || list[0];
        if (page && page.webSocketDebuggerUrl) {
          const ws = new WebSocket(page.webSocketDebuggerUrl);
          await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
          const c = new CDP(ws);
          ws.onmessage = (m) => {
            const msg = JSON.parse(m.data);
            if (msg.id && c.pend.has(msg.id)) {
              const { res, rej } = c.pend.get(msg.id);
              c.pend.delete(msg.id);
              msg.error ? rej(new Error(JSON.stringify(msg.error))) : res(msg.result);
            }
          };
          return c;
        }
      } catch (e) { /* chrome ещё поднимается */ }
      await sleep(500);
    }
    throw new Error("нет соединения с Chrome на порту " + port);
  }
  send(method, params) {
    const id = ++this.id;
    return new Promise((res, rej) => {
      this.pend.set(id, { res, rej });
      this.ws.send(JSON.stringify({ id, method, params: params || {} }));
      setTimeout(() => { if (this.pend.has(id)) { this.pend.delete(id); rej(new Error("timeout " + method)); } }, 60000);
    });
  }
}

function alreadyHave(slug) {
  for (const ext of Object.values(EXT)) {
    const p = path.join(OUTDIR, slug + ext);
    if (fs.existsSync(p) && fs.statSync(p).size > 900) return { dest: p, ext };
  }
  return null;
}

async function main() {
  const state = fs.existsSync(STATE) ? JSON.parse(fs.readFileSync(STATE, "utf8")) : {};
  const todo = ALL.filter((t) => !alreadyHave(t.slug));
  const batch = todo.slice(FROM, TO);
  console.log(`всего задач ${ALL.length}, осталось ${todo.length}, в этом батче ${batch.length}`);
  if (!batch.length) { console.log("нечего делать"); return; }

  const cdp = await CDP.connect(PORT);
  await cdp.send("Page.enable");
  await cdp.send("Runtime.enable");
  console.log("прогрев домена…");
  await cdp.send("Page.navigate", { url: "https://static.wikia.nocookie.net/" });
  await sleep(8000);

  let done = 0, fail = 0;
  for (const t of batch) {
    let ok = false, lastErr = "";
    for (let attempt = 1; attempt <= 3 && !ok; attempt++) {
      try {
        await cdp.send("Page.navigate", { url: t.url });
        await sleep(attempt === 1 ? 900 : 2500 * attempt);
        // отсекаем страницу Cloudflare-проверки и прочий HTML
        let meta = null;
        try {
          const mr = await cdp.send("Runtime.evaluate",
            { expression: CHECK_EXPR, returnByValue: true });
          meta = (mr.result || {}).value;
        } catch (e) { meta = null; }
        const isImageDoc = meta && String(meta.ct || "").startsWith("image/");
        if (!isImageDoc) {
          lastErr = "не изображение: " + JSON.stringify(meta).slice(0, 90);
          await sleep(2000 * attempt);
          continue;
        }
        let v = null;
        for (const expr of [FETCH_EXPR, CANVAS_EXPR]) {
          try {
            const r = await cdp.send("Runtime.evaluate",
              { expression: expr, awaitPromise: true, returnByValue: true });
            v = (r.result || {}).value;
          } catch (e) { v = { ok: false, err: String(e).slice(0, 90) }; }
          if (v && v.ok && v.data && v.data.startsWith("data:image")) break;
        }
        if (v && v.ok && v.data && v.data.startsWith("data:image")) {
          const ext = EXT[v.type] || ".jpg";
          const buf = Buffer.from(v.data.split(",")[1], "base64");
          if (buf.length < 400) throw new Error("мало байт: " + buf.length);
          fs.writeFileSync(path.join(OUTDIR, t.slug + ext), buf);
          state[t.slug] = { file: t.file, url: t.url, local: "img/" + t.slug + ext,
                            w: t.w, h: t.h, mime: v.type, bytes: buf.length };
          ok = true;
        } else { lastErr = JSON.stringify(v).slice(0, 130); }
      } catch (e) { lastErr = String(e).slice(0, 130); }
    }
    if (ok) done++;
    else {
      fail++;
      state[t.slug] = Object.assign({}, state[t.slug], { file: t.file, url: t.url, error: lastErr });
      console.log("  !! " + t.slug + " — " + lastErr);
    }
    if ((done + fail) % 15 === 0) {
      fs.writeFileSync(STATE, JSON.stringify(state, null, 1));
      console.log(`  батч: ок ${done}, ошибок ${fail} (из ${batch.length})`);
    }
    await sleep(150);
  }
  fs.writeFileSync(STATE, JSON.stringify(state, null, 1));
  console.log(`БАТЧ ГОТОВ: ок ${done}, ошибок ${fail}, из ${batch.length}`);
  cdp.ws.close();
}

main().then(() => process.exit(0)).catch((e) => { console.error("FATAL", e); process.exit(1); });
