<!-- daily-summary/v2 covers="2026-11-23" --><div style="font-size: 18px; line-height: 1.6;"><h1>Daily Work Summary — Mon Nov 23, 2026</h1>
<p><strong>168 commits</strong> across <strong>20 repos</strong></p>
<p>🧠 <strong>Skill Vault:</strong> 223 skills total <em>(Vault stats as of 2026-11-22)</em></p>
<hr />
<h2>zero2webmaster</h2>
<h3>crawler (22 commits)</h3>
<p><em>The crawler service was hardened with security controls and freshness validation while grant discovery capabilities were built out to let organizations search for and convert funder pages into structured grant records</em></p>
<ul>
<li>v0.15.0 - any app can fetch a page safely through crawler, with freshness checks (...</li>
<li>docs - private-network guard is live (Kerry deployed v0.14.0); smoke checks passed</li>
<li>v0.14.0 - crawler refuses web addresses whose names point inside private networks ...</li>
<li>v0.13.1 - crawler can tell you when sites start refusing it (built, not deployed)</li>
<li>v0.13.0 - crawler obeys robots.txt and paces its visits to each site (built, not d...</li>
<li>docs - misnomer search is live for org-hq (Kerry deployed v0.12.0)</li>
<li>v0.12.0 - org-hq can search the web for Save The Frogs Day misnomers (built, not d...</li>
<li>v0.11.1 - docs - misnomer search call proposed to org-hq; waiting on its answer</li>
<li>v0.11.1 - grantseeker's grant jobs are live</li>
<li>v0.11.0 - grantseeker can run grant jobs over a whole seed list (built, not deployed)</li>
<li>v0.10.1 - grantseeker's link-to-grant-records endpoint is live</li>
<li>v0.10.0 - grantseeker can turn a pasted funder link into grant records (built, not...</li>
<li>v0.9.0 - Funder pages can be turned into grant records through z2w-ai-engine</li>
<li>v0.8.0 - grantseeker's record additions agreed; funder pages can now be fetched wi...</li>
<li>v0.7.0 - Grant discovery started: record shape, Brave search, and Brave's no-stori...</li>
<li>v0.6.1 - Crawl4AI no longer runs with Editor rights on the Google Cloud project</li>
<li>v0.6.0 - Crawl4AI deploy files in the repo; two unused keys disabled</li>
<li>v0.5.0 - Callers confirmed and 6 weeks of Crawl4AI usage logged; Phase 1 done</li>
<li>v0.4.0 - Log Crawl4AI's daily Cloud Run usage for the Containers decision</li>
<li>v0.3.0 - Health check names this service and still checks Crawl4AI; runbook moved ...</li>
<li>v0.2.0 - docs: Step 2 pre-flight done, live Worker matches this repo; deploy handed to Kerry</li>
<li>v0.2.0 - Bring the crawl gateway in from docker-z2w-multi-lingual, unchanged</li>
</ul>
<h3>grantseeker (21 commits)</h3>
<p><em>The application was refined with improved collaboration features, custom branding, and operational configuration to support Save the Frogs' grant-seeking workflow</em></p>
<ul>
<li>v0.14.0 - AI chats private to whoever starts them, shareable per chat (Kerry's decision, docs)</li>
<li>SAVE THE FROGS! can send its emails from grants@savethefrogs.com (v0.14.0)</li>
<li>v0.13.0 - Box pitch video script and Frog Patrol mock-up; email and terms in the app (docs)</li>
<li>v0.13.0 - Box brief, last outreach mentions updated (docs)</li>
<li>v0.13.0 - Box budget rebuilt to $22,616 with Kerry's teaching hours and paid threat-report r...</li>
<li>v0.13.0 - Box contact facts, mission, expert reviewers and 2025 budget in the app (docs)</li>
<li>v0.13.0 - Box answers and budget loaded into the app; Frog Patrol confirmed (docs)</li>
<li>v0.13.0 - Box brief revised after Kerry and Dr. Nurul Islam's call; own-sender and short-add...</li>
<li>v0.13.0 - invitations come from "SAVE THE FROGS! via Grantseeker", with a note to ...</li>
<li>v0.12.0 - SAVE THE FROGS! now at grants.savethefrogs.com (docs)</li>
<li>v0.12.0 - a workspace can have its own web address (grants.savethefrogs.com)</li>
<li>v0.11.0 - notification bell in the header; comments and co-applicants live</li>
<li>v0.11.0 - comments and co-applicants on each proposal (Step 9g)</li>
<li>v0.10.0 - Step 9f live on production; Box draft loaded (docs only)</li>
<li>v0.10.0 - draft application on each proposal page (Step 9f)</li>
<li>v0.9.1 - record Kerry's AI decisions (ai-engine, $50/$5 monthly limits, AI can be switched ...</li>
<li>v0.9.1 - choosing a stage asks to confirm straight away; Add Link opens the form, ...</li>
<li>v0.9.0 - readable addresses, Final review stage, change any stage with a confirm, ...</li>
<li>v0.8.0 - your organization's logo and colors on every workspace page</li>
<li>v0.7.0 - stage board takes sales' optional words (other languages), same English without th...</li>
<li>v0.7.0 - Box Impact Fund application brief for Kerry and Dr. Nurul Islam to review (due 202...</li>
</ul>
<h3>sales (20 commits)</h3>
<p><em>The sales application progressed through multiple releases with improvements to user experience, error handling, contact management, and internationalization support</em></p>
<ul>
<li>handoff for v0.8.1</li>
<li>v0.8.1 - a save from an expired login goes to the login step instead of saying the connecti...</li>
<li>v0.8.1 - A refused save keeps what you typed; phone is a country picker plus the n...</li>
<li>v0.8.0 - the owner's empty Commission screen says why, instead of 'it starts with the first...</li>
<li>v0.8.0 is live; the production schema change was applied and checked</li>
<li>v0.8.0 - record Contact Registry's key instructions and Kerry's tag notes; fix the registry...</li>
<li>v0.8.0 - Onboarding board, payments and commission (not yet deployed)</li>
<li>v0.7.0 is live; the owner section waits only on the Contact Registry key</li>
<li>v0.7.0 - The restaurant owner's contact, with WhatsApp and Call buttons</li>
<li>v0.6.0 - Readable restaurant addresses, wider pages, green login button</li>
<li>v0.5.0 - readable restaurant addresses, wider pages, green email button</li>
<li>v0.5.0 - docs: sales is live at sales.z2w.us; Step 4 waits only on Kerry's walk-through</li>
<li>v0.5.0 - switch Sentry on with the project's DSN</li>
<li>v0.5.0 - First deploy: the app runs on Vercel with its own database</li>
<li>v0.4.0 - wire Sentry (off until the DSN is filled in) and a last-resort error page</li>
<li>v0.4.0 - Spanish login for the salesperson, and adding her to an existing account</li>
<li>v0.4.0 - docs: a .tsx test under test/ is never collected</li>
<li>v0.4.0 - The Sales board and each restaurant's page, on a phone</li>
<li>v0.3.0 - Spanish and English per person, and a menu for each role</li>
<li>v0.2.0 - Deals data model, both pipelines as data, three roles</li>
</ul>
<h3>contest-management (16 commits)</h3>
<p><em>The application gained features for photo contest judging and artist engagement, while improving entry reporting and link security</em></p>
<ul>
<li>v1.118.0 - Ask for a better photo: advancing entries marked "Needs better cropping...</li>
<li>v1.117.0 - Docs: session 20261124a handoff (throwaway branches deleted, skill updated)</li>
<li>v1.117.0 - Judging: every picture of an entry on one screen, click to enlarge, Try...</li>
<li>v1.116.1 - Contest page shows entries reported to marketing-engine; no Fathom even...</li>
<li>Docs: session 20261123d handoff (v1.115.2, v1.116.0)</li>
<li>v1.116.0 - Report every contest entry to marketing-engine's conversion ledger (26cj)</li>
<li>v1.115.2 - Private links use 16-character codes; old links still work</li>
<li>v1.115.1 - Ask the artist: "Answer Here" links, the question on its own page</li>
<li>v1.115.0 - Ask the artist how it was made, answered in the app (26ck)</li>
<li>Docs: v1.114.0 live, session 20261123b handoff</li>
<li>v1.114.0 - Judging tools: turn a picture, leave one out, correct "how it was made"</li>
<li>v1.113.1 - Docs: 26ch step 5 sent, 238 Photo Contest re-entry emails (Kerry: send)</li>
<li>v1.113.1 - 26ch step 5: footer on every Photo Contest re-entry email; two first names from Kerry</li>
<li>v1.113.1 - 26ch step 5: logo, linked contest name, promo image, new apology wording, names fr...</li>
<li>v1.113.1 - 26ch step 5: Kerry's wording, plus the 2025 and past-entrant groups; 4 tests sent</li>
<li>v1.113.1 - 26ch step 5: find the lost 2026 Photo Contest entrants, re-entry email (dry run)</li>
</ul>
<h3>z2w-ai-engine (16 commits)</h3>
<p><em>The work spans capability documentation, branding assets for a legal-matters product, infrastructure improvements including prompt caching and error handling, and expansion of AI model support</em></p>
<ul>
<li>v0.45.1 - capability list (docs/CAPABILITIES.md); event-engine key script ready for Kerry</li>
<li>v0.45.1 / service v0.40.1 - Upstream image failures reported as provider failures,...</li>
<li>v0.45.0 - STATUS - brand-kit skill shipped; legal-matters and creative-engine asked about wo...</li>
<li>v0.45.0 - Legal Matters brand kit (logo #20 traced to vector, favicons, colors, fonts, brand...</li>
<li>v0.45.0 - legal-matters logo drafts, round 4 (#15 and #16 without the cross look, $0.82)</li>
<li>v0.45.0 - legal-matters logo drafts, round 3 (LM with the scales built in, navy and silver, ...</li>
<li>v0.45.0 - legal-matters logo drafts, round 2 (six marks in new colors, two with LM, $0.81)</li>
<li>v0.45.0 - legal-matters logo drafts, round 1 (six marks, $0.82)</li>
<li>v0.45.0 - ROADMAP - music generation as a candidate (ElevenLabs first)</li>
<li>v0.45.0 - Claude Fable 5.2 in the model registry</li>
<li>STATUS - 0.44.0 published and service 0.40.0 verified live</li>
<li>v0.44.0 / service v0.40.0 - Prompt caching: mark the repeated part, pay a cache re...</li>
<li>v0.43.0 - extract eval run live (4/4, $0.018); crawler app key minted</li>
<li>v0.43.0 - TROUBLESHOOTING - Next.js SecurityFatalError blocks every build</li>
<li>STATUS - 0.43.0 published and service 0.39.0 verified live</li>
<li>v0.43.0 / service v0.39.0 - extract(): a document in, JSON matching your schema out</li>
</ul>
<h3>z2w-skill-vault (15 commits)</h3>
<p><em>Development work improved image interaction in modals, expanded brand management capabilities, refined form field handling and filtering interfaces, and strengthened database migration safety and API logging</em></p>
<ul>
<li>lightbox-and-modal-geometry §5d: a swipe that starts on the photo is taken as an i...</li>
<li>brand-kit: record the owner ruling (ai-studio drafts, creative-engine builds the kit)</li>
<li>file-server-service-api: 5-minute asset links break long lazy-loaded picture pages...</li>
<li>cloudflare-workers-logs-api: filtering on a logged JSON field by name does work se...</li>
<li>New skill: brand-kit — turn a chosen logo into every file people ask for (SVG/PNG/...</li>
<li>list-filter-sort-search: a filter column that is one closed row on a phone and ope...</li>
<li>form-field-standards: phone fields trigger the skill</li>
<li>form-field-standards: phone is a country picker plus the number; async-action-feed...</li>
<li>drizzle-migration-safety: prove a hand-written migration offline (old schema + SQL...</li>
<li>resizable-table-columns: add §7, a draggable two-pane splitter (editor | preview),...</li>
<li>New skill: reading Cloudflare Workers Logs through the API without silently losing...</li>
<li>drizzle-migration-safety: a regex backslash in a sql`` CHECK is eaten by JavaScrip...</li>
<li>brand-is-not-the-account: add Femperium's own AWS account and SES identities to §0</li>
<li>brand-is-not-the-account: agents cannot write Cloudflare DNS or create Sentry proj...</li>
<li>list-filter-sort-search: column chooser in a client-state table (no server action)...</li>
</ul>
<h3>event-engine (11 commits)</h3>
<p><em>The event management system was enhanced to streamline speaker applications and presentation requests, with improvements to application visibility, address formatting, approval workflows, and email notifications to organizers</em></p>
<ul>
<li>v0.217.0 - handoff — DEV TEST rows removed from the dev database</li>
<li>v0.217.0 — choose a date when approving a speaker</li>
<li>v0.216.0 — Sarbani can find speaker applications; applicant photos kept</li>
<li>v0.215.0 — presentation requests from schools and groups</li>
<li>handoff — v0.214.0 live, Tabla Time done</li>
<li>v0.214.0 — readable speaker application addresses (migration 0076 applied to dev +...</li>
<li>v0.213.2 - readable speaker application addresses (not yet deployed — needs migration 0076 fi...</li>
<li>v0.213.2 - handoff — v0.213.x speaker application emails; Tabla Time next</li>
<li>v0.213.2 — From Attendees at most two columns</li>
<li>v0.213.1 — readable email buttons on any brand color; long testimonials span both ...</li>
<li>v0.213.0 — speaker applications email the event's organizers and the admins</li>
</ul>
<h3>contact-registry (8 commits)</h3>
<p><em>Email address validation and import processes were refined to filter out invalid addresses and integrate results from an external validation service</em></p>
<ul>
<li>v0.103.3 - Key handoff for sales names the variables it reads</li>
<li>v0.103.2 - Reconnect groups imported: 4,554 people Bouncer marked deliverable</li>
<li>v0.103.2 - Reconnect import reads Bouncer's results, skips toxic addresses</li>
<li>v0.103.1 - Bouncer file no longer includes our own address</li>
<li>v0.103.0 - Reconnect email: addresses ready for Bouncer</li>
<li>v0.102.0 - LoomInUs: forms-engine's key verified</li>
<li>v0.102.0 - LoomInUs is now a live Contact Registry organization</li>
<li>v0.102.0 - LoomInUs: its Contact Registry database is created; tenant registration waits on K...</li>
</ul>
<h3>static-sites (7 commits)</h3>
<p><em>The section kit component library was expanded with new reusable patterns including numbered steps, countdown blocks, and list layouts</em></p>
<ul>
<li>v1.99.0 - Section kit: numbered steps ("how it works")</li>
<li>Record the v1.98.0 deploy (bd3316ea, routing live 100/100)</li>
<li>v1.98.0 - Section kit: the countdown block</li>
<li>v1.97.0 - videomigrator.com report buttons go to the self-service form</li>
<li>Record the v1.96.0 deploy (4c3aa6e2, routing live 100/100); Kerry: markup is enoug...</li>
<li>v1.96.0 - Section kit: five list patterns from preview.grants.bd</li>
<li>v1.95.0 - Brief: five kit patterns measured off preview.grants.bd (ROADMAP §G)</li>
</ul>
<h3>forms-engine (6 commits)</h3>
<p><em>The presentation request form was developed with clarified Zoom account options, improved spacing, and integration with the event system</em></p>
<ul>
<li>v0.1.0 - Handoff: check the re-queued speaker application, note the missing re-send tool</li>
<li>v0.1.0 - VideoMigrator free report: three steps above a Start button; thank-you names the b...</li>
<li>v0.1.0 - Even spacing between form fields; Kerry's Zoom choice wording</li>
<li>v0.1.0 - Presentation form: say whose Zoom account each choice means</li>
<li>v0.1.0 - Record the Request a Presentation form and the re-subscribe fix</li>
<li>v0.1.0 - Request a Presentation form, delivered to event-engine</li>
</ul>
<h3>femperium-lead-gen (5 commits)</h3>
<p><em>The outreach messaging and lead qualification process were refined, with AI-powered qualification now running before enrichment and visual improvements made to outreach templates</em></p>
<ul>
<li>docs: v1.33.0 deployed by Kerry; VideoMigrator sending plan (separate member AWS a...</li>
<li>docs: session 47 — v1.33.0 awaiting deploy and secret; ROADMAP Step 22 rename to l...</li>
<li>docs: enrichment directive — qualification runs first (v1.33.0)</li>
<li>v1.33.0 - fix: remove em dashes from outreach copy; product image larger, left-aligned under...</li>
<li>feat: v1.33.0 — AI lead qualification before enrichment</li>
</ul>
<h3>ibague-satelital (4 commits)</h3>
<p><em>More info needed for a summary</em></p>
<ul>
<li>v0.19.0 - record Kerry's step 6 decisions (environmental market yes; SAVE THE FROGS! pilot p...</li>
<li>v0.19.0 - research environmental buyers for the imagery method (ROADMAP step 6)</li>
<li>v0.19.0 - internal seal of 2026-11-24 covers the 2015-on folders; capability list added</li>
<li>v0.19.0 - 2026-11-03 seals anchored in Bitcoin (blocks 974334 and 974347)</li>
</ul>
<h3>legal-matters (4 commits)</h3>
<p><em>Brand identity and visual design decisions were applied across the application, including logo, colors, and typography choices</em></p>
<ul>
<li>v0.52.0 - STATUS: keep the system font (Kerry); CourtListener token in place, rate limit not...</li>
<li>v0.52.0 - STATUS: brand decisions (keep Z2W Legal Matters, Z2W logo requested), trademark tr...</li>
<li>v0.52.0 - Fonts comparison for Kerry: today vs the brand kit's Libre Baskerville and Source ...</li>
<li>v0.52.0 - The app wears the Legal Matters logo and colors, in pages, icons and emails</li>
</ul>
<h3>email-engine (3 commits)</h3>
<p><em>The letter editor and image handling were enhanced, and sign-up forms can now distribute free resources via email</em></p>
<ul>
<li>v0.150.0 - A calmer letter editor, and captions that take several links</li>
<li>v0.149.0 - Images get their own link, and an Image button that writes them</li>
<li>v0.148.0 - Sign-up forms can give away a free resource by email</li>
</ul>
<h3>org-hq (3 commits)</h3>
<p><em>The web crawler now captures pages found online and records where they came from, while access to these discovered pages is restricted to staff and a known data gap affecting one organization was corrected</em></p>
<ul>
<li>v0.142.0 - pages found on the web are staff only for now (Kerry)</li>
<li>v0.142.0 - crawler misnomer import leaves out SAVE THE FROGS!'s own sites</li>
<li>v0.142.0 - misnomer pages found on the web by crawler, with their origin recorded</li>
</ul>
<h3>creative-engine (2 commits)</h3>
<p><em>The creative engine's logo guidelines and image template standards were documented and established</em></p>
<ul>
<li>v0.1.0 - record Kerry's logo ruling (ai-studio drafts, creative-engine builds the kit and g...</li>
<li>v0.1.0 - capability list, and the four AI Suite image templates accepted as real-photo layouts</li>
</ul>
<h3>z2w-agent-command-center (2 commits)</h3>
<p><em>Infrastructure-wide alerts can now be marked as seen to clear the alert banner</em></p>
<ul>
<li>Docs - weekly wake 2026-11-23 handoff: v0.96.1 live</li>
<li>v0.96.1 - Infra-wide alerts marked seen leave the red banner</li>
</ul>
<h3>ai-studio (1 commit)</h3>
<p><em>Users can now view full-size images in the gallery with accompanying details and the ability to copy metadata</em></p>
<ul>
<li>Gallery viewer: full-size images with details and Copy Metadata (v0.20.0)</li>
</ul>
<h3>courses-engine (1 commit)</h3>
<p><em>Users can now organize lesson content by dragging columns into their preferred order, selecting topics and speakers from dropdown menus, and adding or removing topics as needed</em></p>
<ul>
<li>Lesson points: drag columns into order, Topic and Said by dropdowns, add and delet...</li>
</ul>
<p><strong>z2w-agent-coordination:</strong> 1 coordination commit<br />
<em>More info needed for a summary</em></p>
<hr />
<p>Daily Work Summary initially created by <a href="https://zero2webmaster.com/kerry-kriger">Zero2Webmaster Founder Dr. Kerry Kriger</a></p>
<p>Contribute to the public repository at: https://github.com/zero2webmaster/daily-work-summary</p>
<p>Need to change the timing or timezone of these emails? <a href="https://github.com/zero2webmaster/daily-work-summary#customizing-the-email-schedule">Click here</a> for instructions.</p>
<p><em>Covers Mon Nov 23, 2026 · generated 2026-11-23 23:18 EST</em></p></div>