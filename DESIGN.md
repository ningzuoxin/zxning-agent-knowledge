# Knowledge Base Design

> English | [中文](./DESIGN.zh.md)

## 1. Directory Structure

```
zxning-agent-knowledge/                      # Knowledge base root (GitHub repo)
├── README.md                                # Project intro & quick start
├── DESIGN.md                                # This design document
├── bootstrap.sh                             # One-command skill installer
├── skills/                                  # Skills source (see chapter 3)
│   ├── zxning-mem-recall/                 # Retrieve skill
│   ├── zxning-mem-remember/                    # Write skill
│   ├── zxning-mem-doctor/                 # Validate skill
│   └── zxning-mem-init/              # Create-repo skill
├── demo-product/                            # Demo business product
│   ├── INDEX.md                             # Product root index (repos table)
│   ├── moc/                                 # Cross-repo knowledge aggregation
│   │   ├── INDEX.md                         # moc index (entry routing)
│   │   ├── 2026-06-18-wechat-login-decision.md
│   │   └── 2026-06-20-order-flow.md
│   ├── api/                                 # Backend repo
│   │   ├── INDEX.md                         # Repo index (entry routing)
│   │   ├── 2026-06-10-orm-choice.md
│   │   ├── 2026-06-15-jwt-reference.md
│   │   └── 2026-06-19-order-api.md
│   ├── webapp/                      # PC Web repo
│   │   ├── INDEX.md
│   │   └── 2026-06-17-order-page.md
│   └── miniapp/                           # WeChat mini-program repo
│       ├── INDEX.md
│       ├── 2026-06-14-wx-login-page.md
│       └── 2026-06-16-wx-payment-incident.md
└── my-blog/                                 # Personal blog (single-repo product, same standardized structure)
    ├── INDEX.md                             # Product root index (1-row repos table)
    ├── blog/                                # Repo directory
    │   ├── INDEX.md
    │   └── 2026-06-15-cors-issue.md
    └── moc/                                 # Cross-repo knowledge aggregation (no entries yet)
        └── INDEX.md                         # moc index (empty table)
```

> Note: after the tool-repo/data-repo split, the product directories (`demo-product/`, `zxning/`, ...) live in the separate data repo `zxning-agent-knowledge-vault` (pointed to by `ZXNING_AGENT_KNOWLEDGE_VAULT`). The tree above shows the pre-split single-repo layout; `bootstrap.sh` now sits at the tool-repo root.

### Naming Rules and Responsibilities

| Name | Naming rule | Type | Responsibility |
| ------------------ | ------------ | ---- | ------------------------------------------------------------------------------ |
| `skills/` | fixed name | dir | Skills source. Must be installed into the working project's agent at runtime |
| `{product}/` | business product name | dir | Product boundary; contains all repos of the product and cross-repo knowledge |
| `{repo}/` | repo name | dir | Repo boundary. Named after the repo's actual directory name (e.g. `api`, `web`); knowledge stays put when the tech stack is replaced |
| `moc/` | fixed name | dir | Cross-repo knowledge aggregation, listed as a special repo in the product root INDEX.md repos table |
| `INDEX.md` | uppercase | file | Layered index with a single responsibility: routing only. Product root: repos table; repo/moc level: entry table |
| `YYYYMMDD-slug.md` | ADR convention | file | Knowledge entry. Sorted by date ascending (oldest first); the slug is self-describing and naturally unique |

## 2. Frontmatter Schema

### Field Definitions

| Field | Required | Type | Values | Applies to | Description |
| --------------- | ---- | -------- | ---------------------------------------------------------------------------------- | -------------------- | -------------------------------------------------------------------------------------------------- |
| `type` | ✅ | enum | `tutorial` \| `how-to` \| `reference` \| `explanation` \| `decision` \| `incident` | all | Knowledge type |
| `status` | ✅ | enum | `proposed` \| `accepted` \| `deprecated` \| `superseded` \| `resolved` | all | Reuses ADR. See status usage below |
| `superseded_by` | conditional | string | file path (relative to the current product root) | `status=superseded` | Points to the superseding entry |
| `confidence` | conditional | enum | `high` \| `medium` \| `low` | required when `type=decision` | Reuses ADR confidence |
| `title` | ✅ | string | free text | all | Entry title |
| `summary` | ✅ | string | < 50 tokens | all | Used by the retrieve skill for matching; must be concise |
| `tags` | ❌ | string[] | free text, kebab-case recommended | all | Auxiliary matching; no controlled vocabulary |
| `date` | ✅ | date | `YYYY-MM-DD` | all | Entry creation date |
| `stack` | ❌ | string | free text | all | Tech-stack marker. Fill in when the knowledge becomes invalid after a stack change (e.g. framework-specific APIs, ORM-specific syntax). Usually omitted for pure business logic |

