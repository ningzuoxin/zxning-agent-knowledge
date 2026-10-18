# 知识库设计文档

> [English](./DESIGN.md) | 中文

## 一、目录结构

```
zxning-agent-knowledge/                      # 知识库根（GitHub 仓库）
├── README.md                                # 项目说明与快速开始
├── DESIGN.md                                # 本设计文档
├── bootstrap.sh                             # 一键安装脚本
├── skills/                                  # skills 源码托管（见第三章）
│   ├── zxning-mem-recall/                 # 读取 skill
│   ├── zxning-mem-remember/                    # 写入 skill
│   ├── zxning-mem-doctor/                 # 校验 skill
│   └── zxning-mem-init/              # 创建 repo skill
├── demo-product/                            # 演示业务产品
│   ├── INDEX.md                             # 产品根索引（repos 表）
│   ├── moc/                                 # 跨 repo 知识聚合
│   │   ├── INDEX.md                         # moc 索引（条目路由）
│   │   ├── 2026-06-18-wechat-login-decision.md
│   │   └── 2026-06-20-order-flow.md
│   ├── api/                                 # 后端 repo
│   │   ├── INDEX.md                         # repo 索引（条目路由）
│   │   ├── 2026-06-10-orm-choice.md
│   │   ├── 2026-06-15-jwt-reference.md
│   │   └── 2026-06-19-order-api.md
│   ├── webapp/                      # PC Web repo
│   │   ├── INDEX.md
│   │   └── 2026-06-17-order-page.md
│   └── miniapp/                           # 微信小程序 repo
│       ├── INDEX.md
│       ├── 2026-06-14-wx-login-page.md
│       └── 2026-06-16-wx-payment-incident.md
└── my-blog/                                 # 个人博客（单 repo 产品，结构同样标准化）
    ├── INDEX.md                             # 产品根索引（repos 表列 1 行）
    ├── blog/                                # repo 目录
    │   ├── INDEX.md
    │   └── 2026-06-15-cors-issue.md
    └── moc/                                 # 跨 repo 知识聚合（暂无条目）
        └── INDEX.md                         # moc 索引（空表）
```

> 注：工具仓/数据仓物理拆分后，产品目录（`demo-product/`、`zxning/` 等）位于独立的数据仓 `zxning-agent-knowledge-vault`（由 `ZXNING_AGENT_KNOWLEDGE_VAULT` 指向）；此图保留拆分前的单仓布局示意，`bootstrap.sh` 现位于工具仓根目录。

### 命名规范与职责

| 名称               | 命名规则     | 类型 | 职责                                                                           |
| ------------------ | ------------ | ---- | ------------------------------------------------------------------------------ |
| `skills/`          | 固定名称     | 目录 | skills 源码托管。实际运行时需安装到工作项目的 agent 下                         |
| `{product}/`       | 业务产品名称 | 目录 | 业务产品边界，包含该产品所有 repo 和跨 repo 知识                               |
| `{repo}/`          | repo 名称    | 目录 | repo 边界。命名取 repo 的实际目录名（如 `api`、`web`），技术栈替换时知识不搬迁 |
| `moc/`             | 固定名称     | 目录 | 跨 repo 知识聚合，作为特殊 repo 列入产品根 INDEX.md 的 repos 表                |
| `INDEX.md`         | 大写         | 文件 | 分层索引，统一职责：只负责路由。产品根：repos 表；repo/moc 级：条目表格        |
| `YYYYMMDD-slug.md` | ADR 规范     | 文件 | 知识条目。按日期升序排列（旧在前），slug 自带语义，天然唯一                    |

## 二、Frontmatter Schema

### 字段定义

