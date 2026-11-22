/**
 * EmbeddedInterview forum API (Cloudflare Worker)
 *
 * Lets visitors post interview experiences and replies on embeddedinterview.com
 * without a GitHub account. Posts are stored as GitHub Discussions in the site
 * repository, and the site rebuilds automatically when one is created.
 *
 * Secrets (Cloudflare dashboard > Worker > Settings > Variables and Secrets):
 *   GITHUB_TOKEN      fine-grained token: this repo only, Discussions read & write
 *   TURNSTILE_SECRET  Cloudflare Turnstile secret key
 * Plain variables:
 *   REPO              Brijeshpratap716/embeddedinterview
 *   ALLOWED_ORIGIN    https://embeddedinterview.com
 */

const LIMITS = { title: 140, field: 120, long: 8000, reply: 4000 };
const CATEGORIES = { "interview-experience": "Interview Experience", "q-a": "Q&A", "general": "General" };
const OUTCOMES = ["Offer", "Rejected", "Pending", "Withdrew"];
const DIFFS = ["Easy", "Medium", "Hard"];
const LEVELS = ["Intern / Fresher", "1-3 years", "3-6 years", "6-10 years", "10+ years"];

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    const allowed = (env.ALLOWED_ORIGIN || "https://embeddedinterview.com").split(",").map(s => s.trim());
    const cors = {
      "Access-Control-Allow-Origin": allowed.includes(origin) ? origin : allowed[0],
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Vary": "Origin",
    };
    const reply = (status, obj) => new Response(JSON.stringify(obj), { status, headers: { ...cors, "Content-Type": "application/json" } });

    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
    if (request.method !== "POST") return reply(405, { error: "Method not allowed" });
    if (!allowed.includes(origin)) return reply(403, { error: "Forbidden origin" });

    let data;
    try { data = await request.json(); } catch { return reply(400, { error: "Invalid request" }); }

    // 1. Human check (Cloudflare Turnstile)
    const ip = request.headers.get("CF-Connecting-IP") || "";
    if (!(await verifyTurnstile(env, data.turnstile, ip))) return reply(403, { error: "Please complete the human check and try again." });

    const path = new URL(request.url).pathname;
    try {
      if (path.endsWith("/api/post")) return reply(200, await createPost(env, data));
      if (path.endsWith("/api/reply")) return reply(200, await createReply(env, data));
      return reply(404, { error: "Not found" });
    } catch (e) {
      const msg = e && e.userMessage ? e.userMessage : "Something went wrong. Please try again in a minute.";
      if (!(e && e.userMessage)) console.error(e);
      return reply(e && e.userMessage ? 400 : 500, { error: msg });
    }
  },
};

/* ---------------------------------------------------------------- helpers */
function bad(msg) { const e = new Error(msg); e.userMessage = msg; throw e; }

