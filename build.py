#!/usr/bin/env python3
"""Static site generator for EmbeddedInterview.com.

Usage:
    python3 build.py            # production build -> ./site  (pretty URLs)
    python3 build.py --preview  # links point at explicit index.html files

Content lives in ./content:
    questions/*.md   one file per topic, each "### Question {E|M|H}" starts a Q&A
    problems/*.md    one coding problem per file
    articles/*.md    one article per file
    quiz.json        multiple-choice questions
"""
import json, os, re, shutil, sys, html, datetime
import markdown
from pygments.formatters import HtmlFormatter

BASE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(BASE, "content")
OUT = os.path.join(BASE, "site")
SITE_URL = "https://embeddedinterview.com"
SITE_NAME = "EmbeddedInterview"
PREVIEW = "--preview" in sys.argv
TODAY = datetime.date.today().isoformat()
DIFF = {"E": "Easy", "M": "Medium", "H": "Hard"}


# ---------------------------------------------------------------- helpers
def slugify(text, maxlen=70):
    s = re.sub(r"<[^>]+>", "", text).lower()
    s = re.sub(r"[`'\"?.,:;()\[\]{}!]", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:maxlen].rstrip("-") or "item"


def md(text):
    return markdown.markdown(
        text,
        extensions=["fenced_code", "codehilite", "tables", "sane_lists"],
        extension_configs={"codehilite": {"guess_lang": False, "css_class": "hl"}},
    )


def plain(text, n=155):
    t = re.sub(r"```.*?```", " ", text, flags=re.S)
    t = re.sub(r"^\s*[-*+]\s+", " ", t, flags=re.M)      # list bullets
    t = re.sub(r"^\s*\|?\s*-{3,}.*$", " ", t, flags=re.M)  # table rules
    t = re.sub(r"[`*_#>|]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return (t[: n - 1] + "…") if len(t) > n else t


def front_matter(raw):
    meta = {}
    if raw.startswith("---"):
        _, fm, body = raw.split("---", 2)
        for line in fm.strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                v = v.strip()
                if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                    v = v[1:-1]                      # strip YAML quotes
                meta[k.strip()] = v
        return meta, body.strip()
    return meta, raw.strip()


def url(path):
    """path like 'topics/c/' -> link usable from root-relative prefix."""
    if PREVIEW and (path == "" or path.endswith("/")):
        return path + "index.html"
    return path


def write(path, content):
    if PREVIEW and path.endswith(".html"):
        content = re.sub(r'href="(?!https?:|mailto:|#)([^"]*/)(#[^"]*)?"', lambda m: f'href="{m.group(1)}index.html{m.group(2) or ""}"', content)
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


# ---------------------------------------------------------------- layout
NAV = [("Topics", "topics/"), ("Questions", "questions/"), ("Practice", "problems/"),
       ("Quiz", "quiz/"), ("Articles", "articles/"), ("Companies", "companies/"), ("Forum", "forum/"), ("Roadmap", "roadmap/")]


AUTHOR = {"@type": "Person", "name": "Brijesh Pratap Singh", "url": "https://embeddedinterview.com/about/",
          "jobTitle": "Senior Embedded Software Engineer",
          "sameAs": ["https://www.linkedin.com/in/brijesh9/"]}


def page(path, title, body, desc="", active="", schema=None):
    depth = path.count("/")
    root = "../" * depth
    nav = "".join(
        f'<a href="{root}{url(h)}" class="{"on" if active == h else ""}">{n}</a>' for n, h in NAV)
    canon = SITE_URL + "/" + (path[: -len("index.html")] if path.endswith("index.html") else path)
    full_title = f"{title} | {SITE_NAME}" if title != SITE_NAME else "Embedded Interview Questions and Answers: Embedded C, RTOS, Linux Drivers | EmbeddedInterview"
    ld = f'<script type="application/ld+json">{json.dumps(schema)}</script>' if schema else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(full_title)}</title>
<meta name="description" content="{html.escape(desc or 'Embedded systems interview questions, coding practice and articles: C, Embedded C, RTOS, Linux device drivers, ARM, I2C, SPI, UART, CAN.')}">
<link rel="canonical" href="{canon}">
<meta property="og:title" content="{html.escape(full_title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{SITE_URL}/static/og.png">
<meta property="og:site_name" content="{SITE_NAME}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/static/favicon-96.png" type="image/png" sizes="96x96">
<link rel="icon" href="/static/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/static/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{root}static/style.css">
<link rel="stylesheet" href="{root}static/code.css">
<script>try{{if(localStorage.getItem('theme')==='dark')document.documentElement.classList.add('dark')}}catch(e){{}}</script>
{ld}
</head>
<body data-root="{root}" data-preview="{1 if PREVIEW else 0}">
<header class="top">
  <div class="wrap bar">
    <a class="brand" href="{root}{url('')}"><span class="chip">&lt;/&gt;</span>Embedded<b>Interview</b></a>
    <nav class="nav" id="nav">{nav}</nav>
    <div class="tools">
      <button class="icon" id="searchBtn" aria-label="Search" title="Search (press /)"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg></button>
      <button class="icon" id="themeBtn" aria-label="Toggle dark mode" title="Dark mode"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg></button>
      <button class="icon menu" id="menuBtn" aria-label="Menu"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 6h16M4 12h16M4 18h16"/></svg></button>
    </div>
  </div>
</header>
<div class="search-pop" id="searchPop" hidden>
  <div class="search-box">
    <input id="searchInput" type="search" placeholder="Search questions, problems, articles…" autocomplete="off">
    <div id="searchResults" class="search-results"></div>
  </div>
