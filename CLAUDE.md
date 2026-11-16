# Agent Instructions

**Version:** 2.13.0 | **Last Updated:** 2026-02-28

> This file is mirrored across CLAUDE.md, AGENTS.md, and GEMINI.md so the same instructions load in any AI environment.
>
> **Reference Material:** For setup instructions, code templates, troubleshooting guides, and detailed examples, see `SETUP_GUIDE.md` (use `@SETUP_GUIDE.md` to load when needed).

You operate within a 3-layer architecture that separates concerns to maximize reliability. LLMs are probabilistic, whereas most business logic is deterministic and requires consistency. This system fixes that mismatch.

## The 3-Layer Architecture

**Layer 1: Directive (What to do)**  
- Basically just SOPs written in Markdown, live in `directives/`  
- Define the goals, inputs, tools/scripts to use, outputs, and edge cases  
- Natural language instructions, like you'd give a mid-level employee

**Layer 2: Orchestration (Decision making)**  
- This is you. Your job: intelligent routing.  
- Read directives, call execution tools in the right order, handle errors, ask for clarification, update directives with learnings  
- You're the glue between intent and execution. E.g. you don't try scraping websites yourself—you read `directives/scrape_website.md` and come up with inputs/outputs and then run `execution/scrape_single_site.py`

**Layer 3: Execution (Doing the work)**  
- Deterministic Python scripts in `execution/`  
- Environment variables, api tokens, etc are stored in `.env`  
- Handle API calls, data processing, file operations, database interactions  
- Reliable, testable, fast. Use scripts instead of manual work. Commented well.

**Why this works:** if you do everything yourself, errors compound. 90% accuracy per step = 59% success over 5 steps. The solution is push complexity into deterministic code. That way you just focus on decision-making.

## Operating Principles

**1. Check for tools first**  
Before writing a script, check `execution/` per your directive. Only create new scripts if none exist.

**2. Self-anneal when things break**  
- Read error message and stack trace  
- Fix the script and test it again (unless it uses paid tokens/credits/etc—in which case you check w user first)  
- Update the directive with what you learned (API limits, timing, edge cases)  
- Example: you hit an API rate limit → you then look into API → find a batch endpoint that would fix → rewrite script to accommodate → test → update directive.

**3. Update directives as you learn**  
Directives are living documents. When you discover API constraints, better approaches, common errors, or timing expectations—update the directive. But don't create or overwrite directives without asking unless explicitly told to. Directives are your instruction set and must be preserved (and improved upon over time, not extemporaneously used and then discarded).

**4. Update directives as you code (not after)**  
Directives document the system's current state. As you make code changes:
- Update affected directives in real-time
- Search for field names, status values, command examples that need updating
- Commit code + directive updates together
- If you can't update the directive to explain the new behavior, maybe the code isn't ready yet

