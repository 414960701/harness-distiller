# Codex-like Agent Loop 实现规范

## 目录

1. 目标与边界
2. 状态机
3. 核心数据结构
4. 主循环伪代码
5. 工具执行
6. Steering 与排队输入
7. 重试与退避
8. 取消与终止
9. 压缩和预算
10. 并发与不变量
11. 测试钩子

## 目标与边界

`公开事实`：Codex 公开源码的 turn runtime 会在模型采样、response item 处理、工具执行与再次采样之间循环。
`设计综合`：下述状态机将公开结构收敛为可移植实现合同，语言可用 Rust、Go、TypeScript 或 Python。
本循环不负责绘制 UI，也不直接访问数据库、shell 或模型 SDK；所有外部能力通过端口注入。

## 状态机

```text
CREATED -> PREPARING -> SAMPLING -> APPLYING_RESPONSE
              ^             |              |
              |             |              +-> WAITING_APPROVAL
              |             |              +-> EXECUTING_TOOLS
              |             |              +-> COMPACTING
              |             |              +-> FINALIZING
              +-------------+----------------------+

任意非终态 --interrupt--> CANCELLING -> INTERRUPTED
任意非终态 --fatal-------> FAILED
FINALIZING ----------------> COMPLETED
```

状态转换必须由单一 turn actor 串行提交。
模型流、工具进程和客户端输入可以并发产生消息，但不能并发改写 turn state。
每次转换先 durable append event，再向订阅者广播。

## 核心数据结构

```text
TurnRuntime {
  thread_id, turn_id, status, step_no,
  input_queue, pending_tool_calls, active_processes,
  context_checkpoint, token_budget,
  cancellation_token, retry_budget,
  last_event_seq, terminal_once
}

StepSnapshot {
  model_config, instructions, visible_history,
  tool_specs, permission_profile, sandbox_profile,
  cwd, workspace_revision, context_version
}
```

`StepSnapshot` 在一次模型采样开始后不可变。
steering、MCP 刷新或配置变化进入下一 step，避免同一请求前后 schema 漂移。
`terminal_once` 用 compare-and-set 保证只提交一次终态。

## 主循环伪代码

```text
run_turn(request):
  append(turn.started)
  state = PREPARING
  enqueue(request.user_input)

  while not terminal:
    if cancelled(): return finish_interrupted()
    drain_control_messages()
    persist_queued_user_items()

    if should_compact():
      state = COMPACTING
      compact_with_checkpoint_or_fallback()
      continue

    snapshot = build_step_snapshot()
    validate_context_and_tool_pairs(snapshot)
    state = SAMPLING

    attempt = 0
    loop:
      result = model.stream(snapshot, cancellation_token)
      if result.ok: break
      if not retryable(result) or attempt >= retry_budget:
        return finish_failed(classify(result))
      emit(model.retry_scheduled, attempt, delay)
      await cancellable_backoff(delay)
      attempt += 1

    state = APPLYING_RESPONSE
    disposition = consume_stream_and_persist_items(result)

    if cancelled(): return finish_interrupted()
    if disposition.has_tool_calls:
      state = EXECUTING_TOOLS
      execute_calls(disposition.calls)
      continue
    if input_queue.not_empty or disposition.requires_followup:
      state = PREPARING
      continue
    if disposition.final_message:
      state = FINALIZING
      return finish_completed()
    return finish_failed(PROTOCOL_INCOMPLETE_RESPONSE)
```

模型 stream 的 delta 可以先广播，但 completed item 必须在聚合内容持久化后发出。
若进程在 delta 后崩溃，恢复时把未闭合 item 标记为 interrupted，不伪造 completed。

## 工具执行

每个工具调用先规范化为 `ToolInvocation`：`call_id`、名称、参数摘要、risk、idempotency class。
router 先验证 schema，再查询 policy，然后交给 enforcement adapter。
纯读工具可以按配置并发；写工具默认串行。
并发调用的 result 按完成顺序落事件，但写回模型历史时必须使用稳定 call id 配对。