| 字段            | 必填 | 类型     | 值域                                                                               | 适用条件             | 说明                                                                                               |
| --------------- | ---- | -------- | ---------------------------------------------------------------------------------- | -------------------- | -------------------------------------------------------------------------------------------------- |
| `type`          | ✅   | enum     | `tutorial` \| `how-to` \| `reference` \| `explanation` \| `decision` \| `incident` | 全部                 | 知识类型                                                                                           |
| `status`        | ✅   | enum     | `proposed` \| `accepted` \| `deprecated` \| `superseded` \| `resolved`             | 全部                 | 复用 ADR。见下方 status 使用说明                                                                   |
| `superseded_by` | 条件 | string   | 文件路径（相对当前产品根目录）                                                     | `status=superseded`  | 指向替代条目                                                                                       |
| `confidence`    | 条件 | enum     | `high` \| `medium` \| `low`                                                        | `type=decision` 必填 | 复用 ADR confidence                                                                                |
| `title`         | ✅   | string   | 自由文本                                                                           | 全部                 | 条目标题                                                                                           |
| `summary`       | ✅   | string   | < 50 tokens                                                                        | 全部                 | 供 skill 检索匹配，必须精炼                                                                        |
| `tags`          | ❌   | string[] | 自由文本，建议 kebab-case                                                          | 全部                 | 辅助检索匹配，无受控词表约束                                                                       |
| `date`          | ✅   | date     | `YYYY-MM-DD`                                                                       | 全部                 | 条目创建日期                                                                                       |
| `stack`         | ❌   | string   | 自由文本                                                                           | 全部                 | 技术栈标识。当知识内容在更换技术栈后即失效时填写（如框架特定 API、ORM 特定语法）。一般业务逻辑不填 |

### type 值域

| type          | 用途              | 正文结构约定                                             |
| ------------- | ----------------- | -------------------------------------------------------- |
| `tutorial`    | 手把手教学        | 学习目标 → 前置要求 → 步骤 → 验证                        |
| `how-to`      | 解决具体任务      | 目标 → 前置条件 → 步骤 → 故障排除                        |
| `reference`   | 准确信息查阅      | 描述性，不指导                                           |
| `explanation` | 原理与设计决策    | 概述 → 核心原理 → 设计考量 → 方案对比                    |
| `decision`    | 架构决策记录      | Context → Options → Decision → Consequences → Confidence |
| `incident`    | 线上事故/踩坑复盘 | 背景 → 根因 → 解决方案 → 行动项                          |

### moc 条目正文结构约定

moc 条目正文除遵循 type 的通用结构外，必须包含两个固定区块，供检索 skill 解析跟随链接：

1. **涉及 repo**（紧跟 frontmatter 之后）：表格形式，列出参与的 repo 及其角色。供人类阅读，skill 不解析。
2. **参考条目**（正文末尾）：列表形式，列出指向各 repo 条目的链接。**格式必须为 markdown 链接** `[文本](相对路径.md)`，路径相对产品根目录。

（区块标题中英文均可：`涉及 repo` / `Involved Repos`、`参考条目` / `References`，skills 均可识别。）

**强制约束**：moc 条目的"参考条目"区块必须为"涉及 repo"表格中的**每一个 repo** 都提供至少一个链接。zxning-mem-doctor skill 会在写入后校验此规则，缺失则报错。此约束确保任何 repo 视角的检索都能通过 moc 条目找回关联知识。

示例见第四章 moc 条目示例。

### status 使用说明

`status` 复用 ADR 机制，但不同 type 的语义不同：

| type                                 | 可用 status                                              | 说明                                       |
| ------------------------------------ | -------------------------------------------------------- | ------------------------------------------ |
| `decision`                           | `proposed` \| `accepted` \| `deprecated` \| `superseded` | 完整 ADR 生命周期                          |
| `incident`                           | `accepted` \| `resolved`                                 | `accepted` = 仍在处理；`resolved` = 已修复关闭 |
| 其他（tutorial/how-to/reference 等） | `accepted` \| `deprecated` \| `superseded`               | 不使用 `proposed`。`accepted` 即"当前有效" |

**语义说明**：

- `deprecated`：条目已过时，不再适用，无明确替代。
- `superseded`：条目被新版本/新方案替代。`superseded_by` 指向替代条目。对非决策类型同样适用（如旧版 API 用法被新版本替代、旧部署流程被新流程替代）。

## 三、Skills 层

INDEX.md 设计为人类可读的 markdown，agent 可直接读取，无需依赖 skills。skills 是可选增强，提供更精准的匹配、schema 校验与索引自动维护。

### 两种使用模式

**直读模式（无需 skills）**：agent 按 AGENTS.md 指引，直接读 INDEX → 匹配条目 → 读全文。适合个人项目、低频场景、快速接入。

```
检索：agent → 读 AGENTS.md → 读 {product}/INDEX.md + {repo}/INDEX.md + moc/INDEX.md → 读命中条目全文
写入：agent → 按 schema 写条目 + 更新 INDEX.md（手动）
新建：agent → 创建产品/repo 目录 + INDEX.md（手动）
```

**Skills 模式（可选增强）**：agent 调用 skills 执行标准化流程。skills 强制 schema 校验、自动维护索引、提供确定性匹配算法。适合高频团队场景。

