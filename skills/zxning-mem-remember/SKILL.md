---
name: zxning-mem-remember
description: Write knowledge entries to the knowledge base. Use when asked to record, save, or document project knowledge, decisions, incidents, or learnings.
allowed-tools: Bash, Read
---

# Write Knowledge Entry

## Workflow

### Step 0: Preconditions

Resolve the knowledge data root (the write target must live under it):
1. Prefer the environment variable `ZXNING_AGENT_KNOWLEDGE_VAULT`
2. If unset, fall back to `knowledge_base_path` from AGENTS.md

Also read `product` / `repo` / `knowledge_conflict` (optional) from AGENTS.md.

### Step 1: Gather information

Confirm with the user or extract from context:
- **Knowledge type** (type): tutorial / how-to / reference / explanation / decision / incident
- **Title** (title)
- **Summary** (summary, < 50 tokens)
- **Tags** (tags, optional)
- **Tech stack** (stack, optional)
- **Body content**
- **Repos involved** (to decide whether this is multi-repo knowledge)

### Step 2: Decide the write location

```
Does the knowledge span multiple repos?
  ├─ yes → repo=moc
  └─ no  → repo=current repo
```

**Multi-repo criterion**: whether the core content spans the implementation or flow of multiple repos. Does the knowledge remain complete and valid after removing the other repos' descriptions?

### Step 3: Conflict detection

```bash
echo '{
  "knowledge_base_path": "...",
  "product": "...",
  "repo": "current repo",
  "summary": "summary text",
  "tags": ["tag1"],
  "strategy": "exact",
  "threshold": 0.3
}' | python scripts/write.py "{knowledge_base_path}" "{product}" "{repo}" detect-conflict
```

`strategy` and `threshold` come from `knowledge_conflict` in AGENTS.md; when unset, strategy = "exact".

**On conflicts**: list the overlapping entries and ask the user whether to update an existing entry or ignore and create a new one.

### Step 4: Generate frontmatter + filename

```bash
echo '{
  "type": "how-to",
  "status": "accepted",
  "title": "Title",
  "summary": "summary text",
  "tags": ["tag1"],
  "date": "YYYY-MM-DD"
}' | python scripts/write.py "{knowledge_base_path}" "{product}" "{repo}" generate-frontmatter
```

The script returns a frontmatter YAML block + the standard filename `YYYYMMDD-slug.md`.

### Step 5: Human confirmation

Print the change summary and wait for the user to enter `y`:

```
Entry to create: {product}/{repo}/{filename}
Change: new entry + new row in INDEX.md
Confirm? (y/N)
```

Continue after the user enters `y`; otherwise roll back (entry content kept in a temp file, not written to disk).

### Step 6: Write entry + update INDEX

```bash
echo '{
  "knowledge_base_path": "...",
  "product": "...",
  "repo": "moc or current repo",
  "filename": "YYYYMMDD-slug.md",
  "frontmatter": "---\ntype: how-to\nstatus: accepted\ntitle: \"...\"\nsummary: \"...\"\ndate: YYYY-MM-DD\ntags: [\"tag1\"]\n---",
  "body": "knowledge body in markdown",
  "type": "how-to",
  "summary": "summary text",
  "tags": ["tag1"]
}' | python scripts/write.py "{knowledge_base_path}" "{product}" "{repo}" create-entry
```

Frontmatter rules:

- The frontmatter block is the single source of truth; the top-level `type`/`summary`/`tags` only backfill fields missing from frontmatter.
- The script parses and validates frontmatter before writing (required fields, enums, decision confidence, superseded_by) and rejects broken YAML with a clear error.
- Quote values containing `: ` with double quotes (`title: "Auth: rework"`) or use `generate-frontmatter`, which quotes automatically.
- `status` values: `proposed` | `accepted` | `deprecated` | `superseded` | `resolved`.

### Step 7: Auto-trigger validation

After writing, automatically invoke the zxning-mem-doctor skill:

```bash
python ../zxning-mem-doctor/scripts/validate.py "{knowledge_base_path}"
```

All pass → done. On errors → print the error list and ask the user whether to fix.

## moc precondition

If the write target is moc but the `moc/` directory doesn't exist, run first:

```bash
echo '{"knowledge_base_path": "...", "product": "..."}' | python scripts/write.py "{knowledge_base_path}" "{product}" "moc" create-moc-index
```

## Dependencies

- Python 3.6+
- PyYAML: `pip install pyyaml`
