#!/usr/bin/env python3
"""Write skill - knowledge entry creation and INDEX.md maintenance.

Usage:
  python write.py <knowledge_base_path> <product> <repo> <command> [args...]

Commands:
  generate-frontmatter  -- Generate frontmatter from provided fields
  detect-conflict       -- Check summary/tags overlap with existing entries
  create-entry          -- Write entry file and update INDEX.md
  update-index          -- Add/remove entry row in INDEX.md
  create-moc-index      -- Create moc/INDEX.md
"""

import sys
import os
import json
import re
import yaml
import datetime
from pathlib import Path
from typing import Optional

REQUIRED_FIELDS = {"type", "status", "title", "summary", "date"}
TYPE_ENUM = {"tutorial", "how-to", "reference", "explanation", "decision", "incident"}
STATUS_ENUM = {"proposed", "accepted", "deprecated", "superseded", "resolved"}
CONFIDENCE_ENUM = {"high", "medium", "low"}


def _yaml_needs_quoting(value: str) -> bool:
    """True when a plain scalar would break or alter YAML parsing."""
    if value != value.strip():
        return True
    if re.search(r":\s", value) or " #" in value:
        return True
    return bool(value.startswith(("&", "*", "!", "|", ">", "%", "@", "`", "{", "[", "#", '"', "'")))


def _yaml_quote(value: str) -> str:
    """Quote a scalar when needed so the generated frontmatter always parses."""
    value = str(value)
    if _yaml_needs_quoting(value):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return value


def _is_table_separator(line: str) -> bool:
    """Match markdown table separator rows in both `|---|` and `| --- |` styles."""
    s = line.strip()
    return s.startswith("|") and set(s) <= {"|", "-", ":", " "}


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text[:60].rstrip("-")


def generate_frontmatter():
    fields = json.loads(sys.stdin.read())
    errors = []
    for f in REQUIRED_FIELDS:
        if f not in fields or not fields[f]:
            errors.append(f"Missing required field: {f}")
    if fields.get("type") and fields["type"] not in TYPE_ENUM:
        errors.append(f"Invalid type value '{fields['type']}', must be one of {', '.join(sorted(TYPE_ENUM))}")
    if fields.get("status") and fields["status"] not in STATUS_ENUM:
        errors.append(f"Invalid status value '{fields['status']}', must be one of {', '.join(sorted(STATUS_ENUM))}")
    if fields.get("type") == "decision" and fields.get("confidence") not in CONFIDENCE_ENUM:
        errors.append("type=decision requires confidence: high/medium/low")
    if fields.get("status") == "superseded" and not fields.get("superseded_by"):
        errors.append("status=superseded requires superseded_by")

    if errors:
        output = {"status": "error", "errors": errors}
        print(json.dumps(output, ensure_ascii=False))
        sys.exit(1)

    fm_parts = ["---"]
    for key in ["type", "status", "title", "summary", "date", "tags", "stack", "confidence", "superseded_by"]:
        if key in fields and fields[key] is not None:
            val = fields[key]
            if isinstance(val, list):
                fm_parts.append(f"{key}: {json.dumps(val)}")
            elif isinstance(val, bool):
                fm_parts.append(f"{key}: {'true' if val else 'false'}")
            else:
                fm_parts.append(f"{key}: {_yaml_quote(val)}")
    fm_parts.append("---")

    output = {
        "status": "ok",
        "frontmatter": "\n".join(fm_parts),
        "filename": f"{fields['date'].replace('-', '')}-{slugify(fields['summary'][:40])}.md"
    }
    print(json.dumps(output, ensure_ascii=False))


def jaccard_similarity(s1: str, s2: str) -> float:
    words1 = set(s1.lower().split())
    words2 = set(s2.lower().split())
    if not words1 or not words2:
        return 0.0
    return len(words1 & words2) / len(words1 | words2)


def embed_similarity(s1: str, s2: str) -> float:
    """Simple word-overlap baseline. Real embedding requires external API."""
    return jaccard_similarity(s1, s2)


