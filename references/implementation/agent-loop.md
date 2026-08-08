# Agent Loop 实现算法

## 目录

- [状态机](#状态机)
- [主循环伪代码](#主循环伪代码)
- [工具批次](#工具批次)
- [取消与 Steering](#取消与-steering)
- [重试与恢复](#重试与恢复)
- [终止与验证](#终止与验证)

## 状态机

```text
QUEUED
  -> PREPARING
  -> MODEL_STREAMING
  -> MODEL_INTERPRETING
     -> COMPLETED                       (自然结束)
     -> AUTHORIZING -> WAITING_APPROVAL (需要用户)
     -> EXECUTING -> OBSERVING -> PREPARING
     -> COMPACTING -> PREPARING
  -> FAILED | CANCELLED | INDETERMINATE
```

状态迁移必须由单写者 orchestrator 提交，不允许 model adapter、tool executor 或 UI 直接修改 Turn.status。

## 主循环伪代码

```python
async def run_turn(turn_id, cancellation):
    turn = store.claim_turn(turn_id)             # lease / single writer
    emit("turn.started", turn)
    while True:
        cancellation.raise_if_cancelled()
        enforce_budget(turn)

        pending_input = store.drain_steering(turn.id)
        context = context_engine.build(
            thread_id=turn.thread_id,
            pending_input=pending_input,
            tool_catalog=tools.snapshot(),
            budget=turn.budget,
        )
        store.save_context_snapshot(context.meta)

        if context.requires_compaction:
            await compact_as_event(context)
            continue

        response = await model.stream(context, cancellation)
        normalized = await persist_model_stream(response)

        if normalized.kind == "final":
            return complete_turn(turn, "natural")
        if normalized.kind == "invalid":
            return fail_or_repair(turn, normalized.error)

        calls = validate_and_normalize_calls(normalized.tool_calls)
        results = await execute_tool_batch(turn, calls, cancellation)
        persist_results_in_original_call_order(results)
```

`context.build` 返回不可变 snapshot；模型调用期间配置变化通过下一轮新 fragment 注入，不改写已发送前缀。

## 工具批次

对每个 call：

1. 完成 tool 名称、版本和 JSON Schema 校验；
2. 规范化 path、command、URL 等 action；
3. 持久化 `tool.proposed` 和 args hash；
4. 调用 policy，得到 allow/deny/ask/amend；
5. ask 时持久化 approval 并进入 `WAITING_APPROVAL`；
6. 执行前写 intent/outbox；
7. executor 使用 capability 和 sandbox 执行；
8. 持久化恰一个最终 ToolResult；
9. 大输出转 artifact，只给模型有界摘要。

并行只允许在：工具声明可并行、资源锁不冲突、策略允许、结果顺序可确定时。持久化结果按原 tool call 顺序，使模型上下文稳定。

## 取消与 Steering

取消是状态，不只是抛异常：

- 记录 cancel requested；
- 通知模型流、tool executor、PTY 和子代理；
- 等待有界 grace period；
- 仍运行的本地进程杀进程树；
- 对未知外部副作用标 `indeterminate`；
- 最终只提交一次 `turn.completed(status=cancelled|indeterminate)`。

Steering 只追加用户 item。若模型正在流式生成，可选择排队到下一 step；若产品明确支持即时 steering，则 adapter 必须有可验证中断/续写合同。不得原地改写本轮初始用户消息。

## 重试与恢复

模型重试：仅对明确 retryable 错误，使用指数退避+jitter，并尊重 `retry_after`。重试复用 step identity，但每次网络 attempt 单独 trace。

工具重试：

- `idempotent` 可在同 args 下重试；
- `keyed` 必须复用 idempotency key；
- `non_idempotent` 在结果未知时不得自动重试；
- 本地可逆动作可用 checkpoint/transaction 回滚后重试。

进程恢复：

1. 找到无终态的 turn；
2. 检查 lease 是否过期；
3. 回放到最后持久 event；
4. 对 `proposed/authorizing` call 可继续；
5. 对 `running` call 查询 executor receipt；
6. 没有 receipt 且可能有副作用时标 indeterminate；
7. 不自动重放 PTY 输入或外部发送。

## 终止与验证

终止原因至少包括：自然结束、用户取消、策略拒绝后模型结束、最大步骤、token/cost/time 预算、不可恢复模型错误、工具错误、sandbox violation、内部错误。

验收必须覆盖：

- 无工具自然回答；
- 单工具和多工具；
- tool call 参数分片；
- approval 接受、拒绝、缩小范围、过期；
- context 达阈值后压缩并继续；
- steering 到达模型调用前、调用中和工具执行中；
- Ctrl-C 与工具完成同时发生；
- 进程在 intent 后、result 前崩溃；
- 重启后不重复不可逆副作用；
- 最大步数导致明确终态而非无限循环。

