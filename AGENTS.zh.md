---
knowledge_base_path: ../zxning-agent-knowledge-vault
product: zxning
repo: zxning-agent-knowledge
knowledge_conflict:
  strategy: jaccard
  threshold: 0.3
---

# Agent Guide

> [English](./AGENTS.md) | 中文

本仓库为知识库工具仓（skills 与文档）；知识数据存放在独立的数据仓 `../zxning-agent-knowledge-vault`（由环境变量 `ZXNING_AGENT_KNOWLEDGE_VAULT` 指向）。

## 知识库根目录解析

知识库数据根（各 product 目录 `zxning/`、`demo-product/` 所在位置）按以下优先级解析：

1. **环境变量 `ZXNING_AGENT_KNOWLEDGE_VAULT`**（推荐）：全局唯一，跨项目、跨 IDE 共享同一知识库；当前指向 `D:\workspaces\zxning\zxning-agent-knowledge-vault`
2. 本文件 frontmatter 的 `knowledge_base_path`（项目级覆盖，默认 `../zxning-agent-knowledge-vault`，即与本仓库并列的数据仓）

所有知识操作——写入条目、检索、创建 product、创建 repo——**都必须发生在解析后的数据根目录下**。解析结果以路径参数传给 skills 脚本（脚本自身不读环境变量，由 agent 解析后传参）。

## 知识库使用方式

若已安装 skills，优先调用对应 skill；否则按以下直读流程：

- **检索知识**：读 `<数据根>/zxning/INDEX.md` 获取产品结构；读 `<数据根>/zxning/zxning-agent-knowledge/INDEX.md` 按 summary/tags/type 匹配条目；读 `<数据根>/zxning/moc/INDEX.md` 检查跨 repo 知识，moc 命中时按"参考条目"中的 markdown 链接读取对应 repo 条目全文。
- **沉淀知识**：按 frontmatter schema（见 DESIGN.md 第二章）写入 `zxning/zxning-agent-knowledge/YYYYMMDD-slug.md` 或 `zxning/moc/`，并更新对应 INDEX.md。多 repo 知识写入 `zxning/moc/`。
- **初始化**：产品/repo 首次接入时，创建产品目录、repo 目录、moc 目录与对应 INDEX.md。
