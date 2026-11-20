(function () {
  "use strict";
  var root = document.body.dataset.root || "";
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };

  /* ---------- storage (safe) ---------- */
  var store = {
    get: function (k, d) { try { var v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set: function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  };
  var done = store.get("ei-done", {});
  function isDone(id) { return !!done[id]; }
  function toggle(id) { if (done[id]) delete done[id]; else done[id] = 1; store.set("ei-done", done); refresh(); }

  /* ---------- theme & menu ---------- */
  $("#themeBtn").addEventListener("click", function () {
    var d = document.documentElement.classList.toggle("dark");
    try { localStorage.setItem("theme", d ? "dark" : "light"); } catch (e) {}
  });
  $("#menuBtn").addEventListener("click", function () { $("#nav").classList.toggle("open"); });

  /* ---------- progress ---------- */
  function refresh() {
    $$("[data-id]").forEach(function (el) {
      var on = isDone(el.dataset.id);
      if (el.classList.contains("mark")) {
        el.classList.toggle("is", on);
        if (!el.dataset.label) el.dataset.label = el.textContent;
        el.textContent = on ? "✓ Done" : el.dataset.label;
      } else el.classList.toggle("done", on);
    });
    $$("[data-topic]").forEach(function (el) {
      var t = el.dataset.topic, total = +el.dataset.total, n = 0;
      for (var k in done) if (k.indexOf(t + "/") === 0) n++;
      if (el.classList.contains("prog-bar")) el.style.width = (100 * n / total) + "%";
      else el.textContent = n + " / " + total + " done";
    });
    applyBank && applyBank();
  }
  document.addEventListener("click", function (e) {
    var m = e.target.closest(".mark");
    if (m) { e.preventDefault(); toggle(m.dataset.id); return; }
    var t = e.target.closest(".tick");
    if (t) { e.preventDefault(); toggle(t.closest(".qa").dataset.id); }
  });

  /* ---------- topic filters ---------- */
  $$(".filters[data-target] .f").forEach(function (b) {
    b.addEventListener("click", function () {
      $$(".filters .f").forEach(function (x) { x.classList.remove("on"); });
      b.classList.add("on");
      var f = b.dataset.f;
      $$(".qa").forEach(function (q) {
        var show = f === "all" || q.dataset.d === f || (f === "todo" && !isDone(q.dataset.id));
        q.classList.toggle("hidden", !show);
      });
    });
  });
  var ex = $("#expandAll");
  if (ex) ex.addEventListener("click", function () {
    var open = ex.textContent === "Expand all";
    $$(".qa").forEach(function (q) { q.open = open; });
    ex.textContent = open ? "Collapse all" : "Expand all";
  });
  if (location.hash) { var h = document.getElementById(location.hash.slice(1)); if (h && h.tagName === "DETAILS") h.open = true; }

  /* ---------- bank / problem table filters ---------- */
  var applyBank = null;
  var bank = $("#bank");
  if (bank) {
    var qi = $("#bankQ"), ti = $("#bankT"), di = $("#bankD"), hd = $("#bankTodo");
    var params = new URLSearchParams(location.search);
    if (params.get("q")) qi.value = params.get("q");
    applyBank = function () {
      var q = qi.value.toLowerCase(), t = ti.value, d = di.value, n = 0, rows = $$("tbody tr", bank);
      rows.forEach(function (r) {
        var ok = (!q || r.textContent.toLowerCase().indexOf(q) >= 0) && (!t || r.dataset.t === t) &&
          (!d || r.dataset.d === d) && (!hd.checked || !isDone(r.dataset.id));
        r.classList.toggle("hidden", !ok); if (ok) n++;
      });
      var dn = rows.filter(function (r) { return isDone(r.dataset.id); }).length;
      $("#bankCount").textContent = n + " shown · " + dn + " / " + rows.length + " done";
    };
    [qi, ti, di, hd].forEach(function (el) { el.addEventListener("input", applyBank); el.addEventListener("change", applyBank); });
  }

  /* ---------- search ---------- */
  var pop = $("#searchPop"), inp = $("#searchInput"), res = $("#searchResults"), idx = null, sel = 0;
  function openSearch() {
    pop.hidden = false; inp.focus();
    if (!idx) fetch(root + "static/search.json").then(function (r) { return r.json(); }).then(function (d) { idx = d; run(); }).catch(function () {
      res.innerHTML = '<div class="empty">Search index could not be loaded.</div>';
    });
  }
  function closeSearch() { pop.hidden = true; }
  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function run() {
    if (!idx) return;
    var q = inp.value.trim().toLowerCase();
    if (!q) { res.innerHTML = '<div class="empty">Type to search ' + idx.length + ' questions, problems and articles. Try “volatile”, “I2C”, “spinlock”.</div>'; return; }
    var words = q.split(/\s+/), out = [];
    idx.forEach(function (it) {
      var t = it.t.toLowerCase(), x = it.x.toLowerCase(), s = 0;
      for (var i = 0; i < words.length; i++) {
        var w = words[i];
        if (t.indexOf(w) >= 0) s += 10; else if (x.indexOf(w) >= 0 || it.s.toLowerCase().indexOf(w) >= 0) s += 2; else { s = 0; break; }
      }
      if (s) out.push([s, it]);
    });
    out.sort(function (a, b) { return b[0] - a[0]; });
    sel = 0;
    res.innerHTML = out.length ? out.slice(0, 30).map(function (o, i) {
      return '<a href="' + root + o[1].u + '"' + (i === 0 ? ' class="sel"' : "") + ">" + esc(o[1].t) + "<small>" + esc(o[1].s) + "</small></a>";
    }).join("") : '<div class="empty">No results for “' + esc(q) + '”.</div>';
  }
  $("#searchBtn").addEventListener("click", openSearch);
  inp.addEventListener("input", run);
  pop.addEventListener("click", function (e) { if (e.target === pop) closeSearch(); });
  document.addEventListener("keydown", function (e) {
    if (e.key === "/" && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)) { e.preventDefault(); openSearch(); }
    if (pop.hidden) return;
    var links = $$("a", res);
    if (e.key === "Escape") closeSearch();
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault(); if (!links.length) return;
      links[sel] && links[sel].classList.remove("sel");
      sel = (sel + (e.key === "ArrowDown" ? 1 : links.length - 1)) % links.length;
      links[sel].classList.add("sel"); links[sel].scrollIntoView({ block: "nearest" });
    }
    if (e.key === "Enter" && links[sel]) location.href = links[sel].href;
  });

  /* ---------- problem editor ---------- */
  var code = $("#code");
  if (code) {
    var key = "ei-code:" + location.pathname;
    var saved = store.get(key, null);
    if (saved) code.value = saved;
    code.addEventListener("input", function () { store.set(key, code.value); });
    code.addEventListener("keydown", function (e) {
      if (e.key === "Tab") {
        e.preventDefault(); var s = code.selectionStart;
        code.value = code.value.slice(0, s) + "    " + code.value.slice(code.selectionEnd);
        code.selectionStart = code.selectionEnd = s + 4; store.set(key, code.value);
      }
    });
    $("#resetCode").addEventListener("click", function () { code.value = $("#starter").value; store.set(key, null); });
    $("#copyCode").addEventListener("click", function () {
      var b = this; (navigator.clipboard ? navigator.clipboard.writeText(code.value) : Promise.reject()).then(function () { b.textContent = "Copied"; setTimeout(function () { b.textContent = "Copy"; }, 1200); }, function () { code.select(); });
    });
  }
  $$("[data-godbolt]").forEach(function (b) {
    b.addEventListener("click", function () {
      var src = document.getElementById(b.dataset.godbolt).value;
      var state = { sessions: [{ id: 1, language: "c", source: src,
        compilers: [{ id: "cg132", options: "-O2 -Wall -Wextra -std=c11" }],
        executors: [{ compiler: { id: "cg132", libs: [], options: "-O2 -std=c11" } }] }] };
      var b64 = btoa(unescape(encodeURIComponent(JSON.stringify(state))));
      window.open("https://godbolt.org/clientstate/" + encodeURIComponent(b64), "_blank", "noopener");
    });
  });

  /* ---------- quiz ---------- */
  var qd = $("#quizData");
  if (qd) {
    var all = JSON.parse(qd.textContent), box = $("#quiz"), set = [], cur = 0, score = 0;
    var best = store.get("ei-quiz-best", null);
    function showBest() { $("#quizBest").textContent = best !== null ? "Best score: " + best + " / 10" : ""; }
    showBest();
    function shuffle(a) { for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; } return a; }
    function start() {
      var c = $("#quizCat").value;
      set = shuffle(all.filter(function (q) { return !c || q.cat === c; })).slice(0, 10); cur = 0; score = 0; render();
    }
    function render() {
      if (cur >= set.length) {
        var pct = Math.round(100 * score / set.length);
        if (set.length === 10 && (best === null || score > best)) { best = score; store.set("ei-quiz-best", best); showBest(); }
        box.innerHTML = '<div class="qcard score"><b>' + score + " / " + set.length + "</b><p>" + (pct >= 80 ? "Interview ready on this set. 🎯" : pct >= 50 ? "Good. Review the explanations you missed." : "Keep going. Read the topic pages, then retry.") + '</p><button class="btn" id="again">Try another set</button></div>';
        $("#again").onclick = start; return;
      }
      var q = set[cur];
      box.innerHTML = '<div class="qcard"><div class="qhead"><span>Question ' + (cur + 1) + " of " + set.length + "</span><span>" + esc(q.cat) + '</span></div><p class="qtext">' + esc(q.q).replace(/`([^`]+)`/g, "<code>$1</code>") + "</p>" +
        q.o.map(function (o, i) { return '<button class="opt" data-i="' + i + '">' + esc(o).replace(/`([^`]+)`/g, "<code>$1</code>") + "</button>"; }).join("") + '<div id="why"></div><div class="qfoot"></div></div>';
      $$(".opt", box).forEach(function (b) {
        b.onclick = function () {
          var i = +b.dataset.i;
          $$(".opt", box).forEach(function (x) { x.disabled = true; if (+x.dataset.i === q.a) x.classList.add("right"); });
          if (i === q.a) score++; else b.classList.add("wrong");
          $("#why").innerHTML = '<div class="why"><b>' + (i === q.a ? "Correct. " : "Not quite. ") + "</b>" + esc(q.e).replace(/`([^`]+)`/g, "<code>$1</code>") + "</div>";
          $(".qfoot", box).innerHTML = '<button class="btn" id="next">' + (cur + 1 < set.length ? "Next →" : "See score") + "</button>";
          $("#next").onclick = function () { cur++; render(); };
        };
      });
    }
    $("#quizStart").addEventListener("click", start);
    box.innerHTML = '<div class="qcard score"><p>Press <b>Start quiz</b> to get 10 random questions.</p></div>';
  }

  refresh();
})();
