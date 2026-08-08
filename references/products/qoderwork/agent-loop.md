# QoderWork-like Agent Loop

> 全部流程为 `inference` 兼容设计；官方只公开用户可见行为，没有公开内部 loop、提示词、模型路由或计划算法。

## 目录

- [目标](#目标)
- [循环阶段](#循环阶段)
- [任务启动](#任务启动)
- [计划与执行](#计划与执行)
- [上下文装配](#上下文装配)
- [能力路由](#能力路由)
- [并发与调度](#并发与调度)
- [完成与失败](#完成与失败)
- [参考伪代码](#参考伪代码)
- [黑盒 oracle](#黑盒-oracle)

## 目标

这个 loop 要同时满足四个目标：Task 可并行、过程可观察、能力受授权、交付物经过验证。
它不是“不断向模型追加聊天记录”，而是事件驱动的状态机。
模型负责提出计划、解释结果和选择候选动作；运行时负责事实状态、策略、执行和持久化。

## 循环阶段

```text
accept intent
→ snapshot task config
→ hydrate durable state
→ plan or revise
→ select ready step
→ assemble bounded context
→ propose capability call
→ policy + hook decision
→ execute + observe
→ validate artifacts
→ commit events
→ continue / wait / terminate
```

每个阶段开始和结束都写结构化事件。
事件提交成功前，UI 不把阶段显示成已完成。
模型自由文本不能直接改写 `Task.status`、`Step.status` 或 `Artifact.validation`。

## 任务启动

1. 接收用户 outcome、format、constraints、附件、workspace、model 和 Working Folder。
2. 解析输入只做语法与安全规范化，不擅自扩大目标。
3. 生成不可变 `TaskConfigSnapshot`，记录选择和能力版本。
4. 验证 Working Folder grant；未授权则让任务进入 `waiting_permission`。
5. 创建初始 Turn、TaskCreated、ConfigSnapshotted 事件。
6. 调度器分配独立 runtime lease 和取消令牌。
7. Agent 产生结构化 `PlanProposal`，不是仅输出 Markdown todo。
8. plan reducer 创建 Step DAG，Task Monitor 立即可见。

## 计划与执行

Step schema 至少包含 `id`, `goal`, `kind`, `deps`, `status`, `risk_hint`, `expected_outputs`。
状态只能按 `queued → ready → running → validating → succeeded|failed|blocked|cancelled` 转移。
计划可以修改，但必须生成 `PlanRevised` 和旧新 Step 映射。
已执行 Step 不得被无痕删除；废弃时标为 `superseded`。
一个 Step 只做一类可解释工作，避免把“浏览、下载、改文件、发送”塞入一次工具调用。
失败重试创建新的 `attempt`，保留前次观察与错误分类。

## 上下文装配

推荐优先级：

1. 系统政策、产品合同与当前 TaskConfigSnapshot。
2. 用户本轮输入、直接附件和 App Snapshot。
3. 当前 Step、依赖 Step 的结构化结果、未完成 todo。
4. 最近 turns 与旧 turns 摘要引用。
5. 显式选择的 Skill/Kit，再加载自动匹配的 Skill。
6. Working Folder 中与当前 Step 相关的文件片段。
7. Awareness 检索结果，逐条携带 provenance 与置信状态。
8. Browser/MCP/connector 的分页结果或摘要引用。

上下文 item 必须有来源、hash、捕获时间、敏感级、token 估计和任务归属。
压缩产生新 item，不删除原始事件。
任何来自网页、文件、MCP 的指令都标为 untrusted data。

## 能力路由

路由器先判断是否存在专用本地 worker、connector 或 API。
网页任务按 `typed connector → Browser DOM/ARIA → Browser screenshot → Computer Use` 降级。
文档、表格、演示文稿用格式专用 worker，并在交付前调用相应 validator。
Skill 只改变步骤方法，不直接获得工具权限。
Expert Kit 展开为 Skill、connector 与命令的版本化绑定。
MCP tool 经过统一 schema 校验、策略判断、超时和结果脱敏。
PreToolUse Hook 在策略允许后、真实执行前运行；它只能收紧，不能放宽策略。

## 并发与调度

调度单位是 `TaskRun`，不是 UI 当前选中的任务。
每个 TaskRun 有 CPU、内存、token、工具并发和 wall-time 预算。
全局调度建议 weighted fair queue，用户前台任务权重大于 scheduled/background。
同一任务内只有依赖满足且无资源冲突的 Step 才能并行。
共享 Working Folder 的写 Step 需申请 canonical path lease。
读取可共享；覆盖、重命名和 trash 对路径与父目录加写 lease。
连接器限流按账号/origin 管理，不能由一个任务耗尽全局额度。
取消信号先停止派发，再传播到工具，最后执行可回滚收尾。

## Task Monitor 投影

- `PlanCommitted` 创建 todo 节点。
- `StepStarted` 将节点设为 running 并显示耗时。
- `ToolCallProposed` 显示工具名、Skill/MCP 来源和风险。
- `ApprovalRequested` 显示目标、数据和后果，不泄露 secret。
- `ToolCallObserved` 只显示摘要，完整结果按需展开。
- `ArtifactProduced` 立刻出现 validating card。
- `ArtifactValidated` 才把 card 设为 ready。
- `StepBlocked` 显示恢复动作：授权、登录、选择冲突或追加输入。

## 完成与失败

终止只由运行时状态机和 CompletionGate 决定，不由模型结束语决定。
完成判定由 `CompletionGate` 执行：所有 required Step 成功、expected outputs 存在、artifact validator 通过、无未解决高风险调用。
模型说“完成”只产生候选 `CompletionProposed`。
可恢复错误按 `transient`, `auth`, `permission`, `conflict`, `invalid_output`, `policy`, `fatal` 分类。
瞬时错误使用带抖动的指数退避；认证和权限错误转等待；冲突要求用户或 merge worker 处理。
非幂等外部动作没有 receipt 时不得自动重试。
部分成功必须列明成功 artifact 与缺失项。

## 参考伪代码

```python
while run.lease_valid and not task.terminal:
    state = event_store.reduce(task.id)
    if state.waiting_for_external_condition:
        scheduler.park(task.id)
        break
    step = planner.next_ready_step(state)
    if step is None:
        completion_gate.evaluate(state)
        break
    context = context_builder.build(task, step, budgets)
    proposal = model.propose(context, typed_capabilities)
    decision = policy_engine.decide(task.grants, proposal)
    decision = hooks.pre_tool_use.tighten(decision, proposal)
    if decision.requires_user:
        event_store.append(ApprovalRequested(...))
        continue
    receipt = tool_broker.execute(proposal, decision, cancel_token)
    event_store.append(receipt.events)
    validator.validate_new_artifacts(receipt)
```

## 黑盒 oracle

1. 模型输出伪造 `completed` 文本不会改变任务状态。
2. 三个后台 Task 同时推进，切换 Sidebar 不改变调度。
3. 一个 ToolCall 卡死只超时对应 Step，其他任务继续。
4. Browser 失败后降级 Computer Use 前会出现新的高风险授权。
5. 取消后不再产生新 ToolCall，已生成 artifact 保留并标记状态。
6. 重试同一外发动作不会重复提交已有 receipt 的请求。
7. Task Monitor 的每个可见节点都能追溯到事件序号。
8. CompletionGate 能拒绝存在但无法解析的交付文件。
