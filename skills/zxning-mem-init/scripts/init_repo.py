#!/usr/bin/env python3
"""Create-repo skill - initialize product/repo knowledge directory.

Usage:
  python init_repo.py <knowledge_base_path> <product> <repo> [--description "product description"]
"""

import sys
import json
from pathlib import Path


def _is_table_separator(line: str) -> bool:
    """Match markdown table separator rows in both `|---|` and `| --- |` styles."""
    s = line.strip()
    return s.startswith("|") and set(s) <= {"|", "-", ":", " "}


def ensure_product_index(product_dir: Path, description: str = ""):
    index_path = product_dir / "INDEX.md"
    if index_path.exists():
        return

    desc_line = f"> {description}" if description else ""
    content = f"""# {product_dir.name} Knowledge Index

{desc_line}

## Repos

| Directory | Role | Stack | Status |
| --- | --- | --- | --- |
"""
    index_path.write_text(content, encoding="utf-8")


def ensure_repo_index(repo_dir: Path):
    index_path = repo_dir / "INDEX.md"
    if index_path.exists():
        return
    content = f"""# {repo_dir.name} Entry Index

| File | type | summary | tags |
| --- | --- | --- | --- |
"""
    index_path.write_text(content, encoding="utf-8")


def ensure_moc(product_dir: Path):
    moc_dir = product_dir / "moc"
    if moc_dir.exists():
        return
    moc_dir.mkdir(parents=True, exist_ok=True)
    moc_index = moc_dir / "INDEX.md"
    moc_index.write_text("# moc Entry Index\n\n| File | type | summary | tags |\n| --- | --- | --- | --- |\n",
                         encoding="utf-8")

    # Add moc row to product INDEX.md
    product_index = product_dir / "INDEX.md"
    if product_index.exists() and "| moc/" not in product_index.read_text(encoding="utf-8"):
        content = product_index.read_text(encoding="utf-8")
        lines = content.rstrip().split("\n")
        # Find the separator line of the repos table (|---|)
        table_sep_idx = -1
        for i, line in enumerate(lines):
            if _is_table_separator(line):
                table_sep_idx = i
                break
        if table_sep_idx >= 0:
            # Insert after the last data row (or after separator if no data rows)
            insert_after = table_sep_idx
            for i in range(table_sep_idx + 1, len(lines)):
                if lines[i].strip().startswith("|") and "/" in lines[i]:
                    insert_after = i
            lines.insert(insert_after + 1, "| moc/ | Cross-repo knowledge | — | active |")
            product_index.write_text("\n".join(lines) + "\n", encoding="utf-8")


def add_repo_to_product_index(product_dir: Path, repo_name: str):
    index_path = product_dir / "INDEX.md"
    if not index_path.exists():
        return

    content = index_path.read_text(encoding="utf-8")
    if f"| {repo_name}/ |" in content:
        return  # already exists

    lines = content.rstrip().split("\n")
    # Find the separator line of the repos table (|---|)
    table_sep_idx = -1
    for i, line in enumerate(lines):
        if _is_table_separator(line):
            table_sep_idx = i
            break
    if table_sep_idx >= 0:
        insert_after = table_sep_idx
        for i in range(table_sep_idx + 1, len(lines)):
            if lines[i].strip().startswith("|") and "/" in lines[i]:
                insert_after = i
        lines.insert(insert_after + 1, f"| {repo_name}/ | — | — | active |")
        index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    if len(sys.argv) < 4:
        print(json.dumps({"error": "Usage: init_repo.py <kb_path> <product> <repo> [--description <desc>]"},
                         ensure_ascii=False))
        sys.exit(1)

    kb_path = Path(sys.argv[1]).resolve()
    product = sys.argv[2]
    repo = sys.argv[3]
    description = ""

    if "--description" in sys.argv:
        idx = sys.argv.index("--description")
        if idx + 1 < len(sys.argv):
            description = sys.argv[idx + 1]

    product_dir = kb_path / product
    repo_dir = product_dir / repo

    # Step 1: Ensure product exists
    product_dir.mkdir(parents=True, exist_ok=True)
    ensure_product_index(product_dir, description)

    # Step 2: Create repo directory + INDEX.md
    repo_dir.mkdir(parents=True, exist_ok=True)
    ensure_repo_index(repo_dir)

    # Step 3: Update product INDEX.md repos table
    add_repo_to_product_index(product_dir, repo)

    # Step 4: Ensure moc exists
    ensure_moc(product_dir)

    output = {
        "status": "ok",
        "created": [
            str(product_dir / "INDEX.md"),
            str(repo_dir / "INDEX.md"),
            str(product_dir / "moc" / "INDEX.md")
        ],
        "updated": [
            str(product_dir / "INDEX.md")
        ]
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
