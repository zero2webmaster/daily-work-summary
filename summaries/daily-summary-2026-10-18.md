<!-- daily-summary/v2 covers="2026-10-18" --><div style="font-size: 18px; line-height: 1.6;"><h1>Daily Work Summary — Sun Oct 18, 2026</h1>
<p><strong>106 commits</strong> across <strong>13 repos</strong></p>
<p>🧠 <strong>Skill Vault:</strong> 194 skills total <em>(Vault stats as of 2026-10-12)</em></p>
<hr />
<h2>zero2webmaster</h2>
<h3>file-server (19 commits)</h3>
<p><em>Secure vault infrastructure and archival capabilities were implemented, along with scripting improvements and documentation updates across multiple session handoffs</em></p>
<ul>
<li>v1.114.0 - Handoff: record Kerry's encrypted vault disk image</li>
<li>v1.114.0 - Session 158 docs: Antelope frozen archive running, handoff</li>
<li>v1.114.0 - Merge pull request #71 from zero2webmaster/freeze-copy</li>
<li>v1.114.0 - freeze_copy.py: cold-archive copy that hashes the source as it reads</li>
<li>v1.113.0 - Session 158 docs: vault backup built, Kerry's key steps, handoff</li>
<li>v1.113.0 - Merge pull request #70 from zero2webmaster/vault-drive-backup</li>
<li>v1.113.0 - Private vault drive backup with a proved read-only key</li>
<li>v1.112.1 - Session 158 docs: tech-debt fixes live, handoff</li>
<li>v1.112.1 - Merge pull request #69 from zero2webmaster/script-env-subsets</li>
<li>v1.112.1 - verify:env-subsets runs on Node 22 and checks the exact error</li>
<li>v1.112.1 - Scripts reach the DB with a DB-only env; titled headers</li>
<li>v1.112.0 - Session 157 docs: private vault live, brand, next-session handoff</li>
<li>v1.112.0 - Merge pull request #68 from zero2webmaster/kerry-brand</li>
<li>v1.112.0 - Kerry Kriger titles and colors on kerrykriger.com</li>
<li>v1.111.2 - Merge pull request #67 from zero2webmaster/provision-vault-steps</li>
<li>v1.111.2 - tenant:provision --vault prints vault-correct next steps</li>
<li>v1.111.1 - Merge pull request #66 from zero2webmaster/env-prefix-hyphen</li>
<li>v1.111.1 - Setup scripts accept a hyphenated tenant name</li>
<li>v1.111.0 - Merge pull request #65 from zero2webmaster/vault-host</li>
</ul>
<h3>pharmies (16 commits)</h3>
<p><em>The medicine tracking application gained capabilities for flexible dosing schedules, exporting data for healthcare providers, and improved usability of the medicine management interface</em></p>
<ul>
<li>v0.1.0 - note why a summary styled as a button came out too tall</li>
<li>v0.1.0 - pause a medicine until a date, tidy the medicine page, and hide the install box on...</li>
<li>v0.1.0 - note Jerald's hydrocortisone is one medicine again in STATUS</li>
<li>v0.1.0 - fix a PDF test that lost a page of text on some dates</li>
<li>v0.1.0 - a dose time can use a different pill, such as a 5 mg pill in the afternoon</li>
<li>v0.1.0 - Download the report as a real PDF, and on a computer download the export files as ...</li>
<li>v0.1.0 - a dose time's amount box says it counts pills, understands "5 mg", and shows what ...</li>
<li>v0.1.0 - Readings: show Saved under the button pressed, ask pulse once, and put Export in t...</li>
<li>v0.1.0 - Queue Kerry's Readings and medicine-page requests ahead of Phase 3 in the handoff</li>
<li>v0.1.0 - Show charts in the printable report: doses taken by week and readings trends</li>
<li>v0.1.0 - Correct the test count in the status file</li>
<li>v0.1.0 - Name the report's PDF pharmies-report-DATE, and plan charts in the report</li>
<li>v0.1.0 - Record the meal rule, every-N-weeks schedules and export in the roadmap, status an...</li>
<li>v0.1.0 - Export for a doctor: share spreadsheet files from the phone, or print a report as ...</li>
<li>v0.1.0 - Let a medicine repeat every few days or weeks, such as an injection every two weeks</li>
<li>v0.1.0 - Add a meal choice: take it, then don't eat for a set number of minutes</li>
</ul>
<h3>z2w-crowdcommerce (13 commits)</h3>
<p><em>Donors can now dedicate personalized messages on virtual bricks within customizable brick-wall campaigns, with staff managing setup and content screening</em></p>
<ul>
<li>v0.37.0 — brick dedications ('In honor of …') on the brick's card, screened by the...</li>
<li>v0.36.0 — donors pick their spot on a brick wall; each gift is one brick sized to ...</li>
<li>v0.35.0 - handoff — wall editor and preview sign-in</li>
<li>v0.35.0 — staff set up brick walls themselves (settings, before/after uploads, sha...</li>
<li>v0.34.2 - changelog test count</li>
<li>v0.34.2 — a signed-out preview link goes to sign-in and back, instead of 'not found'</li>
<li>v0.34.1 - handoff — bricks live, preview link, migration command</li>
<li>v0.34.1 — staff can preview draft campaigns (?preview=1), so the bricks demo can b...</li>
<li>v0.34.0 - bricks go live (migration 0020 applied to production first); grant-page wording as...</li>
<li>v0.34.0 — digital bricks: brick-wall campaigns and the Coyote Hollow demo (migrati...</li>
<li>v0.33.0 - Kerry's 2026-10-18 decisions in ROADMAP; handoff for D2 walkthrough and bricks go-...</li>
<li>v0.33.0 — D2: organizations connect their own Stripe account (restricted key first...</li>
<li>v0.32.1 - D2 Stripe Connect checklist; pilot terms promise our fee is cleared before a disco...</li>
</ul>
<h3>z2w-multi-lingual (13 commits)</h3>
<p><em>A series of quality and translation improvements were deployed, including fixes to prevent translation loss during editing, proper handling of large pages in quality checks, and corrections to cached translations and sitemap handling</em></p>
<ul>
<li>Item 76 live on STF (v0.81.0); /day/ slugs restored and re-queued</li>
<li>v0.81.0 - Editing a page no longer deletes its translations (ROADMAP item 76)</li>
<li>Item 75 confirmed live on STF (v0.80.1, sitemaps return XML)</li>
<li>v0.80.1 - Translated sitemaps load on STF (ROADMAP item 75)</li>
<li>Item 70 confirmed live on STF (v0.80.0, 196 rows Unscored)</li>
<li>v0.80.0 - Pages too large to quality-check are Unscored, not Auto-Approved (ROADMA...</li>
<li>v0.79.0 - WordPress maintenance page no longer fails a job permanently (ROADMAP it...</li>
<li>v0.78.0 - A row checked at write time is not re-judged at serve time (ROADMAP item...</li>
<li>v0.77.0 - ROADMAP item 75: translated sitemaps 404/301 on STF</li>
<li>v0.77.0 - Docs: Search Console results for /es/ and /pt/; item 74 SEO cost</li>
<li>v0.77.0 - Remove unused telemetry class and old flag PNGs</li>
<li>v0.77.0 - Docs: Dr. Kerry / Dr. Kriger glossary rules added on STF; ROADMAP item 74 filed (5...</li>
<li>v0.77.0 - Bulk Tools: fix a wrong word or phrase across cached translations</li>
</ul>
<h3>event-engine (8 commits)</h3>
<p><em>The event management system was enhanced with an organizer-facing events endpoint for chapter reports, a searchable events calendar with improved past-event handling, and updated service authentication configuration</em></p>
<ul>
<li>v0.135.0 - status — grantor service token set on both sides and verified live</li>
<li>v0.135.0 - rebuild so SERVICE_TOKEN_GRANTOR_STF reaches production (Vercel binds env at build...</li>
<li>v0.135.0 docs — changelog, README, status and env example for the organizer events...</li>
<li>v0.135.0 — organizer events endpoint for grantor's chapter reports</li>
<li>v0.134.0 — Ticket Scanner events picked by search with chips, not a checklist</li>
<li>v0.133.1 — a past event shows no "Time to be announced" and no calendar links</li>
<li>v0.133.0 - CLAUDE.md — a new organizer host needs the tenant bucket's CORS entry</li>
<li>v0.133.0 — events calendar; Name section opens read-only and saves the organizatio...</li>
</ul>
<p><strong>z2w-agent-coordination:</strong> 8 coordination commits<br />
<em>More info needed for a summary</em></p>
<h3>docker-z2w-multi-lingual (7 commits)</h3>
<p><em>Per-organization credential storage and spending visibility controls were released</em></p>
<ul>
<li>v1.27.0 - docs: zero2webmaster DeepL key sealed; production Neon password rotated and verifi...</li>
<li>docs: v1.27.0 is live (KEK secret, migration, PR #6 merged, tagged); scratch branc...</li>
<li>v1.27.0 - Merge pull request #6 from zero2webmaster/feat/14.3-credential-vault</li>
<li>v1.27.0 - Per-org provider credential vault (ROADMAP 14.3)</li>
<li>docs: v1.26.0 is live (PR #5 merged, tagged, health verified) [skip ci]</li>
<li>v1.26.0 - Merge pull request #5 from zero2webmaster/feat/14.2c-spend-read</li>
<li>v1.26.0 - GET /api/spend: the org's provider budget before it refuses (ROADMAP 14.2c)</li>
</ul>
<h3>site-control (5 commits)</h3>
<p><em>The content management system now provides more granular control over AI-assisted editing, allowing users to regenerate individual sections and pages with human review before changes take effect</em></p>
<ul>
<li>v0.84.0 - start a new page from one of your existing pages, with AI writing the new wording</li>
<li>v0.83.0 - correct the recorded test count to 3671</li>
<li>v0.83.0 - edit banners, card grids and calls to action by hand; AI can change a section's ba...</li>
<li>v0.82.1 - help text on the AI panels moves behind an "i" info circle</li>
<li>v0.82.0 - ask the AI to change just one block, with review before anything is saved</li>
</ul>
<h3>estate-planning (4 commits)</h3>
<p><em>The application's login and branding were refined, including email delivery improvements and visual consistency across pages</em></p>
<ul>
<li>v0.4.2 - Login works end to end; app renamed Z2W Estate Planning; formatted login ...</li>
<li>v0.4.1 - Logo at the top-left of every page; login emails really send</li>
<li>v0.4.0 - Record the SES sender and region, and the authenticator app as the passkey backup</li>
<li>v0.4.0 - Record that the login test database copy was deleted</li>
</ul>
<h3>z2w-skill-vault (4 commits)</h3>
<p><em>Development work addressed dependencies, formatting issues, and data validation logic across various backend systems</em></p>
<ul>
<li>nextjs-vercel-prod-only-failures §3a: a dependency's lazy createRequire (react-pdf...</li>
<li>html-to-pdf-print-fidelity: pandoc gfm turns dollar amounts into TeX math, mostly ...</li>
<li>rules-are-not-retroactive 6b: the input is mutable too; judge once at write, store...</li>
<li>per-tenant-credential-vault: probe status codes vary by provider; one row per prov...</li>
</ul>
<h3>forms-engine (3 commits)</h3>
<p><em>Conditional logic for grant application questions was refined, and environmental and amphibian-focused questions were added for fiscal sponsor applicants</em></p>
<ul>
<li>v0.1.0 - Record today's session: fiscal-sponsor questions live, conditional questions fixed...</li>
<li>v0.1.0 - Ask fiscal-sponsor applicants about environmental and amphibian work, and when the...</li>
<li>v0.1.0 - Hide conditional questions in the browser until they apply</li>
</ul>
<h3>grantor (3 commits)</h3>
<p><em>Grantee reporting interfaces were enhanced to display chapter events in an editable table format and integrate quarterly report submission capabilities</em></p>
<ul>
<li>v0.135.0 - Widen grantee pages, show chapter events as a table grantees can trim, and add a s...</li>
<li>v0.134.0 - Record that Event Engine's events endpoint and the shared token are live</li>
<li>v0.134.0 - Show a chapter grantee's events from SAVE THE FROGS! Events on their quarterly rep...</li>
</ul>
<h3>marketing-engine (3 commits)</h3>
<p><em>Content management for the marketing engine was migrated from external tools into the project's own database and updated with current information</em></p>
<ul>
<li>v0.1.0 - podcast guest shows moved out of Airtable into the project's own database</li>
<li>v0.1.0 - the software article has Kerry's title, and the Ad Grant walkthrough reflects his ...</li>
<li>v0.1.0 - Kerry's Ad Grant walkthrough, the real holiday shipping dates, and a Zero2Webmaste...</li>
</ul>
<hr />
<p>Daily Work Summary initially created by <a href="https://zero2webmaster.com/kerry-kriger">Zero2Webmaster Founder Dr. Kerry Kriger</a></p>
<p>Contribute to the public repository at: https://github.com/zero2webmaster/daily-work-summary</p>
<p>Need to change the timing or timezone of these emails? <a href="https://github.com/zero2webmaster/daily-work-summary#customizing-the-email-schedule">Click here</a> for instructions.</p>
<p><em>Covers Sun Oct 18, 2026 · generated 2026-10-18 23:28 EDT</em></p></div>