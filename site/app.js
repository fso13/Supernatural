/* ============================================================
   Бестиарий «Сверхъестественного» — логика приложения
   Данные приходят из data.js (window.BESTIARY, window.BUILD)
   ============================================================ */
(function () {
  "use strict";

  var DATA = (window.BESTIARY || []).slice();
  var BUILD = window.BUILD || {};

  /* ---------- утилиты ---------- */
  var CAT_COLORS = {
    "Монстр":   "#c96a3f",
    "Демон":    "#b7222b",
    "Ангел":    "#6fa8dc",
    "Божество": "#c99a3f",
    "Дух":      "#7fb8a4",
    "Ведьма":   "#a274c9",
    "Левиафан": "#5f9e6e",
    "Иное":     "#8c8c99"
  };
  function catColor(c) { return CAT_COLORS[c] || "#8c8c99"; }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
  function crNum(cr) {
    if (cr == null) return 0;
    var s = String(cr).trim();
    if (s.indexOf("/") > -1) { var p = s.split("/"); return (+p[0]) / (+p[1]); }
    var n = parseFloat(s);
    return isNaN(n) ? 0 : n;
  }
  function crLabel(cr) { return "CR " + String(cr == null ? "—" : cr); }

  function list(v) { return Array.isArray(v) ? v.filter(Boolean) : (v ? [v] : []); }

  function dash(v) { return (v === undefined || v === null || v === "" || (Array.isArray(v) && !v.length)) ? "" : v; }

  /* ---------- индексация ---------- */
  DATA.forEach(function (d) {
    d._cr = crNum(d.dnd && d.dnd.cr);
    d._threat = +d.threat || 1;
    d._seasons = list(d.seasons).map(Number).filter(function (n) { return !isNaN(n); });
    d._first = d._seasons.length ? Math.min.apply(null, d._seasons) : 99;
    d._search = [
      d.name_ru, d.name_en, list(d.aka).join(" "), d.category,
      d.summary, (d.dnd && d.dnd.type) || "", list(d.powers).join(" "),
      list(d.weaknesses).join(" "), d.lore, list(d.notable).join(" ")
    ].join(" ").toLowerCase();
  });

  var SPECIES = DATA.filter(function (d) { return d.kind === "creature" || d.kind === "being"; });
  var APPENDIX = DATA.filter(function (d) { return d.kind === "place" || d.kind === "artifact" || d.kind === "lore"; });

  /* ---------- состояние ---------- */
  var state = { q: "", cat: "", threat: "", crmin: "", crmax: "", season: "", sort: "name" };

  /* ---------- параметры в ссылке ---------- */
  function readParams() {
    var p = new URLSearchParams(location.search);
    ["q", "cat", "threat", "crmin", "crmax", "season", "sort"].forEach(function (k) {
      if (p.has(k)) state[k] = p.get(k);
    });
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

  /* ---------- фильтры UI ---------- */
  var cats = {}, threats = {}, seasons = {};
  SPECIES.forEach(function (d) {
    if (d.category) cats[d.category] = (cats[d.category] || 0) + 1;
    threats[d._threat] = (threats[d._threat] || 0) + 1;
    d._seasons.forEach(function (s) { seasons[s] = (seasons[s] || 0) + 1; });
  });

  function fillSelect(el, items, fmt) {
    items.forEach(function (it) {
      var o = document.createElement("option");
      o.value = it[0]; o.textContent = fmt ? fmt(it[0], it[1]) : it[0];
      el.appendChild(o);
    });
  }
  fillSelect(document.getElementById("f-cat"),
    Object.keys(cats).sort().map(function (k) { return [k, cats[k]]; }),
    function (k, n) { return k + " (" + n + ")"; });
  fillSelect(document.getElementById("f-threat"),
    [5, 4, 3, 2, 1].filter(function (t) { return threats[t]; }).map(function (t) { return [t, threats[t]]; }),
    function (t, n) { return t + "/5 — " + n + " шт."; });
  var crs = ["0", "1/8", "1/4", "1/2", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
             "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23",
             "24", "25", "26", "27", "28", "29", "30"];
  fillSelect(document.getElementById("f-crmin"), crs.map(function (c) { return [c]; }));
  fillSelect(document.getElementById("f-crmax"), crs.map(function (c) { return [c]; }));
  fillSelect(document.getElementById("f-season"),
    Object.keys(seasons).map(Number).sort(function (a, b) { return a - b; })
      .map(function (s) { return [s, seasons[s]]; }),
    function (s, n) { return "Сезон " + s + " (" + n + ")"; });

  ["f-cat:cat", "f-threat:threat", "f-crmin:crmin", "f-crmax:crmax", "f-season:season", "f-sort:sort"]
    .forEach(function (pair) {
      var p = pair.split(":");
      document.getElementById(p[0]).addEventListener("change", function (e) {
        state[p[1]] = e.target.value; render();
      });
    });

  var qEl = document.getElementById("q");
  var qtimer;
  qEl.addEventListener("input", function (e) {
    clearTimeout(qtimer);
    var v = e.target.value;
    qtimer = setTimeout(function () { state.q = v.trim().toLowerCase(); render(); }, 130);
  });
  document.getElementById("reset").addEventListener("click", function () {
    state = { q: "", cat: "", threat: "", crmin: "", crmax: "", season: "", sort: "name" };
    qEl.value = "";
    ["f-cat", "f-threat", "f-crmin", "f-crmax", "f-season"].forEach(function (id) {
      document.getElementById(id).value = "";
    });
    document.getElementById("f-sort").value = "name";
    render();
  });

  /* значения из ссылки */
  readParams();
  qEl.value = state.q || "";
  [["f-cat", "cat"], ["f-threat", "threat"], ["f-crmin", "crmin"],
   ["f-crmax", "crmax"], ["f-season", "season"], ["f-sort", "sort"]].forEach(function (p) {
    var el = document.getElementById(p[0]);
    if (state[p[1]]) el.value = state[p[1]];
    state[p[1]] = el.value;
  });

  /* ---------- фильтрация ---------- */
  function match(d) {
    if (state.q) {
      var words = state.q.split(/\s+/);
      for (var i = 0; i < words.length; i++) {
        if (d._search.indexOf(words[i]) === -1) return false;
      }
    }
    if (state.cat && d.category !== state.cat) return false;
    if (state.threat && String(d._threat) !== String(state.threat)) return false;
    if (state.crmin !== "" && d._cr < crNum(state.crmin)) return false;
    if (state.crmax !== "" && d._cr > crNum(state.crmax)) return false;
    if (state.season !== "" && d._seasons.indexOf(+state.season) === -1) return false;
    return true;
  }

  var CMP = {
    name: function (a, b) { return a.name_ru.localeCompare(b.name_ru, "ru"); },
    threat: function (a, b) { return b._threat - a._threat || a.name_ru.localeCompare(b.name_ru, "ru"); },
    cr: function (a, b) { return b._cr - a._cr || a.name_ru.localeCompare(b.name_ru, "ru"); },
    seasons: function (a, b) { return a._first - b._first || a.name_ru.localeCompare(b.name_ru, "ru"); }
  };

  /* ---------- карточки ---------- */
  function threatDots(n) {
    var s = '<span class="threat" title="Опасность в сериале: ' + n + '/5">';
    for (var i = 1; i <= 5; i++) s += '<i class="' + (i <= n ? "on" : "") + '"></i>';
    return s + "</span>";
  }

  /* заглушка, когда на вики не нашлось изображения */
  var CAT_ICON = { "Монстр": "🐾", "Демон": "😈", "Ангел": "😇", "Божество": "⚡",
                   "Дух": "👻", "Ведьма": "🕯", "Левиафан": "🐍", "Иное": "🌀" };

  function initials(name) {
    return String(name || "?").replace(/[^\p{L}\p{N} ]/gu, "").split(/\s+/)
      .filter(Boolean).slice(0, 2)
      .map(function (w) { return w.charAt(0); }).join("").toUpperCase();
  }

  function placeholder(d, cls) {
    var col = catColor(d.category);
    var label = String(d.name_ru || "").replace(/\s*\([^)]*\)\s*/g, " ").trim() || "?";
    return '<div class="ph ' + (cls || "thumb") + '" style="--catcolor:' + col + '">' +
      '<span class="ph-icon">' + (CAT_ICON[d.category] || "✦") + "</span>" +
      '<span class="ph-name">' + esc(label) + "</span>" +
      (d.name_en ? '<span class="ph-en">' + esc(d.name_en) + "</span>" : "") +
      "</div>";
  }

  function thumb(d, cls) {
    var c = cls || "thumb";
    if (d.image) {
      return '<div class="' + c + '"><img loading="lazy" decoding="async" src="' +
        esc(d.image) + '" alt="' + esc(d.name_ru) + '" ' +
        "onerror=\"this.parentNode.classList.add('broken');this.remove()\"></div>";
    }
    return placeholder(d, c);
  }

  /* большая картинка в карточке существа */
  function hero(d) {
    if (d.image) {
      return '<figure class="hero"><img loading="eager" decoding="async" src="' +
        esc(d.image) + '" alt="' + esc(d.name_ru) + '" ' +
        "onerror=\"this.parentNode.classList.add('broken');this.remove()\">" +
        (d.image_file ? '<figcaption>' + esc(d.image_file) +
          " · изображение с Supernatural Wiki</figcaption>" : "") + "</figure>";
    }
    return placeholder(d, "hero ph-hero");
  }

  function card(d) {
    var col = catColor(d.category);
    var cr = d.dnd && d.dnd.cr;
    var hi = d._cr >= 15 ? " hi" : "";
    return '<article class="card" data-slug="' + esc(d.slug) + '" style="--catcolor:' + col + '">' +
      thumb(d) +
      '<div class="card-body">' +
      "<h3>" + esc(d.name_ru) + "</h3>" +
      '<div class="en">' + esc(d.name_en) + "</div>" +
      '<p class="sum">' + esc(d.summary || "") + "</p>" +
      '<div class="badges">' +
        '<span class="badge cat">' + esc(d.category || "—") + "</span>" +
        (cr !== undefined && cr !== "" ? '<span class="badge cr' + hi + '">' + esc(crLabel(cr)) + "</span>" : "") +
        (d.dnd && (d.dnd.type_short || d.dnd.type) ? '<span class="badge">' + esc(d.dnd.type_short || d.dnd.type) + "</span>" : "") +
        threatDots(d._threat) +
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
    if (typeof writeParams === "function") writeParams();
  }

  /* ---------- статблок ---------- */
  function entryList(arr, cls) {
    if (!arr || !arr.length) return "";
    return arr.map(function (e) {
      if (typeof e === "string") return '<p class="entry ' + (cls || "") + '">' + esc(e) + "</p>";
      return '<p class="entry ' + (cls || "") + '"><b>' + esc(e.name) + ".</b> " + esc(e.text) + "</p>";
    }).join("");
  }

  function abilRow(a) {
    var order = [["str", "Сил"], ["dex", "Лов"], ["con", "Тел"], ["int", "Инт"], ["wis", "Мдр"], ["cha", "Хар"]];
    var cells = order.map(function (p) {
      var v = a[p[0]];
      if (v === undefined || v === null || v === "") return "";
      v = +v;
      var mod = Math.floor((v - 10) / 2);
      return "<div><b>" + v + "</b><span>" + p[1] + " " + (mod >= 0 ? "+" : "") + mod + "</span></div>";
    }).join("");
    return '<div class="abil">' + cells + "</div>";
  }

  function statblock(d) {
    var s = d.dnd;
    if (!s) return "";
    function line(label, val) {
      if (!dash(val)) return "";
      return "<p><strong>" + label + "</strong> " + esc(val) + "</p>";
    }
    var secs = "";
    secs += line("Класс доспеха", s.ac);
    secs += line("Хиты", s.hp);
    secs += line("Скорость", s.speed);
    secs += '<div class="rule thin"></div>';
    secs += abilRow(s.abilities || {});
    secs += '<div class="rule thin"></div>';
    secs += line("Спасброски", s.saves);
    secs += line("Навыки", s.skills);
    secs += line("Уязвимость к урону", s.damage_vulnerabilities);
    secs += line("Сопротивление урону", s.damage_resistances);
    secs += line("Иммунитет к урону", s.damage_immunities);
    secs += line("Иммунитет к состояниям", s.condition_immunities);
    secs += line("Чувства", s.senses);
    secs += line("Языки", s.languages);
    secs += line("Бонус мастерства", s.pb != null && s.pb !== "" ? "+" + s.pb : "");
    var crLine = "";
    if (dash(s.cr)) {
      crLine = "<strong>Уровень опасности</strong> " + esc(s.cr) +
        (dash(s.xp) ? " (" + (+s.xp).toLocaleString("ru-RU") + " опыта)" : "");
    }
    secs += crLine ? "<p>" + crLine + "</p>" : "";

    function block(title, arr, cls) {
      if (!arr || !arr.length) return "";
      return '<div class="sec-title">' + title + "</div>" + entryList(arr, cls);
    }

    return '<div class="statblock">' +
      "<h3>" + esc(d.name_ru) + "</h3>" +
      '<p class="sub">' + esc([s.size, s.type, s.alignment].filter(Boolean).join(", ")) + "</p>" +
      '<div class="rule"></div>' + secs +
      block("Особенности", s.traits) +
      block("Действия", s.actions) +
      block("Бонусные действия", s.bonus_actions) +
      block("Реакции", s.reactions) +
      block("Легендарные действия", s.legendary_actions) +
      block("Действия в логове", s.lair_actions) +
      "</div>";
  }

  function detail(d) {
    var col = catColor(d.category);
    var s = d.dnd || {};
    var meta = [];
    if (dash(d.category)) meta.push(["Категория", d.category]);
    if (dash(d.name_en)) meta.push(["Оригинал", d.name_en]);
    if (dash(d.first_appearance)) meta.push(["Первое появление", d.first_appearance]);
    if (d._seasons.length) meta.push(["Сезоны", d._seasons.join(", ")]);
    meta.push(["Опасность в сериале", d._threat + " / 5"]);
    if (dash(s.type)) meta.push(["Тип в D&D", s.type]);
    if (dash(s.cr)) meta.push(["CR", s.cr + (dash(s.xp) ? " · " + (+s.xp).toLocaleString("ru-RU") + " опыта" : "")]);

    var html = '<button class="close" data-close aria-label="Закрыть">✕</button>' +
      '<div class="sheet-head" style="border-color:' + col + '55">' +
        "<h2>" + esc(d.name_ru) + "</h2>" +
        '<div class="en">' + esc(d.name_en) + (dash(s.type) ? " · " + esc(s.type) : "") + "</div>" +
        (list(d.aka).length ? '<div class="aka">Также известно как: ' + esc(list(d.aka).join("; ")) + "</div>" : "") +
      "</div>" +
      hero(d) +
      '<div class="sheet-grid">' +
      '<div class="lore">' +
        "<h4>Кто это</h4><p>" + esc(d.summary || "") + "</p>" +
        "<h4>Описание</h4>" + (d.lore || "").split(/\n\s*\n/).filter(Boolean)
            .map(function (p) { return "<p>" + esc(p) + "</p>"; }).join("") +
        (list(d.powers).length ? "<h4>Силы и способности</h4><ul>" + list(d.powers)
            .map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ul>" : "") +
        (list(d.weaknesses).length ? "<h4>Слабости</h4><ul>" + list(d.weaknesses)
            .map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ul>" : "") +
        (dash(d.hunting) ? "<h4>Как его убить</h4><p>" + esc(d.hunting) + "</p>" : "") +
        (list(d.notable).length ? '<h4>Известные особи</h4><ul class="notable">' + list(d.notable)
            .map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ul>" : "") +
      "</div>" +
      '<div class="col">' +
        "<h4>Карточка</h4>" +
        '<table class="meta-table">' + meta.map(function (m) {
          return "<tr><td>" + esc(m[0]) + "</td><td>" + esc(m[1]) + "</td></tr>";
        }).join("") + "</table>" +
        '<h4>Статблок D&amp;D 5e</h4>' + statblock(d) +
        (dash(s.tactics) ? '<h4>Тактика</h4><p class="dnd-notes">' + esc(s.tactics) + "</p>" : "") +
        (dash(s.ecology) ? '<h4>Экология</h4><p class="dnd-notes">' + esc(s.ecology) + "</p>" : "") +
        (dash(d.dnd_notes) ? '<h4>Заметки мастеру</h4><p class="dnd-notes">' + esc(d.dnd_notes) + "</p>" : "") +
      "</div></div>";
    return html;
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
    var card = e.target.closest(".card");
    if (card) { open(card.getAttribute("data-slug")); return; }
    if (e.target.closest("[data-close]")) close();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !modal.hidden) close();
    if (e.key === "/" && document.activeElement !== qEl && modal.hidden) {
      e.preventDefault(); qEl.focus();
    }
  });

  /* ---------- вкладки ---------- */
  document.getElementById("tabs").addEventListener("click", function (e) {
    var b = e.target.closest(".tab");
    if (!b) return;
    var v = b.getAttribute("data-view");
    Array.prototype.forEach.call(document.querySelectorAll(".tab"), function (t) {
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

    // 1. по CR
    var byCr = SPECIES.slice().sort(CMP.cr);
    out += '<div class="tblwrap"><h3>Существа по уровню опасности (CR), от сильных к слабым</h3>' +
      '<table class="data"><thead><tr><th>CR</th><th>Название</th><th>Тип 5e</th><th>Категория</th>' +
      "<th>Хиты</th><th>Опасность в сериале</th></tr></thead><tbody>" +
      byCr.map(function (d) {
        var s = d.dnd || {};
        return "<tr><td><strong>" + esc(s.cr || "—") + "</strong></td><td>" + esc(d.name_ru) +
          "</td><td>" + esc(s.type || "—") + "</td><td>" + esc(d.category || "—") +
          "</td><td>" + esc(s.hp || "—") + "</td><td>" + d._threat + "/5</td></tr>";
      }).join("") + "</tbody></table></div>";

    // 2. по категориям
    var byCat = {};
    SPECIES.forEach(function (d) { (byCat[d.category] = byCat[d.category] || []).push(d); });
    out += '<div class="tblwrap"><h3>Состав бестиария по категориям</h3>' +
      '<table class="data"><thead><tr><th>Категория</th><th>Существ</th><th>Доля</th>' +
      "<th>Диапазон CR</th><th>Средний CR</th></tr></thead><tbody>" +
      Object.keys(byCat).sort(function (a, b) { return byCat[b].length - byCat[a].length; })
        .map(function (k) {
          var arr = byCat[k];
          var crs2 = arr.map(function (d) { return d._cr; });
          var avg = crs2.reduce(function (a, b) { return a + b; }, 0) / crs2.length;
          var pc = Math.round(arr.length / SPECIES.length * 100);
          return "<tr><td>" + esc(k) + "</td><td>" + arr.length + "</td>" +
            '<td><span class="bar" style="width:' + Math.max(4, pc * 2.2) + 'px"></span> ' + pc + "%</td>" +
            "<td>" + Math.min.apply(null, crs2) + " – " + Math.max.apply(null, crs2) + "</td>" +
            "<td>" + avg.toFixed(1) + "</td></tr>";
        }).join("") + "</tbody></table></div>";

    // 3. по сезонам
    var bySeas = {};
    SPECIES.forEach(function (d) {
      d._seasons.forEach(function (s) { (bySeas[s] = bySeas[s] || []).push(d.name_ru); });
    });
    out += '<div class="tblwrap"><h3>Новые существа по сезонам</h3>' +
      '<table class="data"><thead><tr><th>Сезон</th><th>Существ</th><th>Примеры</th></tr></thead><tbody>' +
      Object.keys(bySeas).map(Number).sort(function (a, b) { return a - b; })
        .map(function (s) {
          var names = bySeas[s];
          return "<tr><td>Сезон " + s + "</td><td>" + names.length + "</td><td>" +
            esc(names.slice(0, 8).join(", ")) + (names.length > 8 ? " …" : "") + "</td></tr>";
        }).join("") + "</tbody></table></div>";

    // 4. быстрые энкаунтеры
    function band(lo, hi, title) {
      var arr = SPECIES.filter(function (d) { return d._cr >= lo && d._cr <= hi; }).sort(CMP.cr);
      return '<div class="tblwrap"><h3>' + title + "</h3>" +
        '<table class="data"><thead><tr><th>CR</th><th>Существо</th><th>Роль в бою</th></tr></thead><tbody>' +
        arr.map(function (d) {
          var s = d.dnd || {};
          return "<tr><td>" + esc(s.cr) + "</td><td>" + esc(d.name_ru) + "</td><td>" +
            esc((s.tactics || "").split(". ")[0].slice(0, 150)) + "</td></tr>";
        }).join("") + "</tbody></table></div>";
    }
    out += band(0, 4, "Уровни 1–4: рядовые монстры недели");
    out += band(5, 10, "Уровни 5–10: серьёзные противники");
    out += band(11, 16, "Уровни 11–16: хозяева сюжета");
    out += band(17, 40, "Уровни 17+: угрозы мирового масштаба");

    host.innerHTML = out;
  }

  /* ---------- инициализация ---------- */
  render();
  tables();
  var appxSort = APPENDIX.slice().sort(CMP.name);
  renderGrid(document.getElementById("grid2"), appxSort, document.getElementById("empty2"));

  var q2 = document.getElementById("q2");
  var q2t;
  q2.addEventListener("input", function (e) {
    clearTimeout(q2t);
    var v = e.target.value.trim().toLowerCase();
    q2t = setTimeout(function () {
      var arr = appxSort.filter(function (d) {
        return !v || v.split(/\s+/).every(function (w) { return d._search.indexOf(w) > -1; });
      });
      renderGrid(document.getElementById("grid2"), arr, document.getElementById("empty2"));
    }, 130);
  });

  /* ---------- экспорт ---------- */
  function download(name, text, mime) {
    var blob = new Blob([text], { type: (mime || "text/plain") + ";charset=utf-8" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url; a.download = name;
    document.body.appendChild(a); a.click();
    document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
  }

  document.getElementById("exp-json").addEventListener("click", function () {
    download("supernatural-bestiary-dnd5e.json", JSON.stringify(DATA, null, 1), "application/json");
  });

  document.getElementById("exp-md").addEventListener("click", function () {
    var out = ["# Бестиарий «Сверхъестественного» — D&D 5e", "",
               "Записей: " + DATA.length + ". Сборка: " + (BUILD.date || "") + ".", ""];
    DATA.forEach(function (d) {
      var s = d.dnd || {};
      out.push("## " + d.name_ru + " (" + d.name_en + ")");
      out.push("");
      out.push("**" + d.category + "** · CR " + (s.cr || "—") + " · опасность " + d._threat + "/5");
      out.push("");
      out.push(d.summary || "");
      out.push("");
      out.push(d.lore || "");
      out.push("");
      if (list(d.powers).length) {
        out.push("**Силы и способности**"); out.push("");
        list(d.powers).forEach(function (p) { out.push("- " + p); });
        out.push("");
      }
      if (list(d.weaknesses).length) {
        out.push("**Слабости**"); out.push("");
        list(d.weaknesses).forEach(function (p) { out.push("- " + p); });
        out.push("");
      }
      if (d.hunting) { out.push("**Как убить.** " + d.hunting); out.push(""); }
      out.push("### Статблок D&D 5e");
      out.push("");
      out.push("*" + [s.size, s.type, s.alignment].filter(Boolean).join(", ") + "*");
      out.push("");
      if (s.ac) out.push("- **Класс доспеха** " + s.ac);
      if (s.hp) out.push("- **Хиты** " + s.hp);
      if (s.speed) out.push("- **Скорость** " + s.speed);
      var a = s.abilities || {};
      out.push("");
      out.push("| СИЛ | ЛОВ | ТЕЛ | ИНТ | МДР | ХАР |");
      out.push("|---|---|---|---|---|---|");
      out.push("| " + ["str", "dex", "con", "int", "wis", "cha"].map(function (k) {
        return a[k] != null ? a[k] : "—";
      }).join(" | ") + " |");
      out.push("");
      [["Спасброски", "saves"], ["Навыки", "skills"],
       ["Сопротивление урону", "damage_resistances"],
       ["Иммунитет к урону", "damage_immunities"],
       ["Иммунитет к состояниям", "condition_immunities"],
       ["Чувства", "senses"], ["Языки", "languages"]].forEach(function (p) {
        if (s[p[1]]) out.push("- **" + p[0] + "** " + s[p[1]]);
      });
      if (s.cr) out.push("- **Уровень опасности** " + s.cr + (s.xp ? " (" + s.xp + " опыта)" : ""));
      out.push("");
      [["Особенности", "traits"], ["Действия", "actions"],
       ["Бонусные действия", "bonus_actions"], ["Реакции", "reactions"],
       ["Легендарные действия", "legendary_actions"],
       ["Действия в логове", "lair_actions"]].forEach(function (p) {
        var arr = s[p[1]] || [];
        if (!arr.length) return;
        out.push("***" + p[0] + "***"); out.push("");
        arr.forEach(function (e) {
          out.push(typeof e === "string" ? "- " + e : "- ***" + e.name + ".*** " + e.text);
        });
        out.push("");
      });
      if (s.tactics) { out.push("**Тактика.** " + s.tactics); out.push(""); }
      if (d.dnd_notes) { out.push("> **Заметки мастеру.** " + d.dnd_notes); out.push(""); }
      out.push("---"); out.push("");
    });
    download("bestiary-supernatural-dnd5e.md", out.join("\n"), "text/markdown");
  });

  document.getElementById("prn").addEventListener("click", function () { window.print(); });

  var b = document.getElementById("build");
  if (b) {
    b.textContent = "Записей в базе: " + DATA.length +
      " (существ: " + SPECIES.length + ", приложение: " + APPENDIX.length + ")" +
      (BUILD.date ? " · сборка " + BUILD.date : "");
  }

  var hash = (location.hash || "").replace("#", "");
  if (hash && DATA.some(function (x) { return x.slug === hash; })) {
    open(hash);
  } else if (hash) {
    var t = document.querySelector('.tab[data-view="' + hash + '"]');
    if (t) t.click();
  }
  window.addEventListener("hashchange", function () {
    var h = (location.hash || "").replace("#", "");
    if (!h && !modal.hidden) close();
    else if (h && DATA.some(function (x) { return x.slug === h; }) && modal.hidden) open(h);
  });
})();
