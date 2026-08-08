# Plan 与任务

## 职责与非目标

Planning 把用户目标变为可观察、可调整、可验证的步骤与依赖，是协作状态而非私有推理文本。
它帮助用户 steering、恢复进度和分派子任务，但不强迫简单任务先写计划。
planner 不直接执行工具、不凭模型自报判定完成，也不暴露隐藏 chain-of-thought。
计划描述“做什么和以何证据完成”，不保存冗长思维过程。

## schema 与状态

```text
Plan {
  id, thread_id, version, goal, status,
  steps[], constraints[], created_by, updated_at
}
PlanStep {
  id, title, status, dependencies[], group_id?,
  owner?, evidence_refs[], blocking_reason?, risk?, estimate?
}
```

Plan 状态：`draft -> active -> completed|cancelled|superseded`。
Step 状态：`pending -> in_progress -> completed|failed|blocked|cancelled`。
同一串行计划最多一个普通 in_progress；并行步骤必须有显式 group 与资源隔离。
每次修改递增 version 并发出 plan event，旧客户端用 compare version 防止覆盖。

## 操作合同

最小操作：create、replace、update_step、append_evidence、cancel、supersede。
完成 step 必须附 artifact、tool result、test、diff 或用户确认等 evidence ref。
依赖未完成时默认不可启动；override 必须可审计并说明原因。
steering 可新增、删除或重排未开始步骤；进行中副作用不能靠改计划取消，需调用 runtime cancel。
检测到目标改变时 supersede 旧计划，不偷偷重写历史版本。

## 四级增量

| 等级 | 新增能力 | 不变量 |
|---|---|---|
| 能跑 | 可选文本/结构化清单 | step id、状态和用户可见 |
| 能用 | durable schema、进度事件、证据、用户修改 | version 与完成证据 |
| 顺手 | 依赖图、并行组、子代理委派、恢复 | 无环依赖与 owner 可追踪 |
| 好用 | 风险/成本调度、组织策略、历史估算、跨任务编排 | 可解释决策和用户 override |

等级增加调度元数据，不改变已有 step 的标识和终态含义。

## 直接升级与回滚

先把文本清单迁移为稳定 step id，再添加依赖、owner 和 estimate。
直接升级好用时，调度器先以 advisory/shadow mode 给建议，不立即自动启动高风险任务。
旧计划缺少字段时用兼容默认值；migration 保留原始文本作为 artifact。
回滚调度器只停止自动分派，不删除已完成证据或改变 step 状态。
新 schema 无法旧读时，将计划设为只读并允许创建兼容的新版本。

## 失败模式与安全

- 依赖循环：创建/更新时检测并拒绝，返回最小 cycle；
- 重复完成：幂等接受相同证据，不重复触发后继；
- 计划漂移：workspace/tool 事实与声明不一致时标记 stale；
- 阻塞无原因：blocked 必须有 reason 与解除条件；
- 恶意计划指令：plan 不是权限来源，不能提升 sandbox；
- 自动调度过载：并发、费用和工具配额由 runtime 强制；
- 子代理失联：owner 状态与结果对账，不能让父计划永久 in_progress。

## 可执行验收

- 简单任务可无 plan 完成，复杂任务可创建并流式更新；
- 两个客户端基于旧 version 更新时一个得到 conflict；
- 完成 step 无 evidence 被拒绝，有 test result 后成功；
- 插入依赖循环返回 cycle 且原计划不变；
- steering 重排 pending step，不修改正在执行工具参数；
- 子代理 cancel 后对应 step 进入 failed/blocked/cancelled 的显式策略状态；
- resume 后 plan、owner、evidence 与实际 turn/item 引用仍有效；
- shadow scheduler 建议与人工执行比较，不产生未经批准副作用。

## 证据与设计综合

`公开事实`：AgentScope Plan、Codex plan item 和多个 workflow framework 都使用结构化步骤或状态图。
`设计综合`：本 schema、单 in-progress 默认与升级策略是通用协作合同。
子代理委派见 [subagents.md](subagents.md)，事件见 [protocol-events.md](protocol-events.md)，评测见 [evals.md](evals.md)。
