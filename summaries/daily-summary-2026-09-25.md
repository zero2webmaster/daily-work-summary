<!-- daily-summary/v2 covers="2026-09-25" --><div style="font-size: 18px; line-height: 1.6;"><h1>Daily Work Summary — Fri Sep 25, 2026</h1>
<p><strong>54 commits</strong> across <strong>11 repos</strong></p>
<p>🧠 <strong>Skill Vault:</strong> 180 skills total <em>(Vault stats as of 2026-09-24)</em></p>
<hr />
<h2>zero2webmaster</h2>
<h3>event-engine (13 commits)</h3>
<p><em>The event management system was redesigned with improved photo viewing, event registration, and organizer tools, along with enhanced mobile usability and administrative controls</em></p>
<ul>
<li>event-engine: v0.76.2 — dim the page behind the photo viewer</li>
<li>event-engine: v0.76.1 — photo viewer fits a phone: shorter stage, arrow-only ...</li>
<li>event-engine: v0.76.0 — gallery viewer (built on static-sites' lightbox) with...</li>
<li>event-engine: v0.75.2 — touch-friendly drag to reorder gallery photos; hub im...</li>
<li>event-engine: v0.75.1 — a 'Register Your Own … Event' page per campaign, with...</li>
<li>event-engine: v0.75.0 — satellite image cards, /organize/<campaign> prefill l...</li>
<li>event-engine: v0.74.1 — outbound event links pointed at a savethefrogs.com 40...</li>
<li>event-engine: v0.74.0 — Edit Event link, admin-set organizer profile links (m...</li>
<li>event-engine: v0.73.0 — a series is one signup; reminders armed on a date's f...</li>
<li>event-engine: v0.72.3 — summary box unlabeled, pale brand tint</li>
<li>event-engine: v0.72.2 — type label under Register Here, reads In Person Event</li>
<li>event-engine: v0.72.1 — no hand-typed state on the registration form; state l...</li>
<li>event-engine: v0.72.0 — the event page reworked from Kerry's read of the DC m...</li>
</ul>
<h3>email-engine (12 commits)</h3>
<p><em>Mailing delivery reliability and reporting were improved, with fixes to handle step failures, better progress tracking, and timezone-aware scheduling capabilities</em></p>
<ul>
<li>v0.83.0 - A large mailing keeps sending when one step fails, and a resumed ma...</li>
<li>Roadmap: timezone-aware sends, so a mailing can arrive at 9 AM in each recipi...</li>
<li>Record the Million Frog March send results and the two fixes it surfaced</li>
<li>v0.82.1 - A mailing's progress and stats now count delivered emails as sent</li>
<li>v0.82.0 - A signature photo with no link now links to the signer's page</li>
<li>v0.81.0 - Letter headings are in the brand color, and a whole line can be bold</li>
<li>v0.80.0 - Letters can have section headings, and a mailing can end on its own...</li>
<li>v0.79.2 - Bogotá added to the timezone city list; Million Frog March announce...</li>
<li>v0.79.1 - The Segments list shows each segment's note behind an info circle; ...</li>
<li>The full-list SAVE THE FROGS! send is unblocked: bounce reports proven From n...</li>
<li>v0.79.0 - SAVE THE FROGS! newsletters come From news@savethefrogs.com again; ...</li>
<li>Record what stands between the engine and a full-list SAVE THE FROGS! send</li>
</ul>
<h3>z2w-social (8 commits)</h3>
<p><em>Documentation and configuration updates were made across Discord management, application deployment, database maintenance, and user-facing features like post interactions</em></p>
<ul>
<li>Docs: Discord cleanup applied and verified; request-to-join decisions</li>
<li>Docs: Discord cleanup previewed and waiting on permission; request-to-join idea</li>
<li>Docs: Discord-mentions scan results and the 14 form webhooks</li>
<li>Docs: installable app and feed likes shipped, three items for Kerry</li>
<li>Likes on profile posts and organization Updates</li>
<li>Make FrogSpace installable as an app (PWA)</li>
<li>Show Reply on grouped posts on phones</li>
<li>Docs: database password rotated, both test branches deleted</li>
</ul>
<h3>z2w-skill-vault (7 commits)</h3>
<p><em>Event display and content editing features were refined to improve usability across different devices and contexts</em></p>
<ul>
<li>scheduled-job-liveness: mode 9, a self-continuing drain that ends because 'se...</li>
<li>Catalog: owner for wordpress-bulk-content-edit</li>
<li>Add wordpress-bulk-content-edit: backup-before-write bulk edits, and FluentCR...</li>
<li>event-timezone-links: don't link every line of a date list; Kerry found four ...</li>
<li>event-timezone-links: converter links are for online events only; an in-perso...</li>
<li>event-timezone-links: a recurring series across any listed city's clock chang...</li>
<li>button-visibility: §5.5 a control revealed on hover does not exist on a phone</li>
</ul>
<h3>contact-registry (3 commits)</h3>
<p><em>Contact management workflows were streamlined to support quick addition, bulk import via paste, error feedback on invalid credentials, and contact recovery</em></p>
<ul>
<li>v0.76.0 - Delete a contact and restore it; the paste box fills in the country</li>
<li>v0.75.1 - Say what is wrong with a mis-pasted AI engine key</li>
<li>v0.75.0 - Quick add a contact, then fill the full record by pasting an email ...</li>
</ul>
<h3>site-control (3 commits)</h3>
<p><em>The static site design was updated with improved layout components, including session handoff support, label customization for content sections, and refined visual presentation of flyer pages</em></p>
<ul>
<li>site-control: z2w.us now opens with the static-sites design, words beside a d...</li>
<li>site-control: session handoff — flyer pages done, eyebrow and title slot ship...</li>
<li>site-control: bands can carry a small label above their headline, and an open...</li>
</ul>
<h3>courses-engine (2 commits)</h3>
<p><em>Users can now sign in to their own academy through a dedicated courses domain</em></p>
<ul>
<li>courses-engine: record that the last copy of the production database is delet...</li>
<li>courses-engine: v0.50.0 — Aharon can sign in to his own academy, at courses.a...</li>
</ul>
<h3>file-server (2 commits)</h3>
<p><em>The upload page layout was streamlined and listing rename functionality was added</em></p>
<ul>
<li>docs: v1.90.0 is merged and deployed on all three hosts [skip ci]</li>
<li>v1.90.0 - rename from the listing, and the upload page loses a row (#37)</li>
</ul>
<h3>org-hq (2 commits)</h3>
<p><em>Three environmental communications articles were prepared and published as WordPress drafts for volunteer review</em></p>
<ul>
<li>v0.60.0 - The three Environmental Communications articles are ready for WordP...</li>
<li>org-hq: next session publishes the three articles as WordPress drafts; volunt...</li>
</ul>
<h3>z2w-admin-suite (1 commit)</h3>
<p><em>Documentation was updated to record the deployment and verification of a release version</em></p>
<ul>
<li>docs: v1.119.5 deployed and verified; QR code qr_id 1 recorded</li>
</ul>
<h3>z2w-ai-suite (1 commit)</h3>
<p><em>Documentation was updated to record responses about resolved chat issues and security key revocation</em></p>
<ul>
<li>Docs: record Kerry's answers (chat bugs die; zero2webmaster.com keys revoked)</li>
</ul>
<hr />
<p>Daily Work Summary initially created by <a href="https://zero2webmaster.com/kerry-kriger">Zero2Webmaster Founder Dr. Kerry Kriger</a></p>
<p>Contribute to the public repository at: https://github.com/zero2webmaster/daily-work-summary</p>
<p>Need to change the timing or timezone of these emails? <a href="https://github.com/zero2webmaster/daily-work-summary#customizing-the-email-schedule">Click here</a> for instructions.</p>
<p><em>Covers Fri Sep 25, 2026 · generated 2026-09-26 03:32 EDT</em></p></div>