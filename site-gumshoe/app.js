/* ============================================================
   Бестиарий GUMSHOE — логика приложения
   Данные из data.js: window.BESTIARY, window.BUILD
   ============================================================ */
(function () {
  "use strict";

  var DATA = (window.BESTIARY || []).slice();
  var BUILD = window.BUILD || {};

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
  var CAT_ICON = { "Монстр": "🐾", "Демон": "😈", "Ангел": "😇", "Божество": "⚡",
                   "Дух": "👻", "Ведьма": "🕯", "Левиафан": "🐍", "Иное": "🌀" };

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
  function initials(name) {
    return String(name || "?").replace(/[^\p{L}\p{N} ]/gu, "").split(/\s+/)
      .filter(Boolean).slice(0, 2)
      .map(function (w) { return w.charAt(0); }).join("").toUpperCase();
  }

  /* ---------- индексация ---------- */
  DATA.forEach(function (d) {
    d._threat = +d.threat || 1;
    d._stab = +((d.stability || {}).test || 0);
    d._wit = +((d.stability || {}).witnessed || 0);
    d._health = +((d.abilities || {})["Здоровье"] || 0);
    d._ht = +d.hit_threshold || 4;
    d._seasons = list(d.seasons).map(Number).filter(function (n) { return !isNaN(n); });
    d._first = d._seasons.length ? Math.min.apply(null, d._seasons) : 99;
    d._search = [
      d.name_ru, d.name_en, list(d.aka).join(" "), d.category,
      d.summary, d.horror, d.lore, d.rule, d.core_clue, d.notes,
      list(d.powers).join(" "), list(d.weaknesses).join(" "),
      (d._inv || []).join(" "),
      (d.special || []).map(function (x) { return x.name + " " + x.text; }).join(" "),
      (d.clues || []).map(function (x) { return x.ability + " " + x.text; }).join(" ")
    ].join(" ").toLowerCase();
  });

  var SPECIES = DATA.filter(function (d) { return d.kind === "creature" || d.kind === "being"; });
  var APPENDIX = DATA.filter(function (d) {
    return d.kind === "place" || d.kind === "artifact" || d.kind === "lore";
  });

  var state = { q: "", cat: "", threat: "", stab: "", kind: "", season: "", sort: "name" };

  /* ---------- заполнение фильтров ---------- */
  var cats = {}, threats = {}, seasons = {};
  SPECIES.forEach(function (d) {
    if (d.category) cats[d.category] = (cats[d.category] || 0) + 1;
    threats[d._threat] = (threats[d._threat] || 0) + 1;
    d._seasons.forEach(function (s) { seasons[s] = (seasons[s] || 0) + 1; });
  });

  function fill(el, items, fmt) {
    items.forEach(function (it) {
      var o = document.createElement("option");
      o.value = it[0];
      o.textContent = fmt ? fmt(it[0], it[1]) : it[0];
      el.appendChild(o);
    });
  }
  fill(document.getElementById("f-cat"),
    Object.keys(cats).sort().map(function (k) { return [k, cats[k]]; }),
    function (k, n) { return k + " (" + n + ")"; });
  fill(document.getElementById("f-threat"),
    [5, 4, 3, 2, 1].filter(function (t) { return threats[t]; })
      .map(function (t) { return [t, threats[t]]; }),
    function (t, n) { return t + "/5 — " + n + " шт."; });
  var stabVals = [];
  SPECIES.forEach(function (d) { if (stabVals.indexOf(d._stab) === -1) stabVals.push(d._stab); });
  stabVals.sort(function (a, b) { return b - a; });
  fill(document.getElementById("f-stab"), stabVals.map(function (v) { return [v]; }),
    function (v) { return v + " и выше"; });
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

  [["f-cat", "cat"], ["f-threat", "threat"], ["f-stab", "stab"],
   ["f-kind", "kind"], ["f-season", "season"], ["f-sort", "sort"]].forEach(function (p) {
    document.getElementById(p[0]).addEventListener("change", function (e) {
      state[p[1]] = e.target.value; render();
    });
  });

  document.getElementById("reset").addEventListener("click", function () {
    state = { q: "", cat: "", threat: "", stab: "", kind: "", season: "", sort: "name" };
    qEl.value = "";
    ["f-cat", "f-threat", "f-stab", "f-kind", "f-season"].forEach(function (id) {
      document.getElementById(id).value = "";
    });
    document.getElementById("f-sort").value = "name";
    render();
  });

  /* ---------- параметры в ссылке ---------- */
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
  [["f-cat", "cat"], ["f-threat", "threat"], ["f-stab", "stab"], ["f-kind", "kind"],
   ["f-season", "season"], ["f-sort", "sort"]].forEach(function (p) {
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
    if (state.stab !== "" && d._stab < +state.stab) return false;
    if (state.kind && d.kind !== state.kind) return false;
    if (state.season !== "" && d._seasons.indexOf(+state.season) === -1) return false;
    return true;
  }

  var CMP = {
    name: function (a, b) { return a.name_ru.localeCompare(b.name_ru, "ru"); },
    threat: function (a, b) { return b._threat - a._threat || a.name_ru.localeCompare(b.name_ru, "ru"); },
    stab: function (a, b) { return b._stab - a._stab || a.name_ru.localeCompare(b.name_ru, "ru"); },
    health: function (a, b) { return b._health - a._health || a.name_ru.localeCompare(b.name_ru, "ru"); }
  };

  /* ---------- карточки ---------- */
  function threatDots(n) {
    var s = '<span class="threat" title="Опасность в сериале: ' + n + '/5">';
    for (var i = 1; i <= 5; i++) s += '<i class="' + (i <= n ? "on" : "") + '"></i>';
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
    var col = catColor(d.category);
    var st = d._stab ? '<span class="badge stab">Ст −' + d._stab + "</span>" : "";
    return '<article class="card" data-slug="' + esc(d.slug) + '" style="--catcolor:' + col + '">' +
      thumb(d) + '<div class="card-body">' +
      "<h3>" + esc(d.name_ru) + "</h3>" +
      '<div class="en">' + esc(d.name_en) + "</div>" +
      '<p class="sum">' + esc(d.horror || d.summary || "") + "</p>" +
      '<div class="badges">' +
        '<span class="badge cat">' + esc(d.category || "—") + "</span>" +
        '<span class="badge ht">ПП ' + d._ht + "</span>" +
        '<span class="badge hp">Зд ' + d._health + "</span>" +
        st + threatDots(d._threat) +
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

  /* ---------- блок GUMSHOE ---------- */
  function listEntries(arr) {
    if (!arr || !arr.length) return "";
    return arr.map(function (e) {
      if (typeof e === "string") return '<p class="entry">' + esc(e) + "</p>";
      return '<p class="entry"><b>' + esc(e.name) + ".</b> " + esc(e.text) + "</p>";
    }).join("");
  }

  function gumshoeBlock(d) {
    var ab = d.abilities || {};
    var order = ["Атлетика", "Бой", "Стрельба", "Здоровье", "Стабильность",
                 "Бдительность", "Скрытность", "Вождение", "Подготовка", "Связи",
                 "Воля", "Вера"];
    var cells = order.filter(function (k) { return ab[k] != null; })
      .map(function (k) {
        return '<div class="pool"><b>' + ab[k] + "</b><span>" + esc(k) + "</span></div>";
      }).join("");
    var st = d.stability || {};
    var L = ['<div class="gs">'];
    L.push('<div class="gs-head"><h3>' + esc(d.name_ru) + "</h3>" +
      '<p class="sub">' + esc([d.category, "опасность " + d._threat + "/5"].join(" · ")) + "</p></div>");
    L.push('<div class="gs-crit">' +
      '<div class="crit"><b>' + d._ht + "</b><span>Порог попадания</span></div>" +
      '<div class="crit"><b>' + esc((d.abilities || {})["Здоровье"] || "—") + "</b><span>Здоровье</span></div>" +
      '<div class="crit"><b>−' + (st.test || 0) + "</b><span>Стабильность</span></div>" +
      '<div class="crit"><b>−' + (st.witnessed || 0) + "</b><span>при виде</span></div>" +
      "</div>");
    if (cells) L.push('<div class="gs-pools">' + cells + "</div>");
    L.push('<div class="gs-line"><b>Урон</b> ' + esc(d.damage || "—") + "</div>");
    if (dash(d.armor)) L.push('<div class="gs-line"><b>Броня</b> ' + esc(d.armor) + "</div>");
    L.push('<div class="gs-line"><b>Потеря Стабильности</b> проверка ' + (st.test || 0) +
      ", при виде чудовищного " + (st.witnessed || 0) + "</div>");
    L.push("</div>");
    return L.join("");
  }

  function cluesBlock(d) {
    var cl = d.clues || [];
    if (!cl.length) return "";
    return "<h4>Улики</h4>" + cl.map(function (c) {
      return '<p class="clue"><span class="ab">' + esc(c.ability) + "</span>" +
        (c.spend ? '<span class="spend">трата ' + c.spend + "</span>" : "") +
        esc(c.text) + "</p>";
    }).join("");
  }

  function detail(d) {
    var col = catColor(d.category);
    var meta = [];
    if (dash(d.category)) meta.push(["Категория", d.category]);
    if (dash(d.name_en)) meta.push(["Оригинал", d.name_en]);
    if (dash(d.first_appearance)) meta.push(["Первое появление", d.first_appearance]);
    if (d._seasons && d._seasons.length) meta.push(["Сезоны", d._seasons.join(", ")]);
    meta.push(["Опасность в сериале", d._threat + " / 5"]);
    meta.push(["Порог попадания", String(d._ht)]);
    meta.push(["Роль", d.kind === "being" ? "высшая сущность" : "существо"]);

    var powers = list(d.powers), weak = list(d.weaknesses), notable = list(d.notable);

    return '<button class="close" data-close aria-label="Закрыть">✕</button>' +
      '<div class="sheet-head" style="border-color:' + col + '55">' +
        "<h2>" + esc(d.name_ru) + "</h2>" +
        '<div class="en">' + esc(d.name_en) + " · " + esc(d.category) + "</div>" +
        (list(d.aka).length ? '<div class="aka">Также известно как: ' +
          esc(list(d.aka).join("; ")) + "</div>" : "") +
      "</div>" +
      hero(d) +
      '<div class="sheet-grid">' +
      '<div class="lore">' +
        (dash(d.horror) ? "<h4>Ужас</h4><p><strong>" + esc(d.horror) + "</strong></p>" : "") +
        "<h4>Кто это</h4><p>" + esc(d.summary || "") + "</p>" +
        "<h4>Описание</h4>" + (d.lore || "").split(/\n\s*\n/).filter(Boolean)
          .map(function (p) { return "<p>" + esc(p) + "</p>"; }).join("") +
        (powers.length ? "<h4>Силы и способности</h4><ul>" + powers
          .map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ul>" : "") +
        (weak.length ? "<h4>Слабости</h4><ul>" + weak
          .map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ul>" : "") +
        (notable.length ? '<h4>Известные особи</h4><ul class="notable">' + notable
          .map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ul>" : "") +
      "</div>" +
      '<div class="col">' +
        "<h4>Карточка</h4>" +
        '<table class="meta-table">' + meta.map(function (m) {
          return "<tr><td>" + esc(m[0]) + "</td><td>" + esc(m[1]) + "</td></tr>";
        }).join("") + "</table>" +
        "<h4>Статблок GUMSHOE</h4>" + gumshoeBlock(d) +
        (d.core_clue ? '<h4>Ключевая улика</h4><p class="core">' + esc(d.core_clue) + "</p>" : "") +
        cluesBlock(d) +
        ((d.special || []).length ? "<h4>Особые способности</h4>" +
          listEntries(d.special) : "") +
        (dash(d.rule) ? "<h4>Правило</h4><p class=\"rule\">" + esc(d.rule) + "</p>" : "") +
        (dash(d.notes) ? "<h4>Заметки ведущему</h4><p class=\"dnd-notes\">" + esc(d.notes) + "</p>" : "") +
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
    if (history.replaceState) {
      history.replaceState(null, "", location.pathname + location.search);
    }
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

  /* ---------- вкладки ---------- */
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

    var byStab = SPECIES.slice().sort(CMP.stab);
    out += '<div class="tblwrap"><h3>Цена взгляда: потеря Стабильности</h3>' +
      '<table class="data"><thead><tr><th>Потеря</th><th>Существо</th><th>Порог</th>' +
      "<th>Здоровье</th><th>Категория</th></tr></thead><tbody>" +
      byStab.map(function (d) {
        return "<tr><td><strong>−" + d._stab + "</strong></td><td>" + esc(d.name_ru) +
          "</td><td>" + d._ht + "</td><td>" + d._health + "</td><td>" +
          esc(d.category) + "</td></tr>";
      }).join("") + "</tbody></table></div>";

    var byHealth = SPECIES.slice().sort(CMP.health);
    out += '<div class="tblwrap"><h3>Крепость: Здоровье и Порог попадания</h3>' +
      '<table class="data"><thead><tr><th>Здоровье</th><th>Существо</th><th>Порог</th>' +
      "<th>Урон</th><th>Стабильность</th></tr></thead><tbody>" +
      byHealth.map(function (d) {
        return "<tr><td><strong>" + d._health + "</strong></td><td>" + esc(d.name_ru) +
          "</td><td>" + d._ht + "</td><td>" + esc((d.damage || "").slice(0, 60)) +
          "</td><td>−" + d._stab + "</td></tr>";
      }).join("") + "</tbody></table></div>";

    var byCat = {};
    SPECIES.forEach(function (d) { (byCat[d.category] = byCat[d.category] || []).push(d); });
    out += '<div class="tblwrap"><h3>Состав бестиария</h3>' +
      '<table class="data"><thead><tr><th>Категория</th><th>Существ</th>' +
      "<th>Средняя потеря Стабильности</th><th>Среднее Здоровье</th>" +
      "<th>Диапазон Порога</th></tr></thead><tbody>" +
      Object.keys(byCat).sort(function (a, b) { return byCat[b].length - byCat[a].length; })
        .map(function (k) {
          var a = byCat[k];
          var avgS = a.reduce(function (s, d) { return s + d._stab; }, 0) / a.length;
          var avgH = a.reduce(function (s, d) { return s + d._health; }, 0) / a.length;
          var hts = a.map(function (d) { return d._ht; });
          return "<tr><td>" + esc(k) + "</td><td>" + a.length + "</td><td>" +
            avgS.toFixed(1) + "</td><td>" + avgH.toFixed(1) + "</td><td>" +
            Math.min.apply(null, hts) + "–" + Math.max.apply(null, hts) + "</td></tr>";
        }).join("") + "</tbody></table></div>";

    function band(lo, hi, title) {
      var arr = SPECIES.filter(function (d) { return d._stab >= lo && d._stab <= hi; }).sort(CMP.name);
      return '<div class="tblwrap"><h3>' + title + "</h3>" +
        '<table class="data"><thead><tr><th>Потеря</th><th>Существо</th>' +
        "<th>Чем берут</th></tr></thead><tbody>" +
        arr.map(function (d) {
          return "<tr><td>−" + d._stab + "</td><td>" + esc(d.name_ru) + "</td><td>" +
            esc((d.rule || "").split(". ")[0].slice(0, 150)) + "</td></tr>";
        }).join("") + "</tbody></table></div>";
    }
    out += band(0, 1, "Почти не бьёт по нервам: потеря Стабильности 0–1");
    out += band(2, 3, "Обычное дело: потеря 2–3");
    out += band(4, 5, "Тяжёлое дело: потеря 4–5");
    out += band(6, 8, "Ломает людей: потеря 6–8");

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

  /* ---------- экспорт ---------- */
  function download(name, text, mime) {
    var blob = new Blob([text], { type: (mime || "text/plain") + ";charset=utf-8" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url; a.download = name;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
  }
  document.getElementById("exp-json").addEventListener("click", function () {
    download("supernatural-bestiary-gumshoe.json", JSON.stringify(DATA, null, 1), "application/json");
  });
  document.getElementById("exp-md").addEventListener("click", function () {
    var out = ["# Бестиарий «Сверхъестественного» — GUMSHOE", "",
               "Записей: " + DATA.length + ". Сборка: " + (BUILD.date || "") + ".", ""];
    DATA.forEach(function (d) {
      var ab = d.abilities || {}, st = d.stability || {};
      out.push("## " + d.name_ru + " (" + d.name_en + ")");
      out.push("");
      if (d.horror) { out.push("*" + d.horror + "*"); out.push(""); }
      out.push("**Порог попадания** " + d._ht + " · **Здоровье** " + ab["Здоровье"] +
               " · **Потеря Стабильности** −" + st.test + " / −" + st.witnessed);
      out.push("");
      out.push("| Способность | Пул |");
      out.push("|---|---|");
      Object.keys(ab).forEach(function (k) { out.push("| " + k + " | " + ab[k] + " |"); });
      out.push("");
      out.push("**Урон.** " + (d.damage || "—"));
      out.push("");
      if ((d.special || []).length) {
        out.push("### Особые способности"); out.push("");
        d.special.forEach(function (s) { out.push("- **" + s.name + ".** " + s.text); });
        out.push("");
      }
      if (d.core_clue) { out.push("**Ключевая улика.** " + d.core_clue); out.push(""); }
      if ((d.clues || []).length) {
        out.push("### Улики"); out.push("");
        d.clues.forEach(function (c) {
          out.push("- **" + c.ability + (c.spend ? " (трата " + c.spend + ")" : "") + "** — " + c.text);
        });
        out.push("");
      }
      if (d.rule) { out.push("**Правило.** " + d.rule); out.push(""); }
      if (d.notes) { out.push("> **Ведущему.** " + d.notes); out.push(""); }
      out.push("---"); out.push("");
    });
    download("bestiary-supernatural-gumshoe.md", out.join("\n"), "text/markdown");
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
