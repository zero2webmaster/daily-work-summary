# Daily Work Summary

**Version:** 1.5.0

Automated daily email summaries of your GitHub development work across all repositories. Runs via GitHub Actions — no server required.

---

## Quick Start

1. **Fork** this repository
2. **Add secrets** — GitHub PAT + Gmail credentials (and optionally one AI key)
3. **Enable workflow permissions** — Settings → Actions → General → Read and write
4. **Run manually** to test, then let the daily cron handle it
5. **Sync your fork** periodically to pull in updates — on GitHub, use **Sync fork** (or **Fetch upstream**) on your fork’s page

---

## How It Works

1. **GitHub Actions** triggers on your schedule (default: 10 PM EST)
2. **PyGithub** fetches every commit you made in the last 24 hours across all repos you own
3. Active repos are **globally sorted by activity** (most commits first)
4. **Optional AI** generates a one-sentence thematic summary per repo
5. The result is saved as `YYYY-MM-DD-GitHub-Daily-Summary.md` and emailed as HTML

---

## How AI Summaries Work

When an AI provider key is configured, each repo's commit messages are sent to your chosen model with this prompt:

> *"In one sentence, describe the type of development work from these git commits. Be concise and professional. Do not list commits; summarize the overall theme."*

**Without AI** — you get the raw commit list:

```
### my-website

**3 commits**

* Add DeepL caching for translations
* Fix SEO meta tags on homepage
* Refactor email queue handler
```

**With AI** — each repo gets a one-sentence summary above the commit list:

```
### my-website
*Performance improvements, SEO fixes, and backend refactoring across translations and email.*

**3 commits**

* Add DeepL caching for translations
* Fix SEO meta tags on homepage
* Refactor email queue handler
```

Each AI call uses a small/fast model (Claude 3.5 Haiku, GPT-4o-mini, or Gemini Flash), so costs are negligible — typically under $0.01/day even across many repos.

---

## Configuration Reference

### Required Secrets

