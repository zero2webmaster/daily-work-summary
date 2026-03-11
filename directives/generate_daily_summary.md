# Directive: Generate Daily Work Summary

**Version:** 1.0.0
**Last Updated:** 2026-03-11
**Owner:** Kerry Kriger

---

## Goal

Generate a smart daily summary of all GitHub commits across every zero2webmaster and personal repository from the last 24 hours. Email the summary and save a Markdown archive.

## Trigger

- **Automated:** GitHub Actions cron at `0 3 * * *` UTC (10pm EST)
- **Manual:** GitHub Actions → "Run workflow" button

## Inputs

| Input | Source | Notes |
|-------|--------|-------|
| GitHub PAT | `PAT_GITHUB` secret | Scopes: `repo`, `read:user` |
| Email credentials | `EMAIL_USERNAME`, `EMAIL_PASSWORD` secrets | Gmail App Password |
| Time window | Last 24 hours from run time | Uses `datetime.utcnow() - timedelta(hours=24)` |

## Process

### Step 1: Authenticate & Fetch Repos
- Authenticate with PyGithub using `PAT_GITHUB`
- Fetch ALL repos the authenticated user owns (including private)
- Skip forks (optional — currently included)

### Step 2: Collect Commits
- For each repo, query commits from last 24 hours
- Filter to commits authored by the authenticated user
- Collect: repo name, commit message (first line), SHA, timestamp

### Step 3: Generate Smart Summary
- Group commits by repository
- Sort repos by commit count (most active first)
- Format each repo section:
  ```
  ## owner/repo-name
  **N commits**
  • N changes: summary1; summary2; summary3 (+M more)
  ```
- Truncate individual commit messages to 80 characters
- If >5 commits in a repo, show first 5 and "(+M more)"
- If zero commits across all repos: "No commits today — well rested! ✅"

### Step 4: Save Markdown Archive
- Write to `summaries/daily-summary-YYYY-MM-DD.md`
- Git add + commit + push from within the workflow

### Step 5: Send Email
- Use `dawidd6/action-send-mail` GitHub Action
- To: kerry@zero2webmaster.com
- Subject: `Daily Work Summary — Day Mon DD`
- Body: HTML-formatted summary
- Skip email if summary file is empty or only contains "no commits" message

## Outputs

| Output | Location | Format |
|--------|----------|--------|
| Email | kerry@zero2webmaster.com | HTML |
| Archive | `summaries/daily-summary-YYYY-MM-DD.md` | Markdown |
| Logs | GitHub Actions run logs | Plaintext |

## Edge Cases

| Scenario | Handling |
|----------|----------|
| No commits in 24h | "No commits today — well rested! ✅" |
| Long commit message | Truncate to 80 chars with `...` |
| 403 PAT error | Log clear error + link to token settings |
| Empty repo (no commits ever) | Skip silently |
| API rate limit (5000/hr) | Exponential backoff, max 3 retries |
| Archived repo | Skip (no recent commits) |
| Fork repos | Include (may want to filter later) |

## Tools/Scripts

| Script | Purpose |
|--------|---------|
| `.github/scripts/generate_summary.py` | Main summary generator (Layer 3) |
| `.github/workflows/daily-summary.yml` | Workflow orchestration |

## Performance

- Typical run: 30-60 seconds (depending on repo count)
- API calls: ~1 per repo + 1 auth call
- Rate limit budget: 5000 calls/hour (PAT), should use <100

## Monitoring

- Check GitHub Actions → "Daily Work Summary" for run history
- Failed runs trigger GitHub's built-in email notifications
- Summary archive in `summaries/` provides historical record

## Lessons Learned

*(Update this section as issues are discovered)*

- Gmail App Passwords must NOT include spaces (Google displays them formatted with spaces)
- GitHub cron schedules may be delayed up to 15-30 min during peak times
- `workflow_dispatch` is essential for testing without waiting for cron