```
检索：agent → zxning-mem-recall → 知识片段
写入：agent → zxning-mem-remember → 自动沉淀 + 自动更新索引
新建：agent → zxning-mem-init → 自动初始化
安装：agent → 运行 bootstrap.sh → 自动安装
```

两种模式可共存，agent 优先使用已安装的 skills，未安装时回退到直读模式。

### skills 托管与安装

- **托管**：skills 源码托管在知识库根目录 `skills/` 下，按 skill 名分目录
- **形式**：每个 skill 是 prompt + 辅助脚本的混合。prompt 由 agent 解释执行，脚本处理文件读写等确定性操作
- **安装**：skills 不在知识库内运行，需安装到工作项目的 agent 下。安装方式见"安装 skill"

### 工作项目配置：AGENTS.md

工作项目（如 `D:/A`）根目录放 `AGENTS.md`，告知 agent 知识库位置和当前项目对应的产品与 repo，并附使用指引供直读模式使用（知识库位置优先由环境变量 `ZXNING_AGENT_KNOWLEDGE_VAULT` 指定，AGENTS.md 的 `knowledge_base_path` 为回退）：

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

本项目对应知识库 demo-product/api。

## 知识库使用方式

若已安装 skills，优先调用对应 skill；否则按以下直读流程：

- **检索知识**：读 `{knowledge_base_path}/{product}/INDEX.md` 获取产品结构；读 `{knowledge_base_path}/{product}/{repo}/INDEX.md` 按 summary/tags/type 匹配条目；读 `{knowledge_base_path}/{product}/moc/INDEX.md` 检查跨 repo 知识，moc 命中时按"参考条目"中的 markdown 链接读取对应 repo 条目全文。
- **沉淀知识**：按 frontmatter schema（见 DESIGN.md 第二章）写入 `{product}/{repo}/YYYYMMDD-slug.md` 或 moc/，并更新对应 INDEX.md。多 repo 知识写入 moc/。
- **初始化**：产品/repo 首次接入时，创建产品目录、repo 目录、moc 目录与对应 INDEX.md。
```

`knowledge_conflict` 为可选配置，控制写入时的冲突检测行为。未配置时默认采用 `exact` 精确匹配。当 agent 框架不读取 AGENTS.md 时，用户可将等价配置迁移到对应平台的配置文件中。

agent 读取 frontmatter 即知道：知识库根路径、当前产品、当前 repo。使用指引让 agent 在未安装 skills 时也能直接操作知识库。

### 检索 skill

**输入**：自然语言 query

**前置**：解析知识库数据根（优先环境变量 `ZXNING_AGENT_KNOWLEDGE_VAULT`，回退 AGENTS.md 的 `knowledge_base_path`）→ 获取 `product` / `repo`

**流程**：

1. 读产品根 `INDEX.md` → 获取 repos 表（moc 作为特殊 repo 列入其中）。**若产品根 INDEX.md 不存在**：返回提示"当前产品未在知识库初始化，建议先调用 zxning-mem-init skill"，终止流程。
2. 读当前 repo 的 `INDEX.md` → 按 summary/tags/type 匹配条目。**若 repo 目录不存在**：返回提示"当前 repo 未在知识库初始化，建议先调用 zxning-mem-init skill"，终止流程。
3. 读 `moc/INDEX.md` → 按 summary/tags/type 匹配条目
4. 读命中条目全文：
   - repo 命中 → 读 repo 条目全文
   - moc 命中 → 读 moc 条目全文 → 读取"参考条目"区块中**所有** markdown 链接指向的条目（不限当前 repo）
5. 返回：当前 repo 命中条目 + moc 命中条目 + moc 参考条目中指向的所有关联条目，**按文件路径去重后**返回。
6. **未命中**：返回"未找到相关知识"，提示 agent 可参考代码 repo 自身文档或手动调用 zxning-mem-remember skill 沉淀新知识

**输出**：相关知识片段（含来源路径），agent 直接执行任务。

### 写入 skill

**输入**：待沉淀的知识内容 + 上下文（涉及的 repo 等）

**前置**：解析知识库数据根（优先环境变量 `ZXNING_AGENT_KNOWLEDGE_VAULT`，回退 AGENTS.md 的 `knowledge_base_path`）→ 获取 `product` / `repo`

**决策树**：

```
知识涉及多 repo？
  ├─ 是 → 写入 moc/，更新 moc/INDEX.md
  └─ 否 → 写入当前 repo 目录，更新 repo INDEX.md