</div>
<main>
{body}
</main>
<footer class="foot">
  <div class="wrap cols">
    <div><a class="brand" href="{root}{url('')}"><span class="chip">&lt;/&gt;</span>Embedded<b>Interview</b></a>
      <p class="muted">Free interview preparation for embedded software, firmware and Linux kernel engineers.</p></div>
    <div><h4>Learn</h4><a href="{root}{url('topics/')}">All topics</a><a href="{root}{url('questions/')}">Question bank</a><a href="{root}{url('roadmap/')}">Roadmap</a></div>
    <div><h4>Practice</h4><a href="{root}{url('problems/')}">Coding problems</a><a href="{root}{url('quiz/')}">MCQ quiz</a><a href="{root}{url('articles/')}">Articles</a><a href="{root}{url('companies/')}">Company guides</a><a href="{root}{url('forum/')}">Forum</a></div>
    <div><h4>Site</h4><a href="{root}{url('about/')}">About</a><a href="{root}{url('contact/')}">Contact</a><a href="{root}{url('privacy/')}">Privacy</a><a href="{root}{url('terms/')}">Terms</a></div>
  </div>
  <div class="wrap copy">© {datetime.date.today().year} EmbeddedInterview.com · Made for engineers who work close to the metal.</div>
</footer>
<script src="{root}static/app.js"></script>
<script data-goatcounter="https://embeddedinterview.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
</body>
</html>"""


def badge(d):
    return f'<span class="badge b{d}">{DIFF[d]}</span>'


# ---------------------------------------------------------------- load content
def load_topics():
    topics = []
    for fn in sorted(os.listdir(os.path.join(CONTENT, "questions"))):
        if not fn.endswith(".md"):
            continue
        raw = open(os.path.join(CONTENT, "questions", fn), encoding="utf-8").read()
        meta, body = front_matter(raw)
        parts = re.split(r"^### ", body, flags=re.M)
        intro = parts[0].strip()
        qs, seen = [], set()
        for p in parts[1:]:
            head, _, ans = p.partition("\n")
            m = re.search(r"\{([EMH])\}\s*$", head)
            d = m.group(1) if m else "M"
            q = re.sub(r"\s*\{[EMH]\}\s*$", "", head).strip()
            s = slugify(q)
            while s in seen:
                s += "-2"
            seen.add(s)
            qs.append({"q": q, "d": d, "slug": s, "md": ans.strip()})
        meta.update(slug=meta.get("slug", fn[:-3]), intro=intro, qs=qs, order=int(meta.get("order", 99)))
        topics.append(meta)
    topics.sort(key=lambda t: t["order"])
    return topics


def load_dir(sub):
    items = []
    for fn in sorted(os.listdir(os.path.join(CONTENT, sub))):
        if fn.endswith(".md"):
            meta, body = front_matter(open(os.path.join(CONTENT, sub, fn), encoding="utf-8").read())
            meta["slug"] = meta.get("slug", fn[:-3])
            meta["body"] = body
            items.append(meta)
    items.sort(key=lambda x: int(x.get("order", 999)))
    return items


TEST_MARK = "/* ---- tests ---- */"


def load_problems():
    raw = open(os.path.join(CONTENT, "problems.src"), encoding="utf-8").read()
    items = []
    for chunk in raw.split("@@@ ")[1:]:
        slug, _, rest = chunk.partition("\n")
        head, _, body = rest.partition("\n## ")
        meta = {}
        for line in head.strip().splitlines():
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
        meta["slug"] = slug.strip()
        meta["body"] = "## " + body.strip()
        items.append(meta)
    items.sort(key=lambda x: int(x.get("order", 999)))
    return items


def runnable_solution(starter, sol):
    """solution functions + the starter's test harness"""
    i = starter.find(TEST_MARK)
    return sol.rstrip() + "\n\n" + starter[i:] if i >= 0 else sol


# ---------------------------------------------------------------- builders
def inline(text):
    """inline markdown (for question titles)"""
    t = html.escape(text)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", t)


def build_topics(topics):
    total = sum(len(t["qs"]) for t in topics)
    # topics index
    cards = "".join(topic_card(t, "../") for t in topics)
    write("topics/index.html", page("topics/index.html", "All Topics", f"""
<section class="wrap pagehead"><h1>Topics</h1><p class="lead">{len(topics)} topics · {total} interview questions with detailed answers. Start at the top and work down, or jump to what your next interview needs.</p></section>
<section class="wrap grid cards">{cards}</section>""", "All embedded systems interview topics: C, pointers, Embedded C, RTOS, ARM Cortex-M, protocols, Linux drivers.", "topics/"))

    for t in topics:
        rows = []
        for i, q in enumerate(t["qs"], 1):
            qid = f"{t['slug']}/{q['slug']}"
            rows.append(f"""<details class="qa" id="{q['slug']}" data-id="{qid}" data-d="{q['d']}">
<summary><span class="num">{i:02d}</span><span class="qt">{inline(q['q'])}</span>{badge(q['d'])}<span class="tick" title="Mark as done">✓</span></summary>
<div class="ans">{md(q['md'])}<p class="permalink"><a href="{url(q['slug'] + '/')}">Open as page →</a> <button class="mark" data-id="{qid}">Mark as done</button></p></div>
</details>""")
        schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q["q"], "acceptedAnswer": {"@type": "Answer", "text": plain(q["md"], 600)}} for q in t["qs"]]}
        body = f"""
<section class="wrap pagehead"><div class="crumbs"><a href="../{url('')}">Topics</a> / {html.escape(t['title'])}</div>
<h1><span class="ticon">{t.get('icon','')}</span>{html.escape(t['title'])}</h1>
<div class="lead">{md(t['intro'])}</div>
<p class="byline">Written by <a href="../../{url('about/')}">Brijesh Pratap Singh</a>, senior embedded software engineer (Qualcomm, Intel, Boeing)</p>
<div class="meta"><span>{len(t['qs'])} questions</span><span>Level: {t.get('level','')}</span><span class="prog" data-topic="{t['slug']}" data-total="{len(t['qs'])}"></span></div>
<div class="filters" data-target=".qa"><button class="f on" data-f="all">All</button><button class="f" data-f="E">Easy</button><button class="f" data-f="M">Medium</button><button class="f" data-f="H">Hard</button><button class="f" data-f="todo">Not done</button><button class="ghost" id="expandAll">Expand all</button></div>
</section>
<section class="wrap qlist">{''.join(rows)}</section>"""
        write(f"topics/{t['slug']}/index.html", page(f"topics/{t['slug']}/index.html",
              f"{t['title']} Interview Questions", body, t.get("desc", ""), "topics/", schema))

        # single question pages
        for i, q in enumerate(t["qs"]):
            prev = t["qs"][i - 1] if i > 0 else None
            nxt = t["qs"][i + 1] if i + 1 < len(t["qs"]) else None
            qid = f"{t['slug']}/{q['slug']}"
            pn = '<div class="pn">' + (f'<a href="../{url(prev["slug"] + "/")}">← {inline(prev["q"])}</a>' if prev else "<span></span>") + \
                 (f'<a class="r" href="../{url(nxt["slug"] + "/")}">{inline(nxt["q"])} →</a>' if nxt else "<span></span>") + "</div>"
            schema = {"@context": "https://schema.org", "@type": "QAPage", "mainEntity": {
                "@type": "Question", "name": q["q"], "answerCount": 1,
                "acceptedAnswer": {"@type": "Answer", "text": plain(q["md"], 1000), "author": AUTHOR}}}
            body = f"""
<article class="wrap narrow single">
<div class="crumbs"><a href="../../{url('')}">Topics</a> / <a href="../{url('')}">{html.escape(t['title'])}</a> / Q{i+1}</div>
<h1>{inline(q['q'])}</h1>
<div class="meta">{badge(q['d'])}<span>{html.escape(t['title'])}</span><button class="mark" data-id="{qid}">Mark as done</button></div>
<div class="prose">{md(q['md'])}</div>
<p class="byline">Written by <a href="../../../{url('about/')}">Brijesh Pratap Singh</a>, senior embedded software engineer</p>
{pn}
</article>"""
            write(f"topics/{t['slug']}/{q['slug']}/index.html",
                  page(f"topics/{t['slug']}/{q['slug']}/index.html", q["q"], body, plain(q["md"]), "topics/", schema))


