# Daily Work Summary

**Version:** 1.0.0 | **Framework:** 2.13.0

Automated daily smart summaries of GitHub development work across all repositories, emailed at 10pm EST.

Groups commits by repo with intelligent summaries instead of raw commit lists:

```
## zero2webmaster/my-website
**3 commits**
• 3 changes: DeepL caching; SEO meta fix; queue refactor
```

---

## How It Works

1. **GitHub Actions** runs a cron job at 10pm EST every night
2. **PyGithub** fetches all commits from the last 24 hours across every repo you own
3. Commits are **grouped by repo** and summarized intelligently
4. A **Markdown archive** is saved to `summaries/daily-summary-YYYY-MM-DD.md`
5. An **HTML email** is sent via Gmail SMTP

---

## Setup (3 Steps)

### Step 1: Create a GitHub Personal Access Token (PAT)

1. Go to **https://github.com/settings/tokens** → **"Generate new token (classic)"**
2. Name it: `daily-work-summary`
3. Set expiration (recommend: 90 days, set a calendar reminder to rotate)
4. Select scopes:
   - **`repo`** (full control) — needed for private repo access
   - **`read:user`** — needed to list all your repos
5. Click **"Generate token"**
6. Copy the token immediately (you won't see it again)

### Step 2: Create a Gmail App Password

> Requires 2-Factor Authentication enabled on your Google account.

1. Go to **https://myaccount.google.com/apppasswords**
2. App name: `Daily Work Summary`
3. Click **"Create"**
4. Copy the **16-character password** (remove spaces if displayed with them)

### Step 3: Add Repository Secrets

1. Go to your repo: **https://github.com/zero2webmaster/daily-work-summary/settings/secrets/actions**
2. Click **"New repository secret"** for each:

| Secret Name | Value |
|---|---|
| `PAT_GITHUB` | Your GitHub PAT from Step 1 |
| `EMAIL_USERNAME` | `kerry@zero2webmaster.com` |
| `EMAIL_PASSWORD` | Your Gmail App Password from Step 2 |

### Step 4: Enable Workflow Permissions

1. Go to **Settings → Actions → General**
2. Under "Workflow permissions," select **"Read and write permissions"**
3. Click **Save**

---

## Testing

### Manual Trigger

1. Go to **Actions** tab in your repository
2. Click **"Daily Work Summary"** in the left sidebar
3. Click **"Run workflow"** → **"Run workflow"**
4. Watch the logs to verify everything works

### What to Expect

**If you have commits today:**
```
Subject: Daily Work Summary — Wed Mar 11

## zero2webmaster/daily-work-summary
**2 commits**
• 2 changes: initial project setup; add smart summary script

## zero2webmaster/my-website
**1 commit**
• fix: update meta description for homepage
```

**If no commits today:**
```
Subject: Daily Work Summary — Wed Mar 11

No commits today — well rested! ✅
```

---

## Project Structure

```
daily-work-summary/
├── .github/
│   ├── workflows/
│   │   └── daily-summary.yml      # GitHub Actions workflow (cron + email)
│   └── scripts/
│       └── generate_summary.py    # Smart summary generator (Layer 3)
├── directives/
│   └── generate_daily_summary.md  # SOP for the summary process (Layer 1)
├── execution/
│   ├── create_env_template.py     # .env file creator for local dev
│   └── install_git_hooks.py       # Git hooks installer
├── summaries/                     # Auto-generated daily Markdown archives
│   └── daily-summary-YYYY-MM-DD.md
├── .cursorrules                   # AI agent project context
├── .cursorignore                  # AI context exclusions
├── .gitignore
├── AGENTS.md                      # 3-layer architecture instructions
├── CHANGELOG.md
├── README.md                      # This file
├── ROADMAP.md                     # Project phases and progress
├── SETUP_GUIDE.md                 # Framework setup reference
├── STATUS.md                      # Current project state
├── TROUBLESHOOTING.md             # Known issues and solutions
├── VERSION                        # Semantic version (1.0.0)
└── requirements.txt               # Python dependencies
```

---

## Schedule

The workflow runs daily at **10:00 PM Eastern Time** (US).

- Cron expression: `0 3 * * *` (3:00 AM UTC)
- UTC offset: EST = UTC-5, EDT = UTC-4
- During Daylight Saving Time (Mar–Nov), the email arrives at **11:00 PM EDT**
- To adjust for DST, change cron to `0 2 * * *` during EDT months

---

## Future Improvements

- AI-powered summaries via OpenAI/Claude API
- Slack / Airtable / Discord delivery
- Filter by repo patterns (WordPress vs AI projects)
- Commit impact analysis (lines changed, files touched)
- Weekly/monthly rollup summaries
- VS Code/Cursor sidebar widget

---

*Built with the [Zero2Webmaster](https://zero2webmaster.com/) 3-Layer Architecture.*
*Version: 1.0.0 | Last Updated: 2026-03-11*
