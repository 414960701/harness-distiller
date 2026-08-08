# Claude-Code-like 产品合同

> 本文规定“实现到什么程度才可以称为 Claude-Code-like harness”。它描述公开可观察行为，不复制 Anthropic 品牌、私有提示词或闭源实现。

## 目录

- [证据标记](#证据标记)
- [产品边界](#产品边界)
- [角色与对象](#角色与对象)
- [核心用例](#核心用例)
- [能力矩阵](#能力矩阵)
- [跨表面合同](#跨表面合同)
- [非功能合同](#非功能合同)
- [成熟度升级](#成熟度升级)
- [完成定义](#完成定义)

## 证据标记

- `official-doc`：官方文档明确说明的行为。
- `public-repo`：公开仓库中的插件、示例或格式可以证明。
- `inference`：本仓库为达到同类用户结果提出的实现方案。
- `forbidden-claim`：没有公开证据，不得写成产品事实。

## 产品边界

### 要解决的问题

`official-doc/behavior`：用户从仓库目录启动编码 Agent，以自然语言交付任务；Agent 收集上下文、执行动作并验证结果。

`inference`：蒸馏产品应把模型看作可替换推理引擎，把 harness 看作状态、策略、执行和界面的所有者。

### 必须拥有

- 一个可中断、可恢复的 gather/action/verify 循环。
- 文件读取、搜索、编辑、Bash 和结构化提问。
- CLAUDE.md、scoped rules 与用户可管理 memory。
- context 预算、诊断、自动和手动 compact。
- allow/ask/deny 权限与独立 sandbox enforcement。
- Plan mode、tasks、subagents 和可选 agent teams。
- session、checkpoint、branch、resume 与 JSONL 等价审计记录。
- hooks、skills、plugins 和 MCP 扩展边界。
- CLI 与 headless；更高等级增加 IDE、Desktop、Web、SDK。

### 明确不拥有

以下也是本产品合同的非目标：

- 模型提供商的私有 system prompt。
- Claude Code 的内部类名、模块树或调度算法。
- 未公开的 compact prompt、cache key 或模型路由规则。
- Anthropic 名称、图标、商标和私有 endpoint。
- 把文件 checkpoint 说成外部副作用事务回滚。

## 角色与对象

### 用户角色

- `operator`：发起任务、steer、interrupt、审批和恢复。
- `admin`：下发 managed policy、网络和插件约束。
- `plugin_author`：提供 skill、hook、agent 或 MCP 集成。
- `surface_client`：CLI、IDE、Desktop、Web 或 SDK adapter。

### 核心领域对象

```text
Workspace -> Session -> Turn -> Item
Session   -> Checkpoint[]
Session   -> AgentRun[] -> ToolCall[]
Policy    -> PermissionRule[] -> Decision[]
Plugin    -> Skill[] | Hook[] | AgentDefinition[] | MCPServer[]
```

`inference`：对象名可以替换，但边界和可观察语义不可缺失。

### Session 不变量

- session id 在 branch 时改变，在 resume 时保持。
- 每个 turn 有唯一终态：completed、failed 或 cancelled。
- tool call 和 result 通过稳定 id 配对。
- 高风险临时权限不随 resume 静默恢复。
- 原始事件追加保存，派生视图可以重建。

## 核心用例

### 修改并验证代码

1. 用户提交目标。
2. runtime 加载可信范围内的指令和记忆。
3. Agent 搜索并读取最少必要上下文。
4. Agent 提交编辑或 Bash tool call。
5. policy 得出 allow、ask 或 deny。
6. sandbox 执行动作并回传结构化结果。
7. Agent 运行测试或检查 diff。
8. Agent 总结结果和未解决风险。

Oracle：最终答复能引用实际变更和验证结果；未执行的测试不得写成已通过。

### Plan mode

1. session 切换至 plan。
2. 读取和搜索仍可用。
3. 修改文件和有副作用 Bash 被 policy 阻断。
4. 计划以结构化 task/dependency 保存。
5. 用户显式批准后切换执行模式。

Oracle：单靠 prompt injection 不能绕过 plan enforcement。

### Resume 与 branch

- resume 重建同一 session 的对话、任务和工具状态。
- branch 从指定点创建新 session，保留 parent 引用。
- replay 不得重复已经提交的外部 mutation。
- 不兼容 schema 必须迁移或给出可操作错误。

### Subagent

- 父 Agent 指定目标、预算、tools 和权限上限。
- 子 Agent 拥有独立 context 和生命周期。
- 子 Agent 不能扩大父级权限。
- 父级默认只接收总结和 artifact 引用。
- cancel 向子进程和工具执行传播。

## 能力矩阵

| 能力 | 能跑 | 能用 | 顺手 | 好用 |
|---|---|---|---|---|
| loop | 单 Agent | 可恢复 | background | 分布式容错 |
| context | 基础截断 | compact | memory/cache telemetry | 策略化预算 |
| permission | 默认 ask | 规则作用域 | managed precedence | 组织审计 |
| sandbox | 能力声明 | 平台隔离 | 网络/秘密策略 | hard-fail 套件 |
| plan/tasks | 文本计划 | 结构化任务 | 依赖和 UI | 团队调度 |
| session | transcript | resume/branch | checkpoint/rewind | 迁移/远程同步 |
| extension | 少量 tools | MCP/skills | hooks/plugins | 签名和治理 |
| surfaces | CLI | headless | IDE | Desktop/Web/SDK |

## 跨表面合同

`official-doc`：Claude Code 提供 CLI、IDE、Desktop、Web、headless/SDK 表面；公开资料不保证所有表面共享一个存储。

`inference`：蒸馏实现应共享 versioned Command/Event protocol，而不是共享 UI 私有对象。

- CLI 必须完整支持流式、审批、中断和 session 选择。
- headless 必须支持机器可读事件、非交互审批策略和退出码。
- IDE 必须把 diff、selection、diagnostics 映射为显式 context item。
- Desktop 必须展示并行 session、终端、编辑器和 preview 的归属。
- Web 必须公开远程执行环境、凭证和断线恢复语义。
- SDK 必须暴露稳定事件，不承诺内部 JSONL 行格式。

## 非功能合同

- 可恢复：进程崩溃后不丢失已落盘事件。
- 可解释：每次 deny/ask 显示匹配规则和来源。
- 可取消：60 秒内所有长任务都应有 heartbeat 或进度事件。
- 可审计：敏感字段脱敏，但关键决策不可静默丢弃。
- 可移植：macOS、Linux、WSL2 的 sandbox 差异通过 capability 暴露。
- 可访问：无颜色、键盘和 screen reader 路径可完成核心任务。
- 可迁移：协议、session、plugin schema 均有版本和迁移策略。

## 成熟度升级

直接从“能用”升“好用”时，先迁移 schema，再升级 protocol、policy、runtime 和 surface。

升级不得改变已有 session id、权限语义和 tool result 配对规则。

新 UI 不得绕开 policy、sandbox 或 event store。

回滚时保留旧事件，只停用新 capability；不可删除用户 session。

## 完成定义

- 所有“必须拥有”均有实现、文档和 contract test。
- 所有公开行为声明能追溯到 [sources.md](sources.md)。
- 所有内部结构描述明确标为 `inference`。
- [acceptance-tests.md](acceptance-tests.md) 的 P0 oracle 全部通过。
- 安全能力按真实平台能力声明，不以 soft prompt 冒充 enforcement。
- 任何人仅阅读本目录即可搭出最小实现并逐级升级。