def topic_card(t, root):
    return f"""<a class="card" href="{root}{url('topics/' + t['slug'] + '/')}">
<div class="ticon">{t.get('icon','')}</div><h3>{html.escape(t['title'])}</h3><p>{html.escape(t.get('desc',''))}</p>
<div class="cardfoot"><span>{len(t['qs'])} questions</span><span class="lvl">{t.get('level','')}</span></div>
<div class="bar"><i class="prog-bar" data-topic="{t['slug']}" data-total="{len(t['qs'])}"></i></div></a>"""


def build_question_bank(topics):
    rows = []
    total = sum(len(t["qs"]) for t in topics)
    for t in topics:
        for q in t["qs"]:
            rows.append(f'<tr data-d="{q["d"]}" data-t="{t["slug"]}" data-id="{t["slug"]}/{q["slug"]}"><td class="st"></td>'
                        f'<td><a href="../{url("topics/" + t["slug"] + "/" + q["slug"] + "/")}">{inline(q["q"])}</a></td>'
                        f'<td class="tt">{html.escape(t["title"])}</td><td>{badge(q["d"])}</td></tr>')
    opts = "".join(f'<option value="{t["slug"]}">{html.escape(t["title"])}</option>' for t in topics)
    body = f"""
<section class="wrap pagehead"><h1>All Embedded Interview Questions</h1><p class="lead">All {total} embedded interview questions and answers on one page: Embedded C, pointers, bit manipulation, ARM Cortex-M, RTOS, I2C/SPI/UART/CAN and Linux device drivers. Filter by topic and difficulty and track what you have finished.</p>
<div class="filters bank"><input id="bankQ" type="search" placeholder="Filter questions…"><select id="bankT"><option value="">All topics</option>{opts}</select>
<select id="bankD"><option value="">All levels</option><option value="E">Easy</option><option value="M">Medium</option><option value="H">Hard</option></select>
<label class="chk"><input type="checkbox" id="bankTodo"> Hide done</label><span class="count" id="bankCount"></span></div></section>
<section class="wrap"><table class="tbl" id="bank"><thead><tr><th></th><th>Question</th><th>Topic</th><th>Level</th></tr></thead><tbody>{''.join(rows)}</tbody></table></section>"""
    write("questions/index.html", page("questions/index.html", f"{total} Embedded Interview Questions and Answers (Embedded C, RTOS, Linux)", body,
          f"All {total} embedded interview questions and answers in one list: Embedded C, pointers, bit manipulation, ARM Cortex-M, RTOS, I2C, SPI, UART, CAN and Linux device drivers. Filter by topic and difficulty.", "questions/"))


def section_body(body):
    """split '## Name' sections of a problem file"""
    secs = {}
    for part in re.split(r"^## ", body, flags=re.M)[1:]:
        name, _, txt = part.partition("\n")
        secs[name.strip().lower()] = txt.strip()
    return secs


