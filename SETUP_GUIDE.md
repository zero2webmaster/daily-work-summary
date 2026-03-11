# Gain Coding Superpowers Via This 3-Layer Architecture Setup

**Version:** 2.5.0 | **Last Updated:** 2026-02-12

**Welcome!** This guide helps ensure the success of your coding projects in Cursor, Windsurf, or similar AI-powered IDEs using the proven 3-layer architecture system.

---

## ⚡ Prerequisites

Before starting:
- [ ] Read `AGENTS.md` to understand the 3-layer architecture (5-minute read)
- [ ] Have your project requirements ready
- [ ] Open your empty project folder in Cursor

---

## 🚀 The Setup Prompt

### ⚠️ IMPORTANT: You MUST Customize This!

**Copy this entire prompt and customize the project specifics section:**

```
Set up this project following the 3-layer architecture in AGENTS.md and the instructions in the STARTER_PROMPT.md file

My project specifics:
- Purpose: [What does this project do?]
- Key APIs: [What external services/APIs will you use?]
- Data sources: [Where does your data come from?]
- Expected outputs: [What will the system produce?]
- Edge cases: [What could go wrong? Special scenarios?]
```

**🔐 IMPORTANT: Do NOT include API keys or tokens here!**  
API keys, tokens, and credentials go in the `.env` file AFTER setup, not in this prompt.

### ✅ Example (Filled In):

```
Set up this project following the 3-layer architecture in AGENTS.md and the instructions in the STARTER_PROMPT.md file

My project specifics:
- Purpose: Migrate 476 videos from Vimeo to Bunny.net to reduce hosting costs from $300/year to $50/year
- Key APIs: Vimeo API, Bunny.net Stream API, Airtable API
- Data sources: Airtable base containing video URLs, titles, and metadata
- Expected outputs: All videos hosted on Bunny.net, Airtable updated with new URLs/embed codes, migration log
- Edge cases: API rate limits, network interruptions during large transfers, private/restricted videos, duplicate videos
```

**Don't skip the customization!** The AI needs these specifics to create the right foundation for your project.

---

## 📝 What the AI Will Create

The AI will automatically set up:

### **Core Files**
- `.cursorrules` - Project-specific rules and context (based on YOUR specifics)
- `.cursorignore` - Excludes large generated files from AI context (node_modules/, venv/, etc.)
- `.gitignore` - Excludes sensitive/temporary files
- `.env` - Environment variables and API keys (template - created via script)
- `VERSION` - Semantic version tracking (starts at 1.0.0)
- `CHANGELOG.md` - Document all changes here

**Note:** `.env` is created using `execution/create_env_template.py` to bypass IDE security restrictions on sensitive files

### **Folder Structure**
```
YourProject/
├── directives/          # What to do (SOPs in Markdown)
├── execution/           # How to do it (Python scripts)
│   └── install_git_hooks.py  # Automated quality checks
└── .tmp/               # Temporary files (never commit)
```

### **Git Hooks (Quality Automation)**
- Smart pre-commit hook installed automatically
- Reminds you to update directives when code changes
- Skips checks for WIP (Work In Progress) commits
- Friendly warnings, not hard blocks

---

## 🎯 How to Fill In Project Specifics

### **1. Purpose**
*What does this project do? What problem does it solve?*

**Examples:**
- "Migrate 476 videos from Vimeo to Bunny.net to reduce hosting costs"
- "Scrape product data from 50 e-commerce sites and generate comparison reports"
- "Automate client onboarding by creating personalized welcome sequences"
- "Generate SEO-optimized blog posts from research notes using GPT-4"

### **2. Key APIs**
*What external services will you integrate with?*

**Examples:**
- "Vimeo API, Bunny.net Stream API, Airtable API"
- "OpenAI GPT-4, Google Sheets, Stripe"
- "Shopify API, SendGrid, AWS S3"
- "Twitter API, Webhook.site, MongoDB Atlas"
- "WordPress REST API, FluentCommunity, FluentCRM"

### **3. Data Sources**
*Where does your input data come from?*

**Examples:**
- "Airtable base with video URLs and metadata"
- "CSV files from client, Shopify product exports"
- "Google Sheets with lead information"
- "JSON files from API, user uploads via web form"

### **4. Expected Outputs**
*What will the system produce? Where will results go?*

**Examples:**
- "Videos hosted on Bunny.net, Airtable updated with new URLs and embed codes, migration log in Google Sheets"
- "Product comparison slides in Google Slides, pricing spreadsheet, email report to client"
- "Welcome emails sent via SendGrid, tracking dashboard in Google Sheets"
- "Published blog posts in WordPress, SEO metadata CSV, performance tracking spreadsheet"

### **5. Edge Cases**
*What could go wrong? What special scenarios need handling?*

**Examples:**
- "API rate limits, network interruptions during large transfers, duplicate videos, private/restricted videos"
- "Invalid product URLs, out-of-stock items, price format variations across sites"
- "Bounced emails, invalid phone numbers, timezone differences for scheduling"
- "Incomplete research notes, duplicate content detection, API quota limits"

---

