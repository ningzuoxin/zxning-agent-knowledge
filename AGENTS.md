---
knowledge_base_path: ../zxning-agent-knowledge-vault
product: zxning
repo: zxning-agent-knowledge
knowledge_conflict:
  strategy: jaccard
  threshold: 0.3
---

# Agent Guide

> English | [中文](./AGENTS.zh.md)

This repo is the knowledge-base tool repo (skills and docs); knowledge data lives in a separate data repo, `../zxning-agent-knowledge-vault` (pointed to by the `ZXNING_AGENT_KNOWLEDGE_VAULT` environment variable).

## Knowledge Base Root Resolution

The knowledge data root (where the product directories `zxning/`, `demo-product/` live) is resolved with the following priority:

1. **Environment variable `ZXNING_AGENT_KNOWLEDGE_VAULT`** (recommended): a single global value, one knowledge base shared across projects and IDEs; currently points to `D:\workspaces\zxning\zxning-agent-knowledge-vault`
2. This file's frontmatter `knowledge_base_path` (project-level override, default `../zxning-agent-knowledge-vault`, i.e. the data repo side by side with this repo)

All knowledge operations — writing entries, retrieval, creating a product, creating a repo — **must happen under the resolved data root**. Pass the resolved path to the skill scripts as a path argument (the scripts do not read environment variables themselves; the agent resolves it and passes it in).

## Knowledge Base Usage

If skills are installed, prefer calling the corresponding skill; otherwise follow this direct-read flow:

- **Retrieve knowledge**: read `<data-root>/zxning/INDEX.md` for the product structure; read `<data-root>/zxning/zxning-agent-knowledge/INDEX.md` to match entries by summary/tags/type; read `<data-root>/zxning/moc/INDEX.md` for cross-repo knowledge — when the moc hits, follow the markdown links in its "References" section to read the linked repo entries in full.
- **Deposit knowledge**: write `zxning/zxning-agent-knowledge/YYYYMMDD-slug.md` or `zxning/moc/` per the frontmatter schema (see DESIGN.md chapter 2), and update the corresponding INDEX.md. Cross-repo knowledge goes to `zxning/moc/`.
- **Initialize**: when a product/repo is onboarded for the first time, create the product directory, repo directory, moc directory, and their INDEX.md files.
