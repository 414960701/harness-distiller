# Harness Distiller Launch Kit

Canonical URL: https://github.com/414960701/harness-distiller

Social images: `assets/marketing/social-preview.png` (lossless, 1280×640) and `assets/marketing/social-preview.jpg` (GitHub upload, under 1 MB)

## Positioning

**One line**

Turn public evidence about AI coding agents into executable, testable harness blueprints.

**Why it matters**

The agent loop is the easy part. Production harnesses also need protocols, state, cancellation, context, permissions, real sandbox enforcement, persistence, recovery, migrations, UI reconstruction, and acceptance tests.

**Proof points**

- 35 implementation-ready knowledge modules
- 9 full product dossiers with 13 documents each
- 4 maturity levels: runnable, usable, productive, polished
- 3 versioned JSON Schema contracts
- 5 dependency-free Python scripts

## Hacker News

Title:

```text
Show HN: Harness Distiller – turn agent product evidence into implementation blueprints
```

URL:

```text
https://github.com/414960701/harness-distiller
```

Suggested first comment:

```text
Hi HN — I built Harness Distiller after repeatedly seeing agent projects stop at model → tool call → loop, while the difficult production work remained implicit.

The repository separates public evidence, observable behavior, protocols, and inference, then turns them into product contracts, capability graphs, implementation guidance, and executable acceptance criteria. It currently contains 35 shared modules and nine full dossiers covering Codex, Claude Code, QoderWork, Aider, OpenCode, OpenHands, AgentScope, LangGraph, and Deep Agents.

It is also usable as a Codex Skill and includes dependency-free scripts for generating and validating a versioned harness blueprint.

The docs are currently strongest in Chinese; the README is bilingual, and English translation contributions are welcome. I would especially value feedback on the capability model and which product dossier to add next.
```

## V2EX · 分享创造

Title:

```text
[开源] Harness Distiller：把 Codex / Claude Code 等 Agent 产品蒸馏成可实现架构
```

Body:

```text
最近整理并开源了一个项目：Harness Distiller。

很多 Agent 教程做到“模型 → 工具调用 → 循环”就结束了，但真正能长期运行的 Harness 还要处理：版本化协议、取消、上下文压缩、审批、真实沙箱、持久化、崩溃恢复、UI 状态重建和迁移。

这个项目把公开产品行为、官方文档、协议和开源代码证据，整理成可执行、可验证、可升级的架构蓝图。不会把对闭源产品的猜测写成源码事实。

当前包含：

- 35 个可直接用于实现的共享知识模块
- 9 套完整产品 dossier，每套 13 篇文档
- Codex、Claude Code、QoderWork、Aider、OpenCode、OpenHands、AgentScope、LangGraph、Deep Agents 配方
- runnable / usable / productive / polished 四级能力模型
- Blueprint、Event、Tool Spec 三套 Schema
- 只依赖 Python 标准库的生成和校验脚本
- 可直接安装为 Codex Skill

项目地址：https://github.com/414960701/harness-distiller

最想听大家反馈两个问题：
1. 这套 capability 分层有没有漏掉你在真实 Agent 工程里踩过的坑？
2. 下一套应该优先拆 Cursor、Windsurf、Cline，还是 CrewAI / AutoGen？

如果对你有用，欢迎 Star 或提交 Issue / PR。
```

## X / Twitter thread

Post 1:

```text
Open-sourced Harness Distiller 🚀

It turns public evidence about AI coding agents into executable, testable harness blueprints.

The agent loop is the easy part. Production needs protocols, state, cancellation, sandboxing, recovery, migrations, and verifiable acceptance tests.

https://github.com/414960701/harness-distiller
```

Post 2:

```text
What is inside:

• 35 implementation-ready modules
• 9 full product dossiers
• 4 maturity levels
• 3 versioned JSON Schemas
• dependency-free blueprint tooling
• a ready-to-install Codex Skill
```

Post 3:

