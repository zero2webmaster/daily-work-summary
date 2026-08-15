#!/usr/bin/env python3
"""Offline unit tests for portfolio_stats.py — no GitHub, no cloning, no cloc.

Covers the two pure functions: parse_cloc_sum (cloc JSON → loc/doc) and
build_portfolio_stats (per-repo entries → aggregate + sorted artifact).

Run:
    source venv/bin/activate
    python .tmp/test_portfolio_stats.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".github" / "scripts"))

from portfolio_stats import (  # noqa: E402
    build_portfolio_stats,
    classify_cloc,
    SCHEMA_VERSION,
)

passed = 0
failed = 0


def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}")


# --- classify_cloc (code vs documentation split) --------------------------

# 1. Mixed payload: code language + a doc language + comments.
#    Python: 1500 code + 200 comment. Markdown: 300 "code" lines (prose) + 0 comment.
#    loc = 1500 (Python code only). doc = 200 (Python comments) + 300 (Markdown) = 500.
cloc_mixed = {
    "header": {"n_files": 14},
    "Python": {"nFiles": 8, "blank": 100, "comment": 200, "code": 1500},
    "Markdown": {"nFiles": 6, "blank": 50, "comment": 0, "code": 300},
    "SUM": {"blank": 150, "comment": 200, "code": 1800, "nFiles": 14},
}
check("classify_cloc splits code vs docs (loc=code langs)", classify_cloc(cloc_mixed)[0] == 1500)
check("classify_cloc folds prose+comments into doc_lines", classify_cloc(cloc_mixed)[1] == 500)

# 2. Multiple code languages: their code sums; their comments go to docs.
cloc_multi = {
    "PHP": {"code": 1000, "comment": 120},
    "JavaScript": {"code": 800, "comment": 80},
    "SUM": {"code": 1800, "comment": 200},
}
check("classify_cloc sums multiple code languages", classify_cloc(cloc_multi) == (1800, 200))

# 3. Missing / non-dict input
check("classify_cloc handles non-dict", classify_cloc(None) == (0, 0))
check("classify_cloc handles list", classify_cloc([1, 2, 3]) == (0, 0))
check("classify_cloc handles empty", classify_cloc({"header": {}}) == (0, 0))

# 4. Non-numeric values coerced to 0
check(
    "classify_cloc coerces bad values to 0",
    classify_cloc({"PHP": {"code": "x", "comment": None}}) == (0, 0),
)

# --- build_portfolio_stats ------------------------------------------------

entries = [
    {"name": "small", "owner": "zero2webmaster", "loc": 100, "doc_lines": 10,
     "last_commit_date": "2026-06-01", "status": "active"},
    {"name": "big", "owner": "zero2webmaster", "loc": 5000, "doc_lines": 800,
     "last_commit_date": "2026-06-17", "status": "active"},
    {"name": "old", "owner": "kerrykriger", "loc": 2000, "doc_lines": 300,
     "last_commit_date": "2025-01-01", "status": "archived"},
]
art = build_portfolio_stats(entries, "2026-06", "2026-06-18T12:00:00Z")

# 5. Schema + metadata
check("schema is portfolio-stats/v1", art["schema"] == SCHEMA_VERSION)
check("period preserved", art["period"] == "2026-06")
check("generated_at preserved", art["generated_at"] == "2026-06-18T12:00:00Z")

# 6. Aggregate math
agg = art["aggregate"]
check("repo_count", agg["repo_count"] == 3)
check("active_repo_count", agg["active_repo_count"] == 2)
check("archived_repo_count", agg["archived_repo_count"] == 1)
check("total_loc sums all repos", agg["total_loc"] == 7100)
check("total_doc_lines sums all repos", agg["total_doc_lines"] == 1110)

# 7. Repos sorted by LoC descending
check("repos sorted by loc desc", [r["name"] for r in art["repos"]] == ["big", "old", "small"])

# 8. None loc/doc (a repo that failed to measure) doesn't crash aggregation
entries_with_null = [
    {"name": "failed", "owner": "x", "loc": None, "doc_lines": None,
     "last_commit_date": None, "status": "active", "error": "clone failed"},
    {"name": "ok", "owner": "x", "loc": 50, "doc_lines": 5,
     "last_commit_date": "2026-06-10", "status": "active"},
]
art2 = build_portfolio_stats(entries_with_null, "2026-06", "2026-06-18T12:00:00Z")
check("null loc treated as 0 in total", art2["aggregate"]["total_loc"] == 50)
check("null doc treated as 0 in total", art2["aggregate"]["total_doc_lines"] == 5)
check("failed repo still counted", art2["aggregate"]["repo_count"] == 2)
check("failed repo preserved with error note", art2["repos"][-1].get("error") == "clone failed")

# 9. Empty portfolio
art3 = build_portfolio_stats([], "2026-06", "2026-06-18T12:00:00Z")
check("empty portfolio repo_count 0", art3["aggregate"]["repo_count"] == 0)
check("empty portfolio total_loc 0", art3["aggregate"]["total_loc"] == 0)
check("empty portfolio repos list empty", art3["repos"] == [])

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
