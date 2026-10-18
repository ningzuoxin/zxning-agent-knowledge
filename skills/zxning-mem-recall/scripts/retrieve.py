#!/usr/bin/env python3
"""Retrieve skill - search knowledge entries by query.

Usage:
  python retrieve.py <knowledge_base_path> <product> <repo> <query>
"""

import sys
import json
import re
import yaml
from pathlib import Path
from typing import List, Dict, Tuple


def read_index(index_path: Path) -> List[Dict]:
    """Parse INDEX.md and return list of entry metadata."""
    if not index_path.exists():
        return []
    content = index_path.read_text(encoding="utf-8")
    entries = []
    for m in re.finditer(r"\| (\d{8}[-.\w]+\.md) \| ([\w-]+) \| (.+?) \| (\[.*\]|\(.*\)) \|", content):
        entries.append({
            "file": m.group(1),
            "type": m.group(2),
            "summary": m.group(3).strip(),
            "tags_str": m.group(4).strip()
        })
    return entries


def read_full_entry(filepath: Path) -> Dict:
    """Read a full entry file and return frontmatter + body."""
    content = filepath.read_text(encoding="utf-8")
    fm = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                fm = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                fm = {}
            body = parts[2].strip()
    return {"frontmatter": fm, "body": body, "path": str(filepath)}


def match_query(query: str, entry: Dict) -> float:
    """Score how well an entry matches the query (0-1)."""
    q = query.lower()
    score = 0.0
    summary = entry.get("summary", "").lower()
    tags_str = entry.get("tags_str", "").lower()
    entry_type = entry.get("type", "").lower()

    query_words = set(q.split())
    summary_words = set(summary.split())

    if q in summary:
        score += 0.5
    if summary_words and query_words:
        overlap = len(summary_words & query_words)
        score += 0.3 * (overlap / len(query_words))
    for word in query_words:
        if word in tags_str:
            score += 0.2
    if q in entry_type:
        score += 0.1

    return min(score, 1.0)


def extract_moc_ref_links(body: str) -> List[str]:
    """Extract all repo entry paths from the moc entry's References section.

    Accepts both the English heading ("References") and the legacy Chinese one ("参考条目").
    """
    links = []
    in_ref = False
    for line in body.split("\n"):
        if "参考条目" in line or (line.lstrip().startswith("#") and "reference" in line.lower()):
            in_ref = True
            continue
        if in_ref:
            if line.startswith("- [") and ".md" in line:
                m = re.search(r"\(([^)]+\.md)\)", line)
                if m:
                    links.append(m.group(1))
            elif not line.startswith("- ") and not line.startswith("  ") and line.strip():
                in_ref = False
    return links


def main():
    if len(sys.argv) < 5:
        print(json.dumps({"error": "Usage: retrieve.py <kb_path> <product> <repo> <query>"}, ensure_ascii=False))
        sys.exit(1)

    kb_path = Path(sys.argv[1]).resolve()
    product = sys.argv[2]
    repo = sys.argv[3]
    query = sys.argv[4]

    product_dir = kb_path / product
    repo_dir = product_dir / repo
    moc_dir = product_dir / "moc"

    results = []
    seen_paths = set()

    # Step 1: Read repo entries
    if repo_dir.exists():
        repo_index = repo_dir / "INDEX.md"
        repo_entries = read_index(repo_index)
        for entry in repo_entries:
            score = match_query(query, entry)
            if score > 0:
                entry_path = repo_dir / entry["file"]
                if entry_path.exists():
                    full = read_full_entry(entry_path)
                    full["score"] = round(score, 3)
                    full["source"] = f"{product}/{repo}/{entry['file']}"
                    if full["path"] not in seen_paths:
                        seen_paths.add(full["path"])
                        results.append(full)

    # Step 2: Read moc entries
    if moc_dir.exists():
        moc_index = moc_dir / "INDEX.md"
        moc_entries = read_index(moc_index)
        moc_hit_entries = []
        for entry in moc_entries:
            score = match_query(query, entry)
            if score > 0:
                entry_path = moc_dir / entry["file"]
                if entry_path.exists():
                    full = read_full_entry(entry_path)
                    full["score"] = round(score, 3)
                    full["source"] = f"{product}/moc/{entry['file']}"
                    moc_hit_entries.append(full)
                    if full["path"] not in seen_paths:
                        seen_paths.add(full["path"])
                        results.append(full)

        # Step 3: For each hit moc entry, read ALL linked repo entries (not just current repo)
        for moc_entry in moc_hit_entries:
            ref_links = extract_moc_ref_links(moc_entry.get("body", ""))
            for link in ref_links:
                # Links are relative to the product root (see DESIGN.md), e.g. "api/20260101-foo.md"
                link_path = (kb_path / product / link).resolve()
                if link_path.exists() and str(link_path) not in seen_paths:
                    # Check if it's a .md file in a repo directory
                    seen_paths.add(str(link_path))
                    full = read_full_entry(link_path)
                    full["score"] = 0.1  # baseline score; moc association itself has value
                    full["source"] = link
                    full["via_moc"] = moc_entry["source"]
                    results.append(full)

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)

    output = {
        "query": query,
        "product": product,
        "repo": repo,
        "total": len(results),
        "results": results,
        "has_results": len(results) > 0
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if not results:
        print(
            f"No knowledge found for '{query}'. Hint: consult the code repo's own docs, or invoke the write skill to deposit new knowledge.",
            file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
