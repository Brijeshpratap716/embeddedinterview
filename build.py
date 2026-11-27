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
import hashlib
# version tag for static files, so browsers fetch fresh copies after every change
ASSET_V = hashlib.sha1(b"".join(open(os.path.join(BASE, "static", f), "rb").read()
                                for f in ("app.js", "style.css"))).hexdigest()[:10]
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
NAV = [("Topics", "topics/"), ("Questions", "questions/"), ("Coding Practice", "problems/"),
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
    full_title = f"{title} | {SITE_NAME}" if title != SITE_NAME else "Embedded Systems Interview Questions & C/C++ Practice | EmbeddedInterview"
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
<link rel="stylesheet" href="{root}static/style.css?v={ASSET_V}">
<link rel="stylesheet" href="{root}static/code.css?v={ASSET_V}">
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
  <div class="wrap copy">© {datetime.date.today().year} EmbeddedInterview.com. All rights reserved.<p>Unauthorized reproduction, redistribution, commercial reuse, or bulk scraping of original website content and source code is prohibited, except as permitted by law.</p></div>
</footer>
<script src="{root}static/app.js?v={ASSET_V}"></script>
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


TOPIC_SEO = {
    "embedded-c": ("Embedded C Interview Questions and Answers", "Prepare for embedded C interviews with questions on volatile, interrupts, registers, memory-mapped I/O, startup code, linker scripts and firmware."),
    "c-programming": ("C Programming Interview Questions for Embedded Engineers", "Practice C programming interview questions on pointers, arrays, structures, memory, macros and bitwise operations for embedded software roles."),
    "linux-device-drivers": ("Linux Device Driver Interview Questions and Answers", "Prepare for Linux device driver interviews: kernel modules, character drivers, interrupts, DMA, device tree, synchronization and driver debugging."),
    "arm-architecture": ("ARM Architecture Interview Questions and Answers", "Prepare for ARM architecture interviews: registers, exception levels, MMU, TLB, caches, barriers, interrupts, boot and virtualization."),
    "microcontrollers-arm": ("ARM Cortex-M and Microcontroller Interview Questions", "Study ARM Cortex-M and microcontroller interview questions on reset, startup, NVIC, exceptions, GPIO, timers and DMA."),
    "rtos": ("RTOS Interview Questions and Answers", "Practice RTOS interview questions on real-time scheduling, tasks, semaphores, mutexes, priority inversion and inter-task communication."),
    "embedded-linux": ("Embedded Linux Interview Questions and Answers", "Prepare for embedded Linux and BSP interviews with bootloaders, kernel boot, device tree, root filesystems and board bring-up."),
    "virtualization": ("QEMU, KVM and Virtualization Interview Questions", "Prepare for virtualization interviews covering QEMU, KVM, hypervisors, virtual CPUs, memory virtualization and device emulation."),
}


def build_topics(topics):
    total = sum(len(t["qs"]) for t in topics)
    # topics index
    cards = "".join(topic_card(t, "../") for t in topics)
    write("topics/index.html", page("topics/index.html", "All Topics", f"""
<section class="wrap pagehead"><h1>Topics</h1><p class="lead">{len(topics)} topics · {total} interview questions with detailed answers. Start at the top and work down, or jump to what your next interview needs.</p></section>
<section class="wrap grid cards">{cards}</section>""", "All embedded systems interview topics: C, pointers, Embedded C, RTOS, ARM Cortex-M, protocols, Linux drivers.", "topics/"))

    for t in topics:
        seo_title, seo_desc = TOPIC_SEO.get(t["slug"], (f"{t['title']} Interview Questions and Answers", t.get("desc", "")))
        rows = []
        for i, q in enumerate(t["qs"], 1):
            qid = f"{t['slug']}/{q['slug']}"
            rows.append(f"""<details class="qa" id="{q['slug']}" data-id="{qid}" data-d="{q['d']}">
<summary><span class="num">{i:02d}</span><span class="qt">{inline(q['q'])}</span>{badge(q['d'])}<span class="tick" title="Mark as done">✓</span></summary>
<div class="ans">{md(q['md'])}<p class="permalink"><a href="{url(q['slug'] + '/')}">Open as page →</a> <button class="mark" data-id="{qid}">Mark as done</button></p></div>
</details>""")
        schema = {"@context": "https://schema.org", "@type": "CollectionPage", "name": seo_title,
                  "description": seo_desc, "url": SITE_URL + "/topics/" + t["slug"] + "/"}
        body = f"""
<section class="wrap pagehead"><div class="crumbs"><a href="../{url('')}">Topics</a> / {html.escape(t['title'])}</div>
<h1><span class="ticon" aria-hidden="true">{t.get('icon','')}</span>{html.escape(seo_title)}</h1>
<div class="lead">{md(t['intro'])}</div>
<p class="byline">Written by <a href="../../{url('about/')}">Brijesh Pratap Singh</a>, senior embedded software engineer (Qualcomm, Intel, Boeing)</p>
<div class="meta"><span>{len(t['qs'])} questions</span><span>Level: {t.get('level','')}</span><span class="prog" data-topic="{t['slug']}" data-total="{len(t['qs'])}"></span></div>
<div class="filters" data-target=".qa"><button class="f on" data-f="all">All</button><button class="f" data-f="E">Easy</button><button class="f" data-f="M">Medium</button><button class="f" data-f="H">Hard</button><button class="f" data-f="todo">Not done</button><button class="ghost" id="expandAll">Expand all</button></div>
</section>
<section class="wrap qlist">{''.join(rows)}</section>"""
        write(f"topics/{t['slug']}/index.html", page(f"topics/{t['slug']}/index.html",
              seo_title, body, seo_desc, "topics/", schema))

        # single question pages
        for i, q in enumerate(t["qs"]):
            prev = t["qs"][i - 1] if i > 0 else None
            nxt = t["qs"][i + 1] if i + 1 < len(t["qs"]) else None
            qid = f"{t['slug']}/{q['slug']}"
            pn = '<div class="pn">' + (f'<a href="../{url(prev["slug"] + "/")}">← {inline(prev["q"])}</a>' if prev else "<span></span>") + \
                 (f'<a class="r" href="../{url(nxt["slug"] + "/")}">{inline(nxt["q"])} →</a>' if nxt else "<span></span>") + "</div>"
            schema = {"@context": "https://schema.org", "@type": "Article", "headline": q["q"],
                      "description": plain(q["md"]), "author": AUTHOR,
                      "mainEntityOfPage": SITE_URL + "/topics/" + t["slug"] + "/" + q["slug"] + "/"}
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
<section class="wrap pagehead"><h1>Embedded Systems Interview Questions and Answers</h1><p class="lead">All {total} embedded interview questions and answers on one page: Embedded C, pointers, bit manipulation, ARM Cortex-M, RTOS, I2C/SPI/UART/CAN and Linux device drivers. Filter by topic and difficulty and track what you have finished.</p>
<div class="filters bank"><input id="bankQ" type="search" placeholder="Filter questions…"><select id="bankT"><option value="">All topics</option>{opts}</select>
<select id="bankD"><option value="">All levels</option><option value="E">Easy</option><option value="M">Medium</option><option value="H">Hard</option></select>
<label class="chk"><input type="checkbox" id="bankTodo"> Hide done</label><span class="count" id="bankCount"></span></div></section>
<section class="wrap"><table class="tbl" id="bank"><thead><tr><th></th><th>Question</th><th>Topic</th><th>Level</th></tr></thead><tbody>{''.join(rows)}</tbody></table></section>"""
    write("questions/index.html", page("questions/index.html", f"{total} Embedded Systems Interview Questions and Answers", body,
          f"All {total} embedded interview questions and answers in one list: Embedded C, pointers, bit manipulation, ARM Cortex-M, RTOS, I2C, SPI, UART, CAN and Linux device drivers. Filter by topic and difficulty.", "questions/"))


def section_body(body):
    """split '## Name' sections of a problem file"""
    secs = {}
    for part in re.split(r"^## ", body, flags=re.M)[1:]:
        name, _, txt = part.partition("\n")
        secs[name.strip().lower()] = txt.strip()
    return secs


def cpp_compatible(code, slug):
    """Keep embedded C function signatures, adapting language differences."""
    replacements = {
        "implement-memmove": [("unsigned char *d = dst;", "auto *d = static_cast<unsigned char *>(dst);"),
                             ("const unsigned char *s = src;", "auto *s = static_cast<const unsigned char *>(src);")],
        "implement-memcpy": [("unsigned char *d = dst;", "auto *d = static_cast<unsigned char *>(dst);"),
                            ("const unsigned char *s = src;", "auto *s = static_cast<const unsigned char *>(src);"),
                            ("/* void * converts implicitly in C */", "/* explicit conversion in C++ */")],
        "implement-memset": [("unsigned char *b=p;", "auto *b=static_cast<unsigned char *>(p);")],
        "memory-pool": [("block_t *b = p;", "auto *b = static_cast<block_t *>(p);")],
        "aligned-malloc": [("uint8_t *p = aligned_alloc_x(aligns[i], 100);",
                            "auto *p = static_cast<uint8_t *>(aligned_alloc_x(aligns[i], 100));")],
        "remove-duplicates-hash": [("slot_t *tab = calloc(cap, sizeof *tab);",
                                    "auto *tab = static_cast<slot_t *>(calloc(cap, sizeof(slot_t)));")],
        "sorted-array-frequencies": [("(struct frequency){a[i],j-i}", "frequency{a[i],j-i}")],
    }
    for old, new in replacements.get(slug, []):
        code = code.replace(old, new)
    if slug == "ring-buffer":
        code = code.replace("#include <stdbool.h>", "#include <atomic>")
        code = code.replace("volatile uint32_t head;", "std::atomic<uint32_t> head;")
        code = code.replace("volatile uint32_t tail;", "std::atomic<uint32_t> tail;")
        code = code.replace('#define COMPILER_BARRIER() __asm__ volatile("" ::: "memory")\n\n', "")
        code = code.replace("r->head = r->tail = 0;", "r->head.store(0); r->tail.store(0);")
        code = code.replace("return r->head - r->tail;", "return r->head.load() - r->tail.load();")
        code = code.replace("uint32_t h = r->head;", "uint32_t h = r->head.load(std::memory_order_relaxed);")
        code = code.replace("h - r->tail == RB_SIZE", "h - r->tail.load(std::memory_order_acquire) == RB_SIZE")
        code = code.replace("uint32_t t = r->tail;", "uint32_t t = r->tail.load(std::memory_order_relaxed);")
        code = code.replace("r->head == t", "r->head.load(std::memory_order_acquire) == t")
        code = re.sub(r"^ *COMPILER_BARRIER\(\);[^\n]*\n", "", code, flags=re.M)
        code = code.replace("r->head = h + 1u;", "r->head.store(h + 1u, std::memory_order_release);")
        code = code.replace("r->tail = t + 1u;", "r->tail.store(t + 1u, std::memory_order_release);")
        code = code.replace("r.head = r.tail = 0xFFFFFFFEu;", "r.head.store(0xFFFFFFFEu); r.tail.store(0xFFFFFFFEu);")
    # C++ standard-library headers and qualified names, without changing the
    # low-level problem interfaces or requiring heavyweight STL abstractions.
    headers = {
        "stdio.h": "cstdio", "stdint.h": "cstdint", "stddef.h": "cstddef",
        "stdlib.h": "cstdlib", "string.h": "cstring", "limits.h": "climits",
    }
    code = re.sub(r"(?m)^#include <stdbool\.h>\n", "", code)
    code = re.sub(r"(?m)^#include <([^>]+)>", lambda m:
                  "#include <" + headers.get(m.group(1), m.group(1)) + ">", code)
    # Skip comments and string/character literals, so expected output stays intact.
    tokens = re.compile(r'''//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|(?<![:\w])(?:u?int(?:8|16|32|64|ptr|max)_t|size_t|ptrdiff_t|printf|puts|malloc|calloc|realloc|free|memcmp|memset|memcpy|memmove|strcmp|strlen|NULL)\b''')
    def qualify(m):
        word = m.group(0)
        if word.startswith(("/", '"', "'")):
            return word
        return "nullptr" if word == "NULL" else "std::" + word
    code = tokens.sub(qualify, code)
    code = re.sub(r"\b([A-Za-z_]\w*)\(void\)", r"\1()", code)
    return code


def problem_sources(p):
    """Return editable starter, test harness and reference solution for each language."""
    s = section_body(p["body"])
    def fenced(section, lang):
        fence = chr(96) * 3
        m = re.search(r"^" + re.escape(fence + lang) + r"\n(.*?)" + fence, s.get(section, ""), re.S | re.M)
        return m.group(1) if m else ""
    def split(starter, sol):
        ti = starter.find(TEST_MARK)
        return ((starter[:ti] if ti >= 0 else starter).rstrip() + "\n",
                starter[ti:] if ti >= 0 else "", sol.rstrip() + "\n")
    starter, sol = fenced("starter code", "c"), fenced("solution", "c")
    cpp_starter = fenced("starter code c++", "cpp") or cpp_compatible(starter, p["slug"])
    cpp_sol = fenced("solution c++", "cpp") or cpp_compatible(sol, p["slug"])
    return {"c": split(starter, sol), "cpp": split(cpp_starter, cpp_sol)}


def build_problems(problems):
    rows = []
    cats = sorted({p["category"] for p in problems})
    for i, p in enumerate(problems, 1):
        rows.append(f'<tr data-d="{p["difficulty"]}" data-t="{slugify(p["category"])}" data-id="p/{p["slug"]}"><td class="st"></td><td class="n">{i}</td>'
                    f'<td><a href="{url(p["slug"] + "/")}">{html.escape(p["title"])}</a></td><td class="tt">{html.escape(p["category"])}</td><td>{badge(p["difficulty"])}</td></tr>')
    opts = "".join(f'<option value="{slugify(c)}">{html.escape(c)}</option>' for c in cats)
    body = f"""
<section class="wrap pagehead"><h1>Embedded C and C++ Coding Interview Questions</h1><p class="lead">{len(problems)} hands-on embedded C and C++ problems: bit manipulation, registers, drivers, buffers, RTOS patterns and parsers. Choose C or C++, write your code in the browser, press Run, and the test harness checks your solution. Each problem has a hint, a reference solution and an explanation.</p>
<div class="filters bank"><input id="bankQ" type="search" placeholder="Filter problems…"><select id="bankT"><option value="">All categories</option>{opts}</select>
<select id="bankD"><option value="">All levels</option><option value="E">Easy</option><option value="M">Medium</option><option value="H">Hard</option></select>
<label class="chk"><input type="checkbox" id="bankTodo"> Hide solved</label><span class="count" id="bankCount"></span></div></section>
<section class="wrap"><table class="tbl" id="bank"><thead><tr><th></th><th>#</th><th>Problem</th><th>Category</th><th>Level</th></tr></thead><tbody>{''.join(rows)}</tbody></table></section>"""
    write("problems/index.html", page("problems/index.html", "Embedded C and C++ Coding Interview Questions", body,
          "Embedded C and C++ coding practice problems with hints and solutions: bit manipulation, ring buffers, drivers, RTOS.", "problems/"))

    for i, p in enumerate(problems):
        s = section_body(p["body"])
        sources = problem_sources(p)
        user_code, tests, sol_user = sources["c"]
        cpp_user, cpp_tests, cpp_sol = sources["cpp"]
        cpp_solution_html = md(chr(96)*3 + "cpp\n" + cpp_sol + chr(96)*3)
        cpp_note = ("<p>In C++, atomic indices use acquire/release ordering to publish data safely between producer and consumer.</p>"
                    if p["slug"] == "ring-buffer" else "")
        nxt = problems[i + 1] if i + 1 < len(problems) else None
        prv = problems[i - 1] if i > 0 else None
        pn = '<div class="pn">' + (f'<a href="../{url(prv["slug"] + "/")}">← {html.escape(prv["title"])}</a>' if prv else "<span></span>") + \
             (f'<a class="r" href="../{url(nxt["slug"] + "/")}">{html.escape(nxt["title"])} →</a>' if nxt else "<span></span>") + "</div>"
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
<p class="howto">Choose C or C++ and write your code on the right and press <b>Run</b> (or Ctrl + Enter). Hidden tests check your functions and print the result below the editor.</p></div>
<div class="tabpane prose" id="t-hint">{md(s.get('hint','Think about the constraints first.'))}</div>
<div class="tabpane prose" id="t-sol"><div id="solution-c">{md(s.get('solution',''))}</div><div id="solution-cpp" hidden>{cpp_note}{cpp_solution_html}</div><p><button class="btn" id="loadSol">Load solution into editor</button></p></div>
<div class="tabpane prose" id="t-exp">{md(s.get('explanation',''))}</div>
{pn}
</section>
<section class="ide-right">
<div class="edtop"><select id="codeLang" aria-label="Programming language" title="Select programming language"><option value="c">C (GCC)</option><option value="cpp">C++ (G++)</option></select><span class="file" id="codeFile">solution.c</span>
<span class="sp"></span><button class="ghost sm" id="resetCode" title="Restore the starter code">Reset</button><button class="ghost sm" id="copyCode">Copy</button><button class="btn run" id="runCode">▶ Run</button></div>
<div class="edwrap"><pre class="gutter" id="gutter" aria-hidden="true">1</pre><textarea id="code" spellcheck="false" autocapitalize="off" autocomplete="off">{html.escape(user_code)}</textarea></div>
<div class="out" id="out"><div class="outhead"><span>Output</span><span class="muted" id="outStatus">Press Run to compile and test your code.</span></div><pre id="outText"></pre></div>
<details class="tests"><summary>Show the hidden tests</summary><pre id="testPreview">{html.escape(tests)}</pre></details>
<textarea id="starter" hidden>{html.escape(user_code)}</textarea><textarea id="tests" hidden>{html.escape(tests)}</textarea><textarea id="solsrc" hidden>{html.escape(sol_user)}</textarea>
<textarea id="starter-cpp" hidden>{html.escape(cpp_user)}</textarea><textarea id="tests-cpp" hidden>{html.escape(cpp_tests)}</textarea><textarea id="solsrc-cpp" hidden>{html.escape(cpp_sol)}</textarea>
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
<p class="byline">By <a href="../../{url('about/')}">Brijesh Pratap Singh</a> · Embedded software engineer</p>
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
    schema = {"@context": "https://schema.org", "@type": "ProfilePage", "mainEntity": AUTHOR} if path == "about/index.html" else None
    write(path, page(path, title, f'<article class="wrap narrow single"><h1>{html.escape(title)}</h1><div class="prose">{md(mdtext)}</div></article>', desc, active, schema))


def build_home(topics, problems, articles, nquiz):
    total = sum(len(t["qs"]) for t in topics)
    cards = "".join(topic_card(t, "") for t in topics)
    featured = [p for p in problems][:6]
    prob = "".join(f'<a class="row" href="{url("problems/" + p["slug"] + "/")}"><span>{html.escape(p["title"])}</span><span class="tt">{html.escape(p["category"])}</span>{badge(p["difficulty"])}</a>' for p in featured)
    arts = "".join(f'<a class="row" href="{url("articles/" + a["slug"] + "/")}"><span>{html.escape(a["title"])}</span><span class="tt">{html.escape(a.get("tag",""))}</span></a>' for a in articles[:6])
    body = f"""
<section class="home-hero">
  <div class="wrap home-hero-grid">
    <div class="home-hero-copy">
      <p class="home-kicker"><span class="home-live"></span> FREE EMBEDDED SYSTEMS INTERVIEW PREPARATION</p>
      <h1>Embedded systems interview questions <span>and coding practice.</span></h1>
      <p class="home-intro">Prepare for embedded software, firmware, BSP and Linux device driver interviews with clear technical answers, hands-on C/C++ coding problems and company interview guides. From freshers to experienced engineers.</p>
      <div class="home-actions">
        <a class="home-primary" href="{url('questions/')}">Explore interview questions <span aria-hidden="true">→</span></a>
        <a class="home-secondary" href="{url('problems/')}"><span aria-hidden="true">&lt;/&gt;</span> Practice C/C++</a>
      </div>
      <div class="home-metrics" aria-label="Learning resources">
        <div><strong>{total:,}</strong><span>Interview questions</span></div>
        <div><strong>{len(problems)}</strong><span>Coding problems</span></div>
        <div><strong>{len(topics)}</strong><span>Technical topics</span></div>
        <div><strong>{nquiz}</strong><span>Quiz questions</span></div>
      </div>
    </div>
    <aside class="home-preview" aria-label="Example coding practice">
      <div class="home-preview-top"><span class="home-dots" aria-hidden="true"><i></i><i></i><i></i></span><span>Interview practice</span><span class="home-lang">C / C++</span></div>
      <div class="home-preview-content">
        <span class="home-example-label">BIT MANIPULATION · SAMPLE PROBLEM</span>
        <h2>Count set bits in an integer</h2>
        <p>Can you solve it without checking every bit?</p>
        <pre aria-label="C code example"><code><span class="home-code-dim">#include</span> <span class="home-code-str">&lt;stdint.h&gt;</span>

<span class="home-code-key">unsigned</span> popcount(uint32_t n)
{{
    <span class="home-code-key">unsigned</span> count = 0;
    <span class="home-code-key">while</span> (n) {{
        n &amp;= n - 1;
        ++count;
    }}
    <span class="home-code-key">return</span> count;
}}</code></pre>
        <div class="home-preview-bottom"><span><b aria-hidden="true">✓</b> Built-in tests &amp; solutions</span><a href="{url('problems/count-set-bits/')}">Try problem →</a></div>
      </div>
    </aside>
  </div>
</section>
<div class="wrap home-entry-wrap">
  <nav class="home-entry" aria-label="Start learning">
    <a href="{url('questions/')}"><span class="home-entry-icon" aria-hidden="true">Q&amp;A</span><span><strong>Interview questions</strong><small>Browse by topic and difficulty</small></span><span class="home-entry-arrow" aria-hidden="true">→</span></a>
    <a href="{url('problems/')}"><span class="home-entry-icon home-entry-code" aria-hidden="true">&lt;/&gt;</span><span><strong>Practice questions</strong><small>Run C and C++ code online</small></span><span class="home-entry-arrow" aria-hidden="true">→</span></a>
    <a href="{url('quiz/')}"><span class="home-entry-icon" aria-hidden="true">MCQ</span><span><strong>Quick quizzes</strong><small>Test your technical knowledge</small></span><span class="home-entry-arrow" aria-hidden="true">→</span></a>
    <a href="{url('companies/')}"><span class="home-entry-icon" aria-hidden="true">Co.</span><span><strong>Company guides</strong><small>Prepare for interview rounds</small></span><span class="home-entry-arrow" aria-hidden="true">→</span></a>
  </nav>
</div>
<section class="wrap home-top" id="learn"><div class="sechead"><h2>Embedded interview questions by topic</h2><a href="{url('topics/')}">All topics →</a></div><p class="home-section-intro">Build your foundations or revise the topics that matter most for your next interview.</p><div class="home-topic-links" aria-label="Popular topics"><a href="{url('topics/c-programming/')}">C programming</a><a href="{url('topics/embedded-c/')}">Embedded C</a><a href="{url('topics/microcontrollers-arm/')}">ARM Cortex-M</a><a href="{url('topics/rtos/')}">RTOS</a><a href="{url('topics/linux-device-drivers/')}">Linux device drivers</a><a href="{url('topics/embedded-linux/')}">Embedded Linux</a></div><div class="grid cards">{cards}</div></section>
<section class="wrap home-why" aria-labelledby="home-why-title">
<div class="home-why-inner">
<div><p class="home-small-label">YOUR INTERVIEW PREPARATION ROADMAP</p><h2 id="home-why-title">Looking for the best embedded systems interview preparation website?</h2>
<p>Choose a resource that covers both the fundamentals and real embedded engineering problems. EmbeddedInterview.com brings together {total:,} technical questions and answers, {len(problems)} coding exercises and {len(topics)} topics in one free platform for freshers and experienced engineers.</p>
<a class="btn" href="{url('roadmap/')}">Explore the preparation roadmap →</a></div>
<div class="home-why-links">
<a href="{url('topics/embedded-c/')}"><strong>Embedded C interview questions</strong><span>Volatile, pointers, interrupts, startup and registers.</span></a>
<a href="{url('problems/')}"><strong>C/C++ coding interview practice</strong><span>Browser editor, test cases, hints and solutions.</span></a>
<a href="{url('topics/arm-architecture/')}"><strong>ARM architecture interview questions</strong><span>Exceptions, memory barriers, MMU and caches.</span></a><a href="{url('topics/rtos/')}"><strong>RTOS interview questions</strong><span>Scheduling, synchronization and real-time concepts.</span></a>
<a href="{url('topics/linux-device-drivers/')}"><strong>Linux device driver interview questions</strong><span>Kernel, BSP, device tree, memory and driver fundamentals.</span></a>
<a href="{url('companies/')}"><strong>Company interview preparation</strong><span>Company guides and <span>community interview experiences</span>.</span></a>
</div></div></section>
<section class="wrap home-author"><div class="home-author-mark" aria-hidden="true">BP</div><div><p class="home-small-label">ABOUT THE FOUNDER</p><h2>Built from embedded engineering experience</h2><p>Created by <a href="{url('about/')}">Brijesh Pratap Singh</a>, an embedded software engineer with about seven years of industry experience spanning Qualcomm, Intel, Boeing and Cyient, including firmware, Linux device drivers, graphics and virtualization. This is an independent learning resource, not affiliated with or endorsed by these companies.</p><a href="{url('about/')}">About the author and editorial approach →</a></div></section>
<section class="wrap two">
<div class="panel"><div class="sechead"><h2>Practice problems</h2><a href="{url('problems/')}">See all →</a></div>{prob}</div>
<div class="panel"><div class="sechead"><h2>Latest articles</h2><a href="{url('articles/')}">See all →</a></div>{arts}</div>
</section>
<section class="wrap"><div class="banner"><div><h2>Test yourself in 5 minutes</h2><p>10 random MCQs with explanations. Track your best score.</p></div><a class="btn big" href="{url('quiz/')}">Take the quiz</a></div></section>
<section class="wrap about-home"><h2>Free embedded systems interview preparation for freshers and experienced engineers</h2>
<p>EmbeddedInterview has {total} embedded interview questions with detailed answers, written the way you would answer in a real interview: the short answer first, then the detail, the common mistakes and the follow-up questions interviewers ask next. The questions cover what firmware, embedded software, BSP and Linux driver interviews actually test: <a href="{url('topics/c-programming/')}">C programming</a>, <a href="{url('topics/pointers-memory/')}">pointers and memory</a>, <a href="{url('topics/embedded-c/')}">Embedded C</a> (volatile, interrupts, linker scripts), <a href="{url('topics/bit-manipulation/')}">bit manipulation</a>, <a href="{url('topics/microcontrollers-arm/')}">ARM Cortex-M microcontrollers</a>, <a href="{url('topics/rtos/')}">RTOS</a>, <a href="{url('topics/communication-protocols/')}">I2C, SPI, UART and CAN</a>, and <a href="{url('topics/linux-device-drivers/')}">Linux kernel and device drivers</a>.</p>
<p>Use the <a href="{url('questions/')}">full list of embedded interview questions</a> to filter by topic and difficulty, practise the {len(problems)} <a href="{url('problems/')}">embedded C and C++ coding interview questions</a> with a browser-based editor and test cases, or follow the <a href="{url('roadmap/')}">preparation roadmap</a> from fresher to senior level.</p>
</section>
<section class="wrap how"><h2>How to use this site</h2><div class="grid three">
<div><b>1. Read</b><p>Work through a topic. Each answer is written the way you would say it in an interview: the short version first, then the detail.</p></div>
<div><b>2. Code</b><p>Solve the practice problems in the built-in editor. Press Run and hidden tests check your code instantly; then compare with the reference solution.</p></div>
<div><b>3. Track</b><p>Mark questions done. Your progress is saved in your browser, so you can see what is left before the interview.</p></div></div></section>"""
    schema = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebSite", "name": SITE_NAME, "alternateName": "Embedded Interview", "url": SITE_URL, "inLanguage": "en"},
        {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL, "logo": SITE_URL + "/static/og.png", "founder": AUTHOR}]}
    write("index.html", page("index.html", SITE_NAME, body, f"Free embedded systems interview preparation: {total} questions and answers, {len(problems)} C/C++ coding problems, ARM, RTOS, Linux drivers, quizzes and company guides.", "", schema))


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
                urls.append(f"<url><loc>{SITE_URL}/{rel}</loc></url>")
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
        v = re.sub(r"<!--.*?-->", "", m.group(2), flags=re.S).strip()
        if v and v != "_No response_":
            fields[m.group(1).strip()] = v
    return fields


