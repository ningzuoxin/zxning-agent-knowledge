"""Tests for the retrieve skill (retrieve.py)."""

import json

from conftest import load_module, run_script


def test_extract_moc_ref_links_english():
    retrieve = load_module("recall", "zk_retrieve")
    body = "intro\n\n## References\n\n- [a](api/20260101-a.md)\n- [b](web/20260102-b.md)\n\ntrailing text\n"
    assert retrieve.extract_moc_ref_links(body) == ["api/20260101-a.md", "web/20260102-b.md"]


def test_extract_moc_ref_links_chinese():
    retrieve = load_module("recall", "zk_retrieve_alt")
    body = "简介\n\n## 参考条目\n\n- [a](api/20260101-a.md)\n\n尾注\n"
    assert retrieve.extract_moc_ref_links(body) == ["api/20260101-a.md"]


def test_direct_hit(kb, add_entry):
    add_entry(summary="auth token refresh flow", tags=["auth"])
    proc = run_script("recall", str(kb), "demo-product", "api", "auth token")
    out = json.loads(proc.stdout)
    assert out["has_results"] is True
    assert out["results"][0]["source"] == "demo-product/api/20260101-test-entry.md"


def test_moc_hit_follows_product_relative_links(kb, add_entry):
    add_entry(summary="auth token refresh flow", tags=["auth"])
    add_entry(repo="moc", filename="20260102-flow.md", type_="explanation",
              summary="cross repo auth flow overview", tags=["auth"],
              body="Cross-repo flow.\n\n## References\n\n- [api entry](api/20260101-test-entry.md)\n")
    # Query hits only the moc entry, not the repo entry itself
    proc = run_script("recall", str(kb), "demo-product", "api", "cross repo overview")
    out = json.loads(proc.stdout)
    sources = [r["source"] for r in out["results"]]
    assert "demo-product/moc/20260102-flow.md" in sources
    # The linked repo entry is recovered via the moc link (source keeps the link's
    # product-root relative path)
    assert "api/20260101-test-entry.md" in sources
    via = [r for r in out["results"] if r.get("via_moc")]
    assert via and via[0]["via_moc"] == "demo-product/moc/20260102-flow.md"


def test_no_hit(kb, add_entry):
    add_entry(summary="auth token refresh flow")
    proc = run_script("recall", str(kb), "demo-product", "api", "zzz unrelated query")
    out = json.loads(proc.stdout)
    assert out["has_results"] is False
    assert proc.returncode == 0
    assert "No knowledge found" in proc.stderr
