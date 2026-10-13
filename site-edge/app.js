/* ============================================================
   Бестиарий «The Edge!» — логика приложения
   ============================================================ */
(function () {
  "use strict";

  var DATA = (window.BESTIARY || []).slice();
  var BUILD = window.BUILD || {};

  var CAT_COLORS = {
    "Монстр":   "#c96a3f", "Демон": "#b7222b", "Ангел": "#6fa8dc",
    "Божество": "#e0b64a", "Дух": "#7fb8a4", "Ведьма": "#a274c9",
    "Левиафан": "#5f9e6e", "Иное": "#8c8c99"
  };
  var CAT_ICON = { "Монстр": "🐾", "Демон": "😈", "Ангел": "😇", "Божество": "⚡",
                   "Дух": "👻", "Ведьма": "🕯", "Левиафан": "🐍", "Иное": "🌀" };
  var UGROZA_ORDER = ["низкая", "средняя", "высокая", "очень высокая", "смертельная"];

  function catColor(c) { return CAT_COLORS[c] || "#8c8c99"; }
  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
  function list(v) { return Array.isArray(v) ? v.filter(Boolean) : (v ? [v] : []); }
  function dash(v) {
    return (v === undefined || v === null || v === "" ||
            (Array.isArray(v) && !v.length)) ? "" : v;
  }

  DATA.forEach(function (d) {
    d._threat = +d.threat || 1;
    d._wounds = +d.wounds || 0;
    d._def = +d.defense || 0;
    d._ugr = UGROZA_ORDER.indexOf(d.ugroza) + 1 || 1;
    d._seasons = list(d.seasons).map(Number).filter(function (n) { return !isNaN(n); });
    d._first = d._seasons.length ? Math.min.apply(null, d._seasons) : 99;
    var a = d.attrs || {};
    d._sum = (a["Тело"] || 0) + (a["Ловкость"] || 0) + (a["Разум"] || 0) + (a["Воля"] || 0);
    d._search = [
      d.name_ru, d.name_en, list(d.aka).join(" "), d.category, d.ugroza,
      d.summary, d.look, d.lore, d.weakness, d.notes,
      list(d.powers).join(" "), list(d.weaknesses).join(" "),
      (d.special || []).map(function (x) { return x.name + " " + x.text; }).join(" "),
      (d.learn || []).map(function (x) { return x.skill + " " + x.text; }).join(" "),
      (d.weapon || []).map(function (x) { return x.name; }).join(" ")
    ].join(" ").toLowerCase();
  });

  var SPECIES = DATA.filter(function (d) { return d.kind === "creature" || d.kind === "being"; });
  var APPENDIX = DATA.filter(function (d) {
    return d.kind === "place" || d.kind === "artifact" || d.kind === "lore";
  });

  var state = { q: "", cat: "", ugr: "", wnd: "", kind: "", season: "", sort: "name" };

  var cats = {}, ugrs = {}, seasons = {};
  SPECIES.forEach(function (d) {
    if (d.category) cats[d.category] = (cats[d.category] || 0) + 1;
    ugrs[d.ugroza] = (ugrs[d.ugroza] || 0) + 1;
    d._seasons.forEach(function (s) { seasons[s] = (seasons[s] || 0) + 1; });
  });

  function fill(el, items, fmt) {
    items.forEach(function (it) {
      var o = document.createElement("option");
      o.value = it[0]; o.textContent = fmt ? fmt(it[0], it[1]) : it[0];
      el.appendChild(o);
    });
  }
  fill(document.getElementById("f-cat"),
    Object.keys(cats).sort().map(function (k) { return [k, cats[k]]; }),
    function (k, n) { return k + " (" + n + ")"; });
  fill(document.getElementById("f-ugr"),
    UGROZA_ORDER.slice().reverse().filter(function (u) { return ugrs[u]; })
      .map(function (u) { return [u, ugrs[u]]; }),
    function (u, n) { return u + " (" + n + ")"; });
  var wnds = [];
  SPECIES.forEach(function (d) {
    var b = Math.floor(d._wounds / 5) * 5;
    if (wnds.indexOf(b) === -1) wnds.push(b);
  });
  wnds.sort(function (a, b) { return a - b; });
  fill(document.getElementById("f-wnd"), wnds.map(function (v) { return [v]; }),
    function (v) { return v + " и больше"; });
  fill(document.getElementById("f-season"),
    Object.keys(seasons).map(Number).sort(function (a, b) { return a - b; })
      .map(function (s) { return [s, seasons[s]]; }),
    function (s, n) { return "Сезон " + s + " (" + n + ")"; });

  var qEl = document.getElementById("q");
  var qt;
  qEl.addEventListener("input", function (e) {
    clearTimeout(qt);
    var v = e.target.value;
    qt = setTimeout(function () { state.q = v.trim().toLowerCase(); render(); }, 130);
  });
  [["f-cat", "cat"], ["f-ugr", "ugr"], ["f-wnd", "wnd"], ["f-kind", "kind"],
   ["f-season", "season"], ["f-sort", "sort"]].forEach(function (p) {
    document.getElementById(p[0]).addEventListener("change", function (e) {
      state[p[1]] = e.target.value; render();
    });
  });
  document.getElementById("reset").addEventListener("click", function () {
    state = { q: "", cat: "", ugr: "", wnd: "", kind: "", season: "", sort: "name" };
    qEl.value = "";
    ["f-cat", "f-ugr", "f-wnd", "f-kind", "f-season"].forEach(function (id) {
      document.getElementById(id).value = "";
    });
    document.getElementById("f-sort").value = "name";
    render();
  });

  function readParams() {
    var p = new URLSearchParams(location.search);
    Object.keys(state).forEach(function (k) { if (p.has(k)) state[k] = p.get(k); });
  }
  function writeParams() {
    if (!history.replaceState) return;
    var p = new URLSearchParams();
    Object.keys(state).forEach(function (k) {
      if (state[k] && !(k === "sort" && state[k] === "name")) p.set(k, state[k]);
    });
    var qs = p.toString();
    history.replaceState(null, "", location.pathname + (qs ? "?" + qs : "") + (location.hash || ""));
  }
  readParams();
  qEl.value = state.q || "";
  [["f-cat", "cat"], ["f-ugr", "ugr"], ["f-wnd", "wnd"], ["f-kind", "kind"],
   ["f-season", "season"], ["f-sort", "sort"]].forEach(function (p) {
    var el = document.getElementById(p[0]);
    if (state[p[1]]) el.value = state[p[1]];
    state[p[1]] = el.value;
  });

  function match(d) {
    if (state.q) {
      var w = state.q.split(/\s+/);
      for (var i = 0; i < w.length; i++) if (d._search.indexOf(w[i]) === -1) return false;
    }
    if (state.cat && d.category !== state.cat) return false;
    if (state.ugr && d.ugroza !== state.ugr) return false;
    if (state.wnd !== "" && d._wounds < +state.wnd) return false;
    if (state.kind && d.kind !== state.kind) return false;
    if (state.season !== "" && d._seasons.indexOf(+state.season) === -1) return false;
    return true;
  }
  var CMP = {
    name: function (a, b) { return a.name_ru.localeCompare(b.name_ru, "ru"); },
    threat: function (a, b) { return b._threat - a._threat || a.name_ru.localeCompare(b.name_ru, "ru"); },
    wounds: function (a, b) { return b._wounds - a._wounds || a.name_ru.localeCompare(b.name_ru, "ru"); },
    def: function (a, b) { return b._def - a._def || a.name_ru.localeCompare(b.name_ru, "ru"); }
  };

  /* ---------- карточки ---------- */
  function ugrozaPips(u) {
    var n = Math.max(1, UGROZA_ORDER.indexOf(u) + 1);
    var s = '<span class="pips" title="Угроза: ' + esc(u) + '">';
    for (var i = 1; i <= 5; i++) s += '<i class="' + (i <= n ? "on u" + n : "") + '"></i>';
    return s + "</span>";
  }
  function placeholder(d, cls) {
    var col = catColor(d.category);
    var label = String(d.name_ru || "").replace(/\s*\([^)]*\)\s*/g, " ").trim() || "?";
    return '<div class="ph ' + (cls || "thumb") + '" style="--catcolor:' + col + '">' +
      '<span class="ph-icon">' + (CAT_ICON[d.category] || "✦") + "</span>" +
      '<span class="ph-name">' + esc(label) + "</span>" +
      (d.name_en ? '<span class="ph-en">' + esc(d.name_en) + "</span>" : "") + "</div>";
  }
  function thumb(d, cls) {
    var c = cls || "thumb";
    if (d.image) {
      return '<div class="' + c + '"><img loading="lazy" decoding="async" src="../site/' +
        esc(d.image) + '" alt="' + esc(d.name_ru) + '" ' +
        "onerror=\"this.parentNode.classList.add('broken');this.remove()\"></div>";
    }
    return placeholder(d, c);
  }
  function hero(d) {
    if (d.image) {
      return '<figure class="hero"><img loading="eager" decoding="async" src="../site/' +
        esc(d.image) + '" alt="' + esc(d.name_ru) + '" ' +
        "onerror=\"this.parentNode.classList.add('broken');this.remove()\"></figure>";
    }
    return placeholder(d, "hero ph-hero");
  }

  function card(d) {
    var a = d.attrs || {};
    return '<article class="card" data-slug="' + esc(d.slug) +
      '" style="--catcolor:' + catColor(d.category) + '">' + thumb(d) +
      '<div class="card-body">' +
      "<h3>" + esc(d.name_ru) + "</h3>" +
      '<div class="en">' + esc(d.name_en) + " · " + esc(d.ugroza) + "</div>" +
      '<p class="sum">' + esc(d.look || d.summary || "") + "</p>" +
      '<div class="attrs-mini">' +
        "<span>Т<b>" + (a["Тело"] || 0) + "</b></span>" +
        "<span>Л<b>" + (a["Ловкость"] || 0) + "</b></span>" +
        "<span>Р<b>" + (a["Разум"] || 0) + "</b></span>" +
        "<span>В<b>" + (a["Воля"] || 0) + "</b></span>" +
      "</div>" +
      '<div class="badges">' +
        '<span class="badge cat">' + esc(d.category) + "</span>" +
        '<span class="badge wnd">Раны ' + d._wounds + "</span>" +
        '<span class="badge def">ЧЦ ' + d._def + "</span>" +
        ugrozaPips(d.ugroza) +
      "</div></div></article>";
  }

  function renderGrid(el, arr, emptyEl) {
    el.innerHTML = arr.map(card).join("");
    if (emptyEl) emptyEl.hidden = arr.length > 0;
  }
  function render() {
    var arr = SPECIES.filter(match).sort(CMP[state.sort] || CMP.name);
    renderGrid(document.getElementById("grid"), arr, document.getElementById("empty"));
    document.getElementById("count").textContent =
      arr.length + " из " + SPECIES.length + " существ" +
      (APPENDIX.length ? "  ·  в приложении ещё " + APPENDIX.length : "");
    document.getElementById("qhint").textContent = arr.length ? "" : "нет совпадений";
    writeParams();
  }

  /* ---------- статблок «The Edge!» ---------- */
  function statblock(d) {
    var a = d.attrs || {};
    var L = ['<div class="es">'];
    L.push('<div class="es-head"><h3>' + esc(d.name_ru) + "</h3>" +
      '<p class="sub">Угроза: <b>' + esc(d.ugroza) + "</b> · " + esc(d.category) + "</p></div>");
    L.push('<div class="es-attrs">' +
      ["Тело", "Ловкость", "Разум", "Воля"].map(function (k) {
        return '<div class="at"><b>' + (a[k] != null ? a[k] : "—") + "</b><span>" + k + "</span></div>";
      }).join("") + "</div>");
    L.push('<div class="es-crit">' +
      '<div class="cr"><b>' + d._wounds + "</b><span>Раны</span></div>" +
      '<div class="cr"><b>' + (d.stress == null ? "—" : d.stress) + "</b><span>Стресс</span></div>" +
      '<div class="cr"><b>' + d._def + "</b><span>ЧЦ защиты</span></div>" +
      '<div class="cr"><b>' + (d.armor ? "+" + d.armor : "0") + "</b><span>Доспех</span></div>" +
      "</div>");
    L.push('<div class="es-line"><b>Расчёт ЧЦ</b> 8 + Ловкость ' + (a["Ловкость"] || 0) +
      " + доспех " + (d.armor || 0) + " = <strong>" + d._def + "</strong></div>");
    if ((d.weapon || []).length) {
      L.push("<h4>Оружие</h4>");
      d.weapon.forEach(function (w) {
        L.push('<div class="es-weap"><span class="wn">' + esc(w.name) + "</span>" +
          '<span class="wb">+' + w.bonus + "</span>" +
          '<span class="wd">' + esc(w.dist) + "</span></div>");
      });
      L.push('<p class="hintline">Урон = (итог атаки − ЧЦ защиты) + бонус оружия.</p>');
    }
    L.push("</div>");
    return L.join("");
  }

  function learnBlock(d) {
    var lr = d.learn || [];
    if (!lr.length) return "";
    return "<h4>Как узнать</h4>" + lr.map(function (c) {
      return '<p class="chk"><span class="sk">' + esc(c.skill) + "</span>" +
        '<span class="at">' + esc(c.attr) + "</span>" +
        '<span class="cc">ЧЦ ' + c.cch + "</span>" + esc(c.text) + "</p>";
    }).join("");
  }

  function specialBlock(d) {
    var sp = d.special || [];
    if (!sp.length) return "";
    return "<h4>Особое</h4>" + sp.map(function (e) {
      return '<p class="entry"><b>' + esc(e.name) + ".</b> " + esc(e.text) + "</p>";
    }).join("");
  }

  function detail(d) {
    var col = catColor(d.category);
    var meta = [];
    if (dash(d.category)) meta.push(["Категория", d.category]);
    if (dash(d.name_en)) meta.push(["Оригинал", d.name_en]);
    if (dash(d.first_appearance)) meta.push(["Первое появление", d.first_appearance]);
    if (d._seasons.length) meta.push(["Сезоны", d._seasons.join(", ")]);
    meta.push(["Угроза", d.ugroza]);
    meta.push(["Роль", d.kind === "being" ? "высшая сущность" : "существо"]);

    var powers = list(d.powers), weak = list(d.weaknesses), notable = list(d.notable);

    return '<button class="close" data-close aria-label="Закрыть">✕</button>' +
      '<div class="sheet-head" style="border-color:' + col + '55">' +
        "<h2>" + esc(d.name_ru) + "</h2>" +
        '<div class="en">' + esc(d.name_en) + " · " + esc(d.category) + " · " + esc(d.ugroza) + "</div>" +
        (list(d.aka).length ? '<div class="aka">Также известно как: ' +
          esc(list(d.aka).join("; ")) + "</div>" : "") +
      "</div>" + hero(d) +
      '<div class="sheet-grid">' +
      '<div class="lore">' +
        (dash(d.look) ? "<h4>Как выглядит</h4><p><strong>" + esc(d.look) + "</strong></p>" : "") +
        "<h4>Кто это</h4><p>" + esc(d.summary || "") + "</p>" +
        "<h4>Описание</h4>" + (d.lore || "").split(/\n\s*\n/).filter(Boolean)
          .map(function (p) { return "<p>" + esc(p) + "</p>"; }).join("") +
        (powers.length ? "<h4>Силы (из сериала)</h4><ul>" + powers
          .map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ul>" : "") +
        (weak.length ? "<h4>Слабости (из сериала)</h4><ul>" + weak
          .map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ul>" : "") +
        (notable.length ? '<h4>Известные особи</h4><ul class="notable">' + notable
          .map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ul>" : "") +
      "</div>" +
      '<div class="col">' +
        "<h4>Карточка</h4>" +
        '<table class="meta-table">' + meta.map(function (m) {
          return "<tr><td>" + esc(m[0]) + "</td><td>" + esc(m[1]) + "</td></tr>";
        }).join("") + "</table>" +
        "<h4>Статблок «The Edge!»</h4>" + statblock(d) +
        specialBlock(d) +
        (dash(d.weakness) ? '<h4>Слабость</h4><p class="weak">' + esc(d.weakness) + "</p>" : "") +
        learnBlock(d) +
        (dash(d.notes) ? '<h4>Заметки хранителю</h4><p class="dnd-notes">' + esc(d.notes) + "</p>" : "") +
      "</div></div>";
  }

  /* ---------- модальное окно ---------- */
  var modal = document.getElementById("modal");
  var sheet = document.getElementById("sheet");
  var lastFocus = null;
  function open(slug) {
    var d = DATA.filter(function (x) { return x.slug === slug; })[0];
    if (!d) return;
    lastFocus = document.activeElement;
    sheet.innerHTML = detail(d);
    modal.hidden = false;
    document.body.style.overflow = "hidden";
    sheet.scrollTop = 0;
    if (history.replaceState) history.replaceState(null, "", "#" + slug);
    sheet.querySelector(".close").focus();
  }
  function close() {
    modal.hidden = true;
    document.body.style.overflow = "";
    if (history.replaceState) history.replaceState(null, "", location.pathname + location.search);
    if (lastFocus) lastFocus.focus();
  }
  document.addEventListener("click", function (e) {
    var c = e.target.closest(".card");
    if (c) { open(c.getAttribute("data-slug")); return; }
    if (e.target.closest("[data-close]")) close();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !modal.hidden) close();
    if (e.key === "/" && document.activeElement !== qEl && modal.hidden) {
      e.preventDefault(); qEl.focus();
    }
  });

  document.getElementById("tabs").addEventListener("click", function (e) {
    var b = e.target.closest("button.tab");
    if (!b) return;
    var v = b.getAttribute("data-view");
    Array.prototype.forEach.call(document.querySelectorAll("button.tab"), function (t) {
      t.classList.toggle("is-active", t === b);
    });
    Array.prototype.forEach.call(document.querySelectorAll(".view"), function (s) {
      s.classList.toggle("is-active", s.id === "view-" + v);
    });
    location.hash = v;
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  /* ---------- таблицы ---------- */
  function tables() {
    var host = document.getElementById("tables");
    var out = "";

    out += '<div class="tblwrap"><h3>Противники по ЧЦ защиты</h3>' +
      '<table class="data"><thead><tr><th>ЧЦ</th><th>Существо</th><th>Раны</th>' +
      "<th>Угроза</th><th>Чем берут</th></tr></thead><tbody>" +
      SPECIES.slice().sort(CMP.def).map(function (d) {
        return "<tr><td><strong>" + d._def + "</strong></td><td>" + esc(d.name_ru) +
          "</td><td>" + d._wounds + "</td><td>" + esc(d.ugroza) + "</td><td>" +
          esc((d.weakness || "").split(". ")[0].slice(0, 120)) + "</td></tr>";
      }).join("") + "</tbody></table></div>";

    out += '<div class="tblwrap"><h3>Живучесть: раны и стресс</h3>' +
      '<table class="data"><thead><tr><th>Раны</th><th>Существо</th><th>Стресс</th>' +
      "<th>Атрибуты Т/Л/Р/В</th><th>Угроза</th></tr></thead><tbody>" +
      SPECIES.slice().sort(CMP.wounds).map(function (d) {
        var a = d.attrs || {};
        return "<tr><td><strong>" + d._wounds + "</strong></td><td>" + esc(d.name_ru) +
          "</td><td>" + (d.stress == null ? "—" : d.stress) + "</td><td>" +
          (a["Тело"] || 0) + "/" + (a["Ловкость"] || 0) + "/" + (a["Разум"] || 0) + "/" +
          (a["Воля"] || 0) + "</td><td>" + esc(d.ugroza) + "</td></tr>";
      }).join("") + "</tbody></table></div>";

    var byU = {};
    SPECIES.forEach(function (d) { (byU[d.ugroza] = byU[d.ugroza] || []).push(d); });
    out += '<div class="tblwrap"><h3>Состав по угрозе</h3>' +
      '<table class="data"><thead><tr><th>Угроза</th><th>Существ</th>' +
      "<th>Средние раны</th><th>Средний ЧЦ</th></tr></thead><tbody>" +
      UGROZA_ORDER.filter(function (u) { return byU[u]; }).map(function (u) {
        var arr = byU[u];
        var avgW = arr.reduce(function (s, d) { return s + d._wounds; }, 0) / arr.length;
        var avgD = arr.reduce(function (s, d) { return s + d._def; }, 0) / arr.length;
        return "<tr><td>" + u + "</td><td>" + arr.length + "</td><td>" +
          avgW.toFixed(1) + "</td><td>" + avgD.toFixed(1) + "</td></tr>";
      }).join("") + "</tbody></table></div>";

    function band(lo, hi, title, note) {
      var arr = SPECIES.filter(function (d) { return d._def >= lo && d._def <= hi; }).sort(CMP.name);
      return '<div class="tblwrap"><h3>' + title + '</h3><p class="lead">' + note + "</p>" +
        '<table class="data"><thead><tr><th>ЧЦ</th><th>Существо</th><th>Раны</th></tr></thead><tbody>' +
        arr.map(function (d) {
          return "<tr><td>" + d._def + "</td><td>" + esc(d.name_ru) + "</td><td>" +
            d._wounds + "</td></tr>";
        }).join("") + "</tbody></table></div>";
    }
    out += band(8, 11, "ЧЦ 8–11: берут новички",
      "Обычно 10–11 — стандарт сцены. Сюда попадают рядовые монстры недели.");
    out += band(12, 14, "ЧЦ 12–14: трудно и опасно",
      "Нужен ранг навыка и трата ресурсов. Основная масса противников.");
    out += band(15, 17, "ЧЦ 15–17: экстремально",
      "Без подготовки и знания слабости — самоубийство.");
    out += band(18, 30, "ЧЦ 18+: легендарно",
      "Архангелы, Всадники, первичные сущности. Победа не через бросок, а через сюжет.");

    host.innerHTML = out;
  }

  /* ---------- инициализация ---------- */
  render();
  tables();
  var appx = APPENDIX.slice().sort(CMP.name);
  renderGrid(document.getElementById("grid2"), appx, document.getElementById("empty2"));
  var q2 = document.getElementById("q2");
  var q2t;
  q2.addEventListener("input", function (e) {
    clearTimeout(q2t);
    var v = e.target.value.trim().toLowerCase();
    q2t = setTimeout(function () {
      renderGrid(document.getElementById("grid2"), appx.filter(function (d) {
        return !v || v.split(/\s+/).every(function (w) { return d._search.indexOf(w) > -1; });
      }), document.getElementById("empty2"));
    }, 130);
  });

  function download(name, text, mime) {
    var blob = new Blob([text], { type: (mime || "text/plain") + ";charset=utf-8" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url; a.download = name;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
  }
  document.getElementById("exp-json").addEventListener("click", function () {
    download("supernatural-bestiary-edge.json", JSON.stringify(DATA, null, 1), "application/json");
  });
  document.getElementById("exp-md").addEventListener("click", function () {
    var out = ["# Бестиарий «Сверхъестественного» — The Edge!", "",
               "Записей: " + DATA.length + ". Сборка: " + (BUILD.date || "") + ".", ""];
    DATA.forEach(function (d) {
      var a = d.attrs || {};
      out.push("## " + d.name_ru + " (" + d.name_en + ")");
      out.push("");
      out.push("**Угроза:** " + d.ugroza + " · **Раны** " + d.wounds +
               (d.stress == null ? "" : " · **Стресс** " + d.stress) +
               " · **ЧЦ защиты** " + d.defense);
      out.push("");
      out.push("**Тело " + a["Тело"] + ", Ловкость " + a["Ловкость"] + ", Разум " +
               a["Разум"] + ", Воля " + a["Воля"] + "**");
      out.push("");
      if (d.look) { out.push("*" + d.look + "*"); out.push(""); }
      out.push("**Оружие:** " + (d.weapon || []).map(function (w) {
        return w.name + " +" + w.bonus + " (" + w.dist + ")";
      }).join(", "));
      out.push("");
      if ((d.special || []).length) {
        out.push("**Особое:**"); out.push("");
        d.special.forEach(function (s) { out.push("- **" + s.name + ".** " + s.text); });
        out.push("");
      }
      if (d.weakness) { out.push("**Слабость.** " + d.weakness); out.push(""); }
      if ((d.learn || []).length) {
        out.push("**Как узнать:**"); out.push("");
        d.learn.forEach(function (c) {
          out.push("- **" + c.skill + "** (" + c.attr + "), ЧЦ " + c.cch + " — " + c.text);
        });
        out.push("");
      }
      if (d.notes) { out.push("> **Хранителю.** " + d.notes); out.push(""); }
      out.push("---"); out.push("");
    });
    download("bestiary-supernatural-edge.md", out.join("\n"), "text/markdown");
  });
  document.getElementById("prn").addEventListener("click", function () { window.print(); });

  var b = document.getElementById("build");
  if (b) {
    b.textContent = "Записей в базе: " + DATA.length +
      " (существ: " + SPECIES.length + ", приложение: " + APPENDIX.length + ")" +
      (BUILD.date ? " · сборка " + BUILD.date : "");
  }
  var sv = document.getElementById("sysver");
  if (sv) sv.textContent = "записей: " + DATA.length;

  var hash = (location.hash || "").replace("#", "");
  if (hash && DATA.some(function (x) { return x.slug === hash; })) open(hash);
  else if (hash) {
    var t = document.querySelector('button.tab[data-view="' + hash + '"]');
    if (t) t.click();
  }
  window.addEventListener("hashchange", function () {
    var h = (location.hash || "").replace("#", "");
    if (!h && !modal.hidden) close();
    else if (h && DATA.some(function (x) { return x.slug === h; }) && modal.hidden) open(h);
  });
})();