def avatar(a=None):
    """Every forum author is shown as Anonymous."""
    return '<span class="who"><span class="anon" aria-hidden="true">?</span>Anonymous</span>'


def when(iso):
    return f'<time data-t="{html.escape(iso)}" datetime="{html.escape(iso)}">{iso[:10]}</time>'


def build_forum():
    path = os.path.join(CONTENT, "forum.json")
    data = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {"discussions": [], "categories": []}
    posts = data.get("discussions", [])
    new_btns = ('<button class="btn" data-open="exp">+ Share interview experience</button>'
                '<button class="btn ghost" data-open="ask" data-cat="q-a">Ask a question</button>'
                '<button class="btn ghost" data-open="ask" data-cat="general">Start a discussion</button>')
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
        rows.append(f"""<a class="fpost" href="{url(slug + '/')}" data-cat="{html.escape(d['category']['slug'])}" data-co="{html.escape(comp)}" data-out="{html.escape(f.get('Outcome',''))}" data-votes="{ncom}" data-time="{html.escape(d['createdAt'])}">
<div class="votes"><b>{ncom}</b><span>{'reply' if ncom == 1 else 'replies'}</span></div>
<div class="fbody"><h3>{html.escape(d['title'])}</h3><div class="fchips">{chips}</div>
<p>{html.escape(plain(preview, 180))}</p>
<div class="fmeta"><span>Anonymous</span>{when(d['createdAt'])}<span class="cat">{html.escape(d['category']['name'])}</span></div></div></a>""")
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

    keep = {"interview-experience": "Interview Experience", "q-a": "Q&A", "general": "General", "announcements": "Announcements"}
    have = {c["slug"] for c in data.get("categories", [])}
    cats = [("all", "All")] + [(k, v) for k, v in keep.items() if k in have and (k != "announcements" or any(d["category"]["slug"] == k for d in posts))]
    if len(cats) == 1:
        cats += [("interview-experience", "Interview Experience"), ("q-a", "Q&A"), ("general", "General")]
    tabs = "".join(f'<button class="f{" on" if s == "all" else ""}" data-cat="{html.escape(s)}">{html.escape(n)}</button>' for s, n in cats)
    co_opts = "".join(f'<option>{html.escape(c)}</option>' for c in sorted(companies, key=str.lower))
    empty = f"""<div class="fempty"><h2>No posts yet. Be the first!</h2>
<p>Share how your last embedded interview went: the company, the rounds, the questions they asked, and what you would prepare differently. It helps everyone preparing for the same roles.</p>
<div class="cta">{new_btns}</div></div>"""
    body = f"""
<section class="wrap pagehead"><h1>Community Forum</h1>
<p class="lead">Real embedded interview experiences, questions and discussions from engineers preparing for firmware, embedded software and Linux driver roles. Post anonymously, no account needed.</p>
<div class="cta fnew">{new_btns}</div>
<p class="fnote" style="margin:4px 0 0">Preparing for a specific company? Read the <a href="{url('../companies/')}">company interview guides</a>.</p>
<div class="filters ftabs">{tabs}</div>
<div class="filters bank"><input id="fq" type="search" placeholder="Search posts…"><select id="fco"><option value="">All companies</option>{co_opts}</select>
<select id="fout"><option value="">Any outcome</option><option>Offer</option><option>Rejected</option><option>Pending</option><option>Withdrew</option></select>
<select id="fsort"><option value="new">Newest</option><option value="top">Most replies</option></select><span class="count" id="fcount">{posts_total} {"discussion" if posts_total == 1 else "discussions"}</span></div>
</section>
<section class="wrap"><div id="flist" class="flist">{''.join(rows) if rows else empty}</div>
<p class="fnote">All posts are anonymous and appear here about a minute after you submit. Please keep it respectful and don't share confidential or NDA-protected material.</p></section>
{forum_forms()}"""
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
<div class="ccta"><div><b>Interviewed at {html.escape(c['company'])} recently?</b><p>Share your own experience and help the next candidate.</p></div><a class="btn ghost" href="../../forum/#share">Share your experience</a></div>
<p class="srcline">Source: summarised from a candidate's public report on <a rel="nofollow noopener" href="{html.escape(c['url'])}">{html.escape(c['source'])}</a>.</p>
</article>"""
    write(f"forum/c-{c['id']}/index.html", page(f"forum/c-{c['id']}/index.html", title, body, plain(c["summary"], 155), "forum/"))


def forum_config():
    p = os.path.join(CONTENT, "forum-config.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"api": "", "turnstile_sitekey": ""}


def forum_scripts():
    cfg = forum_config()
    ts = '<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>' if cfg.get("turnstile_sitekey") else ""
    return f'<div id="forumCfg" data-api="{html.escape(cfg.get("api", ""))}" data-sitekey="{html.escape(cfg.get("turnstile_sitekey", ""))}" hidden></div>{ts}'


def human_check():
    key = forum_config().get("turnstile_sitekey", "")
    return f'<div class="cf-turnstile" data-sitekey="{html.escape(key)}" data-theme="auto"></div>' if key else ""


def reply_form(number):
    return f"""<form class="fform reply-form" data-kind="reply" data-number="{number}">
