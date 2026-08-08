# 产品与知识目录总表

## 结论

完整实现指导版固定为 **21 个产品目录、35 个共享知识文档、12 篇共享实现规范、每个产品 13 个蒸馏文档**。产品文档总量为 273 篇；共享理论与实现合同只写一次，由产品配方引用，避免 21 套实现互相漂移。

当前仓库按里程碑逐篇完成，不用空白占位文件冒充调研完成。`status` 只允许 `researched`、`drafted`、`verified`。

实现级 dossier 已完成 9/21：`codex`、`claude-code`、`qoderwork`、`aider`、`opencode`、`openhands`、`agentscope`、`langgraph`、`deep-agents`。其余 12 个产品保持在计划清单中，只有完成固定来源、13 篇实现文档、产品 capability oracle 和正向生成验证后才提升状态；仓库不创建空白占位 dossier。

## 21 个产品目录

### A. 编码 Agent 产品（13）

| id | 产品 | 公开实现 | 主表面 | 选入原因 |
|---|---|---:|---|---|
| `codex` | OpenAI Codex | 高 | CLI/IDE/Desktop/Cloud | headless app-server、权限与沙箱、事件流、worktree |
| `claude-code` | Claude Code | 中低 | CLI/IDE | hooks、skills/subagents、权限、长任务交互 |
| `qoderwork` | QoderWork | 低 | Desktop/IDE | 工作台式任务编排与成品交付体验 |
| `cursor` | Cursor Agent | 低 | IDE | 代码索引、编辑器原生交互、后台 agent |
| `windsurf` | Windsurf Cascade | 低 | IDE | flow、上下文、命令与编辑器联动 |
| `copilot-agent` | GitHub Copilot coding agent | 中 | IDE/Cloud | GitHub issue/PR 闭环与远程执行 |
| `jules` | Google Jules | 低 | Web/Cloud | 异步远程编码任务 |
| `junie` | JetBrains Junie | 低 | IDE | JetBrains 原生工程模型与审查流程 |
| `aider` | Aider | 高 | CLI | repo map、编辑格式、Git 原子提交 |
| `opencode` | OpenCode | 高 | TUI/Desktop/SDK | 多提供商、client/server、TUI |
| `cline` | Cline | 高 | IDE/SDK/CLI | 人在回路、浏览器与 MCP、可扩展工具 |
| `roo-code` | Roo Code | 高 | IDE | modes、角色化代理、团队式编排 |
| `openhands` | OpenHands | 高 | Web/CLI/Cloud | 事件流、沙箱、远程 runtime、评测 |

### B. 通用 Agent Harness（8）

| id | 产品 | 公开实现 | 核心价值 |
|---|---|---:|---|
| `agentscope` | AgentScope | 高 | 完整 building blocks 与工程化 runtime |
| `langgraph` | LangGraph | 高 | 状态图、Pregel、持久化、human-in-the-loop |
| `deep-agents` | LangChain Deep Agents | 高 | 基于 LangGraph 的 batteries-included harness、workspace、skills、subagents |
| `autogen` | Microsoft AutoGen | 高 | 多 Agent 消息与 runtime |
| `crewai` | CrewAI | 高 | role/crew/flow 编排 |
| `openai-agents-sdk` | OpenAI Agents SDK | 高 | handoff、guardrail、tracing、tool loop |
| `llamaindex-workflows` | LlamaIndex Workflows | 高 | 事件驱动工作流与 RAG 生态 |
| `letta` | Letta | 高 | 有状态 Agent 与长期记忆 |

## 每个产品固定 13 篇

| 文件 | 内容 | 允许的证据 |
|---|---|---|
| `index.md` | 产品定位、状态、导航、适用边界 | 全部 |
| `sources.md` | 版本锁定、源码地图、行为来源与论断映射 | 全部，优先 permalink |
| `product-contract.md` | 可观察行为合同、能力边界、非目标 | 官方文档/协议/行为 |
| `architecture.md` | 进程、模块、协议、状态与部署 | 源码/官方文档优先 |
| `agent-loop.md` | 状态机、伪代码、终止、重试、取消与 steering | 源码/文档/设计综合 |
| `protocol-state.md` | thread/turn/item/event、command 与 schema | 源码/协议/设计综合 |
| `context-tools.md` | 模型、上下文、工具、RAG、记忆、计划 | 源码/文档/行为 |
| `workspace-execution.md` | 文件、shell、patch、Git、worktree、browser/computer executor | 源码/文档/设计综合 |
| `safety-runtime.md` | workspace、权限、沙箱、网络、秘密、恢复 | 源码/文档/行为 |
| `persistence-recovery.md` | 数据 schema、事务、checkpoint、resume、fork、迁移 | 源码/协议/设计综合 |
| `experience.md` | CLI/TUI/IDE/Desktop/Web 信息架构与流程 | 官方文档/行为 |
| `recipe.md` | 与共享架构的差量、等级映射、验收场景 | 明确标为设计综合 |
| `acceptance-tests.md` | 分级黑盒、安全、故障注入与测试 oracle | 行为合同/设计综合 |

前 6 篇只构成研究级 dossier；13 篇齐全且通过内部链接和来源检查后，才构成实现级 dossier。

## 35 个共享知识文档

| 组 | 数量 | 文档 id |
|---|---:|---|
| 内核运行时 | 8 | `agent-loop`, `model-adapter`, `protocol-events`, `context-engine`, `tool-runtime`, `planning`, `middleware-hooks`, `state-persistence` |
| 执行与安全 | 9 | `workspace`, `filesystem`, `shell-process`, `patch-edit`, `sandbox`, `permission-policy`, `network-secrets`, `browser-computer`, `git-worktree` |
| 知识与扩展 | 6 | `rag-index`, `long-term-memory`, `mcp`, `skills-plugins`, `subagents`, `instructions-prompts` |
| 产品表面 | 6 | `cli-tui`, `ide`, `desktop-web`, `diff-review`, `notifications-input`, `auth-settings` |
| 质量与运维 | 6 | `observability`, `evals`, `testing`, `reliability`, `performance-cost`, `deployment-update` |

完整导航见 [knowledge/index.md](knowledge/index.md)。

共享实现规范见 [implementation/index.md](implementation/index.md)。它补充字段级领域模型、协议、算法、数据库、UI 状态、技术栈与交付闸门，任何真正生成 Harness 的任务都必须读取。

## 收敛原则

- 产品目录回答“这个产品哪里不同”。
- 共享知识回答“这个能力怎样正确实现”。
- `recipe.md` 只能覆盖差量，不得复制共享知识全文。
- 闭源产品保留行为兼容目标，但底层实现选公开、可验证、许可证兼容的方案。
- 星标只作为发现线索，不作为质量结论；最终采用必须通过代码结构、维护活跃度、安全边界和测试证据审查。
