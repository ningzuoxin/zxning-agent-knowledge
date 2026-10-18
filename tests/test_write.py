"""Tests for the write skill (write.py)."""

import json
import re

from conftest import load_module, run_json, run_script


def _frontmatter_stdin(**fields):
    return json.dumps(fields)


def test_generate_frontmatter_ok():
    out = run_json("remember", "kb", "p", "r", "generate-frontmatter", stdin_data=_frontmatter_stdin(
        type="how-to", status="accepted", title="T", summary="auth token refresh",
        date="2026-01-01", tags=["a"]))
    assert out["status"] == "ok"
    assert re.fullmatch(r"20260101-[a-z0-9-]+\.md", out["filename"])
    assert out["frontmatter"].startswith("---\n") and out["frontmatter"].endswith("\n---")


def test_generate_frontmatter_invalid_type():
    proc = run_script("remember", "kb", "p", "r", "generate-frontmatter", stdin_data=_frontmatter_stdin(
        type="bogus", status="accepted", title="T", summary="s", date="2026-01-01"))
    assert proc.returncode == 1
    out = json.loads(proc.stdout)
    assert any("Invalid type value" in e for e in out["errors"])


def test_generate_frontmatter_decision_requires_confidence():
    proc = run_script("remember", "kb", "p", "r", "generate-frontmatter", stdin_data=_frontmatter_stdin(
        type="decision", status="accepted", title="T", summary="s", date="2026-01-01"))
    assert proc.returncode == 1
    out = json.loads(proc.stdout)
    assert any("confidence" in e for e in out["errors"])


def test_slugify():
    write = load_module("remember", "zk_write")
    assert write.slugify("Auth Token: Refresh & Flow!") == "auth-token-refresh-flow"


def test_detect_conflict_exact(kb, add_entry):
    add_entry(summary="auth token refresh flow")
    payload = {"knowledge_base_path": str(kb), "product": "demo-product", "repo": "api", "strategy": "exact"}
    hit = run_json("remember", str(kb), "demo-product", "api", "detect-conflict",
                   stdin_data=json.dumps({**payload, "summary": "AUTH TOKEN REFRESH FLOW"}))
    assert hit["has_conflict"] is True
    miss = run_json("remember", str(kb), "demo-product", "api", "detect-conflict",
                    stdin_data=json.dumps({**payload, "summary": "database migration plan"}))
    assert miss["has_conflict"] is False


def test_detect_conflict_jaccard(kb, add_entry):
    add_entry(summary="auth token refresh flow")
    out = run_json("remember", str(kb), "demo-product", "api", "detect-conflict", stdin_data=json.dumps(
        {"knowledge_base_path": str(kb), "product": "demo-product", "repo": "api",
         "summary": "auth token refresh strategy", "strategy": "jaccard", "threshold": 0.3}))
    assert out["has_conflict"] is True


def test_create_entry_updates_index_and_passes_validate(kb, add_entry, validate_kb):
    res = add_entry()
    assert res["status"] == "ok"
    index = (kb / "demo-product" / "api" / "INDEX.md").read_text(encoding="utf-8")
    assert "20260101-test-entry.md" in index
    code, out = validate_kb()
    assert out["summary"]["failed"] == 0, out["results"]


def test_create_moc_index_adds_row_once(kb):
    for _ in range(2):
        out = run_json("remember", str(kb), "demo-product", "api", "create-moc-index",
                       stdin_data=json.dumps({"knowledge_base_path": str(kb), "product": "demo-product"}))
        assert out["status"] == "ok"
    content = (kb / "demo-product" / "INDEX.md").read_text(encoding="utf-8")
    assert content.count("| moc/ |") == 1


def test_generate_frontmatter_quotes_colons():
    out = run_json("remember", "kb", "p", "r", "generate-frontmatter", stdin_data=_frontmatter_stdin(
        type="how-to", status="accepted", title="Auth: rework flow", summary="token: refresh",
        date="2026-01-01", tags=["a"]))
    assert out["status"] == "ok"
    assert 'title: "Auth: rework flow"' in out["frontmatter"]
    assert 'summary: "token: refresh"' in out["frontmatter"]


def test_create_entry_backfills_missing_frontmatter_fields(kb):
    fm = "---\ntype: how-to\nstatus: accepted\ntitle: Partial entry\ndate: 2026-01-02\n---"
    payload = {"knowledge_base_path": str(kb), "product": "demo-product", "repo": "api",
               "filename": "20260102-partial-entry.md", "frontmatter": fm,
               "body": "b", "type": "how-to", "summary": "backfilled summary text", "tags": ["backfill"]}
    out = run_json("remember", str(kb), "demo-product", "api", "create-entry", stdin_data=json.dumps(payload))
    assert out["status"] == "ok", out
    text = (kb / "demo-product" / "api" / "20260102-partial-entry.md").read_text(encoding="utf-8")
    assert "summary: backfilled summary text" in text
    assert "tags: [\"backfill\"]" in text
    index = (kb / "demo-product" / "api" / "INDEX.md").read_text(encoding="utf-8")
    assert "backfilled summary text" in index


def test_create_entry_rejects_broken_yaml(kb):
    fm = "---\ntype: how-to\nstatus: accepted\ntitle: A: broken\ndate: 2026-01-03\nsummary: s\n---"
    payload = {"knowledge_base_path": str(kb), "product": "demo-product", "repo": "api",
               "filename": "20260103-broken.md", "frontmatter": fm, "body": "b"}
    proc = run_script("remember", str(kb), "demo-product", "api", "create-entry", stdin_data=json.dumps(payload))
    assert proc.returncode == 1
    out = json.loads(proc.stdout)
    assert any("YAML parse error" in e for e in out["errors"])
    assert not (kb / "demo-product" / "api" / "20260103-broken.md").exists()