<h3>Write a reply</h3>
<textarea name="body" rows="5" maxlength="4000" required placeholder="Share an answer, a follow-up question or what helped you…"></textarea>
{human_check()}
<div class="frow"><button class="btn" type="submit">Post reply</button><span class="fmsg" role="status"></span></div>
<p class="fhint">Replies are anonymous and appear here about a minute after posting.</p>
</form>"""


def forum_forms():
    lv = "".join(f"<option>{x}</option>" for x in ["Intern / Fresher", "1-3 years", "3-6 years", "6-10 years", "10+ years"])
    return f"""
<dialog class="fdialog" id="dlg-exp"><form class="fform" data-kind="exp">
<div class="fhead"><h2>Share your interview experience</h2><button type="button" class="ghost fclose" aria-label="Close">✕</button></div>
<p class="fhint">Your post is anonymous. Please don't share confidential or NDA-protected material, such as exact take-home tasks.</p>
<div class="fgrid">
<label>Company *<input name="company" required maxlength="120" placeholder="e.g. Qualcomm"></label>
<label>Role *<input name="role" required maxlength="120" placeholder="e.g. Embedded Software Engineer"></label>
<label>Location<input name="location" maxlength="120" placeholder="e.g. Bengaluru"></label>
<label>Experience level *<select name="experience" required><option value="">Choose…</option>{lv}</select></label>
<label>Outcome *<select name="outcome" required><option value="">Choose…</option><option>Offer</option><option>Rejected</option><option>Pending</option><option>Withdrew</option></select></label>
<label>Difficulty *<select name="difficulty" required><option value="">Choose…</option><option>Easy</option><option>Medium</option><option>Hard</option></select></label>
</div>
<label>Rounds and questions *<textarea name="rounds" required rows="7" maxlength="8000" placeholder="Round 1 (online test): C output questions, bit manipulation…&#10;Round 2 (technical): volatile, ISR rules, write a ring buffer…"></textarea></label>
<label>Tips for others<textarea name="tips" rows="3" maxlength="8000" placeholder="What would you prepare differently?"></textarea></label>
<label class="chk"><input type="checkbox" name="nda" required> This post contains no confidential or NDA-protected information.</label>
{human_check()}
<div class="frow"><button class="btn" type="submit">Post anonymously</button><span class="fmsg" role="status"></span></div>
</form></dialog>
<dialog class="fdialog" id="dlg-ask"><form class="fform" data-kind="ask">
<div class="fhead"><h2>Start a discussion</h2><button type="button" class="ghost fclose" aria-label="Close">✕</button></div>
<label>Category<select name="category"><option value="q-a">Q&amp;A: ask a question</option><option value="general">General discussion</option></select></label>
<label>Title *<input name="title" required minlength="5" maxlength="140" placeholder="e.g. How should I prepare for a Linux driver interview in 3 weeks?"></label>
<label>Details *<textarea name="body" required rows="8" maxlength="8000"></textarea></label>
{human_check()}
<div class="frow"><button class="btn" type="submit">Post anonymously</button><span class="fmsg" role="status"></span></div>
<p class="fhint">Your post is anonymous and appears on the forum about a minute after posting.</p>
</form></dialog>
{forum_scripts()}"""


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
        comments.append(f'<div class="comment"><div class="chead">{avatar(c.get("author"))}{when(c["createdAt"])}{ans}</div><div class="prose cbody">{c["bodyHTML"]}</div>{reps}</div>')
    schema = {"@context": "https://schema.org", "@type": "DiscussionForumPosting", "headline": d["title"],
              "url": f'{SITE_URL}/forum/{d["_slug"]}/', "datePublished": d["createdAt"],
              "author": {"@type": "Person", "name": "Anonymous"},
              "interactionStatistic": [{"@type": "InteractionCounter", "interactionType": "https://schema.org/CommentAction", "userInteractionCount": ncom}]}
    body = f"""
