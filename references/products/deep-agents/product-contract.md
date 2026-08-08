# Deep Agents 产品行为合同

## 目录

- [产品定义](#产品定义)
- [证据基线](#证据基线)
- [输入合同](#输入合同)
- [可观察行为](#可观察行为)
- [状态与副作用](#状态与副作用)
- [四级合同](#四级合同)
- [非目标](#非目标)
- [失败与安全](#失败与安全)
- [完成定义](#完成定义)

## 产品定义

Deep Agents 是基于 LangChain agent middleware 与 LangGraph durable runtime 的 Python harness 组装层。

它的辨识度来自以下组合，而不是某个独占算法：

1. 通过 `create_deep_agent` 装配模型、工具、backend 与 middleware；
2. 把大上下文外置到虚拟 filesystem，并通过摘要与引用重新加载；
3. 通过同步或远程异步 subagent 隔离工作上下文；
4. 用 permission + HITL interrupt 控制部分敏感动作；
5. 复用 LangGraph state、checkpoint、interrupt 与 stream；
6. 通过 ACP、CLI、Code 或自建 frontend 投影执行过程。

复刻结果应是“同类行为的可替换 harness”，不是复制 LangChain 品牌、私有云或内部部署。

## 证据基线

本合同锁定 `deepagents==0.7.5`、commit `d60560d695e8c436e11dee96965e7a1447409737`。

字段和默认值来源见 [sources.md](sources.md)。

行为状态分为：

| 状态 | 含义 |
|---|---|
| `documented` | 官方文档声明，尚未在复刻实现运行 |
| `implemented-not-verified` | 已编码，但 oracle 未通过 |
| `verified` | 对应等级的可执行 oracle 通过 |
| `deferred` | 明确不在当前交付范围 |

## 输入合同

`AgentSpec` 至少包含：

```yaml
model: provider:model
system_prompt: string|null
tools: []
middleware: []
backend: state|filesystem|store|composite|sandbox
subagents: []
skills: []
memory: []
permissions: []
interrupt_on: {}
checkpointer: null|configured
store: null|configured
```

规范化阶段必须：

- 显式解析 model，禁止生产配置依赖隐式默认模型；
- 为每个 turn 固化 model/tool/middleware/backend/profile 版本快照；
- 检查 `read_file` 保留于 filesystem tool allowlist；
- 检查执行型 backend 与 permissions 的冲突；
- 当需要 interrupt 时要求 durable checkpointer 和稳定 `thread_id`；
- 将同步、compiled 和 async subagent 分为不同执行合同；
- 校验 skill/memory POSIX 路径和 backend 可达性；
- 不把 MCP、RAG 或 frontend 能力由名称自动推断为已安装。

## 可观察行为

### 最小调用

给定用户消息，agent 必须在有限预算内完成如下闭环：

```text
input -> model -> tool? -> middleware/policy -> backend -> tool result -> model -> final
```

### Filesystem

- 默认 backend 是 state-backed 虚拟 filesystem，不是宿主磁盘。
- 工具集合按 backend 能力动态包含 `execute` 和 `delete`。
- `read_file`、`grep`、`glob` 返回有界、可诊断的结构化结果。
- 大 tool result 或被压缩 history 写入 backend 路径，模型得到摘要和引用。

### Planning

- 0.7.5 默认不注入 `TodoListMiddleware`。
- 用户选择 Deep Agents 风格 planning 时，显式加入 middleware。
- Todo 是公开协作状态，不能存储私有 chain-of-thought。
- 同一模型响应中的并行多次 `write_todos` 必须拒绝或串行化。

### Subagent

- 同步 `task` 调用阻塞父 agent，子 agent 使用独立 messages。
- 父 state 中 messages/todos/structured_response/private fields 不传入子 agent。
- 子 agent 最终只向父返回结构化结果或最后一个非空 assistant 文本。
- 异步 subagent 通过远程 Agent Protocol thread/run，必须可查询、更新和取消。

### Permission/HITL

- filesystem rule 按声明顺序首条匹配；无匹配默认 allow。
- `deny` 在工具实现处强制；`interrupt` 映射为可恢复审批。
- approve/edit/reject/respond 的结果都进入状态与事件日志。
- 规则不覆盖 `execute`、custom tool、MCP；这些必须有独立 policy。

## 状态与副作用

核心状态至少包含：

| 字段 | 所有者 | 说明 |
|---|---|---|
| `messages` | LangGraph/agent | 带稳定 ID 的消息 delta |
| `files` | StateBackend | 默认 backend 的文件字典 |
| `todos` | Todo middleware | opt-in 计划项 |
| `async_tasks` | AsyncSubAgentMiddleware | 远程 thread/run 映射 |
| `_summarization_event` | summarization middleware | private state，不向 subagent 扩散 |
| `structured_response` | structured output | 不从子 agent 直接合并 |

外部副作用必须带稳定 `call_id`、参数摘要、policy decision、commit 状态和幂等策略。

LangGraph checkpoint 提供 graph 恢复点，但不会自动让任意 shell、HTTP 或 SaaS 写操作 exactly-once。

## 四级合同

| 等级 | 必须行为 | 可延后优化 |
|---|---|---|
| `runnable` | 单 agent、显式 Todo、state backend、基本 middleware、有限循环 | 持久存储和远程执行 |
| `usable` | 同步 subagent、skills、memory、filesystem permission、HITL、checkpoint | 并行后台和生产 UI |
| `productive` | RAG adapter、恢复去重、typed stream、评测与观测 | 强隔离、多租户和远程 control plane |
| `polished` | 强 sandbox、remote backend、生产服务、managed permission profile、迁移、SLO | 闭源品牌和私有算法 |

高级等级只增加优化与硬化，不另建 agent loop 或破坏低等级 schema。

## 非目标

- 不承诺复刻 LangSmith 托管服务、Studio 或专有 control plane。
- 不把 backend interface 宣称为安全隔离。
- 不把 AGENTS.md memory 宣称为自动学习系统。
- 不把 filesystem grep 宣称为语义 RAG。
- 不把同步 subagent 宣称为进程级、容器级或租户级隔离。
- 不复制 Deep Agents 页面、图标、品牌或模型默认值。
- 不公开、记录或要求模型 chain-of-thought。
- 不将滚动文档中尚未出现在固定版本的行为写成已实现事实。

## 失败与安全

| 场景 | 必须结果 |
|---|---|
| model 超时 | 有界重试后 `failed`，保留可恢复状态 |
| tool schema 错误 | 结构化错误反馈模型，不执行副作用 |
| permission deny | `ToolMessage(status=error)`，无 backend 写入 |
| interrupt 无 checkpointer | 配置时失败，不静默降级 |
| sandbox 不可用 | fail closed，不回退 LocalShell |
| subagent 不存在 | 返回允许类型列表，不调用任意 graph |
| 子 agent 迟到 | 父取消后不提交结果 |
| checkpoint 位于提交后 | 用 idempotency/receipt 去重 |
| 无法判断副作用 | `indeterminate` 并请求人工确认 |
| skill/memory 注入 | 标记来源和信任级，不能改写 policy |

## 完成定义

只有同时满足以下条件才可称为完整 Deep Agents-like harness：

1. [agent-loop.md](agent-loop.md) 的状态机有实现和终止预算；
2. [protocol-state.md](protocol-state.md) 的事件可被 snapshot + sequence 重放；
3. [workspace-execution.md](workspace-execution.md) 的 backend 合同和 sandbox 边界通过测试；
4. [persistence-recovery.md](persistence-recovery.md) 的崩溃矩阵通过；
5. [acceptance-tests.md](acceptance-tests.md) 对当前等级全部为绿色；
6. 每项 `verified` 都链接测试输出、trace 或 artifact，而非只链接文档。
