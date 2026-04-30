# Troubleshooting Guide

**Project:** Daily Work Summary
**Last Updated:** 2026-04-30

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

### Issue: Cursor/GitHub App Token Can Only See This Repository

**Problem:** Running the daily summary from a Cursor Cloud automation with `PAT_GITHUB="$(gh auth token)"` fails on `GET /user` with `403 Forbidden`, or `gh repo list zero2webmaster` only returns `zero2webmaster/daily-work-summary`.

**Root Cause:** The Cursor GitHub integration token is a repository-scoped GitHub App token. It is sufficient for git operations in this repo, but it does not have the account-wide `repo` + `read:user` access needed to enumerate all personal and Zero2Webmaster repositories.

**Solution:**
1. Run the production GitHub Actions workflow with the `PAT_GITHUB` repository secret configured.
2. Use a classic PAT or fine-grained token that can read all target personal and organization repositories.
3. Do not rely on the local `gh auth token` inside Cursor Cloud for the all-repos scan.

**Verification:** The workflow log should show `Authenticated as: <github-user>` followed by `Found <N> repositories`, where `N` is more than just this repository.

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
| `gh auth token` sees one repo | Cursor GitHub App token is repo-scoped | Use `PAT_GITHUB` workflow secret instead |
| No email received | Wrong App Password | Regenerate at myaccount.google.com/apppasswords |
| Push fails in workflow | Missing write permissions | Settings → Actions → "Read and write permissions" |
| Cron not firing | Workflow not on `main` | Merge to `main` branch |
| Rate limit errors | Too many API calls | Script has built-in exponential backoff |

---

## Best Practices Learned

- Gmail App Passwords are 16 chars with NO spaces (Google displays them with spaces for readability)
- GitHub cron uses UTC time: `0 3 * * *` = 3:00 AM UTC = 10:00 PM EST
- PyGithub's `get_commits(since=...)` is inclusive of the `since` timestamp
- `workflow_dispatch` is essential for testing without waiting for cron
- Cursor Cloud's built-in GitHub token is not a replacement for the account-wide `PAT_GITHUB` secret.

---