## ✅ After Setup: Next Steps

Once the AI completes setup:

### **1. Create GitHub Repository (IMPORTANT)**
Don't skip this! Version control from day one prevents data loss and enables CI/CD.

**What is CI/CD?**
- **CI (Continuous Integration):** Automatic testing when you push code
- **CD (Continuous Deployment):** Automatic deployment to production
- **Example:** Push to GitHub → Tests run → Deploy to website (all automatic!)
- Your project is "CI/CD Ready" because it has proper structure and dependencies

**Steps:**
1. Go to https://github.com/new
2. Repository name: `your-project-name`
3. Description: Brief project description
4. Visibility: **Private** (recommended for business projects)
5. **CRITICAL - Leave ALL these UNCHECKED:**
   - ❌ Add a README file (we already have README.md)
   - ❌ Add .gitignore → Select "None" (we already have custom .gitignore)
   - ❌ Choose a license → Select "None" (add later if needed)
6. Click "Create repository"

**Then connect your local repo:**
```bash
# Replace YOUR_USERNAME and REPO_NAME
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
git branch -M main
git push -u origin main
```

**Verify it worked:**
```bash
git remote -v
# Should show your GitHub URL
```

### **2. Configure Environment**
Edit `.env` file with your actual API keys:

**For Airtable Projects:**

