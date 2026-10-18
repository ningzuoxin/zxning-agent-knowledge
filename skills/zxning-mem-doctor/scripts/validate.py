#!/usr/bin/env python3
"""Validation skill - checks knowledge base consistency and integrity.

Usage:
  python validate.py <knowledge_base_path> [product] [repo]

Output:
  JSON to stdout with check results. Exit code 0 if all pass, 1 otherwise.
"""

import sys
import os
import json
import re
import yaml  # PyYAML
from pathlib import Path
from typing import List, Dict

RESULTS = []


def fail(check: str, detail: str, fix: str):
    RESULTS.append({"check": check, "status": "fail", "detail": detail, "fix": fix})


def pass_(check: str):
    RESULTS.append({"check": check, "status": "pass"})


def collect_md_files(directory: Path) -> List[Path]:
    return sorted([f for f in directory.iterdir() if f.suffix == ".md" and f.name != "INDEX.md"])


def parse_frontmatter(filepath: Path):
    """Return (frontmatter_dict, parse_error). parse_error is None on success."""
    content = filepath.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return {}, None
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, None
    try:
        return yaml.safe_load(parts[1]) or {}, None
    except yaml.YAMLError as exc:
        return {}, str(exc)


def check_index_vs_directory(kb_path: Path):
    """Check product root INDEX.md repos table matches actual directories."""
    required_fields = {"type", "status", "title", "summary", "date"}
    type_enum = {"tutorial", "how-to", "reference", "explanation", "decision", "incident"}
    status_enum = {"proposed", "accepted", "deprecated", "superseded", "resolved"}
    confidence_enum = {"high", "medium", "low"}

    for product_dir in kb_path.iterdir():
        if not product_dir.is_dir() or product_dir.name == "skills" or product_dir.name.startswith("."):
            continue
        index_path = product_dir / "INDEX.md"
        if not index_path.exists():
            fail("product_root_index_exists",
                 f"Product {product_dir.name} is missing INDEX.md",
                 f"Create {index_path} with a title, description, and repos table")
            continue

        actual_dirs = set()
        for d in product_dir.iterdir():
            if d.is_dir() and d.name != "skills":
                actual_dirs.add(d.name)

        index_content = index_path.read_text(encoding="utf-8")
        indexed_dirs = set()
        for m in re.finditer(r"\|\s*(\S+/)\s*\|", index_content):
            dir_name = m.group(1).rstrip("/")
            indexed_dirs.add(dir_name)

        missing = actual_dirs - indexed_dirs
        extra = indexed_dirs - actual_dirs
        if missing:
            fail("repos_table_completeness",
                 f"INDEX.md of product {product_dir.name} is missing directories: {', '.join(sorted(missing))}",
                 f"Add these rows to the repos table")
        if extra:
            fail("repos_table_completeness",
                 f"INDEX.md of product {product_dir.name} has extra directories: {', '.join(sorted(extra))}",
                 f"Remove these rows from the repos table")
        if not missing and not extra:
            pass_("repos_table_completeness")

        for repo_dir_str in actual_dirs:
            if repo_dir_str == "moc":
                continue
            repo_path = product_dir / repo_dir_str
            repo_index = repo_path / "INDEX.md"
            if not repo_index.exists():
                fail("repo_index_exists",
                     f"Repo {product_dir.name}/{repo_dir_str} is missing INDEX.md",
                     f"Create {repo_index} with an empty entry table")
                continue

            md_files = collect_md_files(repo_path)
            index_content_r = repo_index.read_text(encoding="utf-8")
            indexed_files_r = set(re.findall(r"\| (\d{8}[-.\w]+\.md) \|", index_content_r))

            missing_files = set(f.name for f in md_files) - indexed_files_r
            extra_files = indexed_files_r - set(f.name for f in md_files)
            if missing_files:
                fail("entry_table_completeness",
                     f"{product_dir.name}/{repo_dir_str}/INDEX.md is missing entries: {', '.join(sorted(missing_files))}",
                     f"Add these rows to the INDEX.md entry table")
            if extra_files:
                fail("entry_table_completeness",
                     f"{product_dir.name}/{repo_dir_str}/INDEX.md has extra entries: {', '.join(sorted(extra_files))}",
                     f"Remove these rows from the INDEX.md entry table")
            if not missing_files and not extra_files:
                pass_("entry_table_completeness")

            for f in md_files:
                fm, parse_error = parse_frontmatter(f)
                errors = []
                if parse_error:
                    errors.append(f"frontmatter YAML parse error: {parse_error} (quote values containing ': ' with double quotes)")
                else:
                    missing_fields = required_fields - set(fm.keys())
                    if missing_fields:
                        errors.append(f"Missing required fields: {', '.join(sorted(missing_fields))}")
                    if fm.get("type") not in type_enum:
                        errors.append(f"Invalid type value '{fm.get('type')}', not in enum")
                    if fm.get("status") not in status_enum:
                        errors.append(f"Invalid status value '{fm.get('status')}', not in enum")
                    if fm.get("type") == "decision" and fm.get("confidence") not in confidence_enum:
                        errors.append("type=decision but confidence is missing or invalid")
                    if fm.get("status") == "superseded" and not fm.get("superseded_by"):
                        errors.append("status=superseded but superseded_by is missing")

                if errors:
                    for err in errors:
                        fail("frontmatter_schema", f"{f.relative_to(kb_path)}: {err}", "Fix the frontmatter")
                else:
                    pass_("frontmatter_schema")

        # Check moc
        moc_path = product_dir / "moc"
        if moc_path.exists():
            moc_index = moc_path / "INDEX.md"
            if not moc_index.exists():
                fail("moc_index_exists",
                     f"moc/ directory of product {product_dir.name} is missing INDEX.md",
                     f"Create {moc_index}")
            else:
                md_files = collect_md_files(moc_path)
                index_content_m = moc_index.read_text(encoding="utf-8")
                indexed_files_m = set(re.findall(r"\| (\d{8}[-.\w]+\.md) \|", index_content_m))

                missing_m = set(f.name for f in md_files) - indexed_files_m
                extra_m = indexed_files_m - set(f.name for f in md_files)
                if missing_m:
                    fail("moc_entry_table_completeness",
                         f"{product_dir.name}/moc/INDEX.md is missing entries: {', '.join(sorted(missing_m))}",
                         f"Add these rows to moc/INDEX.md")
                if extra_m:
                    fail("moc_entry_table_completeness",
                         f"{product_dir.name}/moc/INDEX.md has extra entries: {', '.join(sorted(extra_m))}",
                         f"Remove these rows from moc/INDEX.md")
                if not missing_m and not extra_m:
                    pass_("moc_entry_table_completeness")

                # Check moc link completeness
                for f in md_files:
                    content = f.read_text(encoding="utf-8")
                    # Extract involved repos from the "Involved Repos" table
                    # (heading accepts English "Involved Repos" or legacy Chinese "涉及 repo")
                    involved_repos = set()
                    in_table = False
                    for line in content.split("\n"):
                        if "涉及 repo" in line or (line.lstrip().startswith("#") and "involved" in line.lower()):
                            in_table = True
                            continue
                        if in_table and line.startswith("|") and not line.lower().startswith("| repo") and not line.startswith("| ---"):
                            parts = [p.strip() for p in line.split("|")]
                            if len(parts) >= 2:
                                involved_repos.add(parts[1])
                        # Blank lines inside a block do not close it (standard markdown puts
                        # a blank line right after the heading)
                        if in_table and line.strip() and not line.startswith("|"):
                            in_table = False

                    if involved_repos:
                        # Extract links from the "References" section
                        # (heading accepts English "References" or legacy Chinese "参考条目")
                        ref_links = set()
                        in_ref = False
                        for line in content.split("\n"):
                            if "参考条目" in line or (line.lstrip().startswith("#") and "reference" in line.lower()):
                                in_ref = True
                                continue
                            if in_ref and line.startswith("- [") and ".md" in line:
                                m = re.search(r"\(([^)]+\.md)\)", line)
                                if m:
                                    link_path = m.group(1)
                                    repo_name = link_path.split("/")[0]
                                    ref_links.add(repo_name)
                            if in_ref and line.strip() and not line.startswith("- ") and not line.startswith("  "):
                                in_ref = False

                        missing_links = involved_repos - ref_links
                        if missing_links:
                            fail("moc_link_completeness",
                                 f"{f.relative_to(kb_path)} is missing links to these repos: {', '.join(sorted(missing_links))}",
                                 f"Add at least one link per involved repo in the References section")


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: validate.py <knowledge_base_path> [product] [repo]"}, ensure_ascii=False))
        sys.exit(1)

    kb_path = Path(sys.argv[1]).resolve()
    if not kb_path.exists():
        print(json.dumps({"error": f"Knowledge base path does not exist: {kb_path}"}, ensure_ascii=False))
        sys.exit(1)

    check_index_vs_directory(kb_path)

    all_pass = all(r["status"] == "pass" for r in RESULTS)
    output = {
        "summary": {"total": len(RESULTS), "passed": sum(1 for r in RESULTS if r["status"] == "pass"),
                    "failed": sum(1 for r in RESULTS if r["status"] == "fail")},
        "results": RESULTS
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
