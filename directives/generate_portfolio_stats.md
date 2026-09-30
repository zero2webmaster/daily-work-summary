# Directive: Generate Portfolio Stats

**Version:** 1.1.0 | **Added:** 2026-06-18 (project v1.9.0) | **Updated:** 2026-09-30 (project v1.14.0: data lines split out of `loc`)

## Goal

Produce a monthly, machine-readable snapshot of every Z2W repository's size —
lines of code (LoC) and documentation/comment lines — and commit it as a
versioned JSON artifact the command center (`agents.z2w.us`) reads and renders
in a portfolio stats panel.

This fulfills the no-urgency bulletin ask from `z2w-agent-command-center`
(filed 2026-06-12, amended 2026-06-17). No rush — the consuming dashboard panel
is pre-deploy.

## Where the artifact lives (critical)

The JSON is committed to the **`zero2webmaster/z2w-agent-coordination`** repo at:

```
stats/portfolio-YYYY-MM.json
```

**NOT** into the daily-work-summary repo. The command center's GitHub token is
fine-grained and scoped to the coordination repo only, so it cannot read an
artifact stored anywhere else. `stats/` in the coordination repo already holds
`skill-vault.json` (schema `skill-vault-stats/v1`); this is the second artifact
in that directory.

## Tools

- **`.github/scripts/portfolio_stats.py`** — computes the stats and writes the
  JSON to the path given by `PORTFOLIO_STATS_OUTPUT`.
- **`.github/workflows/portfolio-stats.yml`** — monthly cron (`0 6 1 * *`) +
  `workflow_dispatch`. Clones the coordination repo, runs the script against it,
  commits + pushes the artifact there.
- **`cloc`** — installed via `apt-get` in the workflow; counts code vs comment
  lines per language. (`scc` / `tokei` are drop-in alternatives.)

## How it works

1. Enumerate every repo via PyGithub (`affiliation="owner,organization_member"`),
   same set the daily summary walks.
