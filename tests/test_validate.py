"""Tests for the validate skill (validate.py)."""

from conftest import entry_fm


def test_fresh_kb_passes(kb, add_entry, validate_kb):
    add_entry()
    code, out = validate_kb()
    assert out["summary"]["failed"] == 0, out["results"]
    assert code == 0


def test_missing_repo_index_detected(kb, validate_kb):
    (kb / "demo-product" / "api" / "INDEX.md").unlink()
    code, out = validate_kb()
    checks = [r for r in out["results"] if r["check"] == "repo_index_exists" and r["status"] == "fail"]
    assert checks
    assert code == 1


def test_entry_missing_from_index_detected(kb, validate_kb):
    (kb / "demo-product" / "api" / "20260201-orphan.md").write_text(entry_fm(summary="orphan entry"), encoding="utf-8")
    code, out = validate_kb()
    checks = [r for r in out["results"] if r["check"] == "entry_table_completeness" and r["status"] == "fail"]
    assert checks and "20260201-orphan.md" in checks[0]["detail"]


def test_invalid_type_value_detected(kb, validate_kb):
    # create-entry now rejects invalid enums at write time; doctor must still catch
    # files written by other means.
    (kb / "demo-product" / "api" / "20260202-bad-type.md").write_text(
        entry_fm(type_="bogus"), encoding="utf-8")
    code, out = validate_kb()
    checks = [r for r in out["results"] if r["check"] == "frontmatter_schema" and r["status"] == "fail"]
    assert checks and "Invalid type value" in checks[0]["detail"]


def test_decision_requires_confidence(kb, validate_kb):
    (kb / "demo-product" / "api" / "20260203-no-confidence.md").write_text(
        entry_fm(type_="decision"), encoding="utf-8")
    code, out = validate_kb()
    checks = [r for r in out["results"] if r["check"] == "frontmatter_schema" and r["status"] == "fail"]
    assert checks and "confidence" in checks[0]["detail"]


def test_superseded_requires_superseded_by(kb, validate_kb):
    (kb / "demo-product" / "api" / "20260204-no-superseded-by.md").write_text(
        entry_fm(status="superseded"), encoding="utf-8")
    code, out = validate_kb()
    checks = [r for r in out["results"] if r["check"] == "frontmatter_schema" and r["status"] == "fail"]
    assert checks and "superseded_by" in checks[0]["detail"]


def test_moc_links_english_headings(kb, add_entry, validate_kb):
    add_entry()
    add_entry(repo="moc", filename="20260102-flow.md", type_="explanation", summary="auth flow", tags=["auth"],
              body="Cross-repo flow.\n\n## Involved repos\n\n| Repo | Why |\n| --- | --- |\n"
                   "| api | owns auth |\n\n## References\n\n- [api entry](api/20260101-test-entry.md)\n")
    code, out = validate_kb()
    assert out["summary"]["failed"] == 0, out["results"]


def test_moc_links_chinese_headings(kb, add_entry, validate_kb):
    add_entry()
    add_entry(repo="moc", filename="20260102-flow.md", type_="explanation", summary="auth flow", tags=["auth"],
              body="跨 repo 流程。\n\n## 涉及 repo\n\n| Repo | 原因 |\n| --- | --- |\n"
                   "| api | 认证入口 |\n\n## 参考条目\n\n- [api 条目](api/20260101-test-entry.md)\n")
    code, out = validate_kb()
    assert out["summary"]["failed"] == 0, out["results"]


def test_moc_missing_link_detected(kb, add_entry, validate_kb):
    add_entry()
    add_entry(repo="moc", filename="20260102-flow.md", type_="explanation", summary="auth flow", tags=["auth"],
              body="Cross-repo flow.\n\n## Involved repos\n\n| Repo | Why |\n| --- | --- |\n"
                   "| api | owns auth |\n\n## References\n\n(none yet)\n")
    code, out = validate_kb()
    checks = [r for r in out["results"] if r["check"] == "moc_link_completeness" and r["status"] == "fail"]
    assert checks and "api" in checks[0]["detail"]


def test_moc_separator_row_not_treated_as_repo(kb, add_entry, validate_kb):
    add_entry()
    add_entry(repo="moc", filename="20260102-flow.md", type_="explanation", summary="auth flow", tags=["auth"],
              body="Cross-repo flow.\n\n## Involved repos\n\n| Repo | Why |\n| --- | --- |\n"
                   "| api | owns auth |\n\n## References\n\n- [api entry](api/20260101-test-entry.md)\n")
    code, out = validate_kb()
    fails = [r["detail"] for r in out["results"] if r["status"] == "fail"]
    assert all("---" not in d for d in fails)


def test_incident_resolved_status_valid(kb, add_entry, validate_kb):
    add_entry(filename="20260104-incident-resolved.md", type_="incident", status="resolved",
              summary="resolved incident entry")
    code, out = validate_kb()
    assert out["summary"]["failed"] == 0, out["results"]


def test_broken_yaml_reported_clearly(kb, validate_kb):
    d = kb / "demo-product" / "api"
    d.mkdir(parents=True, exist_ok=True)
    (d / "INDEX.md").write_text(
        "# api Entry Index\n\n| File | type | summary | tags |\n| --- | --- | --- | --- |\n",
        encoding="utf-8")
    (d / "20260105-broken-yaml.md").write_text(
        "---\ntype: how-to\nstatus: accepted\ntitle: A: broken\ndate: 2026-01-05\nsummary: s\n---\n\nbody",
        encoding="utf-8")
    code, out = validate_kb()
    fails = [r for r in out["results"] if r["status"] == "fail" and "broken-yaml" in r["detail"]]
    assert fails and any("YAML parse error" in r["detail"] for r in fails)
    assert not any("Invalid type value 'None'" in r.get("detail", "") for r in out["results"])