def build_problems(problems):
    rows = []
    cats = sorted({p["category"] for p in problems})
    for i, p in enumerate(problems, 1):
        rows.append(f'<tr data-d="{p["difficulty"]}" data-t="{slugify(p["category"])}" data-id="p/{p["slug"]}"><td class="st"></td><td class="n">{i}</td>'
                    f'<td><a href="{url(p["slug"] + "/")}">{html.escape(p["title"])}</a></td><td class="tt">{html.escape(p["category"])}</td><td>{badge(p["difficulty"])}</td></tr>')
    opts = "".join(f'<option value="{slugify(c)}">{html.escape(c)}</option>' for c in cats)
    body = f"""
<section class="wrap pagehead"><h1>Coding Practice</h1><p class="lead">{len(problems)} hands-on embedded C problems: bit manipulation, registers, drivers, buffers, RTOS patterns and parsers. Write your code in the browser, press Run, and hidden tests tell you instantly whether it works. Each problem has a hint, a reference solution and an explanation.</p>
<div class="filters bank"><input id="bankQ" type="search" placeholder="Filter problems…"><select id="bankT"><option value="">All categories</option>{opts}</select>
<select id="bankD"><option value="">All levels</option><option value="E">Easy</option><option value="M">Medium</option><option value="H">Hard</option></select>
<label class="chk"><input type="checkbox" id="bankTodo"> Hide solved</label><span class="count" id="bankCount"></span></div></section>
<section class="wrap"><table class="tbl" id="bank"><thead><tr><th></th><th>#</th><th>Problem</th><th>Category</th><th>Level</th></tr></thead><tbody>{''.join(rows)}</tbody></table></section>"""
    write("problems/index.html", page("problems/index.html", "Embedded C Coding Problems", body,
          "Embedded C coding practice problems with hints and solutions: bit manipulation, ring buffers, drivers, RTOS.", "problems/"))

    for i, p in enumerate(problems):
        s = section_body(p["body"])
        starter = re.search(r"```c\n(.*?)```", s.get("starter code", ""), re.S)
        sol = re.search(r"```c\n(.*?)```", s.get("solution", ""), re.S)
        starter_code = starter.group(1) if starter else ""
        sol_code = sol.group(1) if sol else ""
        nxt = problems[i + 1] if i + 1 < len(problems) else None
        prv = problems[i - 1] if i > 0 else None
        pn = '<div class="pn">' + (f'<a href="../{url(prv["slug"] + "/")}">← {html.escape(prv["title"])}</a>' if prv else "<span></span>") + \
             (f'<a class="r" href="../{url(nxt["slug"] + "/")}">{html.escape(nxt["title"])} →</a>' if nxt else "<span></span>") + "</div>"
        # split starter into the part the user edits and the hidden test harness
        ti = starter_code.find(TEST_MARK)
        user_code = (starter_code[:ti] if ti >= 0 else starter_code).rstrip() + "\n"
        tests = starter_code[ti:] if ti >= 0 else ""
        sol_user = sol_code.rstrip() + "\n"
        body = f"""
<div class="ide">
<section class="ide-left">
<div class="crumbs"><a href="../{url('')}">← All problems</a> · {html.escape(p['category'])}</div>
<h1>{html.escape(p['title'])}</h1>
<div class="meta">{badge(p['difficulty'])}<button class="mark" data-id="p/{p['slug']}">Mark as solved</button></div>
<div class="tabs" role="tablist">
<button class="tab on" data-tab="t-problem">Problem</button><button class="tab" data-tab="t-hint">Hint</button><button class="tab" data-tab="t-sol">Solution</button><button class="tab" data-tab="t-exp">Explanation</button>
</div>
<div class="tabpane prose on" id="t-problem">{md(s.get('problem',''))}
<p class="howto">Write your code on the right and press <b>Run</b> (or Ctrl + Enter). Hidden tests check your functions and print the result below the editor.</p></div>
<div class="tabpane prose" id="t-hint">{md(s.get('hint','Think about the constraints first.'))}</div>
<div class="tabpane prose" id="t-sol">{md(s.get('solution',''))}<p><button class="btn" id="loadSol">Load solution into editor</button></p></div>
<div class="tabpane prose" id="t-exp">{md(s.get('explanation',''))}</div>
{pn}
</section>
<section class="ide-right">
<div class="edtop"><span class="file">solution.c</span>
<span class="sp"></span><button class="ghost sm" id="resetCode" title="Restore the starter code">Reset</button><button class="ghost sm" id="copyCode">Copy</button><button class="btn run" id="runCode">▶ Run</button></div>
<div class="edwrap"><pre class="gutter" id="gutter" aria-hidden="true">1</pre><textarea id="code" spellcheck="false" autocapitalize="off" autocomplete="off">{html.escape(user_code)}</textarea></div>
<div class="out" id="out"><div class="outhead"><span>Output</span><span class="muted" id="outStatus">Press Run to compile and test your code.</span></div><pre id="outText"></pre></div>
<details class="tests"><summary>Show the hidden tests</summary><pre>{html.escape(tests)}</pre></details>
<textarea id="starter" hidden>{html.escape(user_code)}</textarea><textarea id="tests" hidden>{html.escape(tests)}</textarea><textarea id="solsrc" hidden>{html.escape(sol_user)}</textarea>
</section>
</div>"""
        write(f"problems/{p['slug']}/index.html", page(f"problems/{p['slug']}/index.html", p["title"], body,
              plain(s.get("problem", "")), "problems/"))


def build_articles(articles):
    cards = "".join(f"""<a class="card art" href="{url(a['slug'] + '/')}"><span class="tag">{html.escape(a.get('tag',''))}</span><h3>{html.escape(a['title'])}</h3><p>{html.escape(a.get('desc',''))}</p><div class="cardfoot"><span>{reading_time(a['body'])} min read</span></div></a>""" for a in articles)
    write("articles/index.html", page("articles/index.html", "Articles", f"""
<section class="wrap pagehead"><h1>Articles</h1><p class="lead">Longer explanations of the ideas interviewers love to dig into.</p></section>
<section class="wrap grid cards">{cards}</section>""", "In-depth embedded systems articles: volatile, memory layout, Linux drivers, protocols, interrupts.", "articles/"))
    for a in articles:
        toc = "".join(f'<a href="#{slugify(h)}">{html.escape(h)}</a>' for h in re.findall(r"^## (.+)$", a["body"], re.M))
        body_html = md(a["body"])
        body_html = re.sub(r"<h2>(.*?)</h2>", lambda m: f'<h2 id="{slugify(m.group(1))}">{m.group(1)}</h2>', body_html)
        schema = {"@context": "https://schema.org", "@type": "Article", "headline": a["title"], "description": a.get("desc", ""),
                  "datePublished": a.get("date", TODAY), "author": AUTHOR}
        write(f"articles/{a['slug']}/index.html", page(f"articles/{a['slug']}/index.html", a["title"], f"""
<article class="wrap narrow single">
<div class="crumbs"><a href="../{url('')}">Articles</a> / {html.escape(a.get('tag',''))}</div>
<h1>{html.escape(a['title'])}</h1>
<div class="meta"><span>{reading_time(a['body'])} min read</span><span>{a.get('date','')}</span></div>
{f'<nav class="toc"><b>On this page</b>{toc}</nav>' if toc else ''}
<div class="prose">{body_html}</div>
</article>""", a.get("desc", ""), "articles/", schema))


def reading_time(t):
    return max(1, round(len(t.split()) / 200))