| Secret | Description |
|--------|-------------|
| `PAT_GITHUB` | GitHub Personal Access Token. [Create one](https://github.com/settings/tokens) with scopes: `repo`, `read:user` |
| `EMAIL_USERNAME` | Gmail address used to send (e.g. `you@gmail.com`) |
| `EMAIL_PASSWORD` | [Gmail App Password](https://myaccount.google.com/apppasswords) — 16 characters, no spaces (requires 2FA) |

### Optional AI Secrets

Set **one** of these to enable AI-powered repo summaries. If you set multiple keys, use the `AI_PROVIDER` variable (below) to pick which one to use — otherwise it auto-detects from the first key found.

| Secret | Provider | Default model | Get your key |
|--------|----------|---------------|--------------|
| `OPENROUTER_API_KEY` | [OpenRouter](https://openrouter.ai) | `anthropic/claude-3-5-haiku` | [openrouter.ai/keys](https://openrouter.ai/keys) |
| `ANTHROPIC_API_KEY` | [Anthropic](https://console.anthropic.com) | `claude-3-5-haiku-20241022` | [console.anthropic.com/keys](https://console.anthropic.com/settings/keys) |
| `GOOGLE_API_KEY` | [Google Gemini](https://aistudio.google.com) | `gemini-1.5-flash` | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `OPENAI_API_KEY` | [OpenAI](https://platform.openai.com) | `gpt-4o-mini` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |

> **Tip:** OpenRouter lets you use models from Anthropic, OpenAI, Google, and others with a single key — useful if you want flexibility without managing multiple accounts.

### Optional Airtable Secrets

| Secret | Description |
|--------|-------------|
| `AIRTABLE_PAT` | [Airtable Personal Access Token](https://airtable.com/create/tokens) with scopes: `data.records:read`, `data.records:write`, `schema.bases:read`, `schema.bases:write` |
| `AIRTABLE_BASE_ID` | Your Airtable base ID (`appXXXXXXXXXXXXXX`) — can be stored as a **Secret** *or* a Variable |
| `AIRTABLE_TABLE_SUMMARIES` | Daily Summaries table ID (`tblXXXXXXXXXXXXXX`) — can be stored as a **Secret** *or* a Variable |
| `AIRTABLE_TABLE_REPOS` | Repositories table ID (`tblXXXXXXXXXXXXXX`) — can be stored as a **Secret** *or* a Variable |

### Optional Slack / Discord Secrets

| Secret | Description |
|--------|-------------|
| `SLACK_WEBHOOK_URL` | Slack [Incoming Webhook URL](https://api.slack.com/messaging/webhooks) — format: `https://hooks.slack.com/services/...` |
| `DISCORD_WEBHOOK_URL` | Discord channel webhook URL — format: `https://discord.com/api/webhooks/...` |

### Variables

Set these under **Settings → Secrets and variables → Actions → Variables**:

| Variable | Options | Default |
|----------|---------|---------|
| `DELIVERY_METHOD` | Comma-separated list: `email`, `airtable`, `slack`, `discord`. Also accepts `both` (= `email,airtable`) | `email` |
| `AI_PROVIDER` | `openrouter`, `anthropic`, `gemini`, `openai` | Auto-detects from first available key |
| `EMAIL_TIMEZONE` | Any [IANA timezone](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) (e.g. `America/New_York`, `Europe/London`) | `America/New_York` |
| `AIRTABLE_BASE_ID` | *(Optional — use Variable if not stored as a Secret)* | *(none)* |
| `AIRTABLE_TABLE_SUMMARIES` | *(Optional — use Variable if not stored as a Secret)* | *(none)* |
| `AIRTABLE_TABLE_REPOS` | *(Optional — use Variable if not stored as a Secret)* | *(none)* |

**`DELIVERY_METHOD` examples:**

| Value | What happens |
|-------|--------------|
| `email` | HTML email only (default) |
| `slack` | Slack message only |
| `discord` | Discord embed only |
| `email,slack` | Email + Slack |
| `slack,discord` | Both Slack and Discord |
| `email,airtable,slack,discord` | All four channels |
| `both` | Email + Airtable (backward-compatible alias) |

### Email Schedule (cron)

Edit `.github/workflows/daily-summary.yml` and change the `cron:` line. Cron times are in **UTC**:

| Local time | Timezone | Cron |
|------------|----------|------|
| 10:00 PM | America/New_York (EST) | `0 3 * * *` |
| 10:00 PM | America/New_York (EDT, summer) | `0 2 * * *` |
| 9:00 PM | America/Chicago (CST) | `0 3 * * *` |
| 6:00 PM | America/Los_Angeles (PST) | `0 2 * * *` |
| 8:00 PM | Europe/London (GMT) | `0 20 * * *` |
| 9:00 AM | Asia/Tokyo (JST) | `0 0 * * *` |

Use [crontab.guru](https://crontab.guru) to calculate the right UTC cron for your timezone.

---

## Airtable Integration (Optional)

Save daily summaries and repository data to Airtable for searchable, filterable records with linked relationships. Each day creates a **Daily Summary** record linked to **Repository** records — click a repo to see every day you worked on it.

### Airtable Schema

**Daily Summaries** table:
- Timestamp (YYYY-MM-DD) — primary field
- Date — native date for calendar views
- Summary — full markdown summary
- Repos Worked On — count
- Total Commits — count
- AI Summaries — bulleted AI summaries (no commit details)
- Repositories — linked to Repositories table

**Repositories** table:
- Name — `owner/repo-name`
- URL — GitHub repo link
- Owner — GitHub org/username
- Daily Summaries — linked back to Daily Summaries

### Airtable Setup

Everything is done from inside GitHub — no local Python required.

**Step 1 — Create an Airtable base**

Go to [airtable.com](https://airtable.com) → **Add a base** → name it anything (e.g. "GitHub Daily Work Summary"). Copy the base ID from the URL: `https://airtable.com/appXXXXXXXXXXXXXX/...`

**Step 2 — Create an Airtable PAT**

Go to [airtable.com/create/tokens](https://airtable.com/create/tokens), create a token with these scopes: `data.records:read`, `data.records:write`, `schema.bases:read`, `schema.bases:write`. Grant access to the base you just created.

**Step 3 — Add secrets to GitHub**

Under **Settings → Secrets and variables → Actions → Secrets**, add:
- `AIRTABLE_PAT` — your Airtable Personal Access Token
- `AIRTABLE_BASE_ID` — the base ID (`appXXXXXXXXXXXXXX`)

**Step 4 — Run the Setup Airtable workflow**

Go to **Actions → Setup Airtable Tables → Run workflow → Run workflow**.

This workflow will:
- Create the **Daily Summaries** and **Repositories** tables with the correct fields
- Automatically save `AIRTABLE_TABLE_SUMMARIES` and `AIRTABLE_TABLE_REPOS` as GitHub Variables — no copying or pasting needed
- Safe to re-run — it skips tables that already exist

**Step 5 — Enable Airtable delivery**

Set the `DELIVERY_METHOD` variable to `email,airtable` (or `airtable` for Airtable only). That's it — the next daily run will populate your base.

**If Daily Summaries has no "Repositories" link field:** Add it manually in Airtable: Daily Summaries table → **+** (add field) → **Link to another record** → choose the Repositories table → name the field `Repositories`. Re-run the Daily Work Summary workflow to backfill the links.

> **Note:** All references use Airtable IDs (`appXXX`, `tblXXX`), not names. You can rename tables/bases freely without breaking the integration.

---

## Slack & Discord Integration (Optional)

Get your daily summary posted directly to a Slack channel or Discord server via webhooks — no bot setup required.

### Slack Setup

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From scratch**
2. Name it (e.g. "Daily Work Summary"), choose your workspace
3. Under **Features**, click **Incoming Webhooks** → toggle **Activate Incoming Webhooks** to On
4. Click **Add New Webhook to Workspace**, choose the channel, click **Allow**
5. Copy the Webhook URL (`https://hooks.slack.com/services/...`)
6. Add it as a GitHub Secret: `SLACK_WEBHOOK_URL`
7. Set `DELIVERY_METHOD` to include `slack` (e.g. `slack` or `email,slack`)

### Discord Setup

1. Open your Discord server → right-click the channel → **Edit Channel**
2. Go to **Integrations** → **Webhooks** → **New Webhook**
3. Name it (e.g. "Daily Work Summary"), optionally set an avatar
4. Click **Copy Webhook URL** (`https://discord.com/api/webhooks/...`)
5. Add it as a GitHub Secret: `DISCORD_WEBHOOK_URL`
6. Set `DELIVERY_METHOD` to include `discord` (e.g. `discord` or `email,discord`)

### What the Message Looks Like

**Slack** — uses [Block Kit](https://api.slack.com/block-kit) with a header, stats bar, per-repo sections with linked repo names, optional AI summaries in italics, and a footer link.

**Discord** — uses a rich embed with a green accent color (grey on no-commit days), commit stats as inline fields, and a full per-repo breakdown with hyperlinked repo names.

Both handle message length limits gracefully — long summaries are truncated with `...` and a "...and N more repos" notice if needed.

---

## Setup Guide

### 1. Create a GitHub PAT

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens) → **Generate new token (classic)**
2. Name: `daily-work-summary`
3. Scopes: **`repo`** (full) and **`read:user`**
4. Copy the token immediately — you can't view it again

### 2. Create a Gmail App Password

1. Enable [2-Factor Authentication](https://myaccount.google.com/signinoptions/two-step-verification) on your Google account
2. Go to [App Passwords](https://myaccount.google.com/apppasswords)
3. Create a new app password (name it anything, e.g. "Daily Summary")
4. Copy the 16-character password — no spaces

### 3. Add Secrets

**Settings → Secrets and variables → Actions → Secrets → New repository secret**

| Secret | Value |
|--------|-------|
| `PAT_GITHUB` | Your GitHub token |
| `EMAIL_USERNAME` | Your Gmail address |
| `EMAIL_PASSWORD` | Your Gmail App Password |
| `OPENROUTER_API_KEY` | *(Optional)* Your OpenRouter key |
| `ANTHROPIC_API_KEY` | *(Optional)* Your Anthropic key |
| `GOOGLE_API_KEY` | *(Optional)* Your Google AI key |
| `OPENAI_API_KEY` | *(Optional)* Your OpenAI key |
| `AIRTABLE_PAT` | *(Optional)* Your Airtable PAT ([create one](https://airtable.com/create/tokens)) |
| `SLACK_WEBHOOK_URL` | *(Optional)* Slack Incoming Webhook URL |
| `DISCORD_WEBHOOK_URL` | *(Optional)* Discord channel webhook URL |

Only add the AI key(s) you actually have. One is enough.

### 4. Add Variables (Optional)

**Settings → Secrets and variables → Actions → Variables → New repository variable**

| Variable | Example value |
|----------|---------------|
| `EMAIL_TIMEZONE` | `America/New_York` |
| `AI_PROVIDER` | `openrouter` *(only needed if you set multiple AI keys)* |
| `DELIVERY_METHOD` | `email,airtable` *(comma-separated; default is `email`. Options: `email`, `airtable`, `slack`, `discord`)* |
| `AIRTABLE_BASE_ID` | `appXXXXXXXXXXXXXX` *(only needed if not stored as a Secret)* |
| `AIRTABLE_TABLE_SUMMARIES` | `tblXXXXXXXXXXXXXX` *(only needed if not stored as a Secret)* |
| `AIRTABLE_TABLE_REPOS` | `tblXXXXXXXXXXXXXX` *(only needed if not stored as a Secret)* |

### 5. Enable Workflow Permissions

1. **Settings → Actions → General**
2. Scroll to **Workflow permissions**
3. Select **Read and write permissions**
4. Click **Save**

### 6. Customize the Email Schedule (Optional)

Open `.github/workflows/daily-summary.yml` and update the `cron:` line. See the table above for common times.

---

## Testing

1. Go to **Actions** → **Daily Work Summary**
2. Click **Run workflow** → **Run workflow**
3. Check the Actions log and your inbox within a minute

---

## Project Structure

```
├── .github/
│   ├── workflows/
│   │   ├── daily-summary.yml          # Cron + email + Airtable + webhook workflow
│   │   └── setup-airtable.yml         # One-click Airtable table setup (run once)
│   └── scripts/
│       ├── generate_summary.py        # Summary generator + delivery routing
│       ├── airtable_client.py         # Airtable REST API client
│       └── webhook_client.py          # Slack + Discord webhook delivery
├── summaries/                         # HTML email companions (auto-generated)
├── YYYY-MM-DD-GitHub-Daily-Summary.md # Markdown archive (auto-generated)
├── directives/                        # SOPs
├── execution/
│   ├── setup_airtable.py             # Airtable table creation (used by setup workflow)
│   └── ...
└── requirements.txt
```

---

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues (403 PAT errors, email not sending, AI key errors, rate limits).

---

## Keeping your fork in sync

Forking copies the repo at that moment — you won’t get updates automatically. To pull in changes from the original repo:

- **GitHub UI:** Open your fork → click **Sync fork** (or **Fetch upstream**) → **Update branch**
- **CLI:** Add the upstream remote once, then fetch and merge:
  ```bash
  git remote add upstream https://github.com/zero2webmaster/daily-work-summary.git
  git fetch upstream && git merge upstream/main
  ```

---

## Contributing

Contributions welcome. Open an issue or PR at [github.com/zero2webmaster/daily-work-summary](https://github.com/zero2webmaster/daily-work-summary).

---

*Created by [Dr. Kerry Kriger](https://zero2webmaster.com/kerry-kriger) · [Zero2Webmaster](https://zero2webmaster.com/)*

*Version: 1.5.0 | Last Updated: 2026-03-20*
