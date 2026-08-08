# Claude Code 产品蒸馏索引

## 目录

- [产品定位](#产品定位)
- [闭源边界](#闭源边界)
- [文档分层](#文档分层)
- [推荐读取顺序](#推荐读取顺序)
- [可生成的工程骨架](#可生成的工程骨架)
- [最低交付物](#最低交付物)
- [主要来源](#主要来源)
- [使用边界](#使用边界)
- [维护规则](#维护规则)

## 产品定位

Claude Code 是终端优先、扩展面完整、强调人在回路和长任务交互的编码 Agent。可蒸馏目标是官方公开的行为合同：context gathering/action/verification loop、CLAUDE.md 与 memory、权限和 Bash sandbox、plan/subagent/team、session/checkpoint、MCP/skills/hooks/plugins，以及 CLI/IDE/Desktop/Web/SDK 表面。

## 闭源边界

Claude Code 完整产品源码不可见。公开仓库 anthropics/claude-code 的 README 将用户引向安装和官方文档，仓库内容主要是插件、示例、脚本和 issue；其 LICENSE 使用 Anthropic 商业条款，无开源 SPDX。GitHub 统计语言不能代表闭源 runtime 的实现语言。

因此本目录强制使用三类标记：

- behavior / official-doc：官方明确承诺或可重复观察的产品行为；
- public-repo：公开插件、hook 示例、配置和扩展格式的代码证据；
- inference：为实现相同行为而提出的本仓库设计，不声称等同内部实现。

研究快照：

- status: researched
- retrieved: 2026-08-08
- public repository: https://github.com/anthropics/claude-code
- GitHub API stars: 140591（动态值，仅表示查询时快照）
- repository license: Anthropic commercial terms，非完整产品源码许可

## 文档分层

本 dossier 分为“事实解释层”和“实现合同层”。前者回答 Claude Code 公开表现是什么，后者回答另一个模型应如何搭出具有同类行为的 harness。

不要只读某一篇就开始生成。闭源产品的事实、实现选择和测试必须分别落在正确层级。

### 入口与证据

- [product-contract.md](product-contract.md)：产品边界、必需能力、角色、对象和完成定义。
- [sources.md](sources.md)：官方文档、公开仓库、声明映射和不可证实事项。
- [architecture.md](architecture.md)：公开架构行为、证据边界和推荐架构不变量。

### 核心运行时合同

- [agent-loop.md](agent-loop.md)：gather/action/verify 状态机、steer、interrupt、Plan、tasks、subagents 和 teams。
- [protocol-state.md](protocol-state.md)：Command/Event/Item、状态投影、tool/permission 协议和版本协商。
- [workspace-execution.md](workspace-execution.md)：workspace identity、trust、edit、Bash、权限、sandbox、网络和 worktree。
- [persistence-recovery.md](persistence-recovery.md)：JSONL 等价 event store、session、checkpoint、compact、cache、恢复和迁移。

### 行为专题

- [context-tools.md](context-tools.md)：CLAUDE.md/rules/memory、context、工具、计划、subagent 和扩展的公开行为。
- [safety-runtime.md](safety-runtime.md)：allow/ask/deny、permission modes、平台 sandbox 和安全边界。
- [experience.md](experience.md)：CLI、headless、IDE、Desktop、Web、SDK 与人在回路体验。

### 构建与验证

- [recipe.md](recipe.md)：共享能力差量、公开替代组件、四级构建顺序和升级方式。
- [acceptance-tests.md](acceptance-tests.md)：可自动化的黑盒合同、fixture、故障注入和逐级门槛。

## 推荐读取顺序

### 从零实现

1. 先读 product-contract 和 sources，锁定非目标与证据边界。
2. 读 protocol-state，先定义稳定 schema 和事件不变量。
3. 读 agent-loop，实现可中断和可恢复的主循环。
4. 读 workspace-execution，把 permission 与 sandbox 接入每个动作。
5. 读 persistence-recovery，实现 resume、branch、checkpoint 和 compact。
6. 用 context-tools、safety-runtime、experience 补公开行为细节。
7. 按 recipe 选择成熟度，并跑 acceptance-tests 对应门槛。

### 审查已有实现

1. 用 product-contract 做能力盘点。
2. 用 protocol-state 和 persistence-recovery 检查可恢复性。
3. 用 workspace-execution 和 safety-runtime 检查 enforcement。
4. 用 acceptance-tests 生成缺陷清单。
5. 用 recipe 规划不破坏低等级合同的升级。

## 可生成的工程骨架

实现者可以改模块名，但至少需要以下职责边界：

```text
runtime/        agent loop、turn/run 生命周期、取消
protocol/       command、event、item、schema、migration
context/        instructions、memory、budget、compaction
policy/         permission、mode、managed precedence
execution/      edit、process、sandbox、network、secrets
state/          event store、projection、artifact、checkpoint
extensions/     hooks、skills、plugins、MCP、agent definitions
surfaces/       cli、headless、ide、desktop/web、sdk adapters
evals/          fixtures、contract tests、quality evals
```

这些名称是 `inference`。生成器应维持职责和依赖方向，而不是机械复制目录名。

## 最低交付物

- versioned command/event schema 和 capability negotiation。
- 一个 deterministic fake model 驱动的 loop contract test。
- 一个真实 workspace edit + test 闭环。
- allow/ask/deny 与 platform sandbox capability report。
- session resume/branch 与 crash recovery fixture。
- CLAUDE.md/rules/memory/compact 的 provenance manifest。
- CLI 和 headless 对同一事件 trace 的一致投影。
- dependency/license ledger 与 inference 清单。
- 对应成熟等级的验收报告。

## 主要来源

- Overview: https://code.claude.com/docs/en/overview
- How it works: https://code.claude.com/docs/en/how-claude-code-works
- Documentation index: https://code.claude.com/docs/llms.txt
- Public repository: https://github.com/anthropics/claude-code
- Public plugins: https://github.com/anthropics/claude-code/tree/main/plugins

## 使用边界

可实现行为兼容和相似工作流，不复制 Claude/Anthropic 品牌、图标、专有提示词、私有服务或受保护资产。凡官方文档未说明、公开仓库不可验证的内部算法，都必须保留为 inference 或实现选择。

## 维护规则

- 新增产品行为前先在 sources.md 登记证据等级。
- 新增实现方案标 `inference` 并至少给一个替代实现。
- 修改 schema 同时更新 protocol-state、migration 和 acceptance fixture。
- 修改 permission/sandbox 同时更新攻击测试。
- 修改 surface 不得绕开共享 command/event 协议。
- 每次版本发布记录尚未通过的等级门槛，不能用“Claude-like”掩盖缺失能力。