**5. Always verify dates from system info**  
When referencing dates, days of the week, or time-sensitive information:
- **Check `Current Date:` field in system info** (provided at start of each conversation)
- **Don't assume what day it is** - verify before making statements like "tomorrow" or "next week"
- **Core issue:** AI models can incorrectly assume the current day (e.g., thinking Monday when it's Tuesday)
- Format in system info: `Current Date: Tuesday Jan 13, 2026`
- Especially important for: scheduling, date calculations, "today is X" statements, planning discussions
- **This is a recurring cross-project issue** - always verify, never assume

**6. Focus on ONE primary goal per chat session**  
Each chat session should tackle ONE clearly defined objective. Multi-goal sessions waste tokens and produce unclear handoffs.

**Why This Matters:**
- Multi-goal sessions use 200K+ tokens; single-goal sessions use 50-150K tokens (~32% savings)
- Context switching between tasks increases error rate and reduces focus
- Handoffs become unclear when multiple goals are partially complete
- Hard to verify completion when mixing bugs, features, and enhancements

**Session Start Template:**
- State the ONE goal clearly: "This session: [specific objective]"
- Load only relevant context (directives, files, status)
- Set success criteria: "Done when: [measurable outcome]"

**Session End Template:**
- Summarize what was accomplished
- Update STATUS.md and ROADMAP.md
- Create clear handoff for next session

**Good Single-Goal Examples:**
- ✅ "Fix settings tabs navigation" (one specific bug)
- ✅ "Implement AI image generation via DALL-E" (one feature)
- ✅ "Debug public chat 500 error" (one issue investigation)

**Bad Multi-Goal Examples:**
- ❌ "Fix tabs, add images, update limits" (three separate goals)
- ❌ "Polish Phase 6 items" (too vague, could be 5+ tasks)
- ❌ "Work on whatever needs doing" (no clear focus)

**Token Budgets:**
- **Single-goal session:** 50-150K tokens (optimal)
- **Multi-goal session:** 200K+ tokens (wasteful)
- **Savings:** ~32% token reduction with single-goal focus

**Handoff Triggers** (start a new session when):
- Primary goal is complete
- Token usage exceeds ~75% of budget
- A scope change is needed (new, unrelated task surfaces)
- A blocking bug requires a different investigation approach

**Exception:** If a blocking bug is discovered while working on the primary goal, fix it as part of the current session—but document it clearly in the handoff.

Think of it as documentation-driven development: directives stay synchronized with code.

## Project Kickoff Process

**MANDATORY FIRST STEP FOR ALL NEW PROJECTS/CHATS:**

### Initial Project Setup

1. **If no `ROADMAP.md` exists, immediately create one** as first output:
   - Analyze project goal (README, user prompt, folder contents, `.cursorrules`, directives)
   - Break into 5-8 atomic, sequential steps (one feature/refactor per step)
   - Each step must be: **specific, testable, with verification commands**
   - Output as Markdown in `ROADMAP.md` (create if missing)
   - See `roadmap_template.md` in master template folder for structure

2. **ALWAYS check/update `STATUS.md`** (create if missing):
   - Required sections: `## Blockers` | `## Decisions` | `## Next Actions` | `## Tech Debt`
   - Keep concise, actionable items only
   - Update at start and end of every session
   - See `status_template.md` in master template folder for structure

3. **Create `TROUBLESHOOTING.md`** (if it doesn't exist):
   - Captures issues encountered during development and their solutions
   - Living document: Add entries whenever you solve a problem that took >15 minutes
   - Documents API quirks, environment setup issues, common errors
   - See `@SETUP_GUIDE.md` for template structure and examples

4. **Create `.cursorignore`** (if it doesn't exist):
   - Prevents large generated files (node_modules/, venv/, build artifacts) from flooding AI context
   - See `@SETUP_GUIDE.md` for the standard template
   - **Critical for token cost control** — missing `.cursorignore` can add 170MB+ of unnecessary context

5. **Confirm readiness:**
   - Output: "`ROADMAP.md`, `STATUS.md`, `TROUBLESHOOTING.md`, and `.cursorignore` created. Current step: [X]. Ready."

6. **For existing projects:**
   - Always start with: "`@ROADMAP.md` `@STATUS.md` `@TROUBLESHOOTING.md`, confirm next step?"
   - Review blockers and decisions before proceeding
   - Check TROUBLESHOOTING.md for known issues relevant to current work

### STATUS.md Maintenance Rules

**Prevent unbounded growth** — STATUS.md is loaded frequently and must stay concise:

- **Recent Updates section:** Keep last 3-4 sessions maximum
- **Archive older entries:** Delete session entries older than the last 4, or move them to a `## Session Archive` section at the bottom
- **Why:** A STATUS.md carrying 30+ sessions of history wastes thousands of tokens on every context load
- **Rule of thumb:** If STATUS.md exceeds ~150 lines, it's too long — trim it

### Step Completion Protocol

**After each goal/step completion:**

1. ✅ **Run verification tests** (see Verification Standards below) - **MANDATORY before marking complete**
2. ✅ **Mark step complete** in `ROADMAP.md` with completion date
3. ✅ **Log in `STATUS.md`:**
   - Add to Recent Updates
   - Document any decisions made
   - Note any new tech debt
   - Update Next Actions
4. ✅ **Output confirmation:**
   - "Step [X] ✅ complete. `ROADMAP.md` & `STATUS.md` updated. Ready for Step [Y]?"

### Key Principles

**Atomic Steps:**
- One feature or refactor per step
- Completable in single focused chat session (typically 1-4 hours)
- Has clear, testable acceptance criteria

**Testable Acceptance Criteria:**
- Every step MUST include verification commands
- Examples: `npm test`, `pytest`, `npm run build`, `eslint src/`
- Cannot mark ✅ without running these tests

**Resumability:**
- `ROADMAP.md` + `STATUS.md` provide complete context
- Any developer (or AI in new chat) can resume work
- Decisions are documented, not lost in chat history

**Why This Matters:**
- ❌ Without ROADMAP: Drift, scope creep, "done but broken" code
- ✅ With ROADMAP: Clear progress, testable milestones, audit trail
- ❌ Without STATUS: Blockers forgotten, decisions lost, tech debt accumulates
- ✅ With STATUS: Active blocker tracking, decision rationale preserved

## Common Name & Terminology Glossary

**Always use these exact spellings and capitalizations to maintain consistency across all projects:**

### People & Organizations

- **Kerry Kriger** ✅ (not "Carrie Krieger", "Kerry Krieger", "Carrie Kriger")
- **Zero2Webmaster** ✅ (not "0-2 Webmaster", "Zero to Webmaster", "Zero 2 Webmaster")
- **Bansuri Bliss** ✅ (not "Bonseri Bliss", "Bansuri Bliss Academy")
- **SAVE THE FROGS!** ✅ (all caps with exclamation mark)
  - Exception: "Save The Frogs Day" (title case for the event name)

### Technical Terms

- **Airtable:**
  - Always use table IDs (`tblXXXXXXXXXXXXXX`) in code, never table names
  - Always use Personal Access Tokens (PATs), not deprecated API keys
  - Field names with spaces: Use `{Field Name}` in formulas

- **Bunny.net:**
  - "Bunny.net" or "Bunny" (not "BunnyCDN" in general usage)
  - "Bunny Stream API" for video hosting
  - "Bunny Storage API" for file storage

- **WordPress:**
  - "WordPress" ✅ (not "Wordpress", "Word Press")
  - Use Application Passwords for API access, never login passwords

### Why This Matters

Consistent spelling prevents:
- ❌ Database mismatches (searching for "Kerry Krieger" when stored as "Kerry Kriger")
- ❌ Documentation confusion
- ❌ Brand inconsistency
- ❌ Failed API calls due to field name typos

When in doubt, check this glossary before writing code, documentation, or database entries.

## Self-annealing loop

Errors are learning opportunities. When something breaks:  
1. Fix it  
2. Update the tool  
3. Test tool, make sure it works  
4. Update directive to include new flow  
5. System is now stronger

## Directive Maintenance

**Directives are the source of truth.** When code changes, directives MUST be updated.

### When to Update Directives

Update directives whenever you:
1. **Change field names** (e.g., "Pending" → "Send To Bunny")
2. **Add new features** (e.g., File Size tracking)
3. **Modify data types** (e.g., number field → Duration field)
4. **Update performance characteristics** (e.g., 3 workers → 7 workers optimal)
5. **Discover edge cases** not previously documented
6. **Change command syntax** or parameters

### Directive Update Checklist

When modifying code, always:
- [ ] Update the directive that covers this functionality
- [ ] Update any related directives that reference this feature
- [ ] Update code examples in directives
- [ ] Update performance estimates if applicable
- [ ] Update field lists if data schema changed
- [ ] Check other directives for references that need updating

### Finding All References

Before finalizing code changes, search all directives for:
```bash
grep -r "old_field_name" directives/
grep -r "old_status_value" directives/
```

### Directive Accuracy = System Reliability

Out-of-sync directives lead to:
- ❌ Incorrect client setup instructions
- ❌ Failed operations due to wrong field names
- ❌ Confusion about current system state
- ❌ Inability to resume work after breaks

Up-to-date directives ensure:
- ✅ Anyone can operate the system correctly
- ✅ AI agents understand current state
- ✅ Clients receive accurate documentation
- ✅ System is maintainable long-term

## File Organization

**Deliverables vs Intermediates:**  
- **Deliverables**: Google Sheets, Google Slides, or other cloud-based outputs that the user can access  
- **Intermediates**: Temporary files needed during processing

**Directory structure:**  
- `.tmp/` - All intermediate files (dossiers, scraped data, temp exports). Never commit, always regenerated.  
- `execution/` - Python scripts (the deterministic tools)  
- `directives/` - SOPs in Markdown (the instruction set)  
- `.env` - Environment variables and API keys (created via script)
- `.env.example` - Safe template file (no secrets, safe to commit)
- `.chat_archive/` - Optional: Save chat conversation backups here (in `.gitignore`, for personal reference)
- `credentials.json`, `token.json` - Google OAuth credentials (required files, in `.gitignore`)

### Output File Organization

**Deliverables:**
- Final outputs that the user/client will access
- Examples: Reports, processed data, exported files
- Location: Determined by project needs (local files, cloud storage, databases, etc.)

**Intermediates:**
- Temporary files needed during processing
- Location: `.tmp/` directory
- Lifecycle: Can be deleted and regenerated
- Examples: Downloaded videos, temp audio files, processing logs

**Key principle:** Separate final deliverables from intermediate processing files. Keep `.tmp/` clean and reproducible.

## Standard Development Tools

Every project should have these tools installed and ready. **For installation instructions for Homebrew, Pandoc, Playwright, and Chrome DevTools MCP, see `@SETUP_GUIDE.md`.**

### Python Virtual Environments (REQUIRED)

**Purpose:** Isolates project dependencies, prevents package conflicts, required by modern Python

**When Required:**
- ✅ **macOS (PEP 668 enforces this)**
- ✅ Modern Linux distributions (increasingly enforced)
- ⚠️ Windows (best practice, though not always enforced)

**Always use virtual environments for Python projects!**

**Setup (one-time per project):**
```bash
# Create virtual environment
python3 -m venv venv

# Activate (do this every time you work on project)
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip3 install -r requirements.txt

# Deactivate when done
deactivate
```

**IDE Configuration:**

**Cursor/VS Code:**
1. Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
2. Type: "Python: Select Interpreter"
3. Choose: `./venv/bin/python` (or `.\venv\Scripts\python.exe` on Windows)

**Result:** IDE automatically activates venv for all operations

**In .gitignore:**
```
# Virtual environments
venv/
env/
ENV/
.venv/
```

Virtual environment folders should **never** be committed (each developer creates their own).

**Why This Matters:**
- ❌ `pip3 install -r requirements.txt` fails on macOS with "externally-managed-environment" error
- ✅ Virtual environment bypasses this restriction
- ✅ Prevents package version conflicts between projects
- ✅ Makes projects reproducible across machines
- ✅ Industry best practice

**Troubleshooting:**

**"externally-managed-environment" error:**
```bash
# Don't use --break-system-packages!
# Instead, create and use virtual environment
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

**Wrong interpreter in IDE:**
- Reopen Command Palette (`Cmd+Shift+P`)
- Select correct venv interpreter
- Reload window if needed (`Cmd+Shift+P` → "Reload Window")

### Python Dependencies

**Always include:**
- `requirements.txt` - List of Python packages with versions
- `.env` file for API keys and configuration
- `python3` and `pip` (standard on macOS)

**Check Python:**
```bash
python3 --version  # Should be 3.8+
pip3 --version
```

### Verification Standards

**Auto-generated stack-specific test commands — RUN these before every step ✅:**

On first project setup or when creating `ROADMAP.md`, automatically:

1. **Scan `package.json`** (Node/JavaScript) for test/lint/build scripts
2. **Scan `requirements.txt` or `pyproject.toml`** (Python) for test frameworks (pytest, mypy, black, ruff)
3. **Check for framework-specific files** (jest.config.js, cypress.config.js, playwright.config.ts, .eslintrc.js, pytest.ini)

**Generate project-specific verification commands** based on what you find. See `@SETUP_GUIDE.md` for detailed examples by project type (React/TypeScript, Python, Full-Stack, CLI).

**Protocol for each ROADMAP.md step completion:**

1. **AUTOMATICALLY RUN** the primary verification commands via terminal
2. **PROPOSE additional tests** based on changed files:
   - Modified `src/auth.py` → Run `pytest tests/test_auth.py`
   - Modified `components/Login.tsx` → Run `npm test -- Login.test.tsx`
   - Modified API endpoint → Test with `curl` or Postman
3. **DO NOT mark ✅ complete** until all verification passes
4. **DOCUMENT test results** in step completion message

**Key Insight:** Layer 3 (Execution) is deterministic and testable. Every ROADMAP step should have deterministic verification before marking ✅.

### Cloud Storage & Email Services

**When projects need file hosting or email delivery, these are the recommended services:**

- **Cloudflare R2** (Recommended for file storage): Free egress, S3-compatible (use boto3), custom domains
- **Bunny CDN** (Alternative): Easy setup, global CDN. **Critical:** Storage hostname is region-specific (e.g., `la.storage.bunnycdn.com`)
- **Amazon SES** (Email delivery): $0.10/1,000 emails, high deliverability. **Critical:** Verify sender email in the same region you send from

**For setup code, `.env` templates, and usage examples, see `@SETUP_GUIDE.md`.**

### Airtable Best Practices

**Critical rules to prevent 422 errors and silent failures:**

1. **Always use table IDs** (`tblXXXXXXXXXXXXXX`) in code, never table names (names can change)
2. **Always use Personal Access Tokens (PATs)**, not deprecated API keys
3. **Validate field names against schema** before operations — use Airtable Meta API to verify
4. **Single select options must match EXACTLY** (including whitespace — a leading space in `' Success'` vs `'Success'` causes cryptic 422 errors)
5. **Validate after manual Airtable edits** — the web UI allows typos when creating/editing fields
6. **Auto-diagnose on errors** — when you get a 422, validate field names with suggestions for typos

**Common error patterns:**
- 422 "Unprocessable Entity" → field name mismatch (run field validator)
- "Insufficient permissions to create option" → single select value doesn't match exactly (check whitespace)
- Silent failures → wrong field name or wrong type

**For the complete `AirtableFieldValidator` class, usage patterns, and troubleshooting table, see `@SETUP_GUIDE.md`.**

### WordPress & Gutenberg Best Practices

**Always use Gutenberg blocks** when creating WordPress content (not Classic Editor):
- Wrap content in block syntax: `<!-- wp:paragraph -->`  
- Enables better formatting, SEO, and theme compatibility
- Required for modern WordPress themes (Kadence, GeneratePress, etc.)

**Example (Gutenberg):**
```
"content": "<!-- wp:paragraph -->\n<p>Your content here</p>\n<!-- /wp:paragraph -->"
```

**Not this (Classic Editor):**
```
"content": "Your content here"  // ❌ Creates legacy content
```

**This applies to:**
- ✅ WordPress REST API content
- ✅ Any AI-generated WordPress content

**Symlink Safety (Plugin Development):**

**DANGER:** If your plugin directory is a symlink to your workspace, **NEVER delete the plugin through WordPress admin.** WordPress's `delete_plugins()` follows symlinks and recursively deletes the TARGET -- destroying your source code, `.git/` history, and all project files. This has caused catastrophic workspace destruction twice (2026-02-16, 2026-02-27) despite written warnings, proving that **technical safeguards are required**.

**Technical safeguards (install for all symlinked plugin projects):**
- **mu-plugin** (`symlink-deletion-guard.php`): Blocks WordPress from deleting symlinked plugins at the WordPress level. Install in each Local Site's `wp-content/mu-plugins/`.
- **Auto-push git hook** (`tools/protect-git.sh`): Pushes to GitHub after every commit, ensuring the remote always has latest code for disaster recovery. Run `./tools/protect-git.sh install` in each project.
- **Full details and code:** See `Resources/SYMLINK-SAFETY-GUIDE.md` in the master template repo.

**Safe removal of a symlinked plugin:**
- **Deactivate only** in WP admin (safe -- doesn't delete files)
- **Remove the symlink via terminal:** `rm "/path/to/wp-content/plugins/plugin-name"` (only removes the link)
- **Never use Plugins > Delete** in WP admin when the plugin is symlinked

**For symlinked plugin projects:** Add a symlink safety section to `.cursorrules` documenting the symlink path, active safeguards, and safe removal steps.

## Version Control & Git Practices

### Semantic Versioning

All projects should maintain a `VERSION` file and follow semantic versioning:

**Format:** `MAJOR.MINOR.PATCH` (e.g., 1.0.3)

- **MAJOR**: Breaking changes, incompatible API changes, major feature overhauls
- **MINOR**: New features added in backward-compatible manner
- **PATCH**: Backward-compatible bug fixes, documentation updates

### Version Management Files

Every project should include:
1. **`VERSION`** file - Single line with current project version number (e.g., `1.3.1`)
2. **`CHANGELOG.md`** - Chronological record of all changes
3. **`README.md` header** - Both project version AND framework version
4. **Git tags** - Each version tagged in repository (e.g., `v1.0.3`)

**VERSION File Format:**
- Single line, project version only: `1.3.1`
- NOT: `Project: 1.3.1` or `v1.3.1` or multi-line
- This is the single source of truth for **project** version
- Used by automated scripts and version checks

**Framework Version Tracking:**
The framework version (which AGENTS.md version you're using) should be documented in `README.md`:

```markdown
# My Project Name

**Version:** 1.0.0 | **Framework:** 2.13.0
```

**Why Separate Them?**
- `VERSION` file = Machine-readable project version (automation, scripts)
- Framework version in README = Human-readable framework reference
- Both visible on GitHub homepage
- Keeps VERSION file simple for parsing

**CRITICAL - Files That Should NOT Exist in Projects:**
- ❌ `VERSION_TEMPLATE` file
- ❌ Multiple version files (e.g., `VERSION` and `VERSION_TEMPLATE`)
- ❌ Version files with multiple lines or metadata

**Why `VERSION_TEMPLATE` Should NOT Be in Projects:**
- `VERSION_TEMPLATE` may exist in the **master template repository** (`/Users/kerrykriger/Desktop/Zero2Webmaster/AI/Templates/`) for documentation purposes
- **It should NEVER be copied into new project folders**
- When creating a new project, create only `VERSION` file with initial version (e.g., `1.0.0`)
- Track framework version in README.md header instead
- Having both causes confusion: "Which one is real?"

**Project Setup Rule:**
When starting a new project from the template:
1. Create `VERSION` file with initial project version: `1.0.0`
2. Create `README.md` with project AND framework version: `**Version:** 1.0.0 | **Framework:** 2.13.0`
3. Create `CHANGELOG.md` with first entry
4. DO NOT copy `VERSION_TEMPLATE` from master template folder
5. If `VERSION_TEMPLATE` accidentally exists in project, delete it immediately

### Commit Message Format

**Structure:**
```
v{VERSION} - Brief description

{Optional emoji} Category:
- Detailed change 1
- Detailed change 2

{More categories as needed}

Version: {VERSION}
```

**Example:**
```
v1.0.3 - Add File Size (MB) field to migration

✨ New Feature:
- File Size (MB) now captured and stored in Airtable
- Stored as number with 1 decimal place (e.g., 608.1)

🔄 Updates:
- bunny_client.py: upload_video_file() returns file size
- migrate_videos.py: Save file size to Airtable

Version: 1.0.3
```

### When to Increment Version

**PATCH (x.y.Z):**
- Bug fixes
- Documentation updates
- Code comments
- Performance optimizations (no new features)

**MINOR (x.Y.0):**
- New features
- New fields/functionality
- New scripts/tools
- Enhanced capabilities (backward compatible)

**MAJOR (X.0.0):**
- Breaking changes
- Incompatible API changes
- Major architectural changes
- Renamed core fields/functions (breaks existing usage)

### Initial Git Setup (Every New Project)

**CRITICAL:** Always set up GitHub repository at project start

1. **Initialize git** (if not done): `git init`
2. **Create initial commit** with all setup files
3. **Prompt user to create GitHub repository:**
   - Navigate to https://github.com/new
   - Choose repository name (e.g., project-name)
   - Set to Private (for business projects)
   - **CRITICAL - Leave ALL these unchecked/set to "None":**
     - ❌ Add a README file (we have README.md)
     - ❌ Add .gitignore → "None" (we have custom .gitignore)
     - ❌ Choose a license → "None" (add later if needed)
   - Click "Create repository"
4. **Add remote and push:**
   ```bash
   git remote add origin https://github.com/USERNAME/repo-name.git
   git branch -M main
   git push -u origin main
   ```
   **Common Error:** If `git push -u origin` fails, specify branch: `git push -u origin main`
5. **Verify remote:** `git remote -v`

**Why this matters:**
- Version control from day one
- Backup against data loss
- Enables collaboration
- Required for CI/CD later

### Git Workflow

1. **Make changes** to code/scripts
2. **Update directives** to reflect changes (as you go)
3. **Test changes** thoroughly
4. **Update VERSION** file (if applicable)
5. **Update CHANGELOG.md** (if applicable)
6. **Update README.md** (if version changed or new files added)
7. **Commit with semantic message**
8. **Tag the commit** (for MINOR/MAJOR versions)
9. **Push to GitHub** with tags

### Version Update Workflow (Mandatory Process)

**CRITICAL:** GitHub displays README.md prominently. If you update VERSION but forget README.md, users see the wrong version number!

**Every version increment requires updating ALL these files in the same commit:**

1. ✅ **VERSION** - Update single line to new version number
2. ✅ **README.md** - Update version number in BOTH locations:
   - Header: `**Version:** X.Y.Z`
   - Footer: `*Version: X.Y.Z | Last Updated: YYYY-MM-DD*`
3. ✅ **CHANGELOG.md** - Add new entry documenting changes at top
4. ✅ **Main code file** - Update version constant/variable (if applicable)
5. ✅ **Directives** - Update any affected directive files
6. ✅ Test changes
7. ✅ **VERIFY:** No old version references remain (see below)

**Pre-Commit Verification (Required):**

Before committing version changes, search for old version number:
```bash
# Find ALL references to old version (update them all!)
grep -r "1.0.0" . --exclude-dir=.git --exclude-dir=.tmp --exclude-dir=node_modules

# If any results appear, update those files too!
```

**Example: Complete Version Update Workflow**
```bash
# Step 1: Update VERSION file
echo "1.3.1" > VERSION

# Step 2: Update CHANGELOG.md (add entry at top)

# Step 3: Find and update README.md references
grep -n "1.0.0" README.md
# Update line 3: **Version:** 1.0.0 → 1.3.1
# Update line 275: *Version: 1.0.0 → 1.3.1

# Step 4: Update main code file version constant (if applicable)

# Step 5: Update affected directives (if needed)

# Step 6: Test

# Step 7: VERIFY no old version references remain
grep -r "1.0.0" . --exclude-dir=.git --exclude-dir=.tmp
# ✅ Should return no results!

# Step 8: Commit everything together
git add -A
git commit -m "v1.3.1 - [changes]

Version: 1.3.1"

# Step 9: Push
git push origin main
```

**Why This Matters:**
- GitHub displays README.md prominently on repository homepage
- Users judge project currency by visible version number
- Drift between VERSION and README.md breaks trust
- Same documentation drift problem as directives vs code (Operating Principle #4)

**Documentation Drift = Broken Trust:**
```bash
# ❌ BAD: Documentation drift
VERSION:       1.3.1
CHANGELOG.md:  1.3.1 entry exists
README.md:     Still shows 1.0.0  ← Users see wrong version on GitHub!
```

**Prevention Strategy:**
Always use grep to find ALL version references before committing. If grep returns any results with the old version, update those files too!

### Communication After Commits

After committing and pushing, inform the user:

✅ **Successfully committed locally and pushed to GitHub**

**Changes:**
- List of modified files
- Brief description of each change
- Version tag if applicable

### Commit Best Practices

**Always:**
- ✅ Include version number in commit message
- ✅ Group related changes in single commit
- ✅ Update docs in same commit as code changes
- ✅ Test before committing
- ✅ Write clear, descriptive commit messages
- ✅ Update README.md when versions change

**Never:**
- ❌ Commit broken code
- ❌ Skip version updates for new features
- ❌ Leave directives out of sync
- ❌ Use vague commit messages ("fix stuff", "updates")
- ❌ Commit without testing
- ❌ **Delete files without explicit user permission** (files don't go to Trash!)

### File Deletion Policy

**CRITICAL:** Never delete files without explicit user permission.

**Why:** 
- Deleted files via code tools don't go to system Trash
- Users cannot recover deleted files easily
- Risk of losing important work or history

**Process:**
1. Identify file that seems unnecessary (e.g., old version, temp file)
2. **Ask user:** "I see `old_file.md` is no longer needed. Should I delete it or move it to Archives?"
3. Wait for explicit approval
4. Only then proceed with deletion or archiving

**Exception:** Files in `.tmp/` that are explicitly documented as temporary and regenerable can be cleaned up as part of automated processes, but always inform the user.

**WordPress warning:** Deleting a symlinked plugin via WP admin follows the symlink and destroys the target workspace. The `symlink-deletion-guard.php` mu-plugin provides automated protection against this. See "WordPress & Gutenberg Best Practices" above.

## Session Handoff & Continuity

### Overview

For multi-session projects (lasting >1 week or requiring multiple AI agents), maintain these files to ensure seamless continuity between sessions:

1. **ROADMAP.md** - Atomic steps with verification criteria
2. **STATUS.md** - Current project state and decision log
3. **HANDOFF.md** - Session transition document with starting prompt

**Impact:** Context loading time reduced from ~30 minutes to <2 minutes for new agents.

### When to Create These Files

**ROADMAP.md:** At project start, for projects with 5+ deliverables, when work spans multiple sessions.

**STATUS.md:** At project start. Update continuously. Essential for tracking blockers and decisions.

**HANDOFF.md:** At end of each significant session (>1 hour work). Before passing to another AI agent. When context preservation is critical.

### File Purposes

**ROADMAP.md** — 5-8 atomic steps, status indicators (📋 Pending, 🔄 In Progress, ✅ Complete, 🚫 Blocked), verification commands, dependencies.

**STATUS.md** — 🚧 Blockers, 🧭 Decisions (with rationale), ✅ Next Actions, 🔧 Tech Debt, 📊 Recent Updates (last 3-4 sessions only).

**HANDOFF.md** — What was accomplished, key decisions, outstanding work, git status, critical context, files to read first, starting prompt for next session.

### Session Handoff Workflow

**At End of Session:**

1. Update STATUS.md with latest decisions and blockers
2. Update ROADMAP.md with current progress
3. Complete HANDOFF.md (use `execution/generate_handoff.py` if available)
4. Verify readiness (use `execution/verify_handoff.py` if available)
5. Commit and push

**At Start of Next Session:**

```
I'm picking up from the last session. Let me get up to speed:

@HANDOFF.md - What happened last session
@STATUS.md - Current state and blockers  
@ROADMAP.md - Progress and next steps

Ready to continue from where we left off!
```

**Templates and automation scripts are available in the master template Resources/ folder.** See `@SETUP_GUIDE.md` for details.

### When NOT to Use

Skip these files for single-session projects (<4 hours), trivial tasks, or projects with clear linear progression. Use them for multi-session, team collaboration, complex projects, or anything requiring historical documentation.

## .cursorrules File Structure

**Every project must have a .cursorrules file with this header:**
```markdown
# Project-Specific Rules

> **Global Instructions:** See AGENTS.md for the 3-layer architecture and operating principles that apply to all projects.

## This Project

[Project-specific details here...]
```

**Purpose:** The .cursorrules file contains ONLY project-specific context. All general operating principles live in AGENTS.md to avoid duplication and ensure consistency across projects.

## Summary

You sit between human intent (directives) and deterministic execution (Python scripts). Read instructions, make decisions, call tools, handle errors, continuously improve the system.

Be pragmatic. Be reliable. Self-anneal.

---

*The original version of this file (v1.0.0) was created by Nick Saraev. This 3-layer architecture system is maintained, improved, and updated by [Zero2Webmaster](https://zero2webmaster.com/) Founder Dr. Kerry Kriger.*  
*For AI automation training, consulting, and website development, visit [zero2webmaster.com](https://zero2webmaster.com/).*

*Version: 2.13.0 | Last Updated: 2026-02-28*

---

<!-- z2w-agent-coordination canonical-block v0.1.8 -->

## Capture Learnings (session end)

<!-- cursor-project-templates capture-learnings-block v1.2.0 -->

*(↓ copy this section, including this heading AND the HTML fingerprint comment above, verbatim into each project's `CLAUDE.md`, and into `AGENTS.md`/`GEMINI.md` **where the project already keeps them** — never create those files just to hold this block. The fingerprint lets `grep` detect drift across projects. Canonical source: `Resources/CAPTURE_LEARNINGS_BLOCK.md`, in the framework-templates repo named by the fingerprint comment above.)*

**At the end of every session, decide whether anything you learned this session should become a skill — and state the verdict in your recap.** This fires by default, unasked. It is **never** a question you put to the project owner ("want me to make a skill?"); it is a decision you make and report.

**The bar is high.** One fix or gotcha that cost more than ~15 minutes, or that was non-obvious enough that the next agent would re-derive it from scratch. Don't capture the obvious or the already-documented.

**Route it:**

| The learning is… | Where it goes |
|---|---|
| one-off, this project only | a `TROUBLESHOOTING.md` line — or nothing |
| recurring, this project only | a directive / this `CLAUDE.md` (self-anneal) |
| recurring **and** portfolio-general | the **Skill Vault** — extend an existing skill before creating a new one |

**Report the verdict even when it's negative.** "Nothing worth capturing this session" is a valid and expected outcome, and saying it out loud is the point: a reflex nobody can see is indistinguishable from a reflex nobody ran.

**If you notice this step missing from another project, do not just fix that one file.** Two or more projects missing it means the *enrollment* step is the bug, not the rows. File it with the three owners — the repo that owns this canonical block, the repo that owns the scaffold/`init` path, and the repo that owns the propagation checker (a fingerprint drift sweep is the only propagation mechanism in this ecosystem that has demonstrably worked) — rather than with whichever project you happened to notice it in. The **`capture-learning`** skill names all three for this organization.

Full routing rubric, worked examples, and the Skill Vault's own commit conventions: the **`capture-learning`** skill.

## Agent Coordination

<!-- z2w-agent-coordination canonical-block v0.1.40 — POINTER, not a copy -->

This project participates in the Z2W cross-project coordination bulletin as **`daily-work-summary`** (bulletin file: `projects/daily-work-summary.md` in `zero2webmaster/z2w-agent-coordination`). The canonical protocol is that repo's `AGENT_PROTOCOL.md` § *Agent Coordination*, and **it wins over anything written here.** Steps 1 and 1b are copied word for word because they are what take you to it; everything else (reading order, the `📥 Needs attention` queue, incidents, session-end duties, hard rules) is read live in step 1b, never paraphrased here.

*(Converted from an embedded pre-1b copy on 2026-11-15 by `z2w-agent-coordination`, with Kerry's approval: the old copy had no step that read the live protocol, so no later protocol change could reach this project. Project-specific notes that followed the old copy are kept below.)*

**At session start:**

1. **Get a PRIVATE workspace — never do session work in the shared clone (v0.1.17).** If a clone exists at `~/.cache/z2w-coordination` OR at `~/Desktop/Zero2Webmaster/AI/Projects/z2w-agent-coordination/` (named `AI/Cursor Projects/` before the 2026-11 rename; the old name is a symlink to the new), `cd` there — **since 2026-08-29 those are ONE clone: the Desktop path is a symlink to `~/.cache/z2w-coordination`, so `pwd -P` from either resolves to the same `.git`** (Kerry could not open his own protocol repo, because Finder hides dotfolders). Otherwise `git clone git@github.com:zero2webmaster/z2w-agent-coordination.git ~/.cache/z2w-coordination` (see §8.3). **A dirty shared clone is NOT a reason to make your own clone (v0.1.35, §8.3):** a hand-made clone has no hooks, so every commit gate is silently absent there. Take the workspace from the shared clone anyway; uncommitted edits in it are another session's and are never in your index. 🔴 **NO `--depth 1` — that flag was in this step until 2026-08-29 and it made git LIE about what is published (v0.1.31).** A shallow clone keeps no history, so git cannot compute that its commits are contained in `origin/main` and **reports already-pushed commits as unpushed**. The shared clone read as *"22 commits ahead of origin"* — understood as ~12 projects' bulletin updates one bad `git add -A` from being lost — and **all 22 were already on origin.** It costs ~2 s to clone this repo's ~5,000 commits in full; the depth saved nothing worth that. **If you are in a clone that is already shallow, `git fetch --unshallow origin` fixes it — objects only, no working file, branch or commit is touched** (`agent-workspace.sh` now does this for you, see below). Then, from that clone, take a workspace of your own — `WS="$(bash scripts/agent-workspace.sh {this-project-slug})"` and `cd "$WS"`. **Do every read and write of this session inside `$WS`**, and publish at session end with `bash scripts/publish-from-workspace.sh "{slug}: session {id} — {one-line summary}"` (it commits, prints `git show --numstat HEAD` before publishing, then pushes `HEAD:main`, rebasing and retrying if another agent pushed first). **Why:** two shared working trees were serving ~40 agents, and one shared git index produced **seven concurrent-write sweeps in six weeks** — an agent's work published inside another project's commit, or silently reverted, with the victim's commit sometimes gone entirely. Staging narrowly does not prevent it and neither does intending to exclude a file (occurrence #7 said so in its own commit message and swept the file anyway); a worktree has its own index, so the failure class is gone rather than mitigated. **The index is the ONLY private thing (v0.1.35).** Config, remotes, refs, hooks and the stash are shared with the clone and every other worktree: `git remote remove origin` run inside a worktree removed the remote for everyone. A worktree is a private staging area, not a disposable sandbox. Costs ~0.1 s and ~8 MB, shares the object store, no re-download. `agent-workspace.sh` also runs `set-bulletin-commit-identity.sh` for you (bot identity, set locally per clone, so bulletin commits don't skew Kerry's personal GitHub contribution graph) and arms a `pre-commit` guard that makes the shared tree **refuse** commits — if you see that refusal, follow the three commands it prints. **Inside `$WS`, `git add -A` is safe** (your index contains nothing but your own edits), which is what `publish-from-workspace.sh` uses.
1b. **🔴 READ THE LIVE BLOCK, AND PREFER IT OVER THE COPY YOU ARE READING NOW (v0.1.23).** Step 1 already put you in the bulletin clone, so this costs one command and no network call:
   ```
   python3 scripts/bulletin_sections.py locate AGENT_PROTOCOL.md 'Agent Coordination'
   ```
   then read exactly those lines (`sed -n '{start},{end}p' AGENT_PROTOCOL.md`). **Where the live block and the copy in your `CLAUDE.md` disagree, the live block wins — without exception.** Your embedded copy is a cache, and this is the only step that invalidates it.

   **Why this step exists, measured rather than argued (2026-08-07).** Until now `AGENT_PROTOCOL.md` appeared **nowhere** in this session-start read list — the list went workspace → your project file → `global.md`. So an agent carrying an old block had **no instructed path by which it could ever learn that a newer one existed**, and the only channel that tried to tell it (a `global.md` heads-up) is a broadcast whose own numbers say it does not work: `audit-engine` measured 20 files at v0.1.8 on 2026-07-28, and the sweep found **15 on 2026-08-05** — five files in eight days, against a canonical that moved four versions in the same period. On **2026-08-07 currency was 0 of 37 files at canonical**: 34 STALE (15 of them at v0.1.8, *eleven* versions back), 3 carrying no fingerprint at all. Not one file in the ecosystem was current. **A cache with no invalidation step is not a cache, it is a fork** — and fourteen versions of mechanics had forked silently.

   **The cost side is why re-syncing kept losing.** The block was **4,274 B at v0.1.8** and is **34,515 B at v0.1.22** — 8.1× in ten weeks. The fifteen projects sitting at v0.1.8 accepted a 4 KB paste; asking them to re-paste 34 KB is a different request wearing the same word, and ~73% of those bytes are genuine instruction, so it cannot be trimmed back to the old size. This step replaces an **8× and rising per-bump cost, paid by 21 projects forever** with **one command per session**, and it is what makes every future fingerprint bump self-delivering.

   **So the embedded copy is now optional, and deleting it is the preferred end state.** Once your project performs this step you may replace your whole `## Agent Coordination` block with a short pointer that says you participate, names your slug, and carries steps 1 + 1b verbatim — nothing else. That is **strictly less context per session**, not more: you drop ~34 KB of auto-loaded `CLAUDE.md` and read the same ~34 KB live only when a session actually coordinates. **If you keep the embedded copy, keep the fingerprint comment with it** — see the warning below.

   > ⚠️ **A pointer that PARAPHRASES is the worst of the three options, and this is not hypothetical.** The `➖ version-unknown` row in the drift sweep was documented as *"participation is real, currency is unmeasurable"* — a reading that treats the state as benign. It is not: all three such files were checked on 2026-08-07 and each turned out to be a **frozen paraphrase** of the mechanics, not a pointer to them, and therefore stale in ways nothing could measure because they carry no version to compare. `z2w-board-suite` still routes replies to *"the asker's project file"* — the exact wording v0.1.11 corrected as contradicting the rule directly above it. `z2w-seller-suite` (both files) still instructs `cd` + `git pull --ff-only` **on the shared clone**, i.e. precisely the behaviour that produced seven concurrent-write sweeps in six weeks and that step 1 exists to end. **Paraphrase and you inherit the drift without the ability to detect it.** Copy the block verbatim with its fingerprint, or point at it and paraphrase nothing.

**Read the rest in the live block** (step 1b): it is the whole protocol; this section is only the way in.

