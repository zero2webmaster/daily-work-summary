"""
Airtable API Client

Lightweight client for the Airtable REST API. Uses table/base IDs
(appXXX, tblXXX) so that renaming tables in the Airtable UI never
breaks the integration.

Modeled on the PHP class in z2w-ai-suite/includes/class-airtable-api.php.
"""

import json
import time
from typing import Any

import requests

BASE_URL = "https://api.airtable.com/v0"
META_URL = "https://api.airtable.com/v0/meta"
MAX_RETRIES = 3
RETRY_BACKOFF = 2


class AirtableError(Exception):
    """Raised when the Airtable API returns a non-success response."""

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


class AirtableClient:
    """Airtable REST API client. All identifiers are IDs, never names."""

    def __init__(self, pat: str, base_id: str):
        self.pat = pat
        self.base_id = base_id
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {pat}",
            "Content-Type": "application/json",
        })

    def _request(
        self,
        method: str,
        url: str,
        *,
        json_body: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        """Execute an HTTP request with retry logic for rate limits (429)."""
        for attempt in range(MAX_RETRIES):
            try:
                resp = self._session.request(
                    method, url, json=json_body, params=params, timeout=30
                )
            except requests.RequestException as exc:
                raise AirtableError(f"Network error: {exc}") from exc

            if resp.status_code == 429:
                wait = RETRY_BACKOFF ** (attempt + 1)
                print(f"  Airtable rate-limited, waiting {wait}s...")
                time.sleep(wait)
                continue

            if resp.status_code == 401:
                raise AirtableError(
                    "Invalid Airtable PAT. Check your token at "
                    "https://airtable.com/create/tokens",
                    status_code=401,
                )

            if resp.status_code == 403:
                detail = self._extract_error(resp)
                raise AirtableError(
                    f"Airtable PAT lacks permissions: {detail}. "
                    "Ensure scopes include data.records:read, "
                    "data.records:write, and schema.bases:write.",
                    status_code=403,
                )

            if resp.status_code == 404:
                raise AirtableError(
                    "Airtable resource not found. Check base_id and table IDs.",
                    status_code=404,
                )

            if resp.status_code == 422:
                detail = self._extract_error(resp)
                raise AirtableError(
                    f"Airtable validation error: {detail}. "
                    "Check field names and types match the table schema.",
                    status_code=422,
                )

            if resp.status_code not in (200, 201):
                detail = self._extract_error(resp)
                raise AirtableError(
                    f"Airtable API error ({resp.status_code}): {detail}",
                    status_code=resp.status_code,
                )

            return resp.json()

        raise AirtableError("Airtable rate limit exceeded after retries.")

    @staticmethod
    def _extract_error(resp: requests.Response) -> str:
        try:
            data = resp.json()
            return data.get("error", {}).get("message", resp.text[:200])
        except (json.JSONDecodeError, ValueError):
            return resp.text[:200]

    # ------------------------------------------------------------------
    # Record operations
    # ------------------------------------------------------------------

    def create_record(self, table_id: str, fields: dict[str, Any]) -> dict:
        """Create a single record. Returns the full record dict."""
        url = f"{BASE_URL}/{self.base_id}/{table_id}"
        data = self._request("POST", url, json_body={"fields": fields})
        return {
            "id": data["id"],
            "fields": data["fields"],
            "created_time": data.get("createdTime"),
        }

    def update_record(
        self, table_id: str, record_id: str, fields: dict[str, Any]
    ) -> dict:
        """Partial update (PATCH) a record. Only supplied fields change."""
        url = f"{BASE_URL}/{self.base_id}/{table_id}/{record_id}"
        data = self._request("PATCH", url, json_body={"fields": fields})
        return {
            "id": data["id"],
            "fields": data["fields"],
            "created_time": data.get("createdTime"),
        }

    def query_records(
        self,
        table_id: str,
        *,
        filter_formula: str | None = None,
        sort: list[dict] | None = None,
        max_records: int = 100,
        view: str | None = None,
    ) -> list[dict]:
        """Query records with optional filter, sort, and view (all by ID)."""
        url = f"{BASE_URL}/{self.base_id}/{table_id}"
        params: dict[str, Any] = {"maxRecords": max_records}
        if filter_formula:
            params["filterByFormula"] = filter_formula
        if view:
            params["view"] = view
        if sort:
            for i, s in enumerate(sort):
                params[f"sort[{i}][field]"] = s["field"]
                params[f"sort[{i}][direction]"] = s.get("direction", "asc")

        records: list[dict] = []
        while True:
            data = self._request("GET", url, params=params)
            for rec in data.get("records", []):
                records.append({
                    "id": rec["id"],
                    "fields": rec["fields"],
                    "created_time": rec.get("createdTime"),
                })
            offset = data.get("offset")
            if not offset or len(records) >= max_records:
                break
            params["offset"] = offset

        return records[:max_records]

    def get_record(self, table_id: str, record_id: str) -> dict:
        """Fetch a single record by ID."""
        url = f"{BASE_URL}/{self.base_id}/{table_id}/{record_id}"
        data = self._request("GET", url)
        return {
            "id": data["id"],
            "fields": data["fields"],
            "created_time": data.get("createdTime"),
        }

    def delete_record(self, table_id: str, record_id: str) -> dict:
        """Delete a record by ID."""
        url = f"{BASE_URL}/{self.base_id}/{table_id}/{record_id}"
        data = self._request("DELETE", url)
        return {"id": data["id"], "deleted": data.get("deleted", True)}

    # ------------------------------------------------------------------
    # Schema / Meta API operations
    # ------------------------------------------------------------------

    def create_table(
        self, name: str, fields: list[dict], description: str = ""
    ) -> dict:
        """Create a new table in the base via the Meta API.

        Requires PAT scope: schema.bases:write

        Args:
            name: Table display name.
            fields: List of field definitions per Airtable API spec.
            description: Optional table description.

        Returns:
            Dict with 'id' (tblXXX) and 'name'.
        """
        url = f"{META_URL}/bases/{self.base_id}/tables"
        body: dict[str, Any] = {"name": name, "fields": fields}
        if description:
            body["description"] = description
        data = self._request("POST", url, json_body=body)
        return {"id": data["id"], "name": data["name"]}

    def list_tables(self) -> list[dict]:
        """List all tables in the base (Meta API)."""
        url = f"{META_URL}/bases/{self.base_id}/tables"
        data = self._request("GET", url)
        tables = []
        for t in data.get("tables", []):
            tables.append({
                "id": t["id"],
                "name": t["name"],
                "fields": [
                    {"id": f["id"], "name": f["name"], "type": f.get("type")}
                    for f in t.get("fields", [])
                ],
            })
        return tables
