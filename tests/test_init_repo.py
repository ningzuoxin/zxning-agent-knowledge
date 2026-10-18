"""Tests for the create-repo skill (init_repo.py)."""

from conftest import run_json


def test_creates_full_structure(tmp_path):
    kb = tmp_path / "kb"
    out = run_json("init", str(kb), "demo-product", "api", "--description", "test product")
    assert out["status"] == "ok"
    assert (kb / "demo-product" / "INDEX.md").exists()
    assert (kb / "demo-product" / "api" / "INDEX.md").exists()
    assert (kb / "demo-product" / "moc" / "INDEX.md").exists()


def test_product_index_lists_repo_and_moc(tmp_path):
    kb = tmp_path / "kb"
    run_json("init", str(kb), "demo-product", "api")
    content = (kb / "demo-product" / "INDEX.md").read_text(encoding="utf-8")
    assert "| api/ |" in content
    assert "| moc/ |" in content


def test_idempotent(tmp_path):
    kb = tmp_path / "kb"
    run_json("init", str(kb), "demo-product", "api")
    before = (kb / "demo-product" / "INDEX.md").read_text(encoding="utf-8")
    run_json("init", str(kb), "demo-product", "api")
    after = (kb / "demo-product" / "INDEX.md").read_text(encoding="utf-8")
    assert before == after
    assert after.count("| api/ |") == 1
    assert after.count("| moc/ |") == 1


def test_second_repo_is_appended_once(tmp_path):
    kb = tmp_path / "kb"
    run_json("init", str(kb), "demo-product", "api")
    run_json("init", str(kb), "demo-product", "web")
    content = (kb / "demo-product" / "INDEX.md").read_text(encoding="utf-8")
    assert content.count("| api/ |") == 1
    assert content.count("| web/ |") == 1
