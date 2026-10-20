---
name: zxning-mem-init
description: Initialize a new product or repo structure in the knowledge base. Use when starting work on a new repo or product that hasn't been documented yet.
allowed-tools: Bash, Read
---

# Create Repo

## Workflow

### Step 0: Preconditions

Resolve the knowledge data root (creation targets must live under it):
1. Prefer the environment variable `ZXNING_AGENT_KNOWLEDGE_VAULT`
2. If unset, fall back to `knowledge_base_path` from AGENTS.md

All `{knowledge_base_path}` placeholders in the commands below stand for this resolved path — substitute the actual value, never the literal placeholder.

### Step 1: Gather information

Confirm:
- Knowledge data root (already resolved in Step 0)
- Product name
- Repo name
- Product description (needed when onboarding a new product)
- Repo role and tech stack (optional, for updating the repos table)

### Step 2: Run initialization

```bash
python scripts/init_repo.py "{knowledge_base_path}" "{product}" "{repo}" --description "product description"
```

Script behavior:
1. If the product directory/INDEX.md doesn't exist → create the product directory + product root INDEX.md (title + description + empty repos table)
2. Create the repo directory + repo-level INDEX.md (empty entry table)
3. Add a row to the product root INDEX.md repos table
4. If no `moc/` directory exists under the product root → create `moc/INDEX.md` and add a `moc/` row to the repos table

### Step 3: Human confirmation

Print the change summary:

```
Initialization complete:
  - created: {product}/INDEX.md, {product}/{repo}/INDEX.md, {product}/moc/INDEX.md
  - updated: {product}/INDEX.md (repos table)
```

### Step 4: Verify

Manually invoke the zxning-mem-doctor skill for an integrity check:

```bash
python ../zxning-mem-doctor/scripts/validate.py "{knowledge_base_path}"
```

## Dependencies

- Python 3.6+