<article class="wrap narrow single thread">
<div class="crumbs"><a href="../{url('')}">Forum</a> / {html.escape(d['category']['name'])}</div>
<h1>{html.escape(d['title'])}</h1>
<div class="meta">{avatar()}{when(d['createdAt'])}<span>💬 {ncom} {'reply' if ncom == 1 else 'replies'}</span></div>
{f'<dl class="finfo">{meta}</dl>' if meta else ''}
<div class="prose">{body_html}</div>
<h2 class="sec">{ncom} {'reply' if ncom == 1 else 'replies'}</h2>
{''.join(comments) or '<p class="muted">No replies yet. Be the first to answer.</p>'}
{'' if d.get('locked') else reply_form(d['number'])}
</article>
{forum_scripts()}"""
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
        cta = f"""<div class="ccta"><div><b>Interviewed at {html.escape(c['title'])}?</b><p>Share your experience on the forum and help the next candidate.</p></div><a class="btn" href="../../forum/#share">Share your experience</a></div>"""
        body_html = md(c["body"]).replace('<a href="http', '<a rel="nofollow noopener" href="http')
        schema = {"@context": "https://schema.org", "@type": "Article", "headline": f"{c['title']} Embedded Interview Guide",
                  "description": c.get("desc", ""), "dateModified": TODAY, "author": {"@type": "Organization", "name": SITE_NAME}}
        body = f"""
<article class="wrap narrow single">
<div class="crumbs"><a href="../{url('')}">Company guides</a> / {html.escape(c['title'])}</div>
<h1>{html.escape(c['title'])} Embedded Interview Questions and Preparation Guide</h1>
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