### type Values

| type | Purpose | Body structure convention |
| ------------- | ----------------- | -------------------------------------------------------- |
| `tutorial` | Step-by-step teaching | Learning goals → Prerequisites → Steps → Verification |
| `how-to` | Solve a specific task | Goal → Prerequisites → Steps → Troubleshooting |
| `reference` | Accurate information lookup | Descriptive, not instructional |
| `explanation` | Principles & design decisions | Overview → Core principles → Design considerations → Alternatives |
| `decision` | Architecture decision record | Context → Options → Decision → Consequences → Confidence |
| `incident` | Incident / pitfall post-mortem | Background → Root cause → Solution → Action items |

### moc Entry Body Structure

Beyond the generic type structure, a moc entry body must contain two fixed sections so the retrieve skill can parse and follow links:

1. **Involved Repos** (immediately after the frontmatter): a table listing the participating repos and their roles. For human readers; not parsed by skills.
2. **References** (end of body): a list of links pointing to each repo's entries. **The format must be markdown links** `[text](relative-path.md)`, with paths relative to the product root.

(Section headings accept both English (`Involved Repos` / `References`) and the legacy Chinese forms (`涉及 repo` / `参考条目`); skills recognize both.)

**Hard constraint**: a moc entry's References section must provide at least one link for **every repo** in the Involved Repos table. The zxning-mem-doctor skill enforces this rule after writing and errors on violation. This constraint guarantees that retrieval from any repo's perspective can recover the related knowledge through the moc entry.

See chapter 4 for a moc entry example.

### status Usage

`status` reuses the ADR mechanism, with different semantics per type:

| type | Allowed status | Notes |
| ------------------------------------ | -------------------------------------------------------- | ------------------------------------------ |
| `decision` | `proposed` \| `accepted` \| `deprecated` \| `superseded` | Full ADR lifecycle |
| `incident` | `accepted` \| `resolved` | `accepted` = still open; `resolved` = fixed and closed |
| others (tutorial/how-to/reference etc.) | `accepted` \| `deprecated` \| `superseded` | No `proposed`. `accepted` means "currently valid" |

**Semantics**:

- `deprecated`: the entry is outdated, no longer applicable, with no clear replacement.
- `superseded`: the entry was replaced by a newer version/approach. `superseded_by` points to the replacement. Also applies to non-decision types (e.g. old API usage replaced by a new version, an old deployment flow replaced by a new one).

## 3. Skills Layer

INDEX.md is designed as human-readable markdown that agents can read directly, without depending on skills. Skills are an optional enhancement providing more precise matching, schema validation, and automatic index maintenance.

### Two Usage Modes

**Direct-read mode (no skills)**: the agent follows AGENTS.md guidance — read INDEX → match entries → read full text. Suits personal projects, low-frequency scenarios, quick onboarding.

```
Retrieve: agent → read AGENTS.md → read {product}/INDEX.md + {repo}/INDEX.md + moc/INDEX.md → read matched entries in full
Write:    agent → write entries per schema + update INDEX.md (manual)
Create:   agent → create product/repo directories + INDEX.md (manual)
```

**Skills mode (optional enhancement)**: the agent calls skills to run standardized flows. Skills enforce schema validation, maintain indexes automatically, and provide deterministic matching. Suits high-frequency team scenarios.

```
Retrieve: agent → zxning-mem-recall → knowledge fragments
Write:    agent → zxning-mem-remember → auto deposit + auto index update
Create:   agent → zxning-mem-init → auto init
Install:  agent → run bootstrap.sh → auto install
```

Both modes can coexist; the agent prefers installed skills and falls back to direct-read mode otherwise.