2. For each repo: shallow-clone it, run `cloc --json` (with the exclusions
   below), then split the per-language breakdown honestly:
   - **`loc`** = code lines in *programming* languages (prose and data languages excluded).
   - **`doc_lines`** = all code comments **plus** the lines of prose/doc files
     (Markdown, Text, reStructuredText, AsciiDoc, …).
   - **`data_lines`** = lines in data/markup languages (`DATA_LANGUAGES`: JSON,
     JSON5, YAML, CSV, XML, SVG, XSD, XSLT). Reported separately so nothing is
     hidden, but never counted as code.
   `last_commit_date` comes from `pushed_at`; `status` is `archived` if the repo
   is archived else `active`.

   **cloc exclusions (critical for true numbers):**
   - `--exclude-dir=.specstory,node_modules,vendor,third_party,third-party,dist,build,.next,out,coverage,__pycache__,.venv,venv`
   - `--not-match-f` (`NOT_MATCH_F`, matched against each file's **basename**):
     minified/bundled assets (`*.min.js`, `*-min.css`, `*.bundle.js`),
     lockfiles (`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`,
     `composer.lock`, `bun.lock`), and Drizzle migration snapshots
     (`NNNN_snapshot.json`, e.g. `drizzle/meta/0007_snapshot.json`).

   These exclude things that are committed but are **not the repo's own authored
   source**: AI chat transcripts (`.specstory`), vendored third-party libraries,
   build output, and minified/bundled assets. Discovered 2026-06-18: without
   excluding `.specstory`, that one directory was **85% of z2w-ai-suite's
   apparent 1.3M "lines of code"** (1.46M lines of committed chat logs). The real
   plugin is a fraction of that. Always exclude these for honest counts.

   **Why data lines are split out (2026-09-30, v1.14.0):** Kerry asked why
   `contact-registry` had the most code in the portfolio (163,469 "lines").
   116,261 of them were one Airtable inventory dump,
   `directives/discovery/airtable-contact-inventory.json`. `z2w-agent-command-center`
   measured that about 30% of the portfolio's non-prose lines were JSON,
   lockfiles and CSV/SVG/XML, mostly Drizzle snapshots, `package-lock.json`
   and fixtures. From the **2026-10** snapshot on, `loc` means code only.
3. Aggregate: `repo_count`, `active_repo_count`, `archived_repo_count`,
   `total_loc`, `total_doc_lines`, `total_data_lines`.
4. Write JSON, commit to the coordination repo with a rebase-and-retry push
   (the bulletin clone is written by many agents, so a concurrent push can grab
   the ref lock first — same race the v1.7.0 backfill hit).

## Output schema — `portfolio-stats/v1`

The schema string stays `v1` on purpose. The command center's parser
(`src/lib/portfolio-stats.ts`) returns nothing for any schema other than
`portfolio-stats/v1`, so bumping it would blank the dashboard. The 2026-10
change only **adds** fields (`loc_method`, `data_lines`, `total_data_lines`),
which older readers ignore. `loc_method: "code-only"` marks files that use the
new counting; files for 2026-06 → 2026-09 have no `loc_method`, and their `loc`
still includes data files and lockfiles, so expect totals to drop by roughly a
third between the 2026-09 and 2026-10 snapshots. That drop is the counting
method changing, not deleted work.

```json
{
  "schema": "portfolio-stats/v1",
  "generated_for": "daily-work-summary",
  "period": "2026-06",
  "generated_at": "2026-06-18T12:00:00Z",
  "loc_method": "code-only",
  "aggregate": {
    "repo_count": 26,
    "active_repo_count": 24,
    "archived_repo_count": 2,
    "total_loc": 123456,
    "total_doc_lines": 23456,
    "total_data_lines": 4321
  },
  "repos": [
    {
      "name": "leaderboard",
      "owner": "zero2webmaster",
      "loc": 8421,
      "doc_lines": 1203,
      "data_lines": 610,
      "last_commit_date": "2026-06-17",
      "status": "active"
    }
  ]
}
```

`repos` is sorted by `loc` descending. A repo that fails to clone/measure is
still listed with `loc`/`doc_lines`/`data_lines` = `null` and an `error` note, so the
`repo_count` always reflects the true portfolio size.

**Stable path + field schema matter more than formatting.** Adding a field is
safe. If a field is ever removed or renamed, bump the `schema` version, but only
after the command center accepts the new version, AND signal it in the bulletin
(`projects/daily-work-summary.md`) so the command center's read path doesn't
silently break.

## Resilience posture

- The monthly job is a **separate workflow** from the nightly email, so nothing
  here can ever affect Kerry's morning digest.
- Per-repo work is fully exception-wrapped: a single repo that fails to clone or
  measure is recorded with null metrics, not allowed to abort the run.
- `classify_cloc()`, `NOT_MATCH_F` and `build_portfolio_stats()` are pure/offline
  and covered by `execution/test_portfolio_stats.py` (48 checks), which runs in
  the `Tests` workflow.

## Configuration

- **Secret `PAT_GITHUB`** (already set) — must have `repo` (read all repos +
  **write** to the coordination repo) and `read:user`. Reused from the nightly job.
- **`workflow_dispatch` input `month`** (optional `YYYY-MM`) — override the
  snapshot label; blank = current UTC month. The script also honors `STATS_MONTH`.

## Run it manually

Actions tab → **Portfolio Stats** → Run workflow (optionally set `month`).

Local dry run (writes under `./stats/`):

```bash
source venv/bin/activate
PAT_GITHUB=ghp_xxx python .github/scripts/portfolio_stats.py
```

## Edge cases / notes

- cloc runs over the **committed** files in a shallow clone. Committed vendored
  libraries, build output, `.specstory` chat transcripts, and minified assets
  are excluded via `--exclude-dir` / `--not-match-f` (see "How it works"), so
  they don't inflate the counts. If a new repo introduces a vendored directory
  under a different name, add it to `EXCLUDE_DIRS` in `portfolio_stats.py`.
  A new kind of generated file goes in `NOT_MATCH_F`; a new data format goes in
  `DATA_LANGUAGES` (use cloc's language name, e.g. `JSON`, `YAML`).
- Empty repos (no source files) cloc-measure to `0/0` — recorded, not errored.
- Cadence is monthly by design; the artifact is a size **snapshot**, not a
  monthly delta, so the `period` label is just "when this snapshot was taken."