```

**多 repo 判定标准**：知识的核心内容是否横跨多个 repo 的实现或流程。若移除其他 repo 的描述后知识仍完整有效 → 单 repo；若缺失则不完整 → 多 repo。仅"提及"或"参考"其他 repo 不算多 repo。

**冲突检测**：写入前按 AGENTS.md 中 `knowledge_conflict` 配置的策略（默认 `exact`）匹配已有条目。若发现高度重叠，提示 agent 选择更新已有条目而非新建。

**人工确认**：所有变更在落盘前必须输出变更摘要供用户确认：

```
待创建条目：api/2026-06-25-order-refund.md
变更：新增条目 + api/INDEX.md 新增行
确认执行？(y/N)
```

用户输入 `y` 后继续，否则回滚（条目内容保留到临时文件，不落盘）。人工确认是强制步骤，不可跳过。

**职责**：

1. 生成 frontmatter（按 schema 校验，确保必填字段完整）
2. 生成文件名（`YYYYMMDD-slug.md`）
3. 输出变更摘要 → 等待用户 `y` 确认
4. 写入知识条目文件
5. 更新对应索引（写入 skill 是 INDEX.md 的唯一写入者）：
   - repo 知识 → 更新对应 repo 的 `INDEX.md`
   - 跨 repo 知识 → 更新 `moc/INDEX.md`。**前置检查**：若 `moc/` 目录不存在，先创建 `moc/INDEX.md`（空条目表格），并在产品根 INDEX.md 的 repos 表中新增 `moc/` 行
6. **自动触发 zxning-mem-doctor skill**：写入完成后立即调用 zxning-mem-doctor skill 校验本次变更，校验通过才算写入成功，失败则提示用户修复。

**触发方式**：

- agent 主动调用（完成任务后自动沉淀知识）
- 用户手动调用（显式要求记录某条知识）

### 创建 repo skill

**职责**：在产品下初始化新 repo 的知识目录

1. **前置检查**：若产品目录不存在（首次接入新产品），先创建产品目录 + 产品根 `INDEX.md`（标题 + 一句话说明 + 空 repos 表，格式参照第四章"产品根 INDEX.md"）
2. 在产品目录下创建 repo 目录
3. 创建 repo 级 `INDEX.md`（空条目表格）
4. 更新产品根 `INDEX.md` 的 repos 表（新增一行）
5. **moc 检查**：若产品根下无 `moc/` 目录，则同时创建 `moc/INDEX.md`（空条目表格），并在 repos 表中新增 `moc/` 行。确保产品结构始终完整（repo + moc 对称）。

**触发方式**：agent 接手新 repo 任务时调用，或用户手动调用。

### 安装

skills 通过工具仓根目录的 `bootstrap.sh` 安装到目标 agent 的 skills 目录。由于仓库为私有，需先 clone 到本地，再执行本地安装：

```bash
bash /path/to/zxning-agent-knowledge/bootstrap.sh ~/.config/opencode/skills
```

`bootstrap.sh` 职责：

1. 按参数解析目标目录（codebuddy / trae / copilot / 任意自定义目录，默认 codebuddy + trae）
2. 复制 `zxning-mem-recall/` `zxning-mem-remember/` `zxning-mem-doctor/` `zxning-mem-init/` 到目标 skills 目录
3. 检查环境变量 `ZXNING_AGENT_KNOWLEDGE_VAULT`，缺失时打印配置指引

> bootstrap.sh **不负责创建 AGENTS.md**，那是工作项目的独立配置步骤。

### Validation skill

**职责**：校验知识库的一致性与完整性，作为写入链的强制后置钩子。

**触发方式**：

- zxning-mem-remember skill 自动触发（强制）
- 用户手动调用（定期巡检或怀疑不一致时）

**校验项**：

| 校验项             | 检测内容                                                                            | 修复指引                 |
| ------------------ | ----------------------------------------------------------------------------------- | ------------------------ |
| INDEX 完整性       | 产品根 INDEX.md 的 repos 表是否与目录结构一一对应                                   | 提示具体缺失或多余的行   |
| INDEX 条目完整性   | repo/moc 的 INDEX.md 条目表格是否与目录下 `*.md` 文件一一对应（不含 INDEX.md 自身） | 提示多出的文件或遗漏的行 |
| 条目可访问性       | INDEX.md 中列出的文件路径是否真实存在                                               | 提示断裂的链接           |
| moc 链接完整性     | moc 条目的"参考条目"是否覆盖了"涉及 repo"表格中的所有 repo                          | 提示缺失链接的 repo      |
| Frontmatter schema | 条目文件的 frontmatter 是否满足必填字段要求                                         | 提示缺失字段             |

**工作流**：

```
zxning-mem-remember skill 完成 → 自动调用 zxning-mem-doctor skill
  ├─ 全部通过 → 完成
  └─ 有错误 → 输出错误列表 → 用户确认是否修复 → 修复后重新校验