def build_quiz():
    data = json.load(open(os.path.join(CONTENT, "quiz.json"), encoding="utf-8"))
    cats = sorted({q["cat"] for q in data})
    opts = "".join(f'<option>{html.escape(c)}</option>' for c in cats)
    body = f"""
<section class="wrap narrow pagehead"><h1>MCQ Quiz</h1><p class="lead">{len(data)} multiple-choice questions. Pick a category, answer 10 random questions, and read the explanation after each one.</p>
<div class="filters bank"><select id="quizCat"><option value="">All categories</option>{opts}</select><button class="btn" id="quizStart">Start quiz</button><span class="count" id="quizBest"></span></div></section>
<section class="wrap narrow"><div id="quiz" class="quiz"></div></section>
<script id="quizData" type="application/json">{json.dumps(data)}</script>"""
    write("quiz/index.html", page("quiz/index.html", "Embedded Systems MCQ Quiz", body,
          "Embedded C, RTOS, protocols and Linux kernel multiple-choice quiz with explanations.", "quiz/"))
    return len(data)


def simple_page(path, title, mdtext, desc, active=""):
    write(path, page(path, title, f'<article class="wrap narrow single"><h1>{html.escape(title)}</h1><div class="prose">{md(mdtext)}</div></article>', desc, active))


def build_home(topics, problems, articles, nquiz):
    total = sum(len(t["qs"]) for t in topics)
    cards = "".join(topic_card(t, "") for t in topics)
    featured = [p for p in problems][:6]
    prob = "".join(f'<a class="row" href="{url("problems/" + p["slug"] + "/")}"><span>{html.escape(p["title"])}</span><span class="tt">{html.escape(p["category"])}</span>{badge(p["difficulty"])}</a>' for p in featured)
    arts = "".join(f'<a class="row" href="{url("articles/" + a["slug"] + "/")}"><span>{html.escape(a["title"])}</span><span class="tt">{html.escape(a.get("tag",""))}</span></a>' for a in articles[:6])
    body = f"""
<section class="wrap home-top"><div class="sechead"><h1>Embedded interview questions by topic</h1><a href="{url('topics/')}">All topics →</a></div><div class="grid cards">{cards}</div></section>
<section class="wrap two">
<div class="panel"><div class="sechead"><h2>Practice problems</h2><a href="{url('problems/')}">See all →</a></div>{prob}</div>
<div class="panel"><div class="sechead"><h2>Latest articles</h2><a href="{url('articles/')}">See all →</a></div>{arts}</div>
</section>
<section class="wrap"><div class="banner"><div><h2>Test yourself in 5 minutes</h2><p>10 random MCQs with explanations. Track your best score.</p></div><a class="btn big" href="{url('quiz/')}">Take the quiz</a></div></section>
<section class="wrap about-home"><h2>Embedded interview questions and answers</h2>
<p>EmbeddedInterview has {total} embedded interview questions with detailed answers, written the way you would answer in a real interview: the short answer first, then the detail, the common mistakes and the follow-up questions interviewers ask next. The questions cover what firmware, embedded software, BSP and Linux driver interviews actually test: <a href="{url('topics/c-programming/')}">C programming</a>, <a href="{url('topics/pointers-memory/')}">pointers and memory</a>, <a href="{url('topics/embedded-c/')}">Embedded C</a> (volatile, interrupts, linker scripts), <a href="{url('topics/bit-manipulation/')}">bit manipulation</a>, <a href="{url('topics/microcontrollers-arm/')}">ARM Cortex-M microcontrollers</a>, <a href="{url('topics/rtos/')}">RTOS</a>, <a href="{url('topics/communication-protocols/')}">I2C, SPI, UART and CAN</a>, and <a href="{url('topics/linux-device-drivers/')}">Linux kernel and device drivers</a>.</p>
<p>Use the <a href="{url('questions/')}">full list of embedded interview questions</a> to filter by topic and difficulty, practise the {len(problems)} <a href="{url('problems/')}">embedded C coding interview questions</a> with hidden tests, or follow the <a href="{url('roadmap/')}">preparation roadmap</a> from fresher to senior level.</p>
</section>
<section class="wrap how"><h2>How to use this site</h2><div class="grid three">
<div><b>1. Read</b><p>Work through a topic. Each answer is written the way you would say it in an interview: the short version first, then the detail.</p></div>
<div><b>2. Code</b><p>Solve the practice problems in the built-in editor. Press Run and hidden tests check your code instantly; then compare with the reference solution.</p></div>
<div><b>3. Track</b><p>Mark questions done. Your progress is saved in your browser, so you can see what is left before the interview.</p></div></div></section>"""
    schema = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebSite", "name": SITE_NAME, "alternateName": "Embedded Interview", "url": SITE_URL,
         "potentialAction": {"@type": "SearchAction", "target": SITE_URL + "/questions/?q={q}", "query-input": "required name=q"}},
        {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL, "logo": SITE_URL + "/static/og.png", "founder": AUTHOR}]}
    write("index.html", page("index.html", SITE_NAME, body, f"{total} embedded interview questions and answers with detailed explanations: Embedded C, RTOS, ARM Cortex-M, I2C, SPI, UART, CAN, Linux device drivers, plus coding practice and quizzes.", "", schema))


def build_search(topics, problems, articles, companies=()):
    idx = []
    for c in companies:
        idx.append({"t": f"{c['title']} embedded interview guide", "s": "Company guide", "u": url(f"companies/{c['slug']}/"), "x": c.get("desc", "")})
    for t in topics:
        for q in t["qs"]:
            idx.append({"t": q["q"], "s": t["title"], "u": url(f"topics/{t['slug']}/{q['slug']}/"), "x": plain(q["md"], 300)})
    for p in problems:
        idx.append({"t": p["title"], "s": "Practice · " + p["category"], "u": url(f"problems/{p['slug']}/"), "x": plain(p["body"], 300)})
    for a in articles:
        idx.append({"t": a["title"], "s": "Article", "u": url(f"articles/{a['slug']}/"), "x": a.get("desc", "")})
    write("static/search.json", json.dumps(idx, separators=(",", ":")))


def build_sitemap():
    urls = []
    for dp, _, files in os.walk(OUT):
        for f in files:
            if f == "index.html":
                rel = os.path.relpath(os.path.join(dp, f), OUT).replace("\\", "/")
                rel = rel[: -len("index.html")]
                urls.append(f"<url><loc>{SITE_URL}/{rel}</loc><lastmod>{TODAY}</lastmod></url>")
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(sorted(urls)) + "\n</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    write("CNAME", "embeddedinterview.com\n")
    shutil.copy(os.path.join(BASE, "static", "favicon.ico"), os.path.join(OUT, "favicon.ico"))
    write(".nojekyll", "")
    return len(urls)