### Skills Hosting and Installation

- **Hosting**: skill sources are hosted under the tool-repo root `skills/`, one directory per skill
- **Form**: each skill is a mix of prompt + helper scripts. The prompt is interpreted by the agent; scripts handle deterministic operations like file reads/writes
- **Installation**: skills don't run inside the knowledge repo; they must be installed into the working project's agent. See "Installation" below

### Working-Project Config: AGENTS.md

Place `AGENTS.md` at the root of the working project (e.g. `D:/A`), telling the agent the knowledge base location and the product/repo this project maps to, plus usage guidance for direct-read mode (the knowledge base location is primarily given by the `ZXNING_AGENT_KNOWLEDGE_VAULT` environment variable; `knowledge_base_path` in AGENTS.md is the fallback):

```markdown
---
knowledge_base_path: E:/zxning-agent-knowledge-vault
product: demo-product
repo: api
knowledge_conflict:
  strategy: jaccard # jaccard | embedding | exact
  threshold: 0.3
---

# Agent Guide

This project maps to the demo-product/api knowledge base.

## Knowledge Base Usage

If skills are installed, prefer calling the corresponding skill; otherwise follow this direct-read flow:

- **Retrieve knowledge**: read `{knowledge_base_path}/{product}/INDEX.md` for the product structure; read `{knowledge_base_path}/{product}/{repo}/INDEX.md` to match entries by summary/tags/type; read `{knowledge_base_path}/{product}/moc/INDEX.md` for cross-repo knowledge — when the moc hits, follow the markdown links in its "References" section to read the linked repo entries in full.
- **Deposit knowledge**: write `{product}/{repo}/YYYYMMDD-slug.md` or moc/ per the frontmatter schema (see DESIGN.md chapter 2), and update the corresponding INDEX.md. Cross-repo knowledge goes to moc/.
- **Initialize**: when a product/repo is onboarded for the first time, create the product directory, repo directory, moc directory, and their INDEX.md files.
```

`knowledge_conflict` is optional configuration controlling conflict detection on write. When unset, `exact` matching is used by default. If the agent framework doesn't read AGENTS.md, the user can migrate the equivalent configuration into that platform's config file.

From the frontmatter the agent knows: the knowledge base root path, the current product, the current repo. The usage guidance lets the agent operate the knowledge base directly even without skills installed.

### Retrieve Skill

**Input**: natural-language query

**Precondition**: resolve the knowledge data root (environment variable `ZXNING_AGENT_KNOWLEDGE_VAULT` first, AGENTS.md `knowledge_base_path` as fallback) → get `product` / `repo`

**Flow**:

1. Read the product root `INDEX.md` → get the repos table (moc listed as a special repo). **If the product root INDEX.md doesn't exist**: return "this product is not initialized in the knowledge base; suggest calling the zxning-mem-init skill first", stop.
2. Read the current repo's `INDEX.md` → match entries by summary/tags/type. **If the repo directory doesn't exist**: return "this repo is not initialized in the knowledge base; suggest calling the zxning-mem-init skill first", stop.
3. Read `moc/INDEX.md` → match entries by summary/tags/type
4. Read matched entries in full:
   - repo hit → read the repo entry in full
   - moc hit → read the moc entry in full → read **all** entries pointed to by markdown links in its "References" section (not limited to the current repo)
5. Return: current-repo hits + moc hits + all linked entries referenced by the moc, **deduplicated by file path**.
6. **No hit**: return "no related knowledge found", hinting the agent may consult the code repo's own docs or manually invoke the zxning-mem-remember skill to deposit new knowledge

**Output**: relevant knowledge fragments (with source paths); the agent proceeds with the task directly.

### Write Skill

**Input**: the knowledge content to deposit + context (repos involved, etc.)

**Precondition**: resolve the knowledge data root (environment variable `ZXNING_AGENT_KNOWLEDGE_VAULT` first, AGENTS.md `knowledge_base_path` as fallback) → get `product` / `repo`

**Decision tree**:

```
Does the knowledge span multiple repos?
  ├─ yes → write to moc/, update moc/INDEX.md
  └─ no  → write to the current repo directory, update the repo INDEX.md
```

