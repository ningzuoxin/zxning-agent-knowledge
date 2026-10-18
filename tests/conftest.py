"""Shared fixtures and helpers for the zxning-agent-knowledge test suite.

Run with the repo venv:  .venv/Scripts/python -m pytest tests/ -v
"""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS = REPO_ROOT / "skills"

SCRIPTS = {
    "remember": SKILLS / "zxning-mem-remember" / "scripts" / "write.py",
    "recall": SKILLS / "zxning-mem-recall" / "scripts" / "retrieve.py",
    "doctor": SKILLS / "zxning-mem-doctor" / "scripts" / "validate.py",
    "init": SKILLS / "zxning-mem-init" / "scripts" / "init_repo.py",
}

# Force UTF-8 mode so child processes read/write UTF-8 regardless of Windows locale
ENV = {**os.environ, "PYTHONUTF8": "1"}


def run_script(name, *args, stdin_data=None):
    """Run a skill script as a subprocess and return the completed process."""
    return subprocess.run(
        [sys.executable, str(SCRIPTS[name]), *[str(a) for a in args]],
        input=stdin_data,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=ENV,
    )


def run_json(name, *args, stdin_data=None):
    """Run a skill script and parse its JSON stdout."""
    proc = run_script(name, *args, stdin_data=stdin_data)
    return json.loads(proc.stdout)


def load_module(script_key, module_name):
    """Import a skill script as a module for unit-level tests."""
    spec = importlib.util.spec_from_file_location(module_name, SCRIPTS[script_key])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def entry_fm(type_="how-to", status="accepted", title="Test entry",
             summary="test summary", date="20260101", tags=None, extra=""):
    """Build a valid frontmatter block matching the documented schema."""
    tags = ["test"] if tags is None else tags
    lines = [
        "---",
        f"type: {type_}",
        f"status: {status}",
        f"title: {title}",
        f"summary: {summary}",
        f"date: {date}",
        f"tags: {json.dumps(tags)}",
    ]
    if extra:
        lines.append(extra)
    lines.append("---")
    return "\n".join(lines)


@pytest.fixture
def kb(tmp_path):
    """A fresh knowledge base with product demo-product / repo api / moc, built by init_repo."""
    root = tmp_path / "kb"
    root.mkdir()
    res = run_json("init", str(root), "demo-product", "api", "--description", "test product")
    assert res["status"] == "ok"
    return root


@pytest.fixture
def add_entry(kb):
    """Add an entry via the write skill (creates the file and updates INDEX.md)."""
    def _add(repo="api", filename="20260101-test-entry.md", body="body text", **fm):
        payload = {
            "knowledge_base_path": str(kb),
            "product": "demo-product",
            "repo": repo,
            "filename": filename,
            "frontmatter": entry_fm(**fm),
            "body": body,
            "type": fm.get("type_", "how-to"),
            "summary": fm.get("summary", "test summary"),
            "tags": fm.get("tags") or ["test"],
        }
        return run_json("remember", str(kb), "demo-product", repo, "create-entry", stdin_data=json.dumps(payload))
    return _add


@pytest.fixture
def validate_kb(kb):
    """Run the validate skill against the fixture KB; returns (exit_code, parsed_json)."""
    def _run():
        proc = run_script("doctor", str(kb))
        return proc.returncode, json.loads(proc.stdout)
    return _run
