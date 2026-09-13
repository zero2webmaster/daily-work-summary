<!-- daily-summary/v2 covers="2026-09-12" --><div style="font-size: 18px; line-height: 1.6;"><h1>Daily Work Summary — Sat Sep 12, 2026</h1>
<p><strong>82 commits</strong> across <strong>12 repos</strong></p>
<p>🧠 <strong>Skill Vault:</strong> 162 skills total <em>(Vault stats as of 2026-09-10)</em></p>
<hr />
<h2>zero2webmaster</h2>
<h3>marketing-engine (19 commits)</h3>
<p><em>The marketing engine underwent documentation cleanup and structural refinement, including OCR improvements, conversion tracking updates, nonprofit content organization, and technical optimizations</em></p>
<ul>
<li>marketing-engine: OCR complete 8/8 — and my sample over-predicted a second time</li>
<li>marketing-engine: OCR DPI is derived from page size, not hardcoded at 300</li>
<li>marketing-engine: correct the record — give.savethefrogs.com is deployed but ...</li>
<li>marketing-engine: KEEP Hidden Gold — prose, on recurring giving, landing on a...</li>
<li>marketing-engine: conversion tracking now faces TWO donation systems — and it...</li>
<li>marketing-engine: EXCLUDE the Grantsmanship notes — and do NOT build the guar...</li>
<li>marketing-engine: correct my statement-descriptor claim — Kerry was right to ...</li>
<li>marketing-engine: census the Nonprofit folder — I overstated it 2.1x, and the...</li>
<li>marketing-engine: recommend Nonprofit ICU as vendor end to end, including che...</li>
<li>marketing-engine: capture Kerry's Nonprofit ICU positioning as source facts, ...</li>
<li>marketing-engine: fold Kerry's scope answers and the real Nonprofit ICU posit...</li>
<li>marketing-engine: one guide lineage per house voice — the schema could only h...</li>
<li>marketing-engine: plan the nonprofit corpus — two guides, and the schema chan...</li>
<li>marketing-engine: write out the Zernio Ad Grants test Kerry asked for</li>
<li>marketing-engine: refresh the next-session prompt — measure the outage first,...</li>
<li>marketing-engine: queue three more library folders — Nonprofit is the one to ...</li>
<li>marketing-engine: handoff addendum — the Spanish clearance is reversed, and t...</li>
<li>marketing-engine: Google Ads assets with the limits enforced in code, not cou...</li>
<li>marketing-engine: Agent Coordination block -&gt; pointer form, 51 KB to 9 KB</li>
</ul>
<h3>email-engine (15 commits)</h3>
<p><em>Mailing and messaging features were refined to improve send staging, bounce visibility, list management, and user control over scheduling and field organization</em></p>
<ul>
<li>Recommend how the first SAVE THE FROGS! send should be staged</li>
<li>Stop The Send goes live, and the warning stops naming a vendor</li>
<li>Write down Stop The Send, and what the real SES numbers changed</li>
<li>Stop The Send</li>
<li>Correct the bounce claim, and record a runbook that can actually be run</li>
<li>Get the explanation out of the way, and let a token be issued at all</li>
<li>Write down what shipped and what the March announcement is waiting on</li>
<li>Show the shared bounce risk before the send, not after</li>
<li>Read the message a mailing sent, and search inside it</li>
<li>Link the reversed skill from the handoff too</li>
<li>Point at the reversed list skill</li>
<li>Columns are yours to arrange, and dates say which date they are</li>
<li>The mailings list is a table you can read, and fields stopped teaching</li>
<li>Point at the new skill for what a rename leaves behind</li>
<li>It is a mailing now, and the schedule picker waits until you ask for it</li>
</ul>
<h3>site-control (12 commits)</h3>
<p><em>Aharon's site was integrated with file storage, enabling content like pages, images, and media to be uploaded and accessed</em></p>
<ul>
<li>v0.51.0 - Aharon's ten pages exist on the new site, and there's a list he can...</li>
<li>docs: next-session prompt — Step 40, the drafts and Aharon's review list</li>
<li>v0.50.0 - Aharon's pages become blocks, and every decision about them is writ...</li>
<li>docs: next-session prompt — finish the Step 39 converter</li>
<li>v0.49.0 - Aharon's pictures reach the file store, and our sign-in email has a...</li>
<li>Aharon's site is connected to the file store, and the tool for doing that exi...</li>
<li>checking the file server token is a named command now, not a curl in an old m...</li>
<li>docs: a blank I left in a config value went live and worked perfectly</li>
<li>docs: the file server token checks out on their side, and Sentry is clean at ...</li>
<li>docs: a clean Sentry dashboard can just mean the problem is older than two weeks</li>
<li>v0.48.0 - seven videos on Aharon's site that nobody has ever been able to watch</li>
<li>v0.47.0 - the kalimba track now plays on one page, and the file server token ...</li>
</ul>
<h3>docker-z2w-multi-lingual (10 commits)</h3>
<p><em>Rate limiting and organization-based access controls were improved, along with translation configuration refinements and documentation updates</em></p>
<ul>
<li>docs: v1.22.0 is deployed and confirmed live in production</li>
<li>v1.22.0 - The rate limiter stops being keyed on our own load balancer</li>
<li>docs: the WordPress licence key is linked and its 20,011 rows backfilled</li>
<li>docs: file the global per-IP rate-limit bucket as ROADMAP 14.1d</li>
<li>v1.21.0 - The real orgs exist; orgs get their own reserved slug list</li>
<li>docs: file static-sites' <code>issue --write-env</code> suggestion on the ROADMAP</li>
<li>docs: condense HANDOFF.md and STATUS.md to what is still load-bearing</li>
<li>v1.20.0 — The org dimension (ROADMAP Phase 14, step 14.1) (#2)</li>
<li>docs: the <code>provider</code> default is "deepl", so the intelligent router is opt-in ...</li>
<li>docs: Session 80 — accept ownership of off-WordPress translation config; writ...</li>
</ul>
<h3>z2w-starter-kit (7 commits)</h3>
<p><em>Publishing automation was moved from local machines to continuous integration, resolving environment and state inconsistencies that prevented reliable releases</em></p>
<ul>
<li>v0.30.0 is live on npm, published from CI</li>
<li>docs: session -20260912 - publishing moved to CI, and the first CI run found ...</li>
<li>bump checkout/setup-node to v5</li>
<li><code>npm pack</code> does not build, so the tarball test was reading a stale dist/</li>
<li>three tests only passed because of state this machine happened to have</li>
<li>publish workflow needs Node 22: current npm will not install on Node 20</li>
<li>publish from CI, because the laptop publish cannot get past its own passkey w...</li>
</ul>
<h3>commerce-engine (6 commits)</h3>
<p><em>Product catalog data was cleaned up and made queryable by tag, with database schema and product visibility issues resolved</em></p>
<ul>
<li>Kerry ruled: site-control takes the loominus.art apex, and Step 6 is next</li>
<li>The shop's last missing data: 7 tags are live on production</li>
<li>Kerry ruled on the duplicate Airtable tags: delete five, rename Pillow Cases</li>
<li>Production is now schema-current, and was never two migrations behind</li>
<li>v0.16.0 - Shoppers can filter by tag, and half the tags were not tags</li>
<li>v0.15.1 - The last two products, and the comment that hid them</li>
</ul>
<h3>org-hq (4 commits)</h3>
<p><em>System reliability and user-facing features were improved by fixing database validation, correcting status reporting, preventing crashes on the letters page, and enabling support letter requests through a new form</em></p>
<ul>
<li>v0.50.0 - prove the reference intake against the real tenant databases, not a...</li>
<li>v0.50.0 - STATUS says what actually shipped, and stops telling the next agent...</li>
<li>v0.50.0 - the new badge must not 500 the letters page on a tenant that has no...</li>
<li>v0.50.0 - Somebody can ask for a letter of support through a form, and the re...</li>
</ul>
<h3>grantor (3 commits)</h3>
<p><em>Grant payment tracking and grantee communication were improved to better monitor fund delivery and donor correspondence</em></p>
<ul>
<li>Record that a grant was paid, and let the grantee say whether it arrived</li>
<li>List what Airtable is emailing our grantees, and find both things we thought ...</li>
<li>Write down the step-up re-auth idea Kerry likes, and the count that says not ...</li>
</ul>
<h3>financial-engine (2 commits)</h3>
<p><em>The financial calculation system now guards against invalid currency values in amount entries</em></p>
<ul>
<li>financial-engine: STATUS — record the v0.25.1 currency guard, the four bullet...</li>
<li>v0.25.1 - financial-engine: the bookkeeper's Amount column is guarded against...</li>
</ul>
<h3>z2w-crowdcommerce (2 commits)</h3>
<p><em>Donor email addresses are now normalized to prevent duplicate records from different capitalization or formatting variations</em></p>
<ul>
<li>z2w-crowdcommerce: the cancel-confirmation fix was pinned by nothing — now it...</li>
<li>z2w-crowdcommerce: v0.12.3 — donor_email was stored exactly as typed, and the...</li>
</ul>
<h3>courses-engine (1 commit)</h3>
<p><em>A data storage issue in the courses system was corrected</em></p>
<ul>
<li>courses-engine: v0.42.1 — a Contact Registry key filed under the wrong name w...</li>
</ul>
<h3>file-server (1 commit)</h3>
<p><em>Documentation was updated to clarify site-control requirements in the consumer table</em></p>
<ul>
<li>docs: site-control is in the consumer table at last, and it needs one token p...</li>
</ul>
<hr />
<p>Daily Work Summary initially created by <a href="https://zero2webmaster.com/kerry-kriger">Zero2Webmaster Founder Dr. Kerry Kriger</a></p>
<p>Contribute to the public repository at: https://github.com/zero2webmaster/daily-work-summary</p>
<p>Need to change the timing or timezone of these emails? <a href="https://github.com/zero2webmaster/daily-work-summary#customizing-the-email-schedule">Click here</a> for instructions.</p>
<p><em>Covers Sat Sep 12, 2026 · generated 2026-09-13 01:58 EDT</em></p></div>