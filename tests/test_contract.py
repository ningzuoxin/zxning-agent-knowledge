"""Contract tests: docs, install.sh and the filesystem must stay in sync."""

import re

from conftest import REPO_ROOT, SKILLS

DOC_FILES = ["README.md", "README.zh.md", "AGENTS.md", "AGENTS.zh.md", "DESIGN.md", "DESIGN.zh.md"]


def skill_dirs():
    return {d.name for d in SKILLS.iterdir() if d.is_dir()}


def test_install_installs_exactly_the_existing_skills():
    text = (REPO_ROOT / "install.sh").read_text(encoding="utf-8")
    listed = set(re.search(r"for skill in (.+?); do", text).group(1).split())
    assert listed == skill_dirs()


def test_install_guard_path_exists():
    text = (REPO_ROOT / "install.sh").read_text(encoding="utf-8")
    for ref in re.findall(r"\$SCRIPT_DIR/(skills/[\w-]+/SKILL\.md)", text):
        assert (REPO_ROOT / ref).exists(), ref


def test_skill_name_matches_directory():
    for d in SKILLS.iterdir():
        if not d.is_dir():
            continue
        text = (d / "SKILL.md").read_text(encoding="utf-8")
        name = re.search(r"^name:\s*(\S+)", text, re.MULTILINE).group(1)
        assert name == d.name


def test_skillmd_script_references_exist():
    for d in SKILLS.iterdir():
        if not d.is_dir():
            continue
        text = (d / "SKILL.md").read_text(encoding="utf-8")
        for ref in re.findall(r"[\w./-]+scripts/[\w.-]+\.py", text):
            assert (d / ref).exists(), f"{d.name}: {ref}"


def test_docs_only_reference_real_skill_names():
    real = skill_dirs()
    for fname in DOC_FILES:
        text = (REPO_ROOT / fname).read_text(encoding="utf-8")
        for token in set(re.findall(r"zxning-mem-[a-z-]+", text)):
            assert token in real, f"{fname}: {token}"


def test_snippet_template_well_formed():
    text = (REPO_ROOT / "AGENTS_SNIPPET.md").read_text(encoding="utf-8")
    assert text.count("<!-- zxning-mem:begin") == 1
    assert "<!-- zxning-mem:end -->" in text
    assert "{{PRODUCT}}" in text
    for token in re.findall(r"zxning-mem-[a-z-]+", text):
        assert token in skill_dirs(), token


def test_install_sh_wires_snippet_target():
    text = (REPO_ROOT / "install.sh").read_text(encoding="utf-8")
    assert 'AGENTS_SNIPPET.md' in text
    assert "zxning-mem:begin" in text
    assert "snippet" in text
