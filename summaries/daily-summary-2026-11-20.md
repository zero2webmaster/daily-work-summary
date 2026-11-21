<!-- daily-summary/v2 covers="2026-11-20" --><div style="font-size: 18px; line-height: 1.6;"><h1>Daily Work Summary — Fri Nov 20, 2026</h1>
<p><strong>109 commits</strong> across <strong>15 repos</strong></p>
<p>🧠 <strong>Skill Vault:</strong> 7 improved today · 221 skills total</p>
<hr />
<h2>zero2webmaster</h2>
<h3>videomigrator-engine (24 commits)</h3>
<p><em>Video content and associated metadata are being migrated from Vimeo to Bunny storage, with captions, chapters, and customer libraries reorganized as part of the transition</em></p>
<ul>
<li>v10.56.0 - Handoff: test database copy deleted; no customer has a video waiting to move yet</li>
<li>v10.56.0 - Each customer's Bunny library is stored in Neon, so their videos go to ...</li>
<li>v10.55.0 - Note why a Vimeo Free account's videos cannot be downloaded through the API</li>
<li>v10.55.0 - Handoff: the July 3 2024 Janasamohini private lesson is on Bunny for Kerry to watch</li>
<li>v10.55.0 - Starting a migration from the dashboard no longer touches Airtable</li>
<li>v10.54.0 - Handoff: tags pushed, file-server's VideoMigrator file area waits on Kerry merging...</li>
<li>v10.54.0 - Merge remote-tracking branch 'origin/main' into claude/phone-coordination-captions...</li>
<li>v10.54.0 - Record the caption catch-up on Bansuri Bliss and the merge to main</li>
<li>Merge: customers' existing Vimeo captions move to Bunny (v10.54.0), on Kerry's OK</li>
<li>v10.54.0 - Copy captions for a whole connected library in one run</li>
<li>v10.54.0 - Customers' existing Vimeo captions move to Bunny with their videos</li>
<li>v10.53.1 - Stop doubling the words 'auto-generated' in the caption label</li>
<li>v10.53.1 - Give automatic captions a readable name in Bunny's caption menu</li>
<li>v10.53.1 - Bring customers' existing Vimeo captions over to Bunny when their videos move</li>
<li>v10.53.1 - Handoff: report wording is live; the version tag waits for the laptop</li>
<li>v10.53.1 - Plan the next build: bring customers' existing Vimeo captions over to Bunny when w...</li>
<li>v10.53.1 - Merge the report PDF wording (captions, chapters, Kerry's signature) and the Clip ...</li>
<li>v10.53.1 - Record that Kerry is the Clip Compiler's only user for now, with his later pricing...</li>
<li>v10.53.1 - The report PDF says captions and chapters work on any Bunny plan, and i...</li>
<li>v10.53.0 - Record Kerry's Clip Compiler decisions: finished videos go to File Server and the ...</li>
<li>v10.53.0 - A folder of concert or trip clips becomes one smooth video (command-lin...</li>
<li>v10.52.0 - Handoff: Kerry approved a simpler website estimator; sent to the website agent</li>
<li>v10.52.0 - Handoff: the library report now runs on connect and emails the customer and Kerry</li>
<li>v10.52.0 - A customer who connects Vimeo gets their library report by email, and s...</li>
</ul>
<h3>grantor (20 commits)</h3>
<p><em>The application system was enhanced with improved data collection fields, optional AI review capabilities, better database connection handling, and new analytics features to track grant spending</em></p>
<ul>
<li>v0.209.0 - Each chapter event now asks how many times it happens and the participants' ages; ...</li>
<li>v0.208.0 - Each chapter event now asks when, where, who is hosting it and how many people are...</li>
<li>v0.207.0 - The chapter grant form now needs a sign-in and an active SAVE THE FROGS! membership</li>
<li>v0.206.0 - Applicants choose a quick AI review or a full one that also reads their attached f...</li>
<li>v0.205.1 - The applicant's AI review no longer fails with "came back in a form we could not r...</li>
<li>v0.205.0 - Roadmap: the applicant's AI review should read their attached files (next session'...</li>
<li>v0.205.0 - Applicants can ask for an optional AI review of their chapter application before t...</li>
<li>v0.204.1 - Other funding asks whether it is cash or goods and services, and has a box for any...</li>
<li>v0.204.0 - Chapter form asks whether the activities earn revenue and whether anyone else is f...</li>
<li>v0.203.1 - Sidebar group headings are bold, black and the same size as their links</li>
<li>v0.203.0 - Sidebar regrouped by what is in each group, breadcrumbs on every staff page, and W...</li>
<li>v0.202.2 - A database connection that drops while in use is also handled now, not only an idl...</li>
<li>v0.202.1 - Application page names the grant type under the applicant's name; the comment for ...</li>
<li>v0.202.0 - Old applications' budgets are sorted into expense categories for our statistics, s...</li>
<li>v0.201.1 - A database connection Neon closed while idle no longer crashes the page; it reconn...</li>
<li>v0.201.0 - Applicant goal shown on the Edit My Application page too; Printed Materials help a...</li>
<li>v0.200.3 - Chapter form shows the applicant's goal beside the logo, as a trial before adding ...</li>
<li>v0.200.2 - Chapter form's Executive summary help says what reviewers need; Sarbani's Q4 budge...</li>
<li>v0.200.1 - Handoff: word-break fix, and the open question about Sarbani's uncategorized budge...</li>
<li>v0.200.1 - Dashboard bar labels break only between words, so "Chapter Administrative Grant" n...</li>
</ul>
<h3>forms-engine (12 commits)</h3>
<p><em>Feedback and sign-up forms were added across multiple applications with email delivery through Amazon SES</em></p>
<ul>
<li>v0.1.0 - App feedback form is live; record the SES setup</li>
<li>v0.1.0 - Record the SES sign-in and the free-report test result</li>
<li>v0.1.0 - Zero2Webmaster review queue sign-in, sent through Amazon SES</li>
<li>v0.1.0 - Record the app feedback form and what it waits on</li>
<li>v0.1.0 - App feedback form for every Zero2Webmaster app's footer</li>
<li>v0.1.0 - Letter of support: the confirmation says Dr. Kriger, not Kerry</li>
<li>v0.1.0 - Record the letter-of-support test result and v2</li>
<li>v0.1.0 - Letter of support: what it's for, attachments, and the delivery fix Kerry's test f...</li>
<li>v0.1.0 - Record the letter-of-support form and the VideoMigrator DNS check</li>
<li>v0.1.0 - Letter-of-support request form, delivered to org-hq</li>
<li>v0.1.0 - Record the VideoMigrator free-report form and what it waits on</li>
<li>v0.1.0 - VideoMigrator free-report sign-up form, a real daily entry cap, and "Thank you!" h...</li>
</ul>
<h3>z2w-skill-vault (9 commits)</h3>
<p><em>Authentication sign-in flow was reorganized, and multiple infrastructure areas including file handling, browser testing, and monitoring were corrected or improved</em></p>
<ul>
<li>z2w-magic-link-auth 11.6: sign-in email order is button, then code with where to t...</li>
<li>Skill-listing trial closed: keep the 1% default; button-visibility description bac...</li>
<li>worktree-status reads file ages correctly on Linux; commits that add merge-conflic...</li>
<li>Two cloud-session traps: a depth-1 clone is single-branch, and stat -f || stat -c ...</li>
<li>z2w-magic-link-auth: the check-email screen must be true for every visitor, and th...</li>
<li>driving-a-real-browser: find the Playwright Chromium build instead of hard-coding ...</li>
<li>callout-blocks: a mark in the margin (i / ! / ✓ / ? / “) is the standard replaceme...</li>
<li>Actions concurrency groups keep only one queued run, so a global group drops event...</li>
<li>uptime-kuma-monitor §9.4a: the first retention cut balloons the WAL; truncate + VA...</li>
</ul>
<h3>org-hq (7 commits)</h3>
<p><em>Users can now have Ask, a conversational tool, build and maintain personalized memory profiles about them from documents or conversation, retrieve what Ask remembers, and receive sourced answers based on that memory</em></p>
<ul>
<li>v0.138.0 - Ask answers questions about you from your memory note, and shows a sour...</li>
<li>v0.137.1 - People can find what Ask remembers about them (menu link + link on the ...</li>
<li>v0.137.0 - Start your Ask memory from a document (paste a bio, CV or application, ...</li>
<li>v0.136.0 - per-person memory is live (tenant migration 0043 applied to both organizations)</li>
<li>v0.136.0 - Ask remembers each person (automatic note, seen by them and super-admins)</li>
<li>v0.135.1 - The chat microphone is a circle inside the box, bottom right, like Agen...</li>
<li>v0.135.0 - Ask takes long pastes (20,000 characters) and has a speak button</li>
</ul>
<h3>videomigrator-dashboard (7 commits)</h3>
<p><em>Sign-in experience was improved to offer multiple authentication methods and clearer code entry, while account security was enhanced to prevent user enumeration</em></p>
<ul>
<li>v1.34.0 - Sign-in emails put the button first, then the code with a page to type i...</li>
<li>Handoff: v1.33.0 live (typed sign-in code), forms-engine test explained, Clip Comp...</li>
<li>v1.33.0 - Sign in by typing the 8-digit code from the email, as well as by the link</li>
<li>v1.32.0 - Record the Neon table that holds each customer's Bunny library (already applied by...</li>
<li>Handoff: v1.32.0 live, migration 0024 on main, sign-up token set both sides, test ...</li>
<li>v1.32.0 - Free-report sign-up (dashboard half), short report links, Kerry's email ...</li>
<li>Handoff: v1.31.0 live, migration 0023 on main, callback token set, test branch del...</li>
</ul>
<h3>backup-engine (5 commits)</h3>
<p><em>Backup functionality for the Hetzner translation server was implemented with monitoring and documentation established</em></p>
<ul>
<li>v0.42.0 - handoff starting prompt updated for monitor 111</li>
<li>v0.42.0 - Hetzner backup's Kuma monitor is 111, heartbeat verified</li>
<li>v0.42.0 - status, roadmap and handoff for the Hetzner backup going live</li>
<li>v0.42.0 - capability list (docs/CAPABILITIES.md), first pass from workflows and changelog</li>
<li>v0.42.0 - Back up the Hetzner translation server's key files every week</li>
</ul>
<h3>courses-engine (5 commits)</h3>
<p><em>Educational lesson materials for a grant program were developed and organized, with planning and refinement around lesson structure, budget content, and applicant information handling</em></p>
<ul>
<li>v0.93.0 - Draft three SAVE THE FROGS! applicant lessons: answering the reviewer's questions,...</li>
<li>v0.93.0 - Lesson plan: budget becomes its own lesson, AI lesson retitled, April lesson left ...</li>
<li>v0.93.0 - Lesson plan: no applicant names</li>
<li>v0.93.0 - Plan for the SAVE THE FROGS! applicant lessons, and a running list of lesson-worth...</li>
<li>v0.93.0 - Draft of a new SAVE THE FROGS! grant lesson, to be built in the lesson editor once...</li>
</ul>
<h3>file-server (5 commits)</h3>
<p><em>File storage and migration handling were improved to skip incomplete uploads and support organizational moves to external backup services</em></p>
<ul>
<li>v1.147.1 - docs: session 193 — kerry tenant moved to Kerry's personal Backblaze, verified</li>
<li>v1.147.1 - kerry leaves the weekly manifest job after its bucket move</li>
<li>v1.147.1 - Moving an organization's files skips uploads that never finished (#110)</li>
<li>docs: session 192 — v1.147.0 live; kerry tenant move decided</li>
<li>v1.147.0 - A VideoMigrator organization; lighter images and favicons (#109)</li>
</ul>
<h3>z2w-crowdcommerce (5 commits)</h3>
<p><em>The application now sends donation thank-you emails through the email system, and performance was improved by reducing icon file sizes</em></p>
<ul>
<li>v0.78.1 - ROADMAP lists next session's four items (thank-you switch-on walkthrough, challeng...</li>
<li>v0.78.1 — tab icon asks File Server for a 32px copy (home-screen 180px) instead of...</li>
<li>v0.78.0 - Merge cloud session givingtuesday-1120 notes (HANDOFF, STATUS)</li>
<li>session givingtuesday-1120 — v0.78.0 merged and live (still off); GivingTuesday ch...</li>
<li>v0.78.0 — donation thank-you email via email-engine (once per donor per week, firs...</li>
</ul>
<h3>contact-registry (4 commits)</h3>
<p><em>More info needed for a summary</em></p>
<ul>
<li>v0.101.0 - Add the capability list: everything the Contact Registry does, in plain English</li>
<li>v0.101.0 - Handoff: memorial names tagged deceased; David Wake held for Kerry</li>
<li>v0.101.0 - Link a person to an organization in the admin</li>
<li>v0.100.0 - Deceased people are never mailed</li>
</ul>
<h3>kuma-watchdog (2 commits)</h3>
<p><em>Database maintenance work reduced storage overhead and restored system headroom for normal operations</em></p>
<ul>
<li>v1.16.2 — headroom runway restarts after a VACUUM instead of going blank for a month</li>
<li>v1.16.1 - Kuma DB shrunk 1,047 to 211 MB, headroom back to 10% of RAM; capability list added</li>
</ul>
<h3>vps-ops (2 commits)</h3>
<p><em>Documentation was added to explain the command center's VPS operations in plain language, with automated checks to maintain accuracy</em></p>
<ul>
<li>v0.7.1 - Note that the command center's VPS page is live and reads our bulletin lines</li>
<li>v0.7.1 - Add a plain-English list of everything vps-ops does, with a test that kee...</li>
</ul>
<h3>static-sites (1 commit)</h3>
<p><em>The video migration estimator now displays a range of values, and thank-you page content was updated</em></p>
<ul>
<li>v1.95.0 - videomigrator.com estimator shows a range; thank-you pages re-synced</li>
</ul>
<h3>stripe-ops (1 commit)</h3>
<p><em>Billing infrastructure was decommissioned and associated access credentials were revoked</em></p>
<ul>
<li>v0.6.1 - billing.bansuribliss.com fully retired: DNS removed, its credentials dropped</li>
</ul>
<hr />
<p>Daily Work Summary initially created by <a href="https://zero2webmaster.com/kerry-kriger">Zero2Webmaster Founder Dr. Kerry Kriger</a></p>
<p>Contribute to the public repository at: https://github.com/zero2webmaster/daily-work-summary</p>
<p>Need to change the timing or timezone of these emails? <a href="https://github.com/zero2webmaster/daily-work-summary#customizing-the-email-schedule">Click here</a> for instructions.</p>
<p><em>Covers Fri Nov 20, 2026 · generated 2026-11-20 23:16 EST</em></p></div>