function clean(v, max, required, label) {
  const s = (typeof v === "string" ? v : "").replace(/\r\n/g, "\n").replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g, "").trim();
  if (required && !s) bad(`Please fill in: ${label}`);
  if (s.length > max) bad(`${label} is too long (max ${max} characters).`);
  return s;
}
function pick(v, list, label, required) {
  if (!v && !required) return "";
  if (!list.includes(v)) bad(`Please choose a valid ${label}.`);
  return v;
}
// Stop posts from injecting their own "### Field" headings or @mentions
function safeText(s) { return s.replace(/^#{1,6}\s/gm, "").replace(/@(?=\w)/g, "@​"); }

async function verifyTurnstile(env, token, ip) {
  if (!token || !env.TURNSTILE_SECRET) return false;
  const form = new FormData();
  form.append("secret", env.TURNSTILE_SECRET);
  form.append("response", token);
  if (ip) form.append("remoteip", ip);
  const r = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", { method: "POST", body: form });
  const j = await r.json();
  return j.success === true;
}

async function gql(env, query, variables) {
  const r = await fetch("https://api.github.com/graphql", {
    method: "POST",
    headers: { "Authorization": `bearer ${env.GITHUB_TOKEN}`, "Content-Type": "application/json", "User-Agent": "embeddedinterview-forum" },
    body: JSON.stringify({ query, variables }),
  });
  const j = await r.json();
  if (j.errors) throw new Error(JSON.stringify(j.errors));
  return j.data;
}

async function repoInfo(env) {
  const [owner, name] = (env.REPO || "Brijeshpratap716/embeddedinterview").split("/");
  const d = await gql(env, `query($o:String!,$n:String!){repository(owner:$o,name:$n){id discussionCategories(first:25){nodes{id slug}}}}`, { o: owner, n: name });
  return { owner, name, id: d.repository.id, cats: Object.fromEntries(d.repository.discussionCategories.nodes.map(c => [c.slug, c.id])) };
}

/* ---------------------------------------------------------------- new post */
async function createPost(env, d) {
  const category = d.category in CATEGORIES ? d.category : bad("Please choose a category.");
  let title, body;

  if (category === "interview-experience") {
    const company = clean(d.company, LIMITS.field, true, "Company");
    const role = clean(d.role, LIMITS.field, true, "Role");
    const location = clean(d.location, LIMITS.field, false, "Location");
    const experience = pick(d.experience, LEVELS, "experience level", true);
    const outcome = pick(d.outcome, OUTCOMES, "outcome", true);
    const difficulty = pick(d.difficulty, DIFFS, "difficulty", true);
    const rounds = clean(d.rounds, LIMITS.long, true, "Rounds and questions");
    const tips = clean(d.tips, LIMITS.long, false, "Tips");
    if (d.nda !== true) bad("Please confirm the post contains no confidential information.");
    title = `${company} ${role} - Interview experience`.slice(0, LIMITS.title);
    const f = (k, v) => `### ${k}\n\n${v ? safeText(v) : "_No response_"}\n\n`;
    body = f("Company", company) + f("Role", role) + f("Location", location) + f("Experience level", experience) +
           f("Outcome", outcome) + f("Difficulty", difficulty) + f("Rounds and questions", rounds) + f("Tips for others", tips);
  } else {
    title = clean(d.title, LIMITS.title, true, "Title");
    body = safeText(clean(d.body, LIMITS.long, true, "Details"));
  }
  if (title.length < 5) bad("Please write a slightly longer title.");
  body += "\n<!-- posted anonymously via embeddedinterview.com -->";

  const repo = await repoInfo(env);
  const catId = repo.cats[category] || bad("This category is not available yet.");
  const r = await gql(env, `mutation($r:ID!,$c:ID!,$t:String!,$b:String!){createDiscussion(input:{repositoryId:$r,categoryId:$c,title:$t,body:$b}){discussion{number}}}`,
    { r: repo.id, c: catId, t: title, b: body });
  return { ok: true, number: r.createDiscussion.discussion.number };
}

/* ---------------------------------------------------------------- reply */
async function createReply(env, d) {
  const number = parseInt(d.number, 10);
  if (!(number > 0)) bad("Unknown post.");
  const text = safeText(clean(d.body, LIMITS.reply, true, "Reply"));
  if (text.length < 2) bad("Please write a reply.");
  const [owner, name] = (env.REPO || "Brijeshpratap716/embeddedinterview").split("/");
  const q = await gql(env, `query($o:String!,$n:String!,$num:Int!){repository(owner:$o,name:$n){discussion(number:$num){id locked}}}`, { o: owner, n: name, num: number });
  const disc = q.repository.discussion || bad("This post no longer exists.");
  if (disc.locked) bad("Replies are closed for this post.");
  await gql(env, `mutation($id:ID!,$b:String!){addDiscussionComment(input:{discussionId:$id,body:$b}){comment{id}}}`,
    { id: disc.id, b: text + "\n<!-- posted anonymously via embeddedinterview.com -->" });
  return { ok: true };
}