```text
execute_one(call):
  ensure_unique(call.call_id)
  append(tool.started)
  decision = policy.evaluate(call, step_snapshot)
  if decision.ask: await durable_approval(call)
  if decision.deny: append(tool.completed, denied); return
  lease = executor.prepare(call, sandbox_profile)
  mark_effect_intent(call, lease.idempotency_key)
  result = executor.run(lease, cancellation_token)
  persist_effect_receipt(result)
  append(tool.completed, normalize(result))
```

副作用意图与执行回执解决“执行成功但 result 未写入”的恢复歧义。
无法支持幂等的写操作在不确定状态下必须转人工复核。

## Steering 与排队输入

steering 只能作用于 running turn，并记录 `causation_id`。
若当前处于 `SAMPLING`，实现可选择中止采样并在下一 step 合入，或让当前采样结束后合入。
策略必须稳定且发出 `turn.steering_accepted`，客户端不能靠超时猜测。
若处于写工具临界区，新输入只排队，不修改已批准调用参数。
排队输入按服务端 sequence 排序，并作为 user item 持久化。
当前 turn 已终止时，steer 返回 conflict，并建议客户端创建新 turn。

## 重试与退避

仅对瞬时模型网络错误、明确可重试的 provider 错误和未开始副作用的 executor 错误自动重试。
schema 不匹配、权限拒绝、上下文超限且压缩失败、确定性编译错误不得原样重试。
退避使用指数增长加 jitter，并受 turn deadline 限制。
每次重试发出原因、attempt 和下次时间，但不泄露凭据。
provider 返回 partial stream 后是否重试取决于 response id 和幂等能力；不能把两段内容拼成一个假完成 item。
工具重试必须复用逻辑 call id 与 idempotency key。

## 取消与终止

取消令牌形成树：turn -> model request、tool tasks、process group、subagents。
接收 interrupt 后立即：

1. append `turn.interrupt_requested`；
2. 禁止启动新的模型请求和工具；
3. 取消等待中的退避与审批；
4. 向活动进程组发送温和终止；
5. 超过 grace period 后强制终止；
6. 收集已完成回执；
7. 关闭未完成 item；
8. CAS 提交 `turn.interrupted`。

客户端断线不等同于取消，除非该入口显式采用 disconnect-cancels 策略。
runtime shutdown 先停止接收新 turn，再给活动 turn 检查点或中断。

## 压缩和预算

压缩触发器包括模型上下文阈值、turn 前预算检查和模型超限恢复。
压缩前保存 `context_checkpoint` 和当前 rollout offset。
摘要必须包含当前意图、计划、已改文件、失败命令、未决审批和验证状态。
压缩后重建 tool call/result 配对，并使 world-state baseline 失效后完整重注入。
压缩失败先执行确定性裁剪；仍超限则失败，不允许无限递归压缩。
token、时间、工具次数和费用预算统一作为可观察 resource budget。

## 并发与不变量

- 一个 thread 同时最多一个前台 turn；需要并行时 fork thread 或子代理。
- turn actor 是状态唯一写者；worker 只能返回消息。
- 完成事件一定晚于对应 durable state。
- 终态后拒绝新的 item、tool start 和 model retry。
- tool call/result 在模型可见历史中一一配对。
- approval 不能修改已签名 invocation，只能批准、拒绝或要求重新构造。
- snapshot 建立后配置变化只影响下一 step。
- 所有后台任务都持有父 cancellation token 和 join handle。

## 测试钩子

实现应注入 fake clock、deterministic id、scripted model、fake executor 和 crash point。
关键 crash point：turn started 后、tool intent 后、side effect 后、result append 前、terminal append 前。
property test 应随机交错 delta、steering、approval、interrupt 和 disconnect。
model fixture 应覆盖文本结束、多工具、畸形工具参数、partial stream 和 context overflow。
完整分级场景见 [acceptance-tests.md](acceptance-tests.md)。
协议对象见 [protocol-state.md](protocol-state.md)，恢复算法见 [persistence-recovery.md](persistence-recovery.md)。
固定 commit 的公开源码入口见 [sources.md](sources.md)。
