<!-- daily-summary/v2 covers="2026-11-27" --><div style="font-size: 18px; line-height: 1.6;"><h1>Daily Work Summary — Fri Nov 27, 2026</h1>
<p><strong>173 commits</strong> across <strong>23 repos</strong></p>
<p>🧠 <strong>Skill Vault:</strong> 26 improved today · 227 skills total</p>
<hr />
<h2>zero2webmaster</h2>
<h3>z2w-skill-vault (29 commits)</h3>
<p><em>Session security, authentication flows, and development tooling were hardened across login mechanisms, two-factor authentication, and local testing environments</em></p>
<ul>
<li>z2w-magic-link-auth §3.0d: apps that log in through accounts need a fixed 60-minut...</li>
<li>ai-tells §5a: eyebrows, gradient text and zero-offset glows as visual tells; the f...</li>
<li>instantiate-z2w-project: version-history entry count 75 -&gt; 76 (v1.61.0 entry added)</li>
<li>instantiate-z2w-project: add the missing v1.61.0 version-history entry</li>
<li>file-server-service-api: a timed-out upload may have gone through; unreferenced is...</li>
<li>terminal-secret-hygiene §7.1-ter-bis: collect the R2 account id (and every non-one...</li>
<li>authenticator-app-2fa §11c: new backup codes must never be shown on another of the...</li>
<li>subdomain-vs-subdirectory: a zone redirect rule runs before the Worker route</li>
<li>Browser skill: run the real app with no local database (PGlite for next dev), and ...</li>
<li>authenticator-app-2fa: the lockout fix (§11b.3) now has a tested reference impleme...</li>
<li>uptime-kuma-monitor §11a: Kerry's 2 h floor for checks that read the database, and...</li>
<li>instantiate-z2w-project v1.61.0: mirror CLI v0.59.0 capabilities-version test</li>
<li>Sentry skill: the feature-flag defaults section is whole again; the email-scanner ...</li>
<li>Test suites can no longer commit into the repository they were started from</li>
<li>A free Mac-portability check for shell scripts, at commit time and on GitHub</li>
<li>Three test suites and the session-start hook now work on the Mac, not just in clou...</li>
<li>Size exemptions: the secret-handling skill re-checked and still holds; the magic-l...</li>
<li>Skill checks workflow: checkout step moved to v5, so GitHub stops warning about th...</li>
<li>GitHub now runs the skill checks on every push to main and every pull request, and...</li>
<li>CLAUDE.md: cloud and phone sessions' fresh clones never ran the commit checks (cor...</li>
<li>Commit check now refuses a skill whose header (frontmatter) does not parse as stri...</li>
<li>resizable-table-columns: last colon in the description reworded so it parses as st...</li>
<li>Three skill descriptions parse as strict YAML again (a colon followed by a space r...</li>
<li>Commit check now refuses a description that the commit itself pushes past the 1,53...</li>
<li>Links with a long id in them: send the specific link anyway, say so, and offer the...</li>
<li>local-first-outputs: a quarterly .tmp/ review method (60 of 63 repos never reviewe...</li>
<li>project-migration-audit: Step 1c, run the per-screen inventory first, copy prompts...</li>
<li>sentry-runtime-errors: from 10.78 a scalar httpHeaders works; graphQL and genAI st...</li>
<li>sentry-runtime-errors: Sentry 11 upgrade lessons (beforeSendSpan, queues/mcp axes,...</li>
</ul>
<h3>accounts (17 commits)</h3>
<p><em>A login system was built with organization branding, security features including passkeys and backup codes, app integration capabilities, and went live at accounts.savethefrogs.com</em></p>
<ul>
<li>every login screen and login email now wears the organization's own photo, logo an...</li>
<li>v0.6.1 - Step 6 done: a real app logged in through accounts.savethefrogs.com; estimated the...</li>
<li>v0.6.1 - app logins last 60 minutes from the login here (told to app builders on each app's...</li>
<li>v0.6.1 - measured what a silent app-login renewal costs (18 queries; the cost is the 1 CU d...</li>
<li>v0.6.1 - the live login check passed against accounts.savethefrogs.com (log in with a typed...</li>
<li>the app is now 'SAVE THE FROGS! Accounts', run by SAVE THE FROGS!, on every page, ...</li>
<li>v0.6.0 - record Kuma monitor 114 and plan SAVE THE FROGS! branding (ROADMAP Step 6b)</li>
<li>v0.6.0 - accounts.savethefrogs.com is live; record where the encryption key is kept</li>
<li>v0.6.0 - record the email sender, the GitHub connection and the two steps left before accou...</li>
<li>record Step 6's progress: the database and Vercel project exist, and what Kerry's ...</li>
<li>v0.5.0 - apps can now log people in with the organization's login (OpenID Connect behind ou...</li>
<li>people can make new backup codes and change their second step; admins restore a lo...</li>
<li>passkeys as the default second login step, with backup codes and an email on every...</li>
<li>a second login step for everyone, an authenticator app plus ten backup codes (v0.3.0)</li>
<li>replace the Auth.js login with email link plus code and server-side sessions (v0.2.0)</li>
<li>v0.1.0 - choose oidc-provider as the sign-in server, by a test</li>
<li>Initial scaffold (@zero2webmaster/starter-kit 0.59.0, nextjs, login, host-routed t...</li>
</ul>
<h3>contest-management (17 commits)</h3>
<p><em>Historical art competition records spanning multiple years were imported into the database, with supporting scripts and documentation updated to handle data mapping, file conversions, and connection resilience</em></p>
<ul>
<li>v1.127.1 - Docs: 26cm rulings (poetry waits for spreadsheets, art 2009-2019 from File Server ...</li>
<li>v1.127.1 - Docs: 26cm remaining work listed (poetry, video 2019, art 2009-2019 folders)</li>
<li>v1.127.1 - art-2017 imported with its winners; every Airtable art year done (26cm)</li>
<li>v1.127.1 - Docs: art-2020 entries all linked to people (26cm)</li>
<li>v1.127.1 - art-2020 imported with winners; save reconnects; timed-out uploads reused (26cm)</li>
<li>v1.127.1 - art-2020 placings from savethefrogs.com/art-2020; last PDF converted (26cm)</li>
<li>v1.127.1 - Import script: art-2020 mapping; PDFs become pictures (26cm)</li>
<li>v1.127.1 - Docs: session 20261127b handoff; art-2021 imported and linked (26cm)</li>
<li>v1.127.1 - Directive: award order and terms answers corrected on production</li>
<li>v1.127.1 - Import script: number award levels in rank order across pages</li>
<li>v1.127.1 - Import script: art-2021 base mapping; terms answer read correctly</li>
<li>v1.127.1 - Docs: Alvin Shen's stray art-2023 upload deleted from the File Server</li>
<li>v1.127.1 - Docs: session 20261127a handoff; art-2023 imported and linked (26cm)</li>
<li>v1.127.1 - Directive: Fanni orphan uploads (125 files, 5 failed tries) deleted</li>
<li>v1.127.1 - Docs: session 20261126d handoff; art-2022 imported and linked (26cm)</li>
<li>v1.127.1 - Import script splits a large entry's uploads across submission ids</li>
<li>v1.127.1 - Import script reconnects when the database dropped the connection silently</li>
</ul>
<h3>org-hq (17 commits)</h3>
<p><em>Security upgrades and fixes were applied across dependencies, database connections, and error reporting, alongside improvements to form help text and AI chat logging</em></p>
<ul>
<li>v0.156.0 - note the FrogSpace platform is merged on Kerry's OK</li>
<li>v0.156.0 - FrogSpace becomes one more platform on a social post (off until FrogSpa...</li>
<li>v0.155.0 - queue the art sale page and Ask's Save to memory (Kerry's yes)</li>
<li>v0.155.0 - Deleting or exporting an AI chat is now logged</li>
<li>v0.154.6 - note the zod 4 upgrade is merged on Kerry's OK</li>
<li>v0.154.6 - handoff for the zod 4 upgrade (preview verified, waiting on a signed-in letter-PDF...</li>
<li>v0.154.6 - Pin the naming article's "In recent years" wording with a test</li>
<li>v0.154.6 - zod 3 to 4 security upgrade (via puppeteer-core 25.19)</li>
<li>v0.154.5 - note the form-help fix is merged on Kerry's OK</li>
<li>v0.154.5 - The form-help "i" never says "What goes here?"</li>
<li>v0.154.4 - note the database SSL-warning fix is merged on Kerry's OK</li>
<li>v0.154.4 - Database connections say sslmode=verify-full explicitly</li>
<li>v0.154.3 - note the Sentry 11 upgrade is merged on Kerry's OK</li>
<li>v0.154.3 - Scrub reported message text too (found by the Sentry 11 canary)</li>
<li>v0.154.3 - Sentry 11 upgrade (security), what it collects kept the same</li>
<li>v0.154.2 - note the sharp fix is merged on Kerry's OK</li>
<li>v0.154.2 - Image library security fix (sharp 0.35.5)</li>
</ul>
<h3>backup-engine (12 commits)</h3>
<p><em>Daily backups of files and databases were established for multiple organizations with verification and monitoring in place</em></p>
<ul>
<li>v0.45.1 - Handoff: files-copy heartbeats live-verified (run 46075520913)</li>
<li>v0.45.1 - Both copies of Kerry's files site now report to his Kuma monitor</li>
<li>v0.45.0 - Handoff: files site's R2 copy verified (227 objects, run 46073505198)</li>
<li>v0.45.0 - Kerry's files site also copied daily to his own Cloudflare R2</li>
<li>v0.44.0 - Kerry's files site copied in full (227 files) and now backed up daily</li>
<li>v0.44.0 - STF investments backed up daily; retired bases' final copies kept forever</li>
<li>v0.43.0 - Scope the files-site copy to the tenant folder the read key can list; dry-run summ...</li>
<li>v0.43.0 - Copy Kerry's files site into his backup bucket daily; keep retired bases' final co...</li>
<li>v0.43.0 - STF investments database first backup verified in both places</li>
<li>v0.43.0 - Back up SAVE THE FROGS!'s investments database daily; daily job can run named entr...</li>
<li>v0.43.0 - Kuma monitor 111 is now mapped to this project</li>
<li>v0.43.0 - Skip the moved kerry file tenant; wire STF's investments database</li>
</ul>
<h3>land-history (11 commits)</h3>
<p><em>A blind-screen methodology was developed and applied to a study area, with results validated against a reference map and cryptographically sealed for reproducibility</em></p>
<ul>
<li>v0.3.0 - Make the chance comparison reproducible, and plan screen v2 on a held-out...</li>
<li>v0.2.0 - Score the blind screen against Tom's map, and write up the result honestly</li>
<li>v0.1.0 - Georeference Tom's p. 65 map onto the lidar and trace the five wetlands as the ans...</li>
<li>v0.1.0 - Seal the blind screen's output with OpenTimestamps</li>
<li>v0.1.0 - Run the blind screen once on the Sudith study area: 106 of 3,600 tiles flagged (2.9%)</li>
<li>v0.1.0 - Download the blind screen's 3 km study-area lidar and seal it as evidence batch 02</li>
<li>v0.1.0 - Seal the blind-screen pre-registration with OpenTimestamps</li>
<li>v0.1.0 - Pre-register the blind desk screen before it touches the study area</li>
<li>v0.1.0 - Check the Sudith evidence against its manifest, and seal the manifest with OpenTim...</li>
<li>v0.1.0 - Add Kerry's UC Reserve request PDF (force-added past the PDF ignore rule)</li>
<li>Initial scaffold (z2w-starter-kit 0.59.1) plus the Sudith pilot's starting material</li>
</ul>
<h3>email-engine (9 commits)</h3>
<p><em>Letters and mailings gained features for customization, sharing, and presentation while fixing issues with save states and visual styling</em></p>
<ul>
<li>v0.156.0 - A highlight can be for the monthly letter only</li>
<li>v0.155.0 - Other apps can read what was sent</li>
<li>v0.154.0 - A letter can show an image under its button</li>
<li>v0.153.2 - Save no longer leaves a mailing stuck on unsaved</li>
<li>v0.153.1 - LoomInUs newsletter: shop screenshot added; flowtoys sample is next</li>
<li>v0.153.1 - Zero2Webmaster links are readable green instead of gold</li>
<li>v0.153.0 - Zero2Webmaster letters: logo at the bottom, no line above the greeting</li>
<li>v0.152.1 - GivingTuesday letters and LoomInUs launch newsletter staged, tests sent to Kerry</li>
<li>v0.152.1 - Donation thank-you: members and non-members each get their own closing ...</li>
</ul>
<h3>financial-engine (8 commits)</h3>
<p><em>More info needed for a summary</em></p>
<ul>
<li>Handoff: Zero2Webmaster receipts live on v0.72.0; what to verify next session</li>
<li>v0.72.0 - File-server tenant header for Zero2Webmaster and Bansuri Bliss; Z2W Gmai...</li>
<li>v0.71.0 - Health plan: each pay tier is STF's whole spend on Kerry, plan costs included (Ker...</li>
<li>v0.71.0 - Health plan: three 2027 pay asks for Nick (low, mid, high)</li>
<li>v0.71.0 - Roadmap: Z2W receipts via the zero2webmaster Cloud project; Bansuri Bliss may move...</li>
<li>v0.71.0 - Docs: why IMG's $2,500 deductible fails the HSA test; who pays EA+ and the interna...</li>
<li>v0.71.0 - Docs: Kerry rules Zero2Webmaster and Bansuri Bliss receipts Neon-only; 403(b) esti...</li>
<li>v0.71.0 - Make.com: the Zero2Webmaster account's 5 active scenarios, read from Mak...</li>
</ul>
<h3>site-control (8 commits)</h3>
<p><em>The site infrastructure was enhanced to support hosting a branded articles section under a shared domain, with responsive design refinements and routing updates for the new VideoMigrator articles area</em></p>
<ul>
<li>VideoMigrator header button reads Get My Free Video Migration Report, and fits at ...</li>
<li>v0.131.0 - videomigrator.com/articles Worker route must end in * so links with ?utm_source re...</li>
<li>videomigrator.com/articles lists its articles, with the homepage's own header, foo...</li>
<li>v0.130.0 - roadmap records Kerry's core goal, one list of every page on a site whichever syst...</li>
<li>v0.130.0 - videomigrator.com/articles answers from Site Control (VideoMigrator site created; ...</li>
<li>v0.130.0 - videomigrator.com/articles secret and Worker are live; the zone redirect rule is t...</li>
<li>v0.130.0 - handoff and troubleshooting notes for the videomigrator.com/articles step 1 session</li>
<li>a site can live under a path on someone else's domain, first for videomigrator.com...</li>
</ul>
<h3>videomigrator-engine (8 commits)</h3>
<p><em>Video processing and customer access were improved to use customers' own accounts instead of shared credentials, with better handling of resource constraints and faster connection checks</em></p>
<ul>
<li>v10.66.2 - When Kerry's Mac has under 25 GB free, big video jobs run on the Hetzner server in...</li>
<li>v10.66.2 - Handoff: laptop caught up with the phone sessions, release tags pushed</li>
<li>v10.66.2 - Clip compiler tests no longer fail on a computer that is short of disk space</li>
<li>v10.66.2 - Customers who need to allow downloads are pointed only at Allow downloa...</li>
<li>v10.66.1 - Customers are told the two ways to let us copy their videos, and which ...</li>
<li>v10.66.0 - Handoff: customers' own Vimeo access is live and checked on a real connection</li>
<li>v10.66.0 - Make the Vimeo access check start in seconds instead of minutes</li>
<li>v10.66.0 - Customer migrations copy videos with the customer's own Vimeo access, n...</li>
</ul>
<h3>z2w-starter-kit (7 commits)</h3>
<p><em>Internal initialization messaging and capability validation were improved across multiple releases</em></p>
<ul>
<li>docs: session -20261127d notes (v0.59.2 published)</li>
<li>v0.59.2 - Say so when an internal init skips the Project Registry write</li>
<li>v0.59.1 - docs: session -20261127c notes (land-history instantiated, Project Registry 128)</li>
<li>v0.59.1 - Refuse a description that would break emitted code; accounts instantiated</li>
<li>v0.59.0 - docs: accounts is first in the build queue (Kerry), Project Registry 125; next-ses...</li>
<li>docs: session -20261127 notes (v0.59.0 published)</li>
<li>v0.59.0 - New projects get a test that keeps the capability list's Checked against...</li>
</ul>
<h3>commerce-engine (6 commits)</h3>
<p><em>The system was configured to support membership tracking with renewal and end dates, product categorization for external platforms, and operational setup for a shop including postage and staff communication</em></p>
<ul>
<li>v0.159.0 - Bansuri Bliss shop: postage, warehouse, staff email and 4 draft products set up</li>
<li>v0.159.0 - Plan the Bansuri Bliss shop move to shop.bansuribliss.com before December 22</li>
<li>v0.159.0 - 0058 is on production: members' renewal and end dates can now be stored</li>
<li>v0.159.0 - Members see when their membership renews, ends or resumes</li>
<li>v0.158.1 - Every LoomInUs item now has a product category for Pinterest</li>
<li>v0.158.0 - Footer newsletter beside Connect, clearer shipping question, product ca...</li>
</ul>
<h3>file-server (3 commits)</h3>
<p><em>The financial-engine service was updated to file receipts in a new Business folder location across multiple systems</em></p>
<ul>
<li>docs: session 196 — v1.148.2 live, financial-engine token verified</li>
<li>v1.148.2 - financial-engine may file receipts under Business/ on z2w and bb (#113)</li>
<li>docs: session 196 — v1.148.2 built (PR #113), financial-engine Business/ on z2w + bb</li>
</ul>
<h3>grantseeker (3 commits)</h3>
<p><em>Funder information management was enhanced to allow adding contacts directly from a funder's profile and to display additional details including websites, award sizes, and editable fields</em></p>
<ul>
<li>add a funder's contacts from its page, and fold the proposal page into sections (v...</li>
<li>v0.26.0 live, no hotdog fixed and on the board (docs)</li>
<li>funders get a website, award size and Edit Details (v0.26.0, Step 8c)</li>
</ul>
<h3>ibague-satelital (3 commits)</h3>
<p><em>More info needed for a summary</em></p>
<ul>
<li>v0.19.0 - land-history named and handed to the starter-kit</li>
<li>v0.19.0 - record the wetland pilot plan and Kerry's decisions</li>
<li>v0.19.0 - 2026-11-24 seal anchored in Bitcoin (block 977316); Tom's pilot site recorded</li>
</ul>
<h3>videomigrator-dashboard (3 commits)</h3>
<p><em>Email buttons and video gallery interactions were refined, and informational messaging around video download capabilities was improved</em></p>
<ul>
<li>v1.41.0 - Email buttons use the purple-to-cyan logo gradient; a finished video's W...</li>
<li>v1.40.0 - Email button color options for Kerry to choose from (picture only, no code change)</li>
<li>v1.40.0 - The Vimeo page says which Vimeo plans allow downloading, and skips the A...</li>
</ul>
<h3>z2w-observability-bridge (3 commits)</h3>
<p><em>Webhook integration was completed and deployed, with error tracking now displayed in a readable format</em></p>
<ul>
<li>v0.16.0 - Handoff: webhook coverage back to 38 of 38</li>
<li>Handoff: session #38, v0.16.0 deployed and verified; spend webhook proven; 3 repos...</li>
<li>v0.16.0 - Weekly Sentry trend rendered as a page a person can read</li>
</ul>
<h3>z2w-social (3 commits)</h3>
<p><em>The posting API was deployed to production, enabling organization announcements to be automatically published to a designated channel on a scheduled basis</em></p>
<ul>
<li>v0.1.0 - Status: posting API live, org-hq token set, both apps redeployed</li>
<li>v0.1.0 - Merge service-posts-api: posting API for org-hq (migration 0038 applied to product...</li>
<li>v0.1.0 - Posting API for org-hq: approved announcements into #announcements, scheduled by F...</li>
</ul>
<h3>static-sites (2 commits)</h3>
<p><em>Documentation was deployed and article routing capabilities were added with updated interface labels</em></p>
<ul>
<li>v1.111.0 - Docs: deployed (6752b68f), routing live 104/104</li>
<li>v1.111.0 - videomigrator.com: room for /articles, new button label; "looks AI-made...</li>
</ul>
<h3>agent-framework (1 commit)</h3>
<p><em>More info needed for a summary</em></p>
<ul>
<li>templates 0.5.0 is published; project-creator told to reinstall; coordination scri...</li>
</ul>
<h3>kuma-watchdog (1 commit)</h3>
<p><em>More info needed for a summary</em></p>
<ul>
<li>v1.17.0 — Kuma's live monitor config snapshotted to Neon daily; costly page checks...</li>
</ul>
<p><strong>z2w-agent-coordination:</strong> 1 coordination commit<br />
<em>More info needed for a summary</em></p>
<h3>z2w-crowdcommerce (1 commit)</h3>
<p><em>More info needed for a summary</em></p>
<ul>
<li>v0.80.1 - FluentCRM automation #3 stays on (it only fires for WordPress gifts); thank-you sw...</li>
</ul>
<hr />
<p>Daily Work Summary initially created by <a href="https://zero2webmaster.com/kerry-kriger">Zero2Webmaster Founder Dr. Kerry Kriger</a></p>
<p>Contribute to the public repository at: https://github.com/zero2webmaster/daily-work-summary</p>
<p>Need to change the timing or timezone of these emails? <a href="https://github.com/zero2webmaster/daily-work-summary#customizing-the-email-schedule">Click here</a> for instructions.</p>
<p><em>Covers Fri Nov 27, 2026 · generated 2026-11-27 23:20 EST</em></p></div>