def detect_conflict():
    config = json.loads(sys.stdin.read())
    kb_path = Path(config["knowledge_base_path"])
    product = config["product"]
    repo = config["repo"]
    summary = config["summary"]
    tags = set(config.get("tags", []))
    strategy = config.get("strategy", "exact")
    threshold = config.get("threshold", 0.3)

    target_dir = kb_path / product / repo
    conflicts = []

    if target_dir.exists():
        for f in target_dir.iterdir():
            if f.suffix != ".md" or f.name == "INDEX.md":
                continue
            content = f.read_text(encoding="utf-8")
            if not content.startswith("---"):
                continue
            parts = content.split("---", 2)
            if len(parts) < 3:
                continue
            try:
                fm = yaml.safe_load(parts[1])
            except yaml.YAMLError:
                continue
            if not fm:
                continue

            if strategy == "exact":
                if fm.get("summary", "").strip().lower() == summary.strip().lower():
                    conflicts.append({"file": str(f.relative_to(kb_path)), "summary": fm.get("summary", ""),
                                     "similarity": 1.0})
            elif strategy in ("jaccard", "embedding"):
                sim = jaccard_similarity(fm.get("summary", ""), summary) if strategy == "jaccard" else embed_similarity(
                    fm.get("summary", ""), summary)
                if sim >= threshold:
                    conflicts.append({"file": str(f.relative_to(kb_path)), "summary": fm.get("summary", ""),
                                     "similarity": round(sim, 3)})
                # also check tags overlap
                existing_tags = set(fm.get("tags", []))
                if tags and existing_tags and len(tags & existing_tags) / len(tags | existing_tags) >= threshold:
                    conflicts.append({"file": str(f.relative_to(kb_path)), "summary": fm.get("summary", ""),
                                     "similarity": round(sim, 3)})

    # Deduplicate by file
    seen = set()
    unique_conflicts = []
    for c in conflicts:
        if c["file"] not in seen:
            seen.add(c["file"])
            unique_conflicts.append(c)

    output = {"status": "ok", "conflicts": unique_conflicts,
              "has_conflict": len(unique_conflicts) > 0}
    print(json.dumps(output, ensure_ascii=False))


def create_entry():
    config = json.loads(sys.stdin.read())
    kb_path = Path(config["knowledge_base_path"])
    product = config["product"]
    repo = config["repo"]
    filename = config["filename"]
    frontmatter = config["frontmatter"]
    body = config.get("body", "")

    is_moc = (repo == "moc")
    target_dir = kb_path / product / repo
    target_dir.mkdir(parents=True, exist_ok=True)

    filepath = target_dir / filename

    # Normalize fences, then parse and validate the frontmatter before touching disk.
    fm_text = frontmatter.strip()
    if not fm_text.startswith("---"):
        fm_text = "---\n" + fm_text + "\n---"
    elif not fm_text.endswith("---"):
        fm_text += "\n---"

    parts = fm_text.split("---", 2)
    inner = parts[1] if len(parts) >= 3 else ""
    try:
        fm = yaml.safe_load(inner) or {}
        if not isinstance(fm, dict):
            raise yaml.YAMLError("frontmatter is not a key: value mapping")
    except yaml.YAMLError as exc:
        print(json.dumps({"status": "error", "errors": [
            f"frontmatter YAML parse error: {exc} (quote values containing ': ' with double quotes)"]},
            ensure_ascii=False))
        sys.exit(1)

    # Backfill fields missing in frontmatter from the top-level payload, so callers
    # that only provide summary/type/tags at the top level still get a complete file.
    backfilled = False
    for key in ("type", "status", "title", "summary", "tags"):
        if not fm.get(key) and config.get(key):
            fm[key] = config[key]
            backfilled = True

    errors = []
    missing = REQUIRED_FIELDS - {k for k, v in fm.items() if v}
    if missing:
        errors.append(f"Missing required fields: {', '.join(sorted(missing))}")
    if fm.get("type") and fm["type"] not in TYPE_ENUM:
        errors.append(f"Invalid type value '{fm['type']}', must be one of {', '.join(sorted(TYPE_ENUM))}")
    if fm.get("status") and fm["status"] not in STATUS_ENUM:
        errors.append(f"Invalid status value '{fm['status']}', must be one of {', '.join(sorted(STATUS_ENUM))}")
    if fm.get("type") == "decision" and fm.get("confidence") not in CONFIDENCE_ENUM:
        errors.append("type=decision requires confidence: high/medium/low")
    if fm.get("status") == "superseded" and not fm.get("superseded_by"):
        errors.append("status=superseded requires superseded_by")
    if errors:
        print(json.dumps({"status": "error", "errors": errors}, ensure_ascii=False))
        sys.exit(1)

    if backfilled:
        lines = []
        for k, v in fm.items():
            if v is None:
                continue
            if isinstance(v, list):
                lines.append(f"{k}: {json.dumps(v)}")
            elif isinstance(v, bool):
                lines.append(f"{k}: {'true' if v else 'false'}")
            else:
                lines.append(f"{k}: {_yaml_quote(v)}")
        frontmatter = "---\n" + "\n".join(lines) + "\n---"
    else:
        frontmatter = fm_text

    entry_content = frontmatter
    if body:
        entry_content += "\n\n" + body.strip()

    filepath.write_text(entry_content, encoding="utf-8")

    # Update INDEX.md
    index_path = target_dir / "INDEX.md"
    if not index_path.exists():
        _create_empty_index(index_path, repo)

    _add_to_index(index_path, filename, str(fm.get("type", "")), str(fm.get("summary", "")),
                  fm.get("tags") or [])

    output = {"status": "ok", "file": str(filepath.relative_to(kb_path)),
              "index": str(index_path.relative_to(kb_path))}
    print(json.dumps(output, ensure_ascii=False))