# ---------------------------------------------------------------- forum (GitHub Discussions)
GH_REPO = "Brijeshpratap716/embeddedinterview"
GH_DISC = f"https://github.com/{GH_REPO}/discussions"
FORM_FIELDS = ["Company", "Role", "Location", "Experience level", "Outcome", "Difficulty"]
OUTCOME_CLS = {"Offer": "ok", "Rejected": "no", "Pending": "wait", "Withdrew": "wait"}


def parse_form(body):
    """GitHub discussion forms render as '### Label\n\nvalue' blocks."""
    fields = {}
    for m in re.finditer(r"^### (.+?)\s*\n+(.*?)(?=^### |\Z)", body or "", re.S | re.M):
        v = m.group(2).strip()
        if v and v != "_No response_":
            fields[m.group(1).strip()] = v
    return fields


def avatar(a):
    a = a or {"login": "ghost", "avatarUrl": "", "url": "https://github.com/ghost"}
    img = f'<img src="{html.escape(a["avatarUrl"])}&s=48" alt="" width="24" height="24" loading="lazy">' if a.get("avatarUrl") else ""
    return f'<a class="who" href="{html.escape(a["url"])}" rel="nofollow ugc">{img}{html.escape(a["login"])}</a>'


def when(iso):
    return f'<time data-t="{html.escape(iso)}" datetime="{html.escape(iso)}">{iso[:10]}</time>'


def build_forum():
    path = os.path.join(CONTENT, "forum.json")
    data = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {"discussions": [], "categories": []}
    posts = data.get("discussions", [])
    new_btns = (f'<a class="btn" href="{GH_DISC}/new?category=interview-experience">+ Share interview experience</a>'
                f'<a class="btn ghost" href="{GH_DISC}/new?category=q-a">Ask a question</a>'
                f'<a class="btn ghost" href="{GH_DISC}/new?category=general">Start a discussion</a>')
    rows, companies = [], set()
    for d in posts:
        f = parse_form(d.get("body", ""))
        comp = f.get("Company", "")
        if comp:
            companies.add(comp)
        slug = f'{d["number"]}-{slugify(d["title"], 60)}'
        d["_slug"], d["_fields"] = slug, f
        preview = f.get("Rounds and questions") or re.sub(r"^### .*$", "", d.get("body", ""), flags=re.M)
        chips = ""
        if comp:
            chips += f'<span class="fchip co">{html.escape(comp)}</span>'
        if f.get("Role"):
            chips += f'<span class="fchip">{html.escape(f["Role"])}</span>'
        if f.get("Outcome"):
            chips += f'<span class="fchip fo-{OUTCOME_CLS.get(f["Outcome"], "wait")}">{html.escape(f["Outcome"])}</span>'
        if f.get("Difficulty") in ("Easy", "Medium", "Hard"):
            chips += badge(f["Difficulty"][0])
        ncom = d["comments"]["totalCount"] + sum(len(c["replies"]["nodes"]) for c in d["comments"]["nodes"])
        rows.append(f"""<a class="fpost" href="{url(slug + '/')}" data-cat="{html.escape(d['category']['slug'])}" data-co="{html.escape(comp)}" data-out="{html.escape(f.get('Outcome',''))}" data-votes="{d['upvoteCount']}" data-time="{html.escape(d['createdAt'])}">
<div class="votes"><b>{d['upvoteCount']}</b><span>votes</span></div>
<div class="fbody"><h3>{html.escape(d['title'])}</h3><div class="fchips">{chips}</div>
<p>{html.escape(plain(preview, 180))}</p>
<div class="fmeta"><span>{html.escape((d.get('author') or {}).get('login', 'ghost'))}</span>{when(d['createdAt'])}<span>💬 {ncom}</span><span class="cat">{html.escape(d['category']['name'])}</span></div></div></a>""")
        build_thread(d, f, ncom)

    curated = json.load(open(os.path.join(CONTENT, "curated.json"), encoding="utf-8")) if os.path.exists(os.path.join(CONTENT, "curated.json")) else []
    by_co = {}
    for c in curated:
        by_co.setdefault(c["company"], []).append(c)
    mixed = []
    while any(by_co.values()):
        for co in list(by_co):
            if by_co[co]:
                mixed.append(by_co[co].pop(0))
    curated = mixed
    for c in curated:
        companies.add(c["company"])
        chips = f'<span class="fchip co">{html.escape(c["company"])}</span><span class="fchip">{html.escape(c["role"])}</span>'
        if c.get("outcome"):
            chips += f'<span class="fchip fo-{OUTCOME_CLS.get(c["outcome"], "wait")}">{html.escape(c["outcome"])}</span>'
        if c.get("difficulty") in ("Easy", "Medium", "Hard"):
            chips += badge(c["difficulty"][0])
        place = f' · {html.escape(c["location"])}' if c.get("location") else ""
        when_txt = f'<span>{html.escape(c["when"])}</span>' if c.get("when") else ""
        title = f'{c["company"]} {c["role"]}{" (" + c["location"] + ")" if c.get("location") else ""}: interview experience'
        rows.append(f"""<a class="fpost curated" href="{url('c-' + c['id'] + '/')}" data-cat="interview-experience" data-co="{html.escape(c['company'])}" data-out="{html.escape(c.get('outcome',''))}" data-votes="0" data-time="0000">
<div class="votes src"><b>★</b><span>Curated</span></div>
<div class="fbody"><h3>{html.escape(title)}</h3><div class="fchips">{chips}</div>
<p>{html.escape(plain(c['summary'], 180))}</p>
<div class="fmeta"><span class="cur">Curated</span>{when_txt}<span class="cat">Interview Experience</span></div></div></a>""")
        build_curated(c, title)
    posts_total = len(posts) + len(curated)

    cats = [("all", "All")] + [(c["slug"], c["name"]) for c in data.get("categories", []) if c["slug"] != "polls"]
    if len(cats) == 1:
        cats += [("interview-experience", "Interview Experience"), ("q-a", "Q&A"), ("general", "General")]
    tabs = "".join(f'<button class="f{" on" if s == "all" else ""}" data-cat="{html.escape(s)}">{html.escape(n)}</button>' for s, n in cats)
    co_opts = "".join(f'<option>{html.escape(c)}</option>' for c in sorted(companies, key=str.lower))
    empty = f"""<div class="fempty"><h2>No posts yet. Be the first!</h2>
<p>Share how your last embedded interview went: the company, the rounds, the questions they asked, and what you would prepare differently. It helps everyone preparing for the same roles.</p>
<div class="cta">{new_btns}</div></div>"""
    body = f"""
<section class="wrap pagehead"><h1>Community Forum</h1>
<p class="lead">Real embedded interview experiences, questions and discussions from engineers preparing for firmware, embedded software and Linux driver roles. Sign in with your GitHub account to post, reply and upvote.</p>
<div class="cta fnew">{new_btns}</div>
<p class="fnote" style="margin:4px 0 0">Preparing for a specific company? Read the <a href="{url('../companies/')}">company interview guides</a>.</p>
<div class="filters ftabs">{tabs}</div>
<div class="filters bank"><input id="fq" type="search" placeholder="Search posts…"><select id="fco"><option value="">All companies</option>{co_opts}</select>
<select id="fout"><option value="">Any outcome</option><option>Offer</option><option>Rejected</option><option>Pending</option><option>Withdrew</option></select>
<select id="fsort"><option value="new">Newest</option><option value="top">Top voted</option></select><span class="count" id="fcount">{posts_total} discussions</span></div>
</section>
<section class="wrap"><div id="flist" class="flist">{''.join(rows) if rows else empty}</div>
<p class="fnote">Posts are hosted on <a href="{GH_DISC}">GitHub Discussions</a> and appear here a few minutes after posting. Please keep it respectful and don't share confidential or NDA-protected material.</p></section>"""
    write("forum/index.html", page("forum/index.html", "Embedded Interview Experiences & Community Forum", body,
          "Real embedded interview experiences and discussions: firmware, embedded C and Linux driver interviews at Qualcomm, NXP, Bosch, TI and more.", "forum/"))


