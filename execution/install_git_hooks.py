#!/usr/bin/env python3
"""
Install git hooks for the project.

Installs a pre-commit hook that reminds you to update directives
when code changes are detected. Skips checks for WIP commits.

Usage:
    python3 execution/install_git_hooks.py
"""

import os
import stat

PRE_COMMIT_HOOK = """#!/bin/bash
# Pre-commit hook: Remind to update directives when code changes

STAGED_CODE=$(git diff --cached --name-only | grep -E '\\.(py|yml|yaml)$' | grep -v '__pycache__')
STAGED_DIRECTIVES=$(git diff --cached --name-only | grep '^directives/')

COMMIT_MSG_FILE="$1"
if [ -f ".git/COMMIT_EDITMSG" ]; then
    COMMIT_MSG=$(cat .git/COMMIT_EDITMSG)
else
    COMMIT_MSG=""
fi

# Skip for WIP commits
if echo "$COMMIT_MSG" | grep -qi "^wip"; then
    exit 0
fi

if [ -n "$STAGED_CODE" ] && [ -z "$STAGED_DIRECTIVES" ]; then
    echo ""
    echo "💡 Reminder: You're committing code changes without directive updates."
    echo "   Changed files: $STAGED_CODE"
    echo "   Consider updating directives/ if behavior changed."
    echo ""
    echo "   (Skip this check with: git commit -m 'WIP: ...')"
    echo ""
fi

exit 0
"""


def main():
    git_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), ".git"
    )

    if not os.path.isdir(git_dir):
        print("⚠️  No .git directory found. Initialize git first: git init")
        return

    hooks_dir = os.path.join(git_dir, "hooks")
    os.makedirs(hooks_dir, exist_ok=True)

    hook_path = os.path.join(hooks_dir, "pre-commit")

    with open(hook_path, "w") as f:
        f.write(PRE_COMMIT_HOOK)

    st = os.stat(hook_path)
    os.chmod(hook_path, st.st_mode | stat.S_IEXEC)

    print(f"✅ Pre-commit hook installed at {hook_path}")
    print("   Reminds you to update directives when code changes.")
    print("   Skips for WIP commits automatically.")


if __name__ == "__main__":
    main()