```text
Current recipes cover Codex, Claude Code, QoderWork, Aider, OpenCode, OpenHands, AgentScope, LangGraph, and Deep Agents.

Facts, observable behavior, protocols, and inference stay explicitly separated.
```

Post 4:

```text
If you are building an agent runtime, CLI/TUI, IDE integration, desktop app, web app, SDK, or headless service, I would love feedback on the capability model.

Which product should be distilled next?
```

## Reddit

Choose one relevant subreddit only after reviewing its current self-promotion and flair rules. Do not cross-post the same submission to multiple communities on the same day.

Title:

```text
I open-sourced a knowledge base for designing production-grade AI agent harnesses
```

Body:

```text
I kept seeing agent implementations stop at the loop, while the harder system concerns were scattered across source code, docs, and product behavior.

I built Harness Distiller to organize those concerns into an evidence-backed capability model and implementation blueprint. It covers protocols, state, context, tools, permissions, sandboxing, persistence, recovery, UI reconstruction, migrations, and acceptance tests.

The first release includes 35 shared implementation modules and nine full product dossiers: Codex, Claude Code, QoderWork, Aider, OpenCode, OpenHands, AgentScope, LangGraph, and Deep Agents. It can also be installed as a Codex Skill.

Repository: https://github.com/414960701/harness-distiller

I am looking for technical feedback rather than drive-by promotion: what production concern is still missing, and which product dossier would be most useful next?
```

## 掘金 / 知乎长文

Title:

```text
做一个能用的 AI Agent，Agent Loop 可能只占 10%
```

Opening:

```text
如果把模型接上几个工具，再写一个 while 循环，就能叫 Agent Harness，那么 Codex、Claude Code、OpenHands 这类产品的大部分工程都没有存在的必要。

真正困难的部分从工具第一次执行之后才开始：怎么取消？结果迟到了怎么办？上下文压缩会不会拆散 tool call 和 result？用户点了允许，是否真的存在 OS 级边界？进程崩溃后如何恢复，又怎样保证不会重复一次不可逆操作？

我把这些问题整理成了一个开源项目 Harness Distiller：从公开证据出发，把 AI 编码 Agent 蒸馏成可以实现和验收的架构蓝图。
```

Suggested structure:

1. Agent Loop 为什么只是垂直切片，不是完整产品
2. Harness 的九个关键边界：协议、状态、上下文、工具、策略、执行、持久化、恢复、界面
3. Approval 不等于 Sandbox
4. 为什么 UI 必须能由 snapshot + event 重建
5. runnable → usable → productive → polished 的连续升级模型
6. 九套产品 dossier 中观察到的共同模式与差异
7. 如何把 Harness Distiller 安装为 Codex Skill
8. 开源地址与下一套 dossier 征集

Closing:

```text
项目地址：https://github.com/414960701/harness-distiller

如果你正在做 Agent Runtime、CLI/TUI、IDE、桌面端、Web、SDK 或 headless 服务，欢迎直接拿这套 blueprint 做一次架构对照。也欢迎告诉我：你最希望下一套补 Cursor、Windsurf、Cline，还是 CrewAI / AutoGen？
```

## 30-day cadence

Do not publish everything at once. Each post needs a reason to exist beyond asking for stars.

| Day | Action | New value delivered |
| --- | --- | --- |
| 0 | GitHub Release + Discussion | Bilingual launch, clear proof points |
| 1 | V2EX or 掘金 | Chinese technical origin story |
| 2 | Show HN | International technical launch |
| 4 | X thread | Visual overview and capability model |
| 7 | Reddit | Ask for missing production concerns |
| 10 | Publish one English module translation | Concrete response to accessibility feedback |
| 14 | Release the most-requested new dossier | Community-driven roadmap proof |
| 18 | Architecture deep dive | Reusable technical content, not an ad |
| 23 | Security/recovery checklist | High-signal practitioner resource |
| 30 | v0.2.0 retrospective | Usage, contributors, gaps, and next milestone |

Track stars by referral day, unique visitors, clones, discussion replies, issues, PRs, and repeat contributors. Treat stars as a lagging signal of useful work, not the primary product metric.
