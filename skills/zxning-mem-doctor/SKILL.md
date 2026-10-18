---
name: zxning-mem-doctor
description: Validate knowledge base consistency and integrity. Use when checking INDEX.md completeness, entry-frontmatter schema compliance, or after writing knowledge entries.
allowed-tools: Bash, Read
---

# Validate Knowledge Base

## Checks

| Check | What it detects | Automated fix |
|--------|----------|----------------|
| product root INDEX.md exists | every product directory has an INDEX.md | create in the standard format |
| repos table completeness | the repos table maps 1:1 to directories | add/remove rows |
| repo INDEX.md exists | every repo directory has an INDEX.md | create an empty entry table |
| entry table completeness | the INDEX.md entry table maps 1:1 to `*.md` files | add/remove rows |
| entry accessibility | file paths listed in INDEX.md exist | remove broken links |
| Frontmatter schema | required fields, type/status enums, decision confidence | point out the fields, fix manually |
| moc link completeness | "References" covers every repo in "Involved Repos" | add the missing links |

## Workflow

1. Resolve the knowledge data root (validation is scoped to that directory): prefer the environment variable `ZXNING_AGENT_KNOWLEDGE_VAULT`; if unset, fall back to `knowledge_base_path` from AGENTS.md
2. Run the validation script:

```bash
python scripts/validate.py "{knowledge_base_path}"
```

3. Parse the JSON output:
   - all `pass` → done
   - any `fail` → print each error and ask the user whether to auto-fix
     - user confirms → fix and re-run
     - user declines → exit, keeping the error state

## Triggers

- **Auto after write**: mandatory call once the zxning-mem-remember skill finishes
- **Manual**: run this skill from any project directory

## Dependencies

- Python 3.6+
- PyYAML: `pip install pyyaml`
