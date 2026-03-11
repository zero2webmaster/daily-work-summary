#!/usr/bin/env python3
"""
Airtable Table Setup Script

One-time script that creates the Daily Summaries and Repositories tables
inside an existing Airtable base using the Meta API.

Prerequisites:
  1. Create an Airtable base manually at https://airtable.com
  2. Create a PAT at https://airtable.com/create/tokens with scopes:
     - data.records:read
     - data.records:write
     - schema.bases:read
     - schema.bases:write
     Grant access to the base you created.

Usage:
  AIRTABLE_PAT=patXXX AIRTABLE_BASE_ID=appXXX python3 execution/setup_airtable.py

Output:
  Prints the table IDs (tblXXX) to configure as GitHub repository variables.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".github", "scripts"))

from airtable_client import AirtableClient, AirtableError  # noqa: E402


def get_config() -> tuple[str, str]:
    pat = os.environ.get("AIRTABLE_PAT")
    base_id = os.environ.get("AIRTABLE_BASE_ID")

    if not pat or not base_id:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            pat = pat or os.environ.get("AIRTABLE_PAT")
            base_id = base_id or os.environ.get("AIRTABLE_BASE_ID")
        except ImportError:
            pass

    if not pat:
        print("ERROR: AIRTABLE_PAT not set.")
        print("  Create a token at https://airtable.com/create/tokens")
        print("  Required scopes: data.records:read, data.records:write,")
        print("                   schema.bases:read, schema.bases:write")
        sys.exit(1)

    if not base_id:
        print("ERROR: AIRTABLE_BASE_ID not set.")
        print("  1. Create a base at https://airtable.com")
        print("  2. Copy the base ID from the URL: https://airtable.com/appXXXXXXXXXXXXXX")
        sys.exit(1)

    return pat, base_id


DAILY_SUMMARIES_FIELDS = [
    {
        "name": "Timestamp",
        "type": "singleLineText",
        "description": "Date string in YYYY-MM-DD format (primary field, unique key)",
    },
    {
        "name": "Date",
        "type": "date",
        "options": {"dateFormat": {"name": "iso"}},
        "description": "Airtable native date for calendar views and filtering",
    },
    {
        "name": "Summary",
        "type": "multilineText",
        "description": "Full markdown summary of the day's work",
    },
    {
        "name": "Repos Worked On",
        "type": "number",
        "options": {"precision": 0},
        "description": "Number of repositories with commits",
    },
    {
        "name": "Total Commits",
        "type": "number",
        "options": {"precision": 0},
        "description": "Total commits across all repos",
    },
    {
        "name": "AI Summaries",
        "type": "multilineText",
        "description": "Bulleted list of AI-generated repo summaries (no commit details)",
    },
]

REPOSITORIES_FIELDS = [
    {
        "name": "Name",
        "type": "singleLineText",
        "description": "Repository full name: owner/repo-name",
    },
    {
        "name": "URL",
        "type": "url",
        "description": "GitHub repository URL",
    },
    {
        "name": "Owner",
        "type": "singleLineText",
        "description": "GitHub organization or username",
    },
]


def main():
    print("=" * 55)
    print("Airtable Setup — Daily Work Summary")
    print("=" * 55)

    pat, base_id = get_config()
    client = AirtableClient(pat=pat, base_id=base_id)

    print(f"\nBase ID: {base_id}")

    # Check for existing tables to avoid duplicates
    try:
        existing = client.list_tables()
        existing_names = {t["name"].lower() for t in existing}
    except AirtableError as exc:
        print(f"\nERROR listing existing tables: {exc}")
        print("  Ensure your PAT has schema.bases:read scope and access to this base.")
        sys.exit(1)

    # --- Create Daily Summaries table ---
    summaries_id = None
    if "daily summaries" in existing_names:
        for t in existing:
            if t["name"].lower() == "daily summaries":
                summaries_id = t["id"]
                break
        print(f"\n'Daily Summaries' table already exists: {summaries_id}")
    else:
        try:
            result = client.create_table(
                name="Daily Summaries",
                fields=DAILY_SUMMARIES_FIELDS,
                description="One record per day with summary, commit counts, and AI summaries",
            )
            summaries_id = result["id"]
            print(f"\nCreated 'Daily Summaries' table: {summaries_id}")
        except AirtableError as exc:
            print(f"\nERROR creating Daily Summaries table: {exc}")
            sys.exit(1)

    # --- Create Repositories table ---
    repos_id = None
    if "repositories" in existing_names:
        for t in existing:
            if t["name"].lower() == "repositories":
                repos_id = t["id"]
                break
        print(f"'Repositories' table already exists: {repos_id}")
    else:
        try:
            result = client.create_table(
                name="Repositories",
                fields=REPOSITORIES_FIELDS,
                description="GitHub repositories linked to daily summaries",
            )
            repos_id = result["id"]
            print(f"Created 'Repositories' table: {repos_id}")
        except AirtableError as exc:
            print(f"\nERROR creating Repositories table: {exc}")
            sys.exit(1)

    # --- Add linked record fields (must be done after both tables exist) ---
    # The Meta API's create-table endpoint doesn't support cross-table links
    # in the initial field list, so we add them via a separate PATCH call.
    if summaries_id and repos_id:
        _add_linked_field(client, summaries_id, repos_id)

    # --- Output configuration ---
    print("\n" + "=" * 55)
    print("Setup complete! Add these as GitHub repository VARIABLES:")
    print("  Settings > Secrets and variables > Actions > Variables")
    print("=" * 55)
    print(f"\n  AIRTABLE_TABLE_SUMMARIES = {summaries_id}")
    print(f"  AIRTABLE_TABLE_REPOS     = {repos_id}")
    print(f"\n  (Base ID you already have: AIRTABLE_BASE_ID = {base_id})")
    print(f"\n  Also add AIRTABLE_PAT as a SECRET (not a variable).")
    print(f"\n  Set DELIVERY_METHOD variable to 'both' or 'airtable'")
    print(f"  to enable Airtable delivery.\n")


def _add_linked_field(
    client: AirtableClient, summaries_table_id: str, repos_table_id: str
):
    """Add the bidirectional linked-record field between the two tables.

    Creating a link field on one table automatically creates the inverse
    field on the other table in Airtable.
    """
    url = f"https://api.airtable.com/v0/meta/bases/{client.base_id}/tables/{summaries_table_id}/fields"
    body = {
        "name": "Repositories",
        "type": "multipleRecordLinks",
        "options": {
            "linkedTableId": repos_table_id,
            "inverseLinkFieldName": "Daily Summaries",
        },
    }
    try:
        client._request("POST", url, json_body=body)
        print("Linked 'Daily Summaries.Repositories' <-> 'Repositories.Daily Summaries'")
    except AirtableError as exc:
        if "already exists" in str(exc).lower() or exc.status_code == 422:
            print("Linked record fields already exist (skipped).")
        else:
            print(f"WARNING: Could not create linked field: {exc}")
            print("  You may need to add a 'Link to another record' field manually.")


if __name__ == "__main__":
    main()
