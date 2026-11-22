# Forum posting API (Cloudflare Worker)

Visitors post and reply on embeddedinterview.com/forum without leaving the site and
without an account. The form sends the post to this Worker, which checks it is from
a human (Cloudflare Turnstile) and creates it in GitHub Discussions with a private
token. The site rebuilds automatically, so the post appears in about a minute.

Secrets (the GitHub token and Turnstile secret key) live only in Cloudflare.
Never put them in this repository or in chat.

## Setup (about 10 minutes)

### 1. Create a GitHub token
1. Open https://github.com/settings/personal-access-tokens/new
2. Token name: `embeddedinterview-forum`. Expiration: 1 year (set a reminder to renew).
3. Repository access: **Only select repositories** → `embeddedinterview`.
4. Permissions → Repository permissions → **Discussions: Read and write**. Leave everything else as is.
5. Generate token and copy it (starts with `github_pat_`). Keep the tab open.

### 2. Create a Cloudflare account
Sign up free at https://dash.cloudflare.com/sign-up and verify your email.

### 3. Create the Turnstile widget (spam protection)
1. In the Cloudflare dashboard, open **Turnstile** → **Add widget**.
2. Name: `embeddedinterview forum`. Hostnames: `embeddedinterview.com` and `www.embeddedinterview.com`.
3. Widget mode: **Managed**. Create.
4. You get a **Site Key** (public) and a **Secret Key** (private).

### 4. Create the Worker
1. Dashboard → **Workers & Pages** → **Create** → **Create Worker**.
2. Name it `embeddedinterview-forum` → **Deploy**.
3. Click **Edit code**, delete the sample, paste the whole of `cloudflare/worker.js`, then **Deploy**.
4. Go to the Worker's **Settings → Variables and Secrets** and add:

| Type | Name | Value |
|---|---|---|
| Secret | `GITHUB_TOKEN` | the token from step 1 |
| Secret | `TURNSTILE_SECRET` | the Turnstile Secret Key |
| Text | `REPO` | `Brijeshpratap716/embeddedinterview` |
| Text | `ALLOWED_ORIGIN` | `https://embeddedinterview.com,https://www.embeddedinterview.com` |

5. Copy the Worker's URL, shown at the top (like `https://embeddedinterview-forum.<your-name>.workers.dev`).

### 5. Connect the site
Put the two **public** values in `content/forum-config.json`:

```json
{
  "api": "https://embeddedinterview-forum.<your-name>.workers.dev",
  "turnstile_sitekey": "0x4AAAA..."
}
```

and push. Posting is live after the next deploy.

## Moderation
Every post and reply lands in the repository's **Discussions** tab. Edit, lock or delete
it there; the site updates within a minute. Locked posts hide the reply form.
