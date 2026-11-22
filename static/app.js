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
    var key = "ei-code2:" + location.pathname;
    var gutter = $("#gutter"), outText = $("#outText"), outStatus = $("#outStatus"), out = $("#out");
    var saved = store.get(key, null);
    if (saved) code.value = saved;

    function lines() {
      var n = code.value.split("\n").length, s = "";
      for (var i = 1; i <= n; i++) s += i + "\n";
      gutter.textContent = s;
    }
    function save() { store.set(key, code.value); lines(); }
    lines();
    code.addEventListener("input", save);
    code.addEventListener("scroll", function () { gutter.scrollTop = code.scrollTop; });
    code.addEventListener("keydown", function (e) {
      var s = code.selectionStart, v = code.value;
      if (e.key === "Tab") {
        e.preventDefault();
        code.value = v.slice(0, s) + "    " + v.slice(code.selectionEnd);
        code.selectionStart = code.selectionEnd = s + 4; save();
      } else if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault(); run();
      } else if (e.key === "Enter") {             /* keep the current line's indentation */
        var ls = v.lastIndexOf("\n", s - 1) + 1, ind = (v.slice(ls, s).match(/^[ \t]*/) || [""])[0];
        if (v.charAt(s - 1) === "{") ind += "    ";
        e.preventDefault();
        code.value = v.slice(0, s) + "\n" + ind + v.slice(code.selectionEnd);
        code.selectionStart = code.selectionEnd = s + 1 + ind.length; save();
      }
    });

    $("#resetCode").addEventListener("click", function () {
      if (!confirm("Replace your code with the starter code?")) return;
      code.value = $("#starter").value; store.set(key, null); lines();
    });
    $("#copyCode").addEventListener("click", function () {
      var b = this; (navigator.clipboard ? navigator.clipboard.writeText(code.value) : Promise.reject()).then(function () { b.textContent = "Copied"; setTimeout(function () { b.textContent = "Copy"; }, 1200); }, function () { code.select(); });
    });
    var ls = $("#loadSol");
    if (ls) ls.addEventListener("click", function () {
      if (!confirm("Replace your code with the reference solution?")) return;
      code.value = $("#solsrc").value; save(); run();
    });

    /* tabs */
    $$(".tab").forEach(function (t) {
      t.addEventListener("click", function () {
        $$(".tab").forEach(function (x) { x.classList.toggle("on", x === t); });
        $$(".tabpane").forEach(function (p) { p.classList.toggle("on", p.id === t.dataset.tab); });
      });
    });

    /* run: compile and execute through the Compiler Explorer API */
    function show(state, msg, text) {
      out.className = "out " + state; outStatus.textContent = msg; outText.textContent = text || "";
    }
    function texts(a) {
      /* strip ANSI colour codes (ESC[01m, ESC[K ...) that GCC adds to diagnostics */
      return (a || []).map(function (x) { return x.text; }).join("\n").replace(/\x1b?\[[0-9;]*[mK]/g, "");
    }
    var running = false;
    function run() {
      if (running) return;
      running = true;
      var src = code.value + "\n" + $("#tests").value;
      show("busy", "Compiling and running…", "");
      $("#runCode").disabled = true;
      fetch("https://godbolt.org/api/compiler/cg132/compile", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify({
          source: src, lang: "c", allowStoreCodeDebug: false,
          options: {
            userArguments: "-O1 -std=gnu11 -Wall -fdiagnostics-color=never",
            executeParameters: { args: [], stdin: "" },
            compilerOptions: { executorRequest: true },
            filters: { execute: true }, tools: [], libraries: []
          }
        })
      }).then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      }).then(function (r) {
        var b = r.buildResult || {};
        if (b.code && b.code !== 0) {
          show("bad", "Compile error", texts(b.stderr).replace(/<source>/g, "solution.c"));
          return;
        }
        var stdout = texts(r.stdout), stderr = texts(r.stderr);
        var txt = stdout + (stderr ? "\n" + stderr : "");
        var warn = texts(b.stderr);
        if (warn) txt += "\n\nCompiler warnings:\n" + warn.replace(/<source>/g, "solution.c");
        if (r.code === 0 && /All tests passed/.test(stdout)) {
          show("good", "✓ All tests passed", txt);
          var id = "p/" + location.pathname.replace(/\/$/, "").split("/").pop();
          if (!isDone(id)) toggle(id);
        } else if (r.timedOut || r.code === -1) {
          show("bad", "Timed out: check for an infinite loop", txt);
        } else {
          show("bad", "✗ Some tests failed (exit code " + r.code + ")", txt);
        }
      }).catch(function () {
        show("bad", "Could not reach the online compiler.", "Check your internet connection and try again.\nYou can also copy your code and run it with: gcc -Wall solution.c && ./a.out");
      }).then(function () { running = false; $("#runCode").disabled = false; });
    }
    $("#runCode").addEventListener("click", run);
  }

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
