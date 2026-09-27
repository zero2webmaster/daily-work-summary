<!-- daily-summary/v2 covers="2026-09-26" --><div style="font-size: 18px; line-height: 1.6;"><h1>Daily Work Summary — Sat Sep 26, 2026</h1>
<p><strong>139 commits</strong> across <strong>18 repos</strong></p>
<p>🧠 <strong>Skill Vault:</strong> 180 skills total <em>(Vault stats as of 2026-09-24)</em></p>
<hr />
<h2>zero2webmaster</h2>
<h3>grantor (21 commits)</h3>
<p><em>The grants management system was enhanced to streamline disbursals, grantee communications, and financial record-keeping, including dedicated pages for each payment, improved invitation workflows, and integration with financial tracking</em></p>
<ul>
<li>Bring Save The Frogs Day reports into grantor, add AI advice on final reports...</li>
<li>Switch on project pages for the 113 reports approved before pages existed; me...</li>
<li>Invitation letter: first-name greeting, linked Grants programme, signed by Ke...</li>
<li>Merge Fazle Rabbe's two logins, keep his older address as an alternate; invit...</li>
<li>Merge Biraj's and Sarbani's duplicate grantee logins into the addresses they use</li>
<li>Portal Invitations page: draft, send in batches and check bounces for every p...</li>
<li>Handoff: logins for Kerry's corrected addresses, the no-email list, and the i...</li>
<li>Each disbursal gets its own page; readable grantee addresses with a disbursal...</li>
<li>Disbursal page leads with what was sent; letters only on the first send; uplo...</li>
<li>Disbursals: one page to record a disbursal, grantee logins required, transfer...</li>
<li>Grantees upload signed W-9s encrypted in grantor; clearer W-9 box; countries ...</li>
<li>W-9 rule for US individuals, a page for each grantee letter, and a full Sent ...</li>
<li>Transfer form asks whose account paid and who sent it; grantee form stops ask...</li>
<li>Countries now carry an ISO code beside the name, filled at every write</li>
<li>Send-the-funds queue, one-line pending emails that stay on screen, readable g...</li>
<li>A recorded payment is now sent to financial-engine as an expense; ledger coun...</li>
<li>Handoff: check in with Kerry on the two pending payments on Sep 30</li>
<li>Transfer page: ledger first, pasted Wise text under its own heading</li>
<li>Handoff: who to pay next, and how disbursals now reach the ledger</li>
<li>Recording a transfer now puts the payment in the disbursals ledger itself</li>
<li>A transfer marked Sent now says whether the payment is in the money ledger</li>
</ul>
<h3>z2w-skill-vault (21 commits)</h3>
<p><em>Multiple areas of the application were refined, including form standards, media embedding, content migration, and data handling infrastructure</em></p>
<ul>
<li>file-server-service-api: document ?w= public image variants (file-server v1.9...</li>
<li>human-readable-urls: one DB-side allocator for multi-writer records; redirect...</li>
<li>lightbox + file-server skills: the slideshow variant, and copy site-control's...</li>
<li>list-filter-sort-search: a Question | Answer table's row headers need their o...</li>
<li>async-action-feedback §3d-bis: a reset select goes to its FIRST option, and t...</li>
<li>form-field-standards: file uploads must show their size/type limit and check ...</li>
<li>wordpress-learndash-migration §14: LearnDash progress has two records and the...</li>
<li>youtube-embed-facade §3b: the three related-videos methods, and how the Enhan...</li>
<li>youtube-embed-facade: suggested videos must be the org's own (rel=0 is not en...</li>
<li>vercel-isr-write-budget: force-cache is not forever — the team-shared Data Ca...</li>
<li>form-field-standards: short fields share a row, two-up, and wrap on a phone</li>
<li>wordpress-content-harvest §13.2a: a domain-restricted Vimeo embed answers 403...</li>
<li>New skill youtube-embed-facade: Kerry's branded click-to-play YouTube player ...</li>
<li>rocket-net-mysql-ssh-tunnel: the browser WP-CLI console rejects wp eval; use ...</li>
<li>wordpress-content-harvest §25: a click-to-play YouTube poster has no iframe, ...</li>
<li>project-migration-audit: diff uninstall.php against the activator (tables, op...</li>
<li>Add a copy-ready reference for the "did you mean …@gmail.com?" email check</li>
<li>ROADMAP: Kerry declined a body-budget exemption for zero-is-not-a-pass (HOLD ...</li>
<li>instantiate-z2w-project v1.43.1: the index-to-entry rule is now enforced by a...</li>
<li>sentry-runtime-errors: §3a — email link scanners spend the org's replay quota</li>
<li>save-the-frogs-blog-post: "first annually celebrated amphibian conservation e...</li>
</ul>
<h3>financial-engine (19 commits)</h3>
<p><em>Bank import and grant payment tracking capabilities were enhanced to capture settlement details, payment origins, and account ownership across multiple financial integrations</em></p>
<ul>
<li>v0.36.0 - Bank import: settlement outcome, and the bookkeeper's account numbe...</li>
<li>v0.35.1 - Bank import: royalties (CARD.com, UMB card partner) are Licensing i...</li>
<li>v0.35.0 - Bank of America export: read, checked against its own totals, and s...</li>
<li>docs: crypto is a donation at cash-out (Kerry's ruling); donate.gg is an ordi...</li>
<li>docs: bank statement import design, and Phase 17 - streamlining the annual bo...</li>
<li>docs: handoff - importer first, donate.gg identified, Oct 3 charitybridgefund...</li>
<li>docs: handoff - the Bank of America export arrived; its layout and a first re...</li>
<li>docs: troubleshooting - retiring an unsent Airtable update must carry its fie...</li>
<li>docs: v0.34.0 deployed and migration 0008 applied to STF; handoff names Zero2...</li>
<li>v0.34.0 - what SAVE THE FROGS! owes, and recording the repayment</li>
<li>docs: Stripe replay for all three accounts passes on v0.33.0; replay mode swi...</li>
<li>docs: v0.33.0 deployed to production, writing to Neon only; Stripe replay key...</li>
<li>docs: Wise payment option rename and Reimbursements cleanup confirmed live in...</li>
<li>docs: roadmap - reimbursements page goes in org-hq behind a finance permission</li>
<li>v0.33.0 - transferred by, and cash is always someone's own money</li>
<li>docs: troubleshooting - why a second Airtable correction was silently dropped</li>
<li>docs: handoff - grantor token name and the paidFrom dependency before go-live</li>
<li>v0.32.0 - every grant payment says whose money it was, and what STF now owes</li>
<li>v0.31.0 - grant payments arrive as expenses without Kerry re-typing them</li>
</ul>
<h3>forms-engine (18 commits)</h3>
<p><em>Forms for newsletter signups and cryptocurrency onboarding were built, refined, and published alongside improvements to form submission handling and display</em></p>
<ul>
<li>Mark the newsletter and crypto onboarding forms as switched over on savethefr...</li>
<li>Stop embedded forms from sitting on empty space</li>
<li>Close the session: hand off the two page swaps and the replies to watch</li>
<li>Left-align the questions on a submission's answers page and space them from t...</li>
<li>Record the key revoke, phone checks and thank-you work in the handoff</li>
<li>Refuse impossible phone numbers, format them per country, and give every form...</li>
<li>Record the passing newsletter test and the crypto form fixes in the handoff</li>
<li>Fix the website field that blocked submitting, and polish the crypto form</li>
<li>Publish the newsletter and crypto onboarding forms, and name the org in the f...</li>
<li>Add a Submissions page so staff can read what people typed on every form</li>
<li>Require all six confirmation statements on the crypto onboarding form</li>
<li>Turn the crypto form's currency question into a dropdown, and record what sti...</li>
<li>Build the crypto onboarding form, and find the live page was never showing it</li>
<li>Design how other apps embed our forms: iframe, other domains, and a signed vi...</li>
<li>Point the next session at the consent check, then the crypto onboarding form</li>
<li>Record the newsletter session: form built, switch waiting on the consent perm...</li>
<li>Build the twice-weekly newsletter form, but hold the page switch until we can...</li>
<li>Record that the old March forms are off and the organizer page now redirects ...</li>
</ul>
<h3>courses-engine (14 commits)</h3>
<p><em>Student progress import and course content management were enhanced to support multiple academies with their own separate data sources and WordPress instances</em></p>
<ul>
<li>courses-engine: v0.56.0 — student progress import can read LearnDash's own pe...</li>
<li>courses-engine: v0.55.1 — SAVE THE FROGS! progress dry run: 420 found, 1,043 ...</li>
<li>courses-engine: progress import keeps a separate, stamped cache per academy</li>
<li>courses-engine: v0.55.0 — YouTube suggestions come only from the academy's ow...</li>
<li>courses-engine: v0.54.0 — SAVE THE FROGS! keeps YouTube, SoundCloud and Slide...</li>
<li>courses-engine: record Kerry's decision to keep YouTube, SoundCloud and Slide...</li>
<li>courses-engine: record that every SAVE THE FROGS! course is imported and the ...</li>
<li>courses-engine: v0.53.1 — scripts use each academy's own WordPress; all SAVE ...</li>
<li>courses-engine: the migration check no longer counts the YouTube Subscribe ba...</li>
<li>courses-engine: v0.53.0 — the LearnDash importer works for SAVE THE FROGS!</li>
<li>courses-engine: v0.52.1 — the health check now says which version is deployed</li>
<li>courses-engine: v0.52.0 — each academy can have its own Contact Registry key,...</li>
<li>courses-engine: record that Aharon's academy is live and what is left</li>
<li>courses-engine: v0.51.0 — an academy on its own domain opens on its courses, ...</li>
</ul>
<h3>leaderboard (7 commits)</h3>
<p><em>The lesson page was rebuilt with improved usability, and the system's data synchronization was accelerated through parallel processing</em></p>
<ul>
<li>docs: handoff for v2.36.0, the lesson page rebuild</li>
<li>v2.36.0 - The lesson page: readable addresses, Save lands on it, Edit button</li>
<li>docs: Kerry decided a private class stays at one student; families deferred</li>
<li>v2.35.1 - Saving a lesson no longer erases what you typed</li>
<li>docs: students have left LearnDash (130 courses-engine completions vs 4); 110...</li>
<li>docs: v2.35.0 — the parallel poll is live, 15m42s → 4m20s with identical counts</li>
<li>v2.35.0 - The nightly LearnDash poll runs four requests at a time instead of one</li>
</ul>
<h3>event-engine (6 commits)</h3>
<p><em>Photo gallery management and email presentation were enhanced with captions, client-side resizing, improved editing workflows, and organizational branding across communications</em></p>
<ul>
<li>event-engine: handoff for session event-engine-20260926a (v0.78.2, v0.79.0)</li>
<li>event-engine: v0.79.0 — the org's logo, linked home, at the top of every emai...</li>
<li>event-engine: v0.78.2 — drag a gallery photo by the picture itself, show the ...</li>
<li>event-engine: v0.78.1 — clean gallery tiles; click a photo for an Edit photo ...</li>
<li>event-engine: v0.78.0 — per-photo captions (migration 0024), drafted from the...</li>
<li>event-engine: v0.77.0 — resize photos in the browser before upload (site-cont...</li>
</ul>
<h3>org-hq (5 commits)</h3>
<p><em>A communications series was published with article content added to the website and tracked in the database</em></p>
<ul>
<li>v0.61.0 - Reviewers can go through the misnomer posts at /misnomers, and volu...</li>
<li>org-hq: the /communications series page is live and recorded in Airtable; its...</li>
<li>org-hq: the /communications series page intro is approved and its WordPress c...</li>
<li>org-hq: the first communications article is live and recorded in Airtable; th...</li>
<li>v0.60.1 - The three articles are on savethefrogs.com as drafts, with Kerry's ...</li>
</ul>
<h3>z2w-agent-command-center (5 commits)</h3>
<p><em>The interface was refined to improve clarity of agent status and test metrics, while underlying caching issues were resolved</em></p>
<ul>
<li>Docs - Sentry -D ignored until escalating; /message stays dynamic</li>
<li>v0.65.1 - The Target box shows a quiet agent's name without cutting it off</li>
<li>v0.65.0 - The tests page shows how each project's test count has grown</li>
<li>v0.64.0 - The Decisions page cache problem was Vercel's shared cache dropping...</li>
<li>v0.63.0 - The message picker says which agents have not run lately; a redeplo...</li>
</ul>
<h3>z2w-web-events (5 commits)</h3>
<p><em>A plugin was systematically deactivated and removed across multiple sites with documentation of the decommissioning process</em></p>
<ul>
<li>RETIREMENT.md: plugin deleted from all three sites</li>
<li>RETIREMENT.md: savethefrogs.com measured clear (0 registrations, only Kerry's...</li>
<li>RETIREMENT.md: Kerry requires approval for every follow-up; two sites deleted...</li>
<li>STATUS.md: Session 54 — deactivated everywhere, delete checklist in RETIREMEN...</li>
<li>RETIREMENT.md: where each capability went, decommission ledger, delete checklist</li>
</ul>
<h3>audit-engine (3 commits)</h3>
<p><em>The z2w-web-events plugin was retired across all sites and associated documentation was completed</em></p>
<ul>
<li>z2w-web-events prompt v2: plugin now off all three sites, so the checklist is...</li>
<li>Next session: scope Kerry's pre-launch procedure before plugin #4</li>
<li>Migration prompt for z2w-web-events: finish its retirement doc so deletion is...</li>
</ul>
<h3>support-desk (3 commits)</h3>
<p><em>The system now integrates artificial intelligence for message triage and drafting, with improved handling of communication failures and email delivery</em></p>
<ul>
<li>v0.19.0 — The desk can talk to the AI engine now, and when it can't, nothing ...</li>
<li>v0.18.0 — Real mail is on the desk for the first time, and the Phase 2 tables...</li>
<li>v0.17.1 — Phase 2 is designed: AI triage and drafts, and why an AI category m...</li>
</ul>
<h3>cursor-project-templates (2 commits)</h3>
<p><em>Project templates were updated to support external user access and compatibility with the latest platform version</em></p>
<ul>
<li>cursor-project-templates: record that @zero2webmaster/templates 0.4.0 is publ...</li>
<li>cursor-project-templates: v2.20.0 / WP v3.8.0 — apps with outside users get a...</li>
</ul>
<h3>site-control (2 commits)</h3>
<p><em>The site layout was adjusted so that content bands extend across the full window width while keeping text centered</em></p>
<ul>
<li>site-control: session handoff — bands are full width on z2w.us, card icons next</li>
<li>site-control: bands now run the full width of the window, words stay in the c...</li>
</ul>
<h3>static-sites (2 commits)</h3>
<p><em>Navigation features were gated behind a feature flag and included in the latest release build</em></p>
<ul>
<li>Session 56 wrap-up: STATUS, ROADMAP, HANDOFF, TROUBLESHOOTING</li>
<li>v1.46.0 - The navigation kit is gated and in the build</li>
</ul>
<h3>z2w-ai-suite (2 commits)</h3>
<p><em>Documentation was updated to record capabilities for homes and segment tools outside the main migration dashboard</em></p>
<ul>
<li>Docs: MIGRATION rows 26 and 44 — segment tools not in videomigrator-dashboard...</li>
<li>Docs: record Kerry's homes for the unhomed capabilities (2026-09-26)</li>
</ul>
<h3>z2w-starter-kit (2 commits)</h3>
<p><em>Testing was improved to ensure the skill's version tracking remains consistent across its index and history records</em></p>
<ul>
<li>ci: skip runs when a push changes only this repo's session logs</li>
<li>test: the skill's version index and version history must match, row for row</li>
</ul>
<h3>z2w-templates (2 commits)</h3>
<p><em>The synchronization system was updated to refresh data from the current working copy</em></p>
<ul>
<li>0.4.0</li>
<li>sync: 2026-09-26 — refresh from working copy</li>
</ul>
<hr />
<p>Daily Work Summary initially created by <a href="https://zero2webmaster.com/kerry-kriger">Zero2Webmaster Founder Dr. Kerry Kriger</a></p>
<p>Contribute to the public repository at: https://github.com/zero2webmaster/daily-work-summary</p>
<p>Need to change the timing or timezone of these emails? <a href="https://github.com/zero2webmaster/daily-work-summary#customizing-the-email-schedule">Click here</a> for instructions.</p>
<p><em>Covers Sat Sep 26, 2026 · generated 2026-09-27 04:01 EDT</em></p></div>