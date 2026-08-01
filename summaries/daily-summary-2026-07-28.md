<!-- daily-summary/v2 covers="2026-07-28" --><div style="font-size: 18px; line-height: 1.6;"><h1>Daily Work Summary — Tue Jul 28, 2026</h1>
<p><strong>38 commits</strong> across <strong>7 repos</strong></p>
<p>🧠 <strong>Skill Vault:</strong> 12 improved today · 95 skills total</p>
<hr />
<h2>zero2webmaster</h2>
<h3>z2w-skill-vault (12 commits)</h3>
<p><em>Internal systems and data handling were corrected across authentication, file serving, tenant isolation, spend controls, secret management, and lesson metadata</em></p>
<ul>
<li>zero-is-not-a-pass: \b is not the delimiter boundary you think it is</li>
<li>z2w-magic-link-auth: §10.4 — the Model A variant, where RLS'd tenant data sit...</li>
<li>file-server-service-api: the download URL key differs by endpoint, and a prox...</li>
<li>provider-spend-cap: §2.1.1 — keep the divergence margin small, and don't let ...</li>
<li>terminal-secret-hygiene: cleaning the leaked password out of the settings fil...</li>
<li>Record the description-budget watch, and fix a skill count that disagreed wit...</li>
<li>provider-spend-cap: the 90% margin belongs only on fail-open tiers, and "out ...</li>
<li>Say where a captured lesson's depth belongs: the body, not the description</li>
<li>Stripe: the Elements mode must match the intent type too, and check that ever...</li>
<li>Trim the longest always-loaded skill description back down</li>
<li>terminal-secret-hygiene: a password typed into a command by an agent gets com...</li>
<li>Three lessons from withdrawing 42 wrong findings in one day</li>
</ul>
<h3>z2w-multi-lingual (8 commits)</h3>
<p><em>Free-tier safety and operational reliability were improved through adjustments to usage tracking, safety margins, and documentation updates</em></p>
<ul>
<li>Docs: ROADMAP item 45 — combined free-tier bar sums usage over ALL providers ...</li>
<li>Docs: session close — LT out of routing, item 44 logged, next session = valid...</li>
<li>Settings: fix stale Fix C test guidance — it pointed at Amazon, whose key is ...</li>
<li>Docs: item 41 RETRACTED (not a bug) + production state — translation live on ...</li>
<li>Docs: v0.61.1 — record the two-knobs distinction (safety margin vs on-demand ...</li>
<li>v0.61.1 - Safety margin 10% -&gt; 3%: it was doing a job on_demand_reserve_pct a...</li>
<li>Install the canonical capture-learnings block in CLAUDE.md + AGENTS.md</li>
<li>v0.61.0 - Safe to run on free tiers again (ROADMAP items 20, 41, 42 parts 3+4)</li>
</ul>
<h3>audit-engine (6 commits)</h3>
<p><em>The audit engine was corrected to accurately record findings, withdraw incorrect ones, and prevent their recurrence</em></p>
<ul>
<li>audit-engine: record what the ledger actually says, and put the critical-seve...</li>
<li>audit-engine: a finding id cited in prose is not the finding — fix where retr...</li>
<li>v2.7.0 - the first sweep nobody watched filed 3 critical findings, and all 3 ...</li>
<li>v2.6.0 - write down what today cost, so the next session does not relearn it</li>
<li>audit-engine: record that the 42 wrong findings are now withdrawn</li>
<li>audit-engine: withdraw 42 findings that were wrong, and stop the check that p...</li>
</ul>
<h3>site-control (5 commits)</h3>
<p><em>Sign-in and content management were restructured to use email-based authentication and isolated database schemas for each website</em></p>
<ul>
<li>Record that sign-in is confirmed working, and hand off Step 4</li>
<li>Send sign-in emails from the resend. subdomain, not the root domain</li>
<li>Sign in to the admin with a link emailed to you, instead of a password</li>
<li>Stop a password from ever being committed, and pin down what "page" vs "artic...</li>
<li>Set up the content database, with each website's content walled off from the ...</li>
</ul>
<h3>video-migrator (4 commits)</h3>
<p><em>Storage optimization work was completed for the video library, with old copies removed and storage reclaimed clarified, along with documentation updates for the retrofit process</em></p>
<ul>
<li>Explain the savings (~$150/yr), confirm we did NOT lose 1080p, and write up h...</li>
<li>Correct the storage-reclaimed figure to ~503 GB (a unit slip said 491 GiB) + ...</li>
<li>Mark the retrofit batch runbook DONE and warn against running the two phases ...</li>
<li>Finish optimizing the whole Bansuri video library — old copies deleted, ~491 ...</li>
</ul>
<h3>z2w-seller-suite (2 commits)</h3>
<p><em>Annual donation subscriptions were corrected to point to the proper product configuration</em></p>
<ul>
<li>Terry's annual link would have been blocked at the last step: WooCommerce Sub...</li>
<li>Point Terry's email at the ANNUAL donation product so his recurring gift actu...</li>
</ul>
<h3>grantor (1 commit)</h3>
<p><em>Reviewers can now request additional information from applicants during the review process</em></p>
<ul>
<li>Let reviewers ask applicants for more information</li>
</ul>
<hr />
<p>Daily Work Summary initially created by <a href="https://zero2webmaster.com/kerry-kriger">Zero2Webmaster Founder Dr. Kerry Kriger</a></p>
<p>Contribute to the public repository at: https://github.com/zero2webmaster/daily-work-summary</p>
<p>Need to change the timing or timezone of these emails? <a href="https://github.com/zero2webmaster/daily-work-summary#customizing-the-email-schedule">Click here</a> for instructions.</p>
<p><em>Covers Tue Jul 28, 2026 · generated 2026-07-31 20:06 EDT</em></p></div>