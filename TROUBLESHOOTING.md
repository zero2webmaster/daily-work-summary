# Troubleshooting Guide

**Project:** Daily Work Summary
**Last Updated:** 2026-03-15

---

**This is a living document:** Add new entries whenever you solve a problem that took more than 15 minutes, discover a workaround, or learn something not in the official documentation.

---

## GitHub Actions

### Issue: Workflow Not Triggering on Schedule

**Problem:** Cron schedule doesn't fire, no workflow runs appear in Actions tab.

**Root Cause:** GitHub Actions cron schedules only run on the default branch (usually `main`). Workflows on feature branches don't trigger cron.

**Solution:**
1. Ensure the workflow file is merged to `main`
2. Check that Actions are enabled: Settings → Actions → General → "Allow all actions"
3. Note: GitHub may delay cron runs by up to 15-30 minutes during high load

**Verification:** Manually trigger via Actions tab → "Run workflow" button

---

### Issue: 403 Forbidden When Fetching Repos

**Problem:** `generate_summary.py` returns 403 errors from GitHub API.

**Root Cause:** `PAT_GITHUB` secret missing, expired, or has insufficient scopes.

**Solution:**
1. Go to https://github.com/settings/tokens → Fine-grained tokens (or classic)
2. Ensure scopes: `repo` (full), `read:user`
3. Update secret: Repo Settings → Secrets → Actions → `PAT_GITHUB`
4. Classic tokens: check expiration date

**Verification:** Run workflow manually, check logs for "Authenticated as: <username>"

---

### Issue: Local automation token only sees one repo (`cursor[bot]`)

**Problem:** Running `generate_summary.py` locally with `PAT_GITHUB=$(gh auth token)` returns:
- `Request GET /user failed with 403: Forbidden`
- GraphQL viewer login is `cursor[bot]` with only `zero2webmaster/daily-work-summary` visible

**Root Cause:** Cursor Cloud's `gh` token is an installation/integration token scoped to this single repository, not a full user PAT with `repo` + `read:user` across all personal/org repos.

**Solution / Workaround:**
1. Run summary generation in GitHub Actions where `PAT_GITHUB` secret is configured with full scopes.
2. Keep `generate_summary.py` expecting `PAT_GITHUB` for full-account scans.
3. If local test is needed, export a real user PAT:
   - `export PAT_GITHUB=ghp_...`
   - `python3 .github/scripts/generate_summary.py`

**Verification:** In logs, `Authenticated as:` should be the real account (not `cursor[bot]`), and repo count should match expected org + personal repos.

---

### Issue: Email Not Sending

**Problem:** Workflow runs successfully but no email arrives.

**Root Cause:** Gmail App Password incorrect, or "Less secure apps" setting issue.

**Solution:**
1. Go to https://myaccount.google.com/apppasswords
2. Generate new App Password (requires 2FA enabled)
3. Use the 16-character password WITHOUT spaces
4. Update `EMAIL_PASSWORD` secret in repo settings
5. Check spam/junk folder

**Verification:** Check workflow logs for "Email sent successfully" step

---

### Issue: Workflow Can't Push to Repo

**Problem:** Auto-commit of summary markdown fails with permission error.

**Root Cause:** Repository workflow permissions not set to "Read and write."

**Solution:**
1. Repo Settings → Actions → General → Workflow permissions
2. Select "Read and write permissions"
3. Check "Allow GitHub Actions to create and approve pull requests" (optional)

**Verification:** Run workflow manually, check that `summaries/` directory gets a new file

---

## Quick Reference

| Error | Likely Cause | Quick Fix |
|-------|-------------|-----------|
| 403 on API calls | PAT expired/wrong scopes | Regenerate PAT with `repo` + `read:user` |
| No email received | Wrong App Password | Regenerate at myaccount.google.com/apppasswords |
| Push fails in workflow | Missing write permissions | Settings → Actions → "Read and write permissions" |
| Cron not firing | Workflow not on `main` | Merge to `main` branch |
| Rate limit errors | Too many API calls | Script has built-in exponential backoff |
| Local run only shows one repo | Integration token is repo-scoped | Use PAT in Actions secrets or local env |

---

## Best Practices Learned

- Gmail App Passwords are 16 chars with NO spaces (Google displays them with spaces for readability)
- GitHub cron uses UTC time: `0 3 * * *` = 3:00 AM UTC = 10:00 PM EST
- PyGithub's `get_commits(since=...)` is inclusive of the `since` timestamp
- `workflow_dispatch` is essential for testing without waiting for cron

---