1. **Create dedicated Personal Access Token (PAT):**
   - Go to https://airtable.com/create/tokens
   - Click "Create new token"
   - Token name: `YourProjectName - Cursor Development` (e.g., "VimeoBunny - Cursor Development")
   - Scopes:
     - ✅ `data.records:read` - Read records
     - ✅ `data.records:write` - Write records  
     - ✅ `schema.bases:read` - Read schema
     - ✅ `schema.bases:write` - Write schema (if creating tables)
   - Access:
     - ✅ **Specific base only** (recommended for security)
     - ❌ NOT "All current and future bases" (unless building multi-base tool)
   - Click "Create token"
   - Copy immediately (won't be shown again!)

2. **Add to `.env` file:**
```bash
# Example .env
AIRTABLE_API_KEY=patABCD1234567890...  # Your PAT from step 1
AIRTABLE_BASE_ID=appXXXXXXXXXXXX       # From Airtable base URL
```

**Security Best Practices:**
- One PAT per project (easier to revoke if needed)
- Specific base scope (limits damage if token leaks)
- Never commit `.env` to git (already in `.gitignore`)
- Rotate tokens if compromised

### **3. Verify Git Hooks Installed**
Should happen automatically, but check:
```bash
ls -la .git/hooks/pre-commit
# If missing: python3 execution/install_git_hooks.py
```

### **4. Optional: Install Standard Development Tools**

These tools enhance your workflow but aren't required for basic projects:

**Homebrew** (macOS package manager):
```bash
# Check if installed
brew --version

# Install if missing
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Pandoc** (Markdown → Rich Text converter):
```bash
# Install via Homebrew
brew install pandoc

# Usage: Convert Markdown to RTF for Airtable
python3 execution/md_to_richtext.py notes.md
```

**When you need these:**
- Pandoc: If pasting formatted text into Airtable rich text fields
- Homebrew: Standard macOS tool installer (makes everything easier)

See the Reference Material section below for full details on all tools.

### **5. Create Your First Directive**
Tell the AI what to build:
```
Create a directive for [specific task]. Include:
- Goal and inputs
- Tools/scripts to use
- Expected outputs
- Edge cases to handle
```

### **6. Build and Test**
The AI creates execution scripts, you run and test them. The system self-anneals (gets better with each error).

---

## 🆘 Troubleshooting

### **"Module not found" errors**
```bash
pip3 install -r requirements.txt
```

### **"Permission denied" on git hooks**
```bash
chmod +x .git/hooks/pre-commit
```

### **API authentication errors**
Check your `.env` file has correct credentials

### **Pre-commit hook blocking commits**
- If code changed: Update relevant directives first
- For quick saves: `git commit -m "WIP: work in progress"`
- Emergency bypass: `git commit --no-verify -m "..."`

---

## 💬 Managing Chat Conversations

### **Issue 1: Preventing Data Loss While Drafting**

**Problem:** Cursor does **NOT** auto-save messages you're typing. If Cursor crashes, your draft is lost.

**Solution:**
1. ✅ **Draft long messages in a text editor or word processor** (e.g., TextEdit, Notepad, Word, Google Docs, Notion) and be sure to save your work regularly
2. ✅ **Copy/paste into Cursor** when ready
3. ✅ Click **Return** or **Enter** to send your chat to Cursor

**Note:** Once sent, Cursor saves messages to cloud history.

### **Issue 2: Archiving Past Conversations**

**Problem:** Cursor's cloud chat history is hard to search and not locally accessible.

**Solution: Create local chat archive**

```bash
# Folder already exists and is in .gitignore
mkdir -p .chat_archive

# Export/save important conversations as text files:
# .chat_archive/2024-12-20-1-initial-setup.txt
# .chat_archive/2024-12-20-2-stripe-integration.txt
# .chat_archive/2024-12-21-1-google-workspace.txt
```

**Naming convention:** `YYYY-MM-DD-#-Topic-Name.txt` (# = session number for that day)

**Benefits:**
- ✅ Searchable: `grep -r "Stripe" .chat_archive/`
- ✅ Fast local access
- ✅ Reference past decisions/context
- ✅ Private (never committed to git)

**How to export chats:**
Currently, Cursor does not have a built-in export feature. To save conversations:
1. Manually copy the conversation text from the chat panel
2. Paste into a text file
3. Save in `.chat_archive/` with naming convention above
4. Alternatively, use screenshots or screen recording for visual reference

---

## 📚 Learn More

**For detailed information, see AGENTS.md:**
- **3-Layer Architecture** - Why this approach works (90% → 99.9% reliability)
- **Directive Maintenance** - How to keep docs in sync with code
- **Version Control** - Semantic versioning, commit formats, git workflow
- **Self-Annealing Loop** - How the system improves itself over time

---

## 💡 Pro Tips

- **Directives are living documents** - Update them as you learn (pre-commit hook reminds you)
- **Use WIP commits for quick saves** - Hook skips checks: `git commit -m "WIP: ..."`
- **Everything in .tmp/ is temporary** - Never commit, always regenerate
- **Check existing tools first** - Before creating new scripts, check `execution/`
- **Ask the AI for help** - It's your pair programmer: "How do I implement [feature]?"

---

## 🎯 You're Ready!

1. **Customize** the project specifics in the prompt above
2. **Copy** the entire customized prompt
3. **Paste** into Cursor
4. **Let the AI** build your project foundation

You'll have a professional, maintainable, self-documenting system in minutes.

**Happy building!** 🚀

---

# Reference Material

> **This section contains setup instructions, code templates, and detailed examples relocated from AGENTS.md to reduce per-message token cost.** The AI does not need this material on every message — use `@SETUP_GUIDE.md` to load it when needed.

---

## .cursorignore Template

**Purpose:** Prevents large generated files from being included in AI context, significantly reducing token cost.

**Important:** `.cursorignore` blocks AI access entirely. Do NOT add files you need to @-reference (like SETUP_GUIDE.md, TROUBLESHOOTING.md, or HANDOFF.md). Only block truly never-needed content.

**Standard template for new projects:**

```
# Dependencies (large, auto-generated)
node_modules/
package-lock.json

# Virtual environments
venv/
env/
.venv/
ENV/

# Build outputs
dist/
build/
*.pyc
__pycache__/

# Temporary/generated files
.tmp/
*.log
```

**Why this matters:**
- `node_modules/` alone can be 170MB+ — that's millions of tokens if indexed
- `package-lock.json` is typically 10,000+ lines of auto-generated data
- Virtual environments contain thousands of installed package files
- None of these files are useful for the AI during coding

**Customization:** Add project-specific exclusions as needed (e.g., large data files, compiled assets, vendor directories).

---

## TROUBLESHOOTING.md Template

**Purpose:** Every project encounters unique issues during development. `TROUBLESHOOTING.md` captures solutions so they're not lost in chat history or commit messages. This document saves hours of debugging time for future developers (or your future self).

**Create this file at project start** and update it as a living document throughout development.

### When to Add an Entry

Add a troubleshooting entry whenever:
1. ✅ You solve a problem that took more than 15 minutes
2. ✅ You discover a workaround for API/tool quirks
3. ✅ You encounter an error not covered in official documentation
4. ✅ You learn a best practice through trial and error
5. ✅ You fix environment setup or configuration issues

**Document it immediately** - future you will thank you!

### Template Structure

```markdown
# Troubleshooting Guide

**Project:** [Project Name]  
**Last Updated:** [Date]

---

**📝 This is a living document:** Add new entries whenever you solve a problem that took more than 15 minutes, discover a workaround, or learn something not in the official documentation. Future you (and your team) will thank you!

---

## [Technology/Service/Component Name]

### Issue: [Brief Description]

**Problem:** What went wrong (error message, unexpected behavior, etc.)

**Root Cause:** Why it happened (API limitation, configuration issue, timing, etc.)

**Solution:** How to fix it (step-by-step instructions)

**Verification:** How to test the fix worked

---

## Quick Reference

[Common commands, error messages, gotchas that don't need full entries]

---

## Best Practices Learned

[Patterns and approaches discovered during development]

---
```

### Real-World Examples

**Example Entry 1 - API Integration:**
```markdown
## FluentCart API

### Issue: Product Creation Returns 404 Error

**Problem:** Creating product via REST API returns 404 even with valid endpoint

**Root Cause:** FluentCart uses WooCommerce products directly. There is no separate "FluentCart products" endpoint. Must use `/wp-json/wc/v3/products` instead.

**Solution:**
- Use WooCommerce REST API, not FluentCart API
- Product created in WooCommerce automatically appears in FluentCart
- Requires WooCommerce consumer key/secret (not FluentCart credentials)

**Verification:**
curl -X GET https://example.com/wp-json/wc/v3/products \
  -u consumer_key:consumer_secret
```

**Example Entry 2 - Environment Setup:**
```markdown
## Python Virtual Environment

### Issue: "externally-managed-environment" Error on macOS

**Problem:** `pip3 install -r requirements.txt` fails with PEP 668 error

**Root Cause:** macOS enforces PEP 668 to prevent system Python modification

**Solution:**
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt

**Verification:**
which python3  # Should show path inside venv/
pip3 list      # Shows installed packages
```

**Example Entry 3 - MCP Tools:**
```markdown
## MCP Tool Configuration

### Issue: Browser Tools Not Available

**Problem:** mcp_cursor-browser-extension tools don't appear in tool list

**Root Cause:** MCP server configuration file missing or malformed

**Solution:**
- Check `~/.cursor/mcp.json` exists
- Verify cursor-browser-extension is listed in servers
- Restart Cursor after config changes

**Verification:**
List available tools - should see mcp_cursor-browser-extension_*
```

### Standard Project Files Reference

After project setup, you should have:
- ✅ `ROADMAP.md` - Project steps and progress
- ✅ `STATUS.md` - Current blockers, decisions, next actions
- ✅ `TROUBLESHOOTING.md` - Issues encountered and solutions (this file)
- ✅ `README.md` - Project overview and setup instructions
- ✅ `CHANGELOG.md` - Version history and changes
- ✅ `.cursorrules` - AI agent instructions
- ✅ `.cursorignore` - AI context exclusions
- ✅ `directives/` - SOPs and workflows
- ✅ `execution/` - Python scripts and tools

### Benefits of TROUBLESHOOTING.md

**Time Savings:**
- Typical project saves 2-4 hours by avoiding re-solving known issues
- Onboarding new developers: Hours → Minutes
- Context switching: Remember solutions from weeks ago instantly

**Knowledge Capture:**
- API quirks and undocumented behavior
- Environment-specific issues (macOS vs Windows)
- Integration gotchas between services
- Performance optimization discoveries

**Self-Annealing:**
- Project gets easier to work on over time
- Institutional knowledge grows automatically
- Future problems solved by past solutions
- Documentation emerges from real work

**Best Practice:** Update TROUBLESHOOTING.md in the same commit as the fix. If you can't document the solution clearly, maybe the fix isn't complete yet.

---

## Standard Development Tools (Full Setup)

### Homebrew (macOS Package Manager)

**Check if installed:**
```bash
brew --version
```

**Install if missing:**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

After installation, add to PATH:
```bash
echo >> ~/.zprofile
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### Pandoc (Document Converter)

**Purpose:** Convert Markdown to rich text formats (RTF, DOCX, HTML) for Airtable, Google Docs, etc.

**Check if installed:**
```bash
pandoc --version
```

**Install:**
```bash
brew install pandoc
```

**Usage in projects:**
- Script: `execution/md_to_richtext.py` - Convert Markdown → RTF for Airtable
- Directive: `directives/markdown_to_airtable_richtext.md` - Complete workflow guide

**Example:**
```bash
# Convert any Markdown file to rich text
python3 execution/md_to_richtext.py notes.md

# Opens notes.rtf in TextEdit
# Copy (Cmd+A, Cmd+C) → Paste into Airtable rich text field
```

### Playwright (Browser Automation)

**Purpose:** Powers browser automation, testing, and Chrome DevTools MCP

**Check if installed:**
```bash
npx playwright --version
```

**Install:**
```bash
npm install -g playwright
npx playwright install chromium
```

**What it does:**
- Enables Chrome DevTools MCP (browser control via AI)
- Automated testing of web applications
- Screenshot capture and visual verification
- Form filling and UI interaction testing

**Required by:**
- Chrome DevTools MCP (`chrome-devtools-mcp`)
- Any browser automation tasks
- Frontend testing workflows

**Note:** First use of Chrome DevTools MCP will auto-install Playwright if missing, but manual installation is recommended for better control.

### Project Setup Script

Consider adding `execution/check_dependencies.py` to verify all tools are installed:

```python
#!/usr/bin/env python3
"""Check that all required dependencies are installed."""

import subprocess
import sys

def check_command(command: str, name: str) -> bool:
    try:
        subprocess.run([command, '--version'], 
                      capture_output=True, check=True)
        print(f"✅ {name} installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"❌ {name} not found")
        return False

def main():
    # Check if in virtual environment
    in_venv = sys.prefix != sys.base_prefix
    if in_venv:
        print("✅ Running in virtual environment")
    else:
        print("⚠️  NOT in virtual environment")
        print("   Activate with: source venv/bin/activate")
    
    checks = [
        ('brew', 'Homebrew'),
        ('pandoc', 'Pandoc'),
        ('python3', 'Python 3'),
        ('pip3', 'pip'),
        ('npx', 'npx (Node.js)'),
    ]
    
    results = [check_command(cmd, name) for cmd, name in checks]
    
    # Check Playwright separately (npx command)
    try:
        subprocess.run(['npx', 'playwright', '--version'], 
                      capture_output=True, check=True)
        print("✅ Playwright installed")
        results.append(True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Playwright not found")
        results.append(False)
    
    if not all(results):
        print("\n⚠️  Some dependencies are missing. See setup instructions.")
        sys.exit(1)
    else:
        print("\n🎉 All dependencies installed!")

if __name__ == '__main__':
    main()
```

---

## MCP Servers (Model Context Protocol)

**MCP servers extend Cursor's capabilities** by connecting to external tools and services.

### Chrome DevTools MCP (Browser automation and testing)

**Purpose:**
- Automate browser interactions for testing
- Fill forms, click buttons, navigate pages
- Take screenshots, inspect elements
- Verify frontend behavior without manual testing

**Prerequisites:**
- Playwright must be installed: `npm install -g playwright && npx playwright install chromium`
- See Playwright section above for full setup

**Setup:**

Add to Cursor settings (`~/Library/Application Support/Cursor/User/settings.json`):

```json
"mcpServers": {
    "chrome-devtools": {
        "command": "npx",
        "args": ["-y", "chrome-devtools-mcp"]
    }
}
```

**Or via Cursor Settings UI:**
1. Open Cursor Settings (Cmd+,)
2. Search for "MCP"
3. Click "Edit in settings.json"
4. Add the chrome-devtools configuration above

**Usage:**
- AI can control Chrome browser directly
- Test forms, checkout flows, dashboards
- No need to manually test every change
- Automated screenshot capture for visual verification

**Example prompts:**
```
Navigate to localhost:3000 and test the checkout form with test data
Take a screenshot of the homepage after clicking the "Buy Now" button
Fill in the contact form and verify the confirmation message appears
```

**Note:** Project-specific MCPs should be configured per project, not in master template. Chrome DevTools is universal and has no credential requirements.

---

## .env File Creation

**Important:** IDE security restrictions may block direct `.env` creation. Use this pattern:

1. **Create via script:** `execution/create_env_template.py`
2. **Structure template with clear sections:**
   ```
   # ============================================
   # REQUIRED - Project won't work without these
   # ============================================
   AIRTABLE_API_KEY=...
   
   # ============================================
   # OPTIONAL - Comment out if not needed
   # ============================================
   # SMTP_HOST=...
   ```

3. **WordPress Security:** Always use Application Passwords
   - **Never use login password in .env** (security risk!)
   - Create at: WordPress Admin → Users → Profile → Application Passwords
   - Name it clearly: "Cursor Local Development"
   - Benefits: Revocable, scoped to REST API only, doesn't expose admin access
   
4. **EMAIL SENDING FROM YOUR SITE:**
   - WordPress email is unreliable: it is often blocked as spam
   - As such, best practice is to configure (1) an external SMTP service; and connect it to (2) an Email Sending Service
   - FluentSMTP is an excellent free WordPress plugin
   - Amazon SES, SendGrid, MailerSend, Brevo and Gmail API are well known Email Sending Services; visit their pricing pages to determine which fits your needs and budget. Some offer a limited amount of daily or monthly emails for free.
   - Document SMTP setup in project directives

5. **Environment Flag Reminder:**
   - Default: `ENVIRONMENT=development`
   - **Reminder:** When deploying to production, switch to `ENVIRONMENT=production`
   - Set reminder in deployment checklist/documentation

---

## Cloud Storage & Email Services (Full Setup)

**CDN/Storage options for hosting files (certificates, images, downloads):**

### Cloudflare R2 (Recommended)

**Why R2:**
- ✅ **Free egress** (no bandwidth charges)
- ✅ **S3-compatible** (use boto3)
- ✅ **Custom domains** (professional URLs)
- ✅ **Simple pricing** ($0.015/GB storage, minimal operations cost)

**Setup:**
1. Create bucket at https://dash.cloudflare.com/ → R2
2. Generate API token with Object Read & Write permissions
3. Connect custom domain (e.g., `cdn.example.com`) OR use R2.dev URL for testing
4. Add to `.env`:
   ```bash
   R2_ACCESS_KEY_ID=your_access_key
   R2_SECRET_ACCESS_KEY=your_secret_key
   R2_ENDPOINT_URL=https://[account-id].r2.cloudflarestorage.com
   R2_BUCKET_NAME=your-bucket-name
   R2_PUBLIC_URL=https://cdn.example.com  # or https://pub-xxxxx.r2.dev
   ```

**Usage (boto3/S3-compatible):**
```python
import boto3

s3 = boto3.client(
    service_name='s3',
    endpoint_url=os.getenv('R2_ENDPOINT_URL'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
    region_name='auto'
)

s3.put_object(
    Bucket='your-bucket',
    Key='path/to/file.pdf',
    Body=file_content,
    ContentType='application/pdf'
)
```

**Common Issue:** API tokens with Object Read/Write only permissions will fail `list_buckets()` - this is normal and can be skipped in tests.

### Bunny CDN (Alternative)

**Why Bunny:**
- ✅ Easy setup
- ✅ Global CDN
- ⚠️ Bandwidth charges apply

**Critical Setup Detail:**
- **Storage hostname is region-specific** (e.g., `la.storage.bunnycdn.com`, not `storage.bunnycdn.com`)
- Find your hostname: Dashboard → Storage Zone → FTP & API Access tab
- Common regions: `la` (Los Angeles), `ny` (New York), `sg` (Singapore)

**Add to `.env`:**
```bash
BUNNY_STORAGE_ZONE=your-zone-name
BUNNY_STORAGE_HOSTNAME=la.storage.bunnycdn.com  # Region-specific!
BUNNY_STORAGE_API_KEY=your_storage_password  # From FTP & API Access tab
BUNNY_CDN_URL_BASE=https://your-zone.b-cdn.net
```

**Test connection:**
```python
import requests

url = f"https://{hostname}/{zone}/"
headers = {'AccessKey': api_key}
response = requests.get(url, headers=headers)
# 200 = success, 401 = wrong key or hostname
```

### Amazon SES (Email Delivery)

**Why SES:**
- ✅ Reliable, high deliverability
- ✅ Cost-effective ($0.10 per 1,000 emails)
- ✅ Production-ready (after sandbox approval)

**Setup:**
1. Create IAM user: AWS Console → IAM → Users → Add user
2. Permissions: `AmazonSESFullAccess`
3. Create access key (save Access Key ID + Secret Access Key)
4. Verify sender email: SES Console → Verified identities → Create identity
5. **Important:** Verify email in the **same region** you'll send from (check console URL)

**Add to `.env`:**
```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_SES_REGION=us-west-2  # Must match where email is verified!
EMAIL_FROM=contact@example.com  # Must be verified in SES
EMAIL_FROM_NAME=Your Organization
```

**Usage (boto3):**
```python
import boto3

ses = boto3.client('ses', region_name=os.getenv('AWS_SES_REGION'))

ses.send_email(
    Source='contact@example.com',
    Destination={'ToAddresses': ['recipient@example.com']},
    Message={
        'Subject': {'Data': 'Subject'},
        'Body': {'Html': {'Data': '<html>...</html>'}}
    }
)
```

**Common Issues:**
- ❌ "Email not verified" → Wrong region (email verified in `us-east-1` but sending from `us-west-2`)
- ❌ "Sandbox restrictions" → Request production access (Settings → Account dashboard)
- ✅ Test verification: `ses.list_verified_email_addresses()`

**Storage Priority Pattern:**
```python
# Auto-detect available storage
if all([r2_key, r2_secret, r2_endpoint, r2_bucket]):
    storage = 'r2'  # Preferred
elif all([bunny_key, bunny_zone]):
    storage = 'bunny'  # Fallback
else:
    storage = 'local'  # No cloud storage
```

---

## Airtable Field Validation (Full Reference)

**Field Name Validation — Preventing 422 Errors**

Airtable 422 "Unprocessable Entity" errors often indicate field name mismatches, but error messages don't specify which field. Small typos (capitalization, spaces) can cause production failures.

### The Problem

**Common scenarios:**
- Code uses `'Run Date/Time'` but Airtable has `'Run Date'` (different name)
- Code uses `'Success'` but Airtable has `' Success'` (leading space in single select)
- Error says "Insufficient permissions to create new select option" (misleading)
- No indication which field is wrong or what fields actually exist

**Root causes:**
- Manual Airtable edits introduce typos when creating fields
- Single select options must match EXACTLY (including whitespace)
- Field names change during schema evolution
- No built-in validation before API calls

### The Solution: Field Validation Tool

**Create** `execution/validate_airtable_fields.py`:

```python
#!/usr/bin/env python3
"""
Airtable Field Validator - Prevents field name mismatch errors.

Usage:
  # Manual validation
  python3 execution/validate_airtable_fields.py
  
  # In scripts (auto-diagnostic on error)
  try:
      airtable.update_record(record_id, fields)
  except Exception as e:
      validator.validate_with_suggestions(table_id, expected_fields)
"""

import os
import requests
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

class AirtableFieldValidator:
    """Validates field names against actual Airtable schema."""
    
    def __init__(self):
        self.pat = os.getenv('AIRTABLE_PAT')
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
    
    def get_table_fields(self, table_id: str) -> Dict[str, str]:
        """Get all field names and types from a table via Meta API."""
        url = f'https://api.airtable.com/v0/meta/bases/{self.base_id}/tables'
        headers = {'Authorization': f'Bearer {self.pat}'}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        for table in data.get('tables', []):
            if table['id'] == table_id:
                return {
                    field['name']: field['type']
                    for field in table['fields']
                }
        
        raise ValueError(f"Table {table_id} not found")
    
    def validate_with_suggestions(
        self, 
        table_id: str, 
        expected_fields: List[str]
    ) -> Dict:
        """Validate and suggest corrections for typos."""
        actual_fields = self.get_table_fields(table_id)
        actual_names = set(actual_fields.keys())
        expected_names = set(expected_fields)
        
        missing = expected_names - actual_names
        
        if missing:
            print(f"\n⚠️  Field Validation Issues:")
            for field in missing:
                print(f"❌ Missing: '{field}'")
                
                # Find similar fields
                similar = self._find_similar(field, actual_names)
                if similar:
                    print(f"💡 Did you mean: {', '.join(repr(s) for s in similar)}?")
        
        return {
            'valid': len(missing) == 0,
            'missing': sorted(missing),
            'schema': actual_fields
        }
    
    def _find_similar(self, target: str, candidates: List[str]) -> List[str]:
        """Find similar field names using fuzzy matching."""
        target_lower = target.lower()
        target_words = set(target_lower.split())
        
        similar = []
        for candidate in candidates:
            candidate_lower = candidate.lower()
            
            # Exact match (different case)
            if target_lower == candidate_lower:
                similar.append((candidate, 1.0))
                continue
            
            # Word overlap
            candidate_words = set(candidate_lower.split())
            if target_words and candidate_words:
                overlap = len(target_words & candidate_words)
                total = len(target_words | candidate_words)
                similarity = overlap / total
                
                if similarity >= 0.6:
                    similar.append((candidate, similarity))
        
        similar.sort(key=lambda x: x[1], reverse=True)
        return [name for name, score in similar[:3]]
```

### Usage Patterns

**1. Manual Validation (before operations):**
```bash
python3 execution/validate_airtable_fields.py

# Output:
✅ All fields valid for Holdings Table
✅ All fields valid for Update Logs Table
```

**2. Auto-Diagnostic (on errors):**
```python
try:
    airtable.update_record(record_id, fields)
except Exception as e:
    logger.error(f"Update failed: {e}")
    
    # Auto-validate to diagnose
    validator = AirtableFieldValidator()
    validator.validate_with_suggestions(table_id, list(fields.keys()))
    
    # Shows:
    # ⚠️  Field name mismatch detected!
    # ❌ Missing: 'Run Date/Time'
    # 💡 Did you mean: 'Run Date'?
```

### Critical Rules

**1. Single Select Options Must Match EXACTLY**
```python
# ❌ Code: 'Success' vs Airtable: ' Success' (leading space)
# Result: 422 "Insufficient permissions to create new select option"

# ✅ Always verify options via Meta API:
url = f'https://api.airtable.com/v0/meta/bases/{base_id}/tables'
for field in table['fields']:
    if field['type'] == 'singleSelect':
        for choice in field['options']['choices']:
            name = choice['name']
            print(f"'{name}' (length: {len(name)})")
            if name.startswith(' ') or name.endswith(' '):
                print("⚠️  Whitespace detected!")
```

**2. Use Table IDs (not names)**
```python
# ✅ Good: tbl5t8EQlkeLe18MA (ID - stable)
# ❌ Bad: "Holdings" (name can change)
```

**3. Validate After Manual Edits**
- Airtable web UI allows typos when creating fields
- Run validator after schema changes
- Catches capitalization differences (`'Day of Week'` vs `'Day Of Week'`)

### Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| 422 Unprocessable Entity | Field name mismatch | Run field validator |
| "Insufficient permissions to create option" | Single select value doesn't match exactly | Check for leading/trailing spaces |
| Field not updating | Wrong field name in code | Validate against schema |
| Silent failures | Field exists but wrong type | Check field types in validator output |

### When to Validate

1. **Before first deployment** - Verify all field names match
2. **After manual Airtable edits** - Catch typos immediately
3. **On Airtable API errors** - Auto-diagnose field issues
4. **When onboarding developers** - Show expected schema
5. **Before major refactoring** - Ensure field name consistency

---

## Verification Standards (Detailed Examples)

### Example: Auto-Generated Standards for React + TypeScript

```markdown
## Verification Standards for This Project

**Primary Commands** (run before marking any step ✅):
- `npm test` - Run all unit tests (Jest)
- `npm run build` - Verify production build succeeds
- `npm run lint` - Check for linting errors (ESLint)
- `npm run typecheck` - TypeScript type checking

**File-Scoped Commands** (when working on specific files):
- `npm test -- ComponentName.test.tsx` - Run tests for specific component
- `eslint --fix src/components/ComponentName.tsx` - Fix linting issues

**E2E Tests** (for user-facing features):
- `npm run test:e2e` - Run Cypress/Playwright tests

**✅ Completion Criteria:**
- All tests pass (100% of existing tests)
- Build completes without errors
- Zero linter errors
- Zero TypeScript errors
- New features have tests written
```

### Example: Auto-Generated Standards for Python

```markdown
## Verification Standards for This Project

**Primary Commands** (run before marking any step ✅):
- `pytest` - Run all unit tests
- `mypy .` - Type checking
- `ruff check .` - Linting
- `black --check .` - Format checking

**File-Scoped Commands** (when working on specific files):
- `pytest tests/test_module.py` - Run specific test file
- `ruff check --fix src/module.py` - Fix linting issues
- `black src/module.py` - Format specific file

**✅ Completion Criteria:**
- All tests pass (100% of existing tests)
- Zero mypy errors
- Zero ruff errors
- Code formatted with black
- New features have tests written
```

### ✅ Criteria by Project Type

**Frontend (React/Vue/Angular):**
- ✅ All unit tests pass
- ✅ E2E tests pass for new features
- ✅ Build completes without warnings
- ✅ No console errors in browser
- ✅ Responsive design verified (mobile/desktop)

**Backend (API/Microservices):**
- ✅ All unit tests pass
- ✅ Integration tests pass
- ✅ API endpoints respond correctly (test with curl/Postman)
- ✅ Database migrations run successfully
- ✅ Authentication/authorization working

**Full-Stack:**
- ✅ Frontend tests pass
- ✅ Backend tests pass
- ✅ Integration between frontend/backend verified
- ✅ End-to-end user flow tested

**Python Scripts/CLI:**
- ✅ Pytest suite passes
- ✅ Type checking clean (mypy)
- ✅ Linting clean (ruff/flake8)
- ✅ Script runs successfully with test inputs
- ✅ Error handling tested

---

## Session Handoff & Continuity (Detailed Reference)

### File Templates

**Templates are available in the master template Resources/ folder:**

- **`Resources/roadmap_template.md`** - Copy and customize for your project
- **`Resources/status_template.md`** - Copy and customize for your project
- **`Resources/handoff_template.md`** - Use for each session handoff

**Usage:**
```bash
# Copy templates to your project (when needed)
cp ~/path/to/templates/Resources/roadmap_template.md ./ROADMAP.md
cp ~/path/to/templates/Resources/status_template.md ./STATUS.md

# Generate handoff at end of session
python3 execution/generate_handoff.py
```

### ROADMAP.md Example

```markdown
### Step 3: ✅ Database Schema Implementation
**Status:** Complete (2026-01-10)

**Tasks:**
- [x] Create migrations for users table
- [x] Add indexes for performance
- [x] Seed initial data

**Verification:**
pytest tests/test_db.py

**Dependencies:** Step 2 (Environment Setup)
```

### STATUS.md Example

```markdown
## 🚧 Blockers

**API Rate Limiting**
- **Impact:** Cannot test bulk operations
- **Status:** Investigating caching solution
- **ETA:** Needs decision from user

## 🧭 Decisions

### Decision: Use PostgreSQL over SQLite
**Date:** 2026-01-10

**Rationale:** Project requires full-text search and concurrent writes. PostgreSQL provides better performance for these use cases.

**Alternatives Considered:** SQLite (too limited), MongoDB (overkill)

**Impact:** Requires PostgreSQL installation in production environment.
```

### HANDOFF.md Structure

A complete HANDOFF.md includes:
- ✅ **What Was Accomplished** - Deliverables this session
- 🎯 **Key Decisions Made** - Decisions with full context
- 📋 **Outstanding Work Items** - Immediate, short-term, medium-term tasks
- 🚧 **Known Issues/Blockers** - Current blockers
- 📦 **Git Status** - Branch, commit, push status
- 🔑 **Critical Context** - Architecture, tech stack, key files
- 📚 **Files to Read First** - Priority reading order with time estimates
- ⚠️ **Warnings** - Critical things to avoid
- ✅ **Session Verification** - Pre-handoff checklist
- 🚀 **Starting Prompt** - Optimized prompt for next session
- 💡 **Suggested Improvements** - Process/structure improvements
- 🎓 **Session Learnings** - What worked, what could improve

### Automation Scripts

Two Python scripts in `Resources/execution_scripts/` help automate handoff generation:

**generate_handoff.py** - Auto-generates HANDOFF.md draft from current project state:
- Reads git log for recent commits
- Parses STATUS.md for current blockers
- Extracts ROADMAP.md progress
- Reads VERSION file
- Generates HANDOFF.md template with TODOs

```bash
python3 execution/generate_handoff.py
python3 execution/generate_handoff.py --output custom_handoff.md
```

**verify_handoff.py** - Verifies handoff readiness before ending session:
- Git status clean (or only safe untracked files)
- All commits pushed to remote
- VERSION file exists and valid
- ROADMAP.md and STATUS.md exist
- HANDOFF.md complete (no [TODO] placeholders)

```bash
python3 execution/verify_handoff.py
python3 execution/verify_handoff.py --strict  # Treat warnings as errors
```

### Benefits

✅ **Context Loading:** 30 min → <2 min (93% reduction)
✅ **No Lost Context:** Decisions and architecture preserved between sessions
✅ **Clear Progress Tracking:** Always know what's done and what's next
✅ **Decisions Documented:** Real-time capture with rationale
✅ **Clean Handoffs:** No confusion about project state
✅ **Self-Documenting:** Handoff becomes project history
✅ **Automation Support:** Scripts reduce manual work

### Real-World Example

**VideoMigrator.com Project** implemented this system and saw:
- Session startup: 30 minutes → 90 seconds
- Zero context loss between 5+ AI agents
- All architectural decisions preserved with rationale
- Clear progress tracking (38% complete, 5 of 8 steps done)
- New agents productive immediately

---

*This setup system is part of the 3-Layer Architecture framework of [Zero2Webmaster](https://zero2webmaster.com/).*  
*Learn more about AI-powered automation at [zero2webmaster.com](https://zero2webmaster.com/).*

*Version: 2.5.0 | Last Updated: 2026-02-12*
