"""Tests for the vault HTML site builder (scripts/build_site.py)."""

import importlib.util
import json

from conftest import REPO_ROOT


def _load_builder():
    spec = importlib.util.spec_from_file_location("build_site", REPO_ROOT / "scripts" / "build_site.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_build_generates_html_with_entries(kb, add_entry):
    builder = _load_builder()
    add_entry()
    out = builder.build(kb)
    assert out.exists() and out.name == "index.html"
    page = out.read_text(encoding="utf-8")
    assert "Knowledge Vault" in page
    assert "20260101-test-entry.md" in page
    assert "test summary" in page


def test_build_escapes_script_breakers(kb, add_entry):
    builder = _load_builder()
    add_entry(body="evil </script> payload")
    out = builder.build(kb)
    data_blob = out.read_text(encoding="utf-8").split("const DATA = ")[1].split(";\n")[0]
    assert "</script>" not in data_blob
    parsed = json.loads(data_blob.replace("<\\/", "</"))
    bodies = [e["body"] for p in parsed for r in p["repos"] for e in r["entries"]]
    assert any("</script> payload" in b for b in bodies)


def test_build_skips_index_and_empty_repos(kb, add_entry):
    builder = _load_builder()
    (kb / "demo-product" / "empty-repo").mkdir()
    (kb / "demo-product" / "empty-repo" / "INDEX.md").write_text("# empty\n", encoding="utf-8")
    out = builder.build(kb)
    page = out.read_text(encoding="utf-8")
    assert "empty-repo" not in page
    assert "INDEX.md" not in page.split("const DATA = ")[1].split(";\n")[0]