```

### Skills 层对现有设计的影响

| 影响点        | 变化                                                 |
| ------------- | ---------------------------------------------------- |
| INDEX.md 读者 | 首要读者从 agent 改为 zxning-mem-recall skill      |
| frontmatter   | 从"人类约定"变为"skill 的机器契约"，必须严格、可解析 |
| INDEX.md 维护 | 从"agent 手动更新"变为"zxning-mem-remember skill 自动维护" |
| 入口          | 工作项目根 AGENTS.md 是 skills 的运行时配置入口      |
| 安装          | 通过 bootstrap.sh 一键安装，无单独 skill             |

## 四、文件示例

以 `demo-product`（演示产品，含 api + webapp + miniapp 三个 repo）为例。repo 级示例仅以 `api` 演示，其他 repo 结构相同。

### 1. 产品根 `INDEX.md`

```markdown
# demo-product 知识索引

> 演示产品，由 api(Java/Play) + webapp(React 16) + miniapp(小程序) 组成。

## Repos

| 目录            | 角色         | 技术栈                        | 状态   |
| --------------- | ------------ | ----------------------------- | ------ |
| api/            | 后端 API     | Java 8, Play Framework, MySQL | active |
| webapp/ | PC Web 前端  | React 16, Create React App    | active |
| miniapp/      | 微信小程序   | 原生小程序                    | active |
| moc/            | 跨 repo 知识 | —                             | active |
```

### 2. `moc/INDEX.md`

```markdown
# moc 条目索引

| 文件                                | type     | summary                                         | tags             |
| ----------------------------------- | -------- | ----------------------------------------------- | ---------------- |
| 2026-06-18-wechat-login-decision.md | decision | 微信登录方案选型：后端中转 session              | [auth, wechat]   |
| 2026-06-20-order-flow.md            | how-to   | 下单端到端流程，跨 api+webapp+miniapp | [order, payment] |
```

### 3. repo 级 `INDEX.md`（如 `api/INDEX.md`）

```markdown
# api 条目索引

| 文件                        | type      | summary                        | tags       |
| --------------------------- | --------- | ------------------------------ | ---------- |
| 2026-06-10-orm-choice.md    | decision  | ORM 选型 TypeORM vs Prisma     | [database] |
| 2026-06-15-jwt-reference.md | reference | JWT token 结构、签发与校验速查 | [auth]     |
| 2026-06-19-order-api.md     | how-to    | 订单创建接口入参校验与事务处理 | [order]    |
```

### 4. repo 知识条目（如 `api/2026-06-15-jwt-reference.md`）

```markdown
---
type: reference
status: accepted
title: JWT 速查
summary: JWT token 结构、签发与校验速查
tags: [auth]
date: 2026-06-15
stack: play
---

## token 结构

Header.Payload.Signature，Payload 含 userId、role、exp。

## 签发

使用 java-jwt 签发，15 分钟过期。关键代码见代码仓库。

## 校验

使用 java-jwt 校验并提取 claim。

## 刷新

`/auth/refresh` 端点用 refresh token 换新 access token。
```

### 5. moc 条目（如 `moc/2026-06-20-order-flow.md`）

```markdown
---
type: how-to
status: accepted
title: 下单完整流程
summary: 用户从选择商品到支付成功的端到端流程，跨小程序+API+PC Web
tags: [order, payment]
date: 2026-06-20
---

## 涉及 repo

| repo           | 角色   | 做了什么                           |
| -------------- | ------ | ---------------------------------- |
| miniapp      | 用户端 | 展示商品 → 提交订单 → 发起支付     |
| api            | 后端   | 创建订单 → 生成支付参数 → 处理回调 |
| webapp | 管理端 | 查看订单列表 → 审核/退款操作       |

## 流程

1. 小程序端调 `api` 创建订单，获取支付参数后调起微信支付
2. 微信支付回调 `api` 更新订单状态，PC Web 管理端查看订单

## 参考条目

- [订单创建 API 实现](api/2026-06-19-order-api.md)
- [PC 端订单列表页](webapp/2026-06-17-order-page.md)
- [支付回调踩坑记录](miniapp/2026-06-16-wx-payment-incident.md)
```
