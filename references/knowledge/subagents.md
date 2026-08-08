# Subagents

## 职责与非目标

子代理把一个明确、可独立验收的子任务交给隔离执行单元，并返回带 lineage 的结果。
它不是无限递归的“多 Agent 魔法”，不共享父代理的隐式可变状态，也不能自动扩大权限和预算。
父代理仍拥有目标分解、冲突处理、结果整合和最终责任。
仅在工作可并行或需要专长/故障隔离时委派；小任务的编排成本可能高于收益。

## 委派 schema

```yaml
Delegation:
  id: string
  parent_run_id: string
  objective: string
  deliverable_schema: object
  context_refs: [item_ref]
  workspace_view: readonly|isolated_write|worktree
  capability_grants: [grant_ref]
  budgets: {tokens, wall_time, tool_calls, child_count}
  status: queued|running|waiting|succeeded|failed|cancelled
SubagentResult:
  delegation_id: string
  summary: string
  artifacts: [artifact_ref]
  evidence: [event_ref]
  unresolved: [string]
```

接口包括 `spawn(delegation)`, `send(message)`, `cancel`, `wait`, `collect`, `merge`。
上下文以引用切片传递，不默认复制完整 transcript、secrets 或其他子任务结果。
结果是普通 item/artifact，由父代理验证后才能写入最终结论。

## 所有权与调度

只读子任务可并行；写任务使用独立 worktree/temp workspace 或显式路径所有权。
禁止两个子代理在未知情况下编辑同一文件；合并由父级或专用 merge step 完成。
每层 child_count、总 token、工具并发和 wall time 都从父级预算扣除。
取消从父传播到所有后代；子代理完成不会自动终止父任务。
嵌套委派保留完整 lineage，最大深度和扇出由策略限定。

## 四级增量

### `runnable` 能跑

不要求子代理；单 Agent 顺序完成任务并保留可拆分接口。

### `usable` 能用

支持单层单子代理、明确 context refs、预算、取消和结构化结果。

### `productive` 顺手

增加多子代理并行、专长 profile、worktree/写所有权、公平调度和结果合并。

### `polished` 好用

增加受限嵌套、远程 worker、组织策略、成本/SLO、审计、故障重调度和质量评估。

## 直接升级与回滚

先把内部函数调用改为 Delegation/Result schema，再引入真正并行和隔离 workspace。
启用嵌套前建立全树预算、取消和 lineage；远程执行最后开启。
升级期间可让调度器保持 concurrency=1，验证结果等价后增加并发。
回滚停止新委派、取消或收拢后代，保留已提交 artifact 与事件，不强删工作区。

## 失败模式与安全

- 重复工作：objective 与 owned paths 明确，父级去重。
- 上下文泄漏：按最小 context refs 传递，secret/grant 不隐式继承。
- 写冲突：path lease/worktree + hash 合并，不使用 last-writer-wins。
- 失控递归：最大深度、扇出和总预算硬限制。
- 子级卡死：heartbeat、deadline、cancel 与可终止 worker。
- 结果伪造：父级验证 artifact/hash/test，不仅接受 summary。
- 权限升级：子 grant 必须是父 grant 子集。

## 验收 oracle

1. 两个只读子任务并行且不共享隐藏 transcript。
2. 两个写任务命中同一文件时在执行前阻止或隔离。
3. 父取消后所有后代停止派发新工具。
4. 子级请求父级没有的权限必定拒绝。
5. 失败子任务的原因与未完成项被父级汇总，不伪装整体成功。
6. 嵌套总消耗不超过父任务预算。

## 来源与设计综合

可参考 [Structured Concurrency](https://vorpus.org/blog/notes-on-structured-concurrency-or-go-statement-considered-harmful/) 的生命周期原则与 [Git worktree](https://git-scm.com/docs/git-worktree) 的写隔离思路。
产品具体的 agent tree UI、远程 worker 和事件格式由 dossier 决定；共享层只规定委派、所有权和回收合同。