def build_curated(c, title):
    meta = "".join(f'<div><dt>{k}</dt><dd>{html.escape(c[v])}</dd></div>' for k, v in
                   [("Company", "company"), ("Role", "role"), ("Location", "location"), ("When", "when"), ("Outcome", "outcome"), ("Difficulty", "difficulty")] if c.get(v))
    qs = "".join(f"<li>{inline(q)}</li>" for q in c.get("questions", []))
    guide = slugify(c["company"]) if c["company"] != "NXP" else "nxp"
    guide_link = f'<a href="../../companies/{url(guide + "/")}">{html.escape(c["company"])} interview guide</a>' if os.path.exists(os.path.join(CONTENT, "companies", guide + ".md")) else ""
    body = f"""
<article class="wrap narrow single thread">
<div class="crumbs"><a href="../{url('')}">Forum</a> / Interview Experience</div>
<h1>{html.escape(title)}</h1>
<div class="meta"><span class="fchip src-badge">Curated</span></div>
<dl class="finfo">{meta}</dl>
<div class="prose"><h3>What happened</h3><p>{inline(c['summary'])}</p>
{f'<h3>Questions reported</h3><ul>{qs}</ul>' if qs else ''}</div>
{f'<div class="tactions">See also: {guide_link}</div>' if guide_link else ''}
<div class="ccta"><div><b>Interviewed at {html.escape(c['company'])} recently?</b><p>Share your own experience and help the next candidate.</p></div><a class="btn ghost" href="{GH_DISC}/new?category=interview-experience">Share your experience</a></div>
<p class="srcline">Source: summarised from a candidate's public report on <a rel="nofollow noopener" href="{html.escape(c['url'])}">{html.escape(c['source'])}</a>.</p>
</article>"""
    write(f"forum/c-{c['id']}/index.html", page(f"forum/c-{c['id']}/index.html", title, body, plain(c["summary"], 155), "forum/"))


def build_thread(d, f, ncom):
    meta = "".join(f'<div><dt>{html.escape(k)}</dt><dd>{html.escape(f[k])}</dd></div>' for k in FORM_FIELDS if f.get(k))
    body_html = d.get("bodyHTML", "")
    if meta:  # drop the field blocks GitHub rendered, they are shown in the info box
        for k in FORM_FIELDS + ["Confirmation"]:
            body_html = re.sub(r"<h3[^>]*>\s*" + re.escape(html.escape(k, quote=False)) + r"\s*</h3>\s*(<p[^>]*>.*?</p>|<ul.*?</ul>)", "", body_html, flags=re.S)
    comments = []
    for c in d["comments"]["nodes"]:
        reps = "".join(f'<div class="reply"><div class="chead">{avatar(r.get("author"))}{when(r["createdAt"])}</div><div class="prose cbody">{r["bodyHTML"]}</div></div>' for r in c["replies"]["nodes"])
        ans = '<span class="fchip fo-ok">✓ Answer</span>' if c.get("isAnswer") else ""
        comments.append(f'<div class="comment"><div class="chead">{avatar(c.get("author"))}{when(c["createdAt"])}<span class="cv">▲ {c["upvoteCount"]}</span>{ans}</div><div class="prose cbody">{c["bodyHTML"]}</div>{reps}</div>')
    schema = {"@context": "https://schema.org", "@type": "DiscussionForumPosting", "headline": d["title"],
              "url": f'{SITE_URL}/forum/{d["_slug"]}/', "datePublished": d["createdAt"],
              "author": {"@type": "Person", "name": (d.get("author") or {}).get("login", "ghost")},
              "interactionStatistic": [{"@type": "InteractionCounter", "interactionType": "https://schema.org/CommentAction", "userInteractionCount": ncom},
                                       {"@type": "InteractionCounter", "interactionType": "https://schema.org/LikeAction", "userInteractionCount": d["upvoteCount"]}]}
    body = f"""
<article class="wrap narrow single thread">
<div class="crumbs"><a href="../{url('')}">Forum</a> / {html.escape(d['category']['name'])}</div>
<h1>{html.escape(d['title'])}</h1>
<div class="meta">{avatar(d.get('author'))}{when(d['createdAt'])}<span>▲ {d['upvoteCount']} votes</span><span>💬 {ncom} replies</span></div>
{f'<dl class="finfo">{meta}</dl>' if meta else ''}
<div class="prose">{body_html}</div>
<div class="tactions"><a class="btn" href="{html.escape(d['url'])}">Reply or upvote on GitHub ↗</a></div>
<h2 class="sec">{ncom} {'reply' if ncom == 1 else 'replies'}</h2>
{''.join(comments) or '<p class="muted">No replies yet. Be the first to answer.</p>'}
</article>"""
    desc = plain(f.get("Rounds and questions") or d.get("body", ""), 155)
    write(f"forum/{d['_slug']}/index.html", page(f"forum/{d['_slug']}/index.html", d["title"], body, desc, "forum/", schema))


