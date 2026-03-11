#!/usr/bin/env python3
"""
Create .env template for local development and testing.

Usage:
    python3 execution/create_env_template.py

Note: This project primarily runs via GitHub Actions with repository secrets.
The .env file is only needed for local testing of generate_summary.py.
"""

import os

ENV_TEMPLATE = """# ============================================
# Daily Work Summary - Local Development
# ============================================
# This .env is for LOCAL TESTING ONLY.
# In production, these are GitHub Actions secrets.
# ============================================

# REQUIRED - GitHub Personal Access Token
# Create at: https://github.com/settings/tokens
# Scopes needed: repo, read:user
PAT_GITHUB=ghp_your_token_here

# OPTIONAL - Email (only needed if testing email locally)
EMAIL_USERNAME=kerry@zero2webmaster.com
EMAIL_PASSWORD=your_gmail_app_password_here

# OPTIONAL - AI-powered repo summaries (set one provider + key)
# AI_PROVIDER=openrouter  # or: anthropic, gemini, openai
# OPENROUTER_API_KEY=sk-or-...
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# GOOGLE_API_KEY=...
"""


def main():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

    if os.path.exists(env_path):
        print(f"⚠️  .env already exists at {env_path}")
        print("   Delete it first if you want to regenerate.")
        return

    with open(env_path, "w") as f:
        f.write(ENV_TEMPLATE.lstrip())

    print(f"✅ Created .env at {env_path}")
    print("   Edit it with your actual credentials before testing locally.")


if __name__ == "__main__":
    main()
