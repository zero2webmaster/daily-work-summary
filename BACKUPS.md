# Backup Plan — daily-work-summary

> 📦 **Delivered 2026-09-22 by `z2w-starter-kit` v0.37.0** to a repo scaffolded before this
> file joined the Z2W project standard. It is an **unfilled stub** — nothing in it was
> measured from this repo. Fill it in, or mark it N/A and say why.

> A first-class, tracked artifact for every Z2W project. State here what parts
> of this project need backups, which are actually backed up, how, and when each
> was last verified. Keep it up to date.

**Project:** daily-work-summary
**Status:** Stub — fill in each surface below (or mark N/A).
**Last Updated:** 2026-09-22

---

## Backup surfaces

For each surface: whether it needs a backup, whether one exists, the
method/destination, the cadence, and when it was last verified.

| Surface | Needs backup? | Backed up? | Method / destination | Cadence | Last verified |
|---|---|---|---|---|---|
| Source code | Yes | | GitHub (`zero2webmaster/daily-work-summary`) | on push | |
| Database (e.g. Neon Postgres) | | | nightly `pg_dump` → R2 / Backblaze | | |
| Object storage (e.g. Backblaze B2) | | | mirror → Cloudflare R2 | | |
| Secrets / env vars | | | (where are they recoverable from?) | | |
| Other (config, DNS, …) | | | | | |

## Restore test

A backup you have never restored from is a hope, not a backup. Note the last
time a restore was actually exercised:

- **Last restore drill:** ______________

---

## Status tracking

Mirror the high-level state to the project inventory's `backup_plan` field. The
command center can then surface each project's backup status / last-completed.

---

*Scaffolded 2026-09-22 via [[instantiate-z2w-project]] — mirrored by `@zero2webmaster/starter-kit`.*
