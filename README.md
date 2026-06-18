# Daily Work Summary

**Version:** 1.6.0

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
3. Commits are **grouped by account → repo**, sorted by activity (most commits first)
4. **Optional AI** generates a one-sentence thematic summary per repo
5. The result is saved as a **Markdown archive** in `summaries/` and emailed as HTML

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
| `OPENROUTER_API_KEY` | [OpenRouter](https://openrouter.ai) | `anthropic/claude-haiku-4.5` | [openrouter.ai/keys](https://openrouter.ai/keys) |
| `ANTHROPIC_API_KEY` | [Anthropic](https://console.anthropic.com) | `claude-haiku-4-5-20251001` | [console.anthropic.com/keys](https://console.anthropic.com/settings/keys) |
| `GOOGLE_API_KEY` | [Google Gemini](https://aistudio.google.com) | `gemini-2.5-flash` | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `OPENAI_API_KEY` | [OpenAI](https://platform.openai.com) | `gpt-5-mini` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |

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

### Optional Monitoring Secret (dead-man's-switch)

| Secret | Description |
|--------|-------------|
| `UPTIME_KUMA_PUSH_URL` | [Uptime Kuma](https://github.com/louislam/uptime-kuma) **Push** monitor URL — format: `https://<your-kuma-host>/api/push/<token>`. The workflow pings it *after* a successful run, so a silent outage (the cron stops, the guard skips, or the send fails) trips an alert in hours instead of going unnoticed for days. Leave unset to disable — the heartbeat step no-ops. Suggested Kuma heartbeat interval: ~36h. |

### Variables

Set these under **Settings → Secrets and variables → Actions → Variables**:

| Variable | Options | Default |
|----------|---------|---------|
| `DELIVERY_METHOD` | Comma-separated list: `email`, `airtable`, `slack`, `discord`. Also accepts `both` (= `email,airtable`) | `email` |
| `AI_PROVIDER` | `openrouter`, `anthropic`, `gemini`, `openai` | Auto-detects from first available key |
| `EMAIL_TIMEZONE` | IANA timezone identifier — see [Customizing the email schedule](#customizing-the-email-schedule) below | `America/New_York` |
| `EMAIL_SEND_HOUR` | Local hour (0–23) at which the email should go out — see [Customizing the email schedule](#customizing-the-email-schedule) | `22` |
| `EMAIL_SEND_MINUTE` | Local minute (0–59) | `30` |
| `EMAIL_SEND_WINDOW_MIN` | Acceptable delay after the target time, in minutes — rides out GitHub cron's typical 5–15 min jitter | `60` |
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

### Customizing the email schedule

**TL;DR — set three Variables and you're done. No cron math, no YAML edits, no daylight-saving fiddling.**

The workflow itself fires hourly. The Python script then checks whether your local clock has reached your target time before doing any real work — so 23 of the 24 hourly runs exit in a couple of seconds and only the run nearest your target sends the email. This means you can change your timezone or your preferred send time without ever touching `.github/workflows/daily-summary.yml`.

#### Step 1 — Pick your timezone

In **Settings → Secrets and variables → Actions → Variables**, create a variable named `EMAIL_TIMEZONE` and set it to an [IANA timezone identifier](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) — `Area/Location` style, no spaces. Examples:

| Where you are | Value to use |
|---|---|
| US East Coast | `America/New_York` |
| US Central | `America/Chicago` |
| US Mountain | `America/Denver` |
| US West Coast | `America/Los_Angeles` |
| UK | `Europe/London` |
| Central Europe | `Europe/Berlin` |
| India | `Asia/Kolkata` |
| Singapore | `Asia/Singapore` |
| Japan | `Asia/Tokyo` |
| Sydney | `Australia/Sydney` |

The script handles daylight saving automatically — `America/New_York` flips between EST and EDT for you. Search the [Wikipedia table](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) for any city or region.

#### Step 2 — Pick what time you want the email

Add two more variables:

- `EMAIL_SEND_HOUR` — the local hour you want the email, in 24-hour format (`0`–`23`). Default `22` (10 PM).
- `EMAIL_SEND_MINUTE` — the local minute (`0`–`59`). Default `30`.

So out of the box, the email arrives around **10:30 PM in `America/New_York`**. If you want it at 9 PM in `Australia/Sydney`, set `EMAIL_TIMEZONE=Australia/Sydney`, `EMAIL_SEND_HOUR=21`, `EMAIL_SEND_MINUTE=0` — that's all.

#### Step 3 — (Optional) widen or tighten the window

GitHub's cron is often delayed 5–15 minutes during peak hours. The script accepts a window of minutes AFTER your target time during which the run still counts. Default is **60 minutes** — generous enough that a 30-minute cron delay still fires the email, narrow enough that two consecutive hourly runs never both fire.

Set `EMAIL_SEND_WINDOW_MIN` if you need a different window. The window is one-sided (only AFTER the target), so the email never goes out earlier than your configured time.

#### Why this works the way it does

GitHub Actions cron schedules are UTC-only and can't read from your repo's variables. The old approach was to hand-calculate the right UTC cron and edit `.github/workflows/daily-summary.yml` every time you moved or daylight saving started. The new approach moves the schedule decision into the Python script, which CAN read your variables — so the schedule lives where the rest of your settings live, and the workflow YAML stays unchanged.

#### Manual sends

Want to send the email right now regardless of the schedule? Go to **Actions → Daily Work Summary → Run workflow**. Manual `workflow_dispatch` runs bypass the time-of-day guard.

#### A working example

You live in Berlin, you usually wrap up work around 11 PM, and you want the email shortly after:

| Variable | Value |
|---|---|
| `EMAIL_TIMEZONE` | `Europe/Berlin` |
| `EMAIL_SEND_HOUR` | `23` |
| `EMAIL_SEND_MINUTE` | `15` |

Done. The 23:00–23:59 hourly run will send the email; every other hour's run will exit in seconds. The email subject's date, the markdown heading inside the email, the filename in `summaries/`, the commit message, and the "Generated at" timestamp at the bottom of the email will all show the Berlin-local date, so the email arriving at 23:15 on June 5 will reference June 5's work (not June 6 like a UTC-anchored summary would).

#### When the cron line itself might still need a change

The only reason to edit `.github/workflows/daily-summary.yml` directly is if you want to change how often the workflow CHECKS the time. The default `'5 * * * *'` (hourly at :05) is right for almost every use case. If you wanted minute-level precision, you could switch to `'*/15 * * * *'` (every 15 minutes) and tighten the window — but that burns more GitHub Actions minutes for no real benefit.

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
| `EMAIL_TIMEZONE` | `America/New_York` — see [Customizing the email schedule](#customizing-the-email-schedule) for format and the [full list of valid names](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) |
| `EMAIL_SEND_HOUR` | `22` (local hour 0–23, default 22 = 10 PM) |
| `EMAIL_SEND_MINUTE` | `30` (local minute 0–59, default 30) |
| `EMAIL_SEND_WINDOW_MIN` | `60` (acceptable cron delay in minutes, default 60) |
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

Set `EMAIL_TIMEZONE`, `EMAIL_SEND_HOUR`, and `EMAIL_SEND_MINUTE` as Variables in step 4 above. No need to edit `.github/workflows/daily-summary.yml`. Full walkthrough in [Customizing the email schedule](#customizing-the-email-schedule).

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
├── summaries/                         # Daily archives (auto-generated)
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

*Version: 1.6.0 | Last Updated: 2026-06-17*