def _create_empty_index(path: Path, name: str):
    path.write_text(f"# {name} Entry Index\n\n| File | type | summary | tags |\n| --- | --- | --- | --- |\n",
                    encoding="utf-8")


def _add_to_index(index_path: Path, filename: str, entry_type: str, summary: str, tags: list):
    content = index_path.read_text(encoding="utf-8").rstrip()
    tags_str = json.dumps(tags) if tags else "[]"
    new_line = f"| {filename} | {entry_type} | {summary} | {tags_str} |"
    # Check if already exists
    if f"| {filename} |" in content:
        content = re.sub(rf"\| {re.escape(filename)} \|.*", new_line, content)
    else:
        content += f"\n{new_line}\n"
    index_path.write_text(content, encoding="utf-8")


def create_moc_index():
    config = json.loads(sys.stdin.read())
    kb_path = Path(config["knowledge_base_path"])
    product = config["product"]

    moc_dir = kb_path / product / "moc"
    moc_dir.mkdir(parents=True, exist_ok=True)
    moc_index = moc_dir / "INDEX.md"
    if not moc_index.exists():
        moc_index.write_text("# moc Entry Index\n\n| File | type | summary | tags |\n| --- | --- | --- | --- |\n",
                             encoding="utf-8")

    # Also ensure product root INDEX.md has moc in repos table
    product_index = kb_path / product / "INDEX.md"
    if product_index.exists():
        content = product_index.read_text(encoding="utf-8")
        if "| moc/" not in content:
            # Find the repos table and add moc row
            lines = content.split("\n")
            new_lines = []
            in_table = False
            table_ended = False
            for line in lines:
                new_lines.append(line)
                if _is_table_separator(line):
                    in_table = True
                elif in_table and line.strip().startswith("| ") and "/" in line:
                    continue
                elif in_table and not line.strip().startswith("| "):
                    if not table_ended:
                        new_lines.insert(-1, "| moc/ | Cross-repo knowledge | — | active |")
                        table_ended = True
                    in_table = False
            product_index.write_text("\n".join(new_lines), encoding="utf-8")

    output = {"status": "ok", "moc_index": str(moc_index.relative_to(kb_path))}
    print(json.dumps(output, ensure_ascii=False))


def main():
    if len(sys.argv) < 5:
        print(json.dumps({"error": "Usage: write.py <kb_path> <product> <repo> <command>"}, ensure_ascii=False))
        sys.exit(1)

    kb_path = sys.argv[1]
    product = sys.argv[2]
    repo = sys.argv[3]
    command = sys.argv[4]

    commands = {
        "generate-frontmatter": generate_frontmatter,
        "detect-conflict": detect_conflict,
        "create-entry": create_entry,
        "create-moc-index": create_moc_index,
    }

    if command not in commands:
        print(json.dumps({"error": f"Unknown command: {command}"}, ensure_ascii=False))
        sys.exit(1)

    commands[command]()


if __name__ == "__main__":
    main()
