# AgentScope-like Agent Loop

## 目录

证据边界 → Reply 状态机 → 持久 schema → 参考算法 → Action → Permission/HITL → 取消 → 重试 → Middleware → Plan/Team → 测试。

## 证据与设计边界

固定源码的 `Agent.reply/reply_stream/_reply/_reasoning/_acting/_next_action` 明确呈现 ReAct 控制流，`AgentState.reply_context` 保存 `reply_id/cur_iter`，Event 定义 reply/model/tool/HITL/interrupt/终态。以下状态机保留这些可观察语义，并补充持久化、幂等与 lease；补充部分是可靠 harness 的 `inference`，不是声称原类逐字段实现。

## Reply 状态机

```text
IDLE -> ACCEPTING -> PREPARING -> MODEL_STREAMING
MODEL_STREAMING -> ASSEMBLING_TOOL_CALL -> POLICY_CHECK
POLICY_CHECK -> WAITING_CONFIRMATION | EXECUTING_TOOL | RECORDING_DENIAL
WAITING_CONFIRMATION -> EXECUTING_TOOL | RECORDING_DENIAL | CANCELLING
EXECUTING_TOOL -> COMMITTING_RESULT -> PREPARING
MODEL_STREAMING -> COMMITTING_ANSWER -> COMPLETED
any nonterminal -> CANCELLING -> INTERRUPTED
any nonterminal -> FAILED
PREPARING at max_iters -> EXCEEDED_MAX_ITERS
```

终态只有 `completed | interrupted | error | exceed_max_iters`。终态 append 使用 compare-and-set；迟到的 model chunk、confirm 或 tool result 标为 `ignored_after_terminal`，不得改写终态。

## 持久 loop schema

```json
{
  "session_id": "ses_01",
  "reply_id": "rep_01",
  "status": "waiting_confirmation",
  "cur_iter": 2,
  "max_iters": 12,
  "active_model_call_id": null,
  "active_tool_call_ids": ["call_7"],
  "waiting_request_id": "confirm_7",
  "capability_snapshot_hash": "sha256:...",
  "state_version": 18,
  "lease_owner": "worker-a",
  "lease_expires_at": "2026-08-08T12:00:30Z",
  "cancel_requested_at": null
}
```

## 参考算法

```text
run_reply(command):
  dedupe(command.idempotency_key)
  acquire_session_lease(command.session_id)
  append(REPLY_START); checkpoint(ACCEPTING)
  observe(command.message); run_middleware(before_reply)
  while state.cur_iter < config.max_iters:
    check_cancel(); checkpoint(PREPARING)
    maybe_compress_or_offload_context()
    input = assemble_context(snapshot, state, tools)
    stream = model.call(input, tool_schemas, cancellation)
    append_model_and_block_events(stream)
    action = next_action(assembled_message)
    if action.final: commit_message_and_terminal(COMPLETED); return
    for call in schedule(action.tool_calls, concurrency_policy):
      validate_schema_and_normalize(call)
      decision = permission.check(context, tool.check_permissions(call))
      if decision.ask: persist_continuation_and_wait(call, decision)
      if decision.deny: append_tool_denial(call, decision); continue
      result = execute_once(call, decision, workspace_lease)
      commit_tool_result(result)
    state.cur_iter += 1; checkpoint(PREPARING)
  append(EXCEED_MAX_ITERS); commit_terminal(EXCEEDED_MAX_ITERS)
```

## Action 选择

- 完整 assistant message 无未完成 tool call：终止。
- 一个或多个完整 tool call：按工具声明的并发策略执行；默认有副作用工具串行。
- partial JSON、缺失 tool name 或 schema 不合法：生成结构化 tool error 回到 context，不直接执行。
- structured output 未满足 schema：在配置允许的额外 iteration 内修复；耗尽后 error，不把原文本伪装为结构化成功。
- 终止原因由 runtime 决定，不能仅解析模型自然语言“完成”。

## Permission 与 HITL continuation

`PermissionDecision` 为 `allow | deny | ask`，工具还可返回 passthrough。ASK 时保存规范化参数 hash、decision reason、建议 rule、过期时间和 continuation location。确认结果必须同时匹配 request id、session、reply、call、args hash；“本次允许”和“写入规则”分开提交。拒绝作为 tool result 反馈，允许 agent 重规划。

## 取消语义

取消 token 传播到 model adapter、tool backend、MCP client 和 artifact upload。取消请求先持久化再广播；可取消 backend 应终止子进程，不可取消远端调用标为 `cancel_pending` 并忽略迟到结果。已经跨越外部副作用 commit point 的调用不得假装回滚，应记录 `effect_unknown | effect_committed` 并进入人工恢复。

## 重试语义

- model 网络错误：只在没有提交语义 chunk 时透明重试；否则开启新 model call id，并保留前一失败事件。
- read-only tool：可用同一 idempotency key 有界重试。
- side-effect tool：只有 backend 支持幂等键或确认未开始时才能自动重试。
- permission denial、schema error、context overflow 不是网络重试；分别反馈重规划、修参或压缩。
- 每次重试记录 attempt、backoff、cause 和 trace id。

## Middleware 顺序

固定顺序建议：`before_reply -> before_reasoning -> before_model -> after_model -> after_reasoning -> before_tool -> permission -> executor -> after_tool -> after_reply`。压缩有独立 hook。middleware 能修改 context 或结果时必须记录 provenance；安全 middleware 失败默认 fail closed，观测 middleware 可配置 fail open。

## Plan、Team 与外部输入

Plan 是 `Task[]` 的持久投影，更新产生 event，不把自然语言 checklist 当唯一真相。Team worker 使用独立 session loop，通过 inbox/team tools 传递消息；leader 不直接突变 worker state。运行中用户追加输入进入 inbox，在安全 checkpoint 合并；不得与当前工具参数无锁拼接。

## 最小测试 oracle

- scripted model 依次产生 text→tool call→final，事件顺序与 context 回写完全匹配。
- 在 model stream、ASK、tool process、commit 前后分别取消，均只有一个终态。
- 同一 submit command 发送两次只创建一个 reply。
- side-effect tool 在 result append 后崩溃，恢复不再次执行。
- 达到 max_iters 发 `EXCEED_MAX_ITERS` 与 `REPLY_END`，不再调用模型。
- middleware 抛错时按类别执行 fail-open/fail-closed，不悬挂 session lease。

实现完成后还必须通过 [acceptance-tests.md](acceptance-tests.md) 的等级测试。