# ---------------------------------------------------------------- company interview guides
RESEARCHED = "November 2026"


def build_companies():
    items = load_dir("companies")
    cards = []
    for c in items:
        focus = "".join(f'<span class="fchip">{html.escape(x.strip())}</span>' for x in c.get("focus", "").split(","))
        cards.append(f"""<a class="card" href="{url(c['slug'] + '/')}"><h3>{html.escape(c['title'])}</h3>
<p>{html.escape(c.get('roles',''))}</p><div class="fchips">{focus}</div>
<div class="cardfoot"><span>{html.escape(c.get('hubs',''))}</span></div></a>""")
        intro = f"""<p class="muted cnote2">Processes differ by team, level and country, so treat this as a typical picture, not a guarantee. Last updated: {RESEARCHED}.</p>"""
        srcs = [x.split("|", 1) for x in c.get("sources", "").split(" ; ") if "|" in x]
        nums = " ".join(f'<a rel="nofollow noopener" href="{html.escape(u)}">[{i}]</a>' for i, (_, u) in enumerate(srcs, 1))
        names = ", ".join(dict.fromkeys(n for n, _ in srcs))
        srcline = f'<p class="srcline">Sources: summarised from candidates\' public interview reports on {html.escape(names)} {nums}</p>' if srcs else ""
        meta = f"""<dl class="finfo"><div><dt>Roles</dt><dd>{html.escape(c.get('roles',''))}</dd></div><div><dt>Hiring hubs</dt><dd>{html.escape(c.get('hubs',''))}</dd></div><div><dt>Focus</dt><dd>{html.escape(c.get('focus',''))}</dd></div></dl>"""
        cta = f"""<div class="ccta"><div><b>Interviewed at {html.escape(c['title'])}?</b><p>Share your experience on the forum and help the next candidate.</p></div><a class="btn" href="{GH_DISC}/new?category=interview-experience">Share your experience</a></div>"""
        body_html = md(c["body"]).replace('<a href="http', '<a rel="nofollow noopener" href="http')
        schema = {"@context": "https://schema.org", "@type": "Article", "headline": f"{c['title']} Embedded Interview Guide",
                  "description": c.get("desc", ""), "dateModified": TODAY, "author": {"@type": "Organization", "name": SITE_NAME}}
        body = f"""
<article class="wrap narrow single">
<div class="crumbs"><a href="../{url('')}">Company guides</a> / {html.escape(c['title'])}</div>
<h1>{html.escape(c['title'])} Embedded Interview Guide</h1>
{meta}{intro}
<div class="prose">{body_html}</div>
{cta}
{srcline}
</article>"""
        write(f"companies/{c['slug']}/index.html", page(f"companies/{c['slug']}/index.html",
              f"{c['title']} Embedded Software Interview Questions & Process", body, c.get("desc", ""), "companies/", schema))
    body = f"""
<section class="wrap pagehead"><h1>Company Interview Guides</h1>
<p class="lead">How embedded, firmware and Linux driver interviews usually run at {len(items)} top semiconductor and tech companies: the rounds, the topics that come up most, example questions candidates reported, practice questions and how to prepare.</p></section>
<section class="wrap grid cards">{''.join(cards)}</section>
<section class="wrap"><div class="ccta"><div><b>Don't see your company?</b><p>Share your interview experience on the forum. Popular companies get their own guide.</p></div><a class="btn" href="{url('../forum/')}">Go to the forum</a></div></section>"""
    write("companies/index.html", page("companies/index.html", "Embedded Interview Guides by Company: Qualcomm, NVIDIA, Intel and more", body,
          "Embedded and firmware interview process and questions at Qualcomm, NVIDIA, Intel, Samsung, AMD, Arm, Apple, Microsoft, Boeing, NXP, TI and Bosch.", "companies/"))
    return items


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(os.path.join(BASE, "static"), os.path.join(OUT, "static"))
    with open(os.path.join(OUT, "static", "code.css"), "w") as f:
        f.write(HtmlFormatter(style="github-dark").get_style_defs(".hl"))
    topics = load_topics()
    problems = load_problems()
    articles = load_dir("articles")
    build_topics(topics)
    build_question_bank(topics)
    build_problems(problems)
    build_articles(articles)
    nquiz = build_quiz()
    build_home(topics, problems, articles, nquiz)
    build_forum()
    companies = build_companies()
    for name in ["roadmap", "about", "contact", "privacy", "terms"]:
        meta, body = front_matter(open(os.path.join(CONTENT, "pages", name + ".md"), encoding="utf-8").read())
        simple_page(f"{name}/index.html", meta.get("title", name.title()), body, meta.get("desc", ""), f"{name}/" if name == "roadmap" else "")
    write("404.html", page("404.html", "Page not found", '<section class="wrap narrow single"><h1>404: segmentation fault</h1><p class="lead">This address does not map to any page. <a href="/">Go home</a> or use search.</p></section>'))
    build_search(topics, problems, articles, companies)
    n = build_sitemap()
    print(f"Built {n} pages: {len(topics)} topics, {sum(len(t['qs']) for t in topics)} questions, "
          f"{len(problems)} problems, {len(articles)} articles, {nquiz} MCQs -> {OUT}")


if __name__ == "__main__":
    main()
