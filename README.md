# EmbeddedInterview.com

Source for **embeddedinterview.com**: a static website with embedded-systems interview questions, coding practice problems, an MCQ quiz and articles.

No database and no server code: `build.py` turns the Markdown in `content/` into plain HTML in `site/`. Any static host can serve it, for free.

## What's inside

| Path | What it is |
|---|---|
| `content/questions/*.md` | One file per topic. Every `### Question {E\|M\|H}` heading starts a new Q&A (E = Easy, M = Medium, H = Hard). |
| `content/problems.src` | All coding problems. Each starts with `@@@ slug`, then metadata, then `## Problem`, `## Starter code`, `## Hint`, `## Solution`, `## Explanation`. |
| `content/articles/*.md` | Long-form articles. |
| `content/quiz.json` | MCQs: `cat` (category), `q`, `o` (options), `a` (index of correct option), `e` (explanation). |
| `content/pages/*.md` | Roadmap, About, Contact, Privacy, Terms. |
| `static/` | CSS, JavaScript (search, progress tracking, quiz, editor), favicon. |
| `build.py` | The generator. |
| `.github/workflows/deploy.yml` | Builds and publishes to GitHub Pages on every push. |

## Build locally

```sh
pip install markdown pygments
python3 build.py              # writes ./site
cd site && python3 -m http.server 8000   # open http://localhost:8000
```

## Add content

**A new question:** open the topic file in `content/questions/` and add:

```md
### What is a mailbox in an RTOS? {M}
Your answer in Markdown. Code blocks, tables and lists all work.
```

**A new topic:** copy any topic file, change the front matter (`slug`, `title`, `icon`, `level`, `order`, `desc`).

**A new problem:** copy a block in `content/problems.src`. Keep the `/* ---- tests ---- */` line in the starter code: the "Run solution" button joins the solution with everything after that line.

Then run `python3 build.py` (or just push, if you use the GitHub workflow).

## Deploy to embeddedinterview.com

### Option A — GitHub Pages (free, automatic)

1. Create a GitHub repository (for example `embeddedinterview`) and push this folder to it.
2. In the repository: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. The workflow in `.github/workflows/deploy.yml` builds and publishes the site on every push to `main`.
4. In **Settings → Pages → Custom domain**, enter `embeddedinterview.com` and save. (The build also writes a `CNAME` file.)
5. At your domain registrar, set these DNS records:

   | Type | Name | Value |
   |---|---|---|
   | A | @ | 185.199.108.153 |
   | A | @ | 185.199.109.153 |
   | A | @ | 185.199.110.153 |
   | A | @ | 185.199.111.153 |
   | CNAME | www | `<your-github-username>.github.io` |

   Delete any existing "parking" A records or URL-forwarding the registrar added.
6. Once DNS has propagated (minutes to a few hours), tick **Enforce HTTPS** in Settings → Pages.

### Option B — Cloudflare Pages or Netlify (free)

- **Cloudflare Pages:** connect the GitHub repo, build command `pip install markdown pygments && python3 build.py`, output directory `site`. Add `embeddedinterview.com` under Custom domains; easiest if the domain's DNS is on Cloudflare.
- **Netlify:** same build command and publish directory `site`; add the domain under Domain management and follow the DNS records it shows.
- **No Git at all:** run `python3 build.py` and drag the `site` folder onto Netlify Drop (app.netlify.com/drop) or upload it to any web host's `public_html`.

## After launch

1. **Google Search Console:** add the domain property, verify through DNS, and submit `https://embeddedinterview.com/sitemap.xml`.
2. **Bing Webmaster Tools:** import from Search Console.
3. **Contact email:** the Contact page uses `contact@embeddedinterview.com`. Create that mailbox or a forwarding address at your registrar (many offer free email forwarding), or change it in `content/pages/contact.md`.
4. **Analytics (optional):** add a privacy-friendly script (Plausible, Cloudflare Web Analytics) in the `<head>` in `build.py`, and update `content/pages/privacy.md` to mention it.
5. **AdSense (optional):** once the site has traffic, apply, then add the ad script in `build.py` and update the privacy policy.

## Content licence

All questions, answers, articles and code were written for this site. Keep it that way: copying another site's question bank would breach their copyright and can get pages removed from search results.