**Multi-repo criterion**: whether the core content spans the implementation or flow of multiple repos. If the knowledge remains complete and valid after removing the other repos' descriptions → single repo; if it becomes incomplete → multi-repo. Merely "mentioning" or "referencing" other repos does not count.

**Conflict detection**: before writing, match existing entries using the strategy from AGENTS.md `knowledge_conflict` (default `exact`). On high overlap, prompt the agent to update the existing entry instead of creating a new one.

**Human confirmation**: all changes must print a change summary for user confirmation before hitting disk:

```
Entry to create: api/2026-06-25-order-refund.md
Change: new entry + new row in api/INDEX.md
Confirm? (y/N)
```

Continue after the user enters `y`; otherwise roll back (entry content kept in a temp file, not written to disk). Human confirmation is a mandatory step and cannot be skipped.

**Responsibilities**:

1. Generate the frontmatter (schema-validated, required fields complete)
2. Generate the filename (`YYYYMMDD-slug.md`)
3. Print the change summary → wait for user `y`
4. Write the knowledge entry file
5. Update the corresponding index (the write skill is the only writer of INDEX.md):
   - repo knowledge → update that repo's `INDEX.md`
   - cross-repo knowledge → update `moc/INDEX.md`. **Precondition**: if the `moc/` directory doesn't exist, first create `moc/INDEX.md` (empty entry table) and add a `moc/` row to the product root repos table
6. **Auto-trigger the zxning-mem-doctor skill**: right after writing, call zxning-mem-doctor to check this change; the write counts as successful only if validation passes, otherwise prompt the user to fix.

**Triggers**:

- agent-initiated (auto deposit after finishing a task)
- user-initiated (explicitly asking to record some knowledge)

### Create-repo Skill

**Responsibility**: initialize a new repo's knowledge directory under a product

1. **Precondition**: if the product directory doesn't exist (first onboarding of the product), first create the product directory + product root `INDEX.md` (title + one-line description + empty repos table; format per chapter 4 "Product Root INDEX.md")
2. Create the repo directory under the product directory
3. Create the repo-level `INDEX.md` (empty entry table)
4. Update the product root `INDEX.md` repos table (add a row)
5. **moc check**: if there's no `moc/` directory under the product root, also create `moc/INDEX.md` (empty entry table) and add a `moc/` row to the repos table. This keeps the product structure always complete (repo + moc symmetric).

**Triggers**: called when the agent takes on a new repo's task, or manually by the user.

### Installation

Skills are installed into a target agent's skills directory via the tool-repo root `bootstrap.sh`. The repo is private: clone it locally first, then run the local installer:

```bash
bash /path/to/zxning-agent-knowledge/bootstrap.sh ~/.config/opencode/skills
```

`bootstrap.sh` responsibilities:

1. Resolve the target directory from the arguments (codebuddy / trae / copilot / any custom directory; defaults to codebuddy + trae)
2. Copy `zxning-mem-recall/` `zxning-mem-remember/` `zxning-mem-doctor/` `zxning-mem-init/` into the target skills directory
3. Check the `ZXNING_AGENT_KNOWLEDGE_VAULT` environment variable and print setup guidance if it's missing

> bootstrap.sh **does not create AGENTS.md**; that's a separate configuration step for the working project.

### Validate Skill

**Responsibility**: check the knowledge base's consistency and integrity; the mandatory post-hook of the write chain.

**Triggers**:

- auto-triggered by the zxning-mem-remember skill (mandatory)
- user-initiated (periodic audits, or when inconsistency is suspected)

**Checks**:

| Check | What it detects | Fix guidance |
| ------------------ | ----------------------------------------------------------------------------------- | ------------------------ |
| INDEX completeness | the product root INDEX.md repos table maps 1:1 to the directory structure | points out the missing/extra rows |
| INDEX entry completeness | the repo/moc INDEX.md entry tables map 1:1 to the `*.md` files (excluding INDEX.md itself) | points out extra files or missing rows |
| Entry accessibility | the file paths listed in INDEX.md actually exist | points out broken links |
| moc link completeness | a moc entry's "References" covers every repo in its "Involved Repos" table | points out repos missing links |
| Frontmatter schema | the entry files' frontmatter satisfies the required fields | points out missing fields |

