---
name: zxning-mem-recall
description: Search and retrieve knowledge entries from the knowledge base. Use when asked to find, search, or look up past decisions, incidents, how-tos, or references.
allowed-tools: Bash, Read
---

# Retrieve Knowledge

## Workflow

### Step 0: Preconditions

Resolve the knowledge data root (retrieval is scoped to that directory):
1. Prefer the environment variable `ZXNING_AGENT_KNOWLEDGE_VAULT`
2. If unset, fall back to `knowledge_base_path` from AGENTS.md

Also read `product` / `repo` from AGENTS.md.

All `{knowledge_base_path}` placeholders in the commands below stand for this resolved path — substitute the actual value, never the literal placeholder.

### Step 1: Run retrieval

```bash
python scripts/retrieve.py "{knowledge_base_path}" "{product}" "{repo}" "{query}"
```

Script behavior:
1. Read `{product}/{repo}/INDEX.md`, match entries by summary/tags/type
2. Read `{product}/moc/INDEX.md`, match entries by summary/tags/type
3. On a moc hit, read **all** entries pointed to by the markdown links in its "References" section (not limited to the current repo)
4. Deduplicate by file path and return sorted by match score, descending

### Step 2: Handle results

**Hits** → return the relevant knowledge fragments (with source paths) and proceed with the task.

**No hits** → return "no related knowledge found"; hint that the user may consult the code repo's own docs or invoke the zxning-mem-remember skill to deposit new knowledge.

## Dependencies

- Python 3.6+
- PyYAML: `pip install pyyaml`
