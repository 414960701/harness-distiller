# Aider 产品蒸馏索引

## 范围与结论

本目录把 Aider 蒸馏成可由其他大模型执行的实现规范，而不是功能介绍。研究基线为 2026-08-08 可访问的官方文档，以及 `Aider-AI/aider@5dc9490bb35f9729ef2c95d00a19ccd30c26339c`。该提交日期为 2026-05-22；2026-08-08 复核时 GitHub 显示约 48,043 stars、Apache-2.0。

Aider 的产品核心不是“拥有很多通用工具”，而是一个收敛的 terminal Coder：把显式聊天文件、只读文件、repo map、历史和约束编排成提示；要求模型按 edit format 返回机器可应用的修改；在本地工作树落盘；以 Git、lint、test 和 reflection 构成可逆反馈环。

本 dossier 已达到 `implementation-grade`。它足以指导实现 Aider-like CLI，但不宣称逐字复制所有 prompt，也不把 Aider 误写成 Codex/Claude Code 等具备强 sandbox、MCP、通用 tool calling 或 subagent runtime 的产品。

## 阅读顺序

1. [sources.md](sources.md)：版本、固定提交链接和证据强度。
2. [product-contract.md](product-contract.md)：必须可观察到的行为、非目标和领域对象。
3. [architecture.md](architecture.md)：Coder、Model、Repo、RepoMap、IO、Commands 的边界。
4. [agent-loop.md](agent-loop.md)：单轮 Coder loop、reflection、终止、取消和重试。
5. [protocol-state.md](protocol-state.md)：thread/turn/item/event 兼容协议与状态机。
6. [context-tools.md](context-tools.md)：repo map、tree-sitter、PageRank、历史总结和 edit formats。
7. [workspace-execution.md](workspace-execution.md)：文件编辑、Git、lint/test 与 shell 执行。
8. [safety-runtime.md](safety-runtime.md)：确认、路径边界和没有强 sandbox 的事实边界。
9. [persistence-recovery.md](persistence-recovery.md)：chat history、Git checkpoint、cache、恢复和迁移。
10. [experience.md](experience.md)：CLI modes、斜杠命令、流式输出和反馈。
11. [recipe.md](recipe.md)：四级增量与直接升级规则。
12. [acceptance-tests.md](acceptance-tests.md)：行为、安全、故障和升级 oracle。

## 实现完成定义

一个实现只有同时满足以下条件，才可称为 Aider-like：

- `code` 模式能从模型响应解析至少一种 edit format，并在授权后原子写入文件；
- `ask` 模式绝不写文件；`architect` 模式由 architect 先提出方案、editor 再生成 edits；
- repo map 不是文件名清单，而是符号定义/引用图的 token-budgeted 投影；
- 上下文超限前可压缩旧历史，且保留最新对话与文件真值；
- AI 修改和用户已有 dirty change 可由 Git 提交边界区分；
- lint/test 的非零退出码可反馈给模型，但修复循环有次数上限；
- `/undo` 仅允许回退当前会话记录的 Aider commit，并拒绝 dirty、merge 或已推送危险场景；
- 无 Git、无网络、模型超时、malformed edit、cache 损坏时都给出确定结果；
- 没有实现强隔离时，UI 和文档明确标记 `host execution`，不得声称 sandboxed。

## 产品边界

| 能力 | Aider 基线 | 蒸馏实现要求 |
|---|---|---|
| 主循环 | 单 foreground Coder turn | 保持单写者；不得暗中并发编辑同一工作树 |
| 模型 | main、weak、可选 editor | adapter 统一，角色和费用分别记录 |
| 编辑 | whole、diff、diff-fenced、udiff 等 | 至少一个能跑，逐级增加；parser 与 applier 分离 |
| 仓库理解 | tree-sitter tags + graph rank + code tree | 必须有降级路径和 token 预算 |
| 执行 | 本机文件、Git、lint/test、确认后的 shell | 默认不等于 OS sandbox |
| 恢复 | Git commit、`/undo`、chat history、tag cache | Git 是恢复真源；cache 可重建 |
| 扩展 | CLI/config/model metadata | 不默认包含 MCP、插件平台或 subagents |

## 证据标签

- `official-doc`：Aider 官方网站或随仓库发布的文档。
- `code`：固定 commit 的公开源码，可直接定位实现。
- `test`：固定 commit 的测试所表达的行为。
- `inference`：为了构建稳定产品而做的设计综合，不声称是原实现。

所有关键结论应能在 [sources.md](sources.md) 找到来源；闭源 provider 行为、托管基础设施和未公开产品数据不在本目录范围内。