**Workflow**:

```
zxning-mem-remember skill done → auto-call the zxning-mem-doctor skill
  ├─ all pass → done
  └─ errors → print the error list → user confirms fixes → re-validate after fixing
```

### Impact of the Skills Layer on the Original Design

| Aspect | Change |
| ------------- | ---------------------------------------------------- |
| INDEX.md reader | the primary reader shifts from the agent to the zxning-mem-recall skill |
| frontmatter | from "human convention" to a "machine contract for skills"; must be strict and parseable |
| INDEX.md maintenance | from "manual agent updates" to "auto-maintained by the zxning-mem-remember skill" |
| Entry point | the working project's root AGENTS.md is the runtime config entry for skills |
| Installation | one command via bootstrap.sh; no separate skill |

## 4. File Examples

Using the `demo-product` product (with api + webapp + miniapp repos) as an example. Repo-level examples show `api` only; the other repos are structured identically.

### 1. Product Root `INDEX.md`

```markdown
# demo-product Knowledge Index

> Demo product, composed of api (Java/Play) + webapp (React 16) + miniapp (mini program).

## Repos

| Directory       | Role         | Stack                         | Status |
| --------------- | ------------ | ----------------------------- | ------ |
| api/            | Backend API  | Java 8, Play Framework, MySQL | active |
| webapp/ | PC Web front | React 16, Create React App    | active |
| miniapp/      | Mini program | Native mini program           | active |
| moc/            | Cross-repo knowledge | —                     | active |
```

### 2. `moc/INDEX.md`

```markdown
# moc Entry Index

| File                                | type     | summary                                                        | tags             |
| ----------------------------------- | -------- | -------------------------------------------------------------- | ---------------- |
| 2026-06-18-wechat-login-decision.md | decision | WeChat login approach: backend-mediated session                | [auth, wechat]   |
| 2026-06-20-order-flow.md            | how-to   | End-to-end ordering flow across api+webapp+miniapp   | [order, payment] |
```

### 3. Repo-Level `INDEX.md` (e.g. `api/INDEX.md`)

```markdown
# api Entry Index

| File                        | type      | summary                                                       | tags       |
| --------------------------- | --------- | ------------------------------------------------------------- | ---------- |
| 2026-06-10-orm-choice.md    | decision  | ORM choice: TypeORM vs Prisma                                 | [database] |
| 2026-06-15-jwt-reference.md | reference | JWT token structure, issuance & verification quick reference  | [auth]     |
| 2026-06-19-order-api.md     | how-to    | Order creation API input validation & transaction handling    | [order]    |
```

### 4. Repo Knowledge Entry (e.g. `api/2026-06-15-jwt-reference.md`)

```markdown
---
type: reference
status: accepted
title: JWT Quick Reference
summary: JWT token structure, issuance & verification quick reference
tags: [auth]
date: 2026-06-15
stack: play
---

## Token structure

Header.Payload.Signature; the payload carries userId, role, exp.

## Issuance

Issued with java-jwt, 15-minute expiry. Key code lives in the code repo.

## Verification

Verify and extract claims with java-jwt.

## Refresh

The `/auth/refresh` endpoint exchanges a refresh token for a new access token.
```

### 5. moc Entry (e.g. `moc/2026-06-20-order-flow.md`)

```markdown
---
type: how-to
status: accepted
title: Full ordering flow
summary: End-to-end flow from product selection to successful payment, across mini program + API + PC Web
tags: [order, payment]
date: 2026-06-20
---

## Involved Repos

| Repo           | Role     | What it does                                   |
| -------------- | -------- | ---------------------------------------------- |
| miniapp      | Client   | Show products → submit order → start payment   |
| api            | Backend  | Create order → build payment params → handle callback |
| webapp | Admin    | View order list → audit / refund operations    |

## Flow

1. The mini program calls `api` to create the order, then starts WeChat Pay with the returned payment params
2. WeChat Pay callbacks `api` to update the order status; the PC Web admin views orders

## References

- [Order creation API implementation](api/2026-06-19-order-api.md)
- [PC order list page](webapp/2026-06-17-order-page.md)
- [Payment callback incident notes](miniapp/2026-06-16-wx-payment-incident.md)
```
