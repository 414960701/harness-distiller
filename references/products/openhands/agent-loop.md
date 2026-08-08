# OpenHands-like Agent Loop 实现规格

## 目录

- [状态机](#状态机)
- [启动与初始化](#启动与初始化)
- [单步算法](#单步算法)
- [并行工具](#并行工具)
- [确认与阻断](#确认与阻断)
- [终止与失败](#终止与失败)
- [取消与恢复](#取消与恢复)
- [重试和预算](#重试和预算)
- [伪代码](#伪代码)
- [实现检查](#实现检查)

## 状态机

内部 conversation 状态采用：

`idle -> running -> {waiting_for_confirmation, paused, finished, error, stuck}`。

`waiting_for_confirmation -> idle/running` 由 approve/reject 触发；`paused -> running` 由显式 resume/run 触发。

对共享 thread/turn 协议的映射：

| Conversation status | Turn 投影 |
|---|---|
| idle | 无活动 turn 或 queued |
| running | running |
| waiting_for_confirmation | waiting_approval |
| paused | interrupted |
| finished | completed |
| error | failed |
| stuck | failed，error.code=`stuck` |
| deleting | thread deleting，不是 turn 终态 |

状态终止必须有事件证据；只改内存 enum 不算完成。

## 启动与初始化

1. 验证 agent、LLM profile、tools、workspace、budget 和 confirmation policy。
2. 获取 conversation 单写者 lease；进程内模式获取 FIFO/actor lock。
3. create-or-resume state，加载 EventLog 与 active leaf。
4. 懒加载 plugins、skills、MCP 和 file agents，冻结本 run capability snapshot。
5. 若 active branch 尚无 SystemPromptEvent，则在首条用户消息前追加。
6. 检查未匹配 ActionEvent；仅对已知未执行/中断项追加合成错误。
7. 创建 cancellation token、iteration/budget counter 和 root trace span。
8. 追加 status running，并开始循环。

System prompt 分静态 cacheable 与动态 context；动态部分可以包含 workspace、repo、secret 名称/描述，但绝不能包含 secret 值。

## 单步算法

每个 step：

1. 检查 cancel、pause、lease、迭代和预算。
2. 取 active branch，构造 View；确保 action/observation 配对和 condenser batch 原子性。
3. 若超 context 阈值，运行 condenser 并追加 condensation event，再重建 View。
4. 将 View 转为 provider-neutral messages，带 frozen tool specs。
5. 流式调用 LLM；token delta 只用于体验，完整 response 才可 dispatch。
6. response 为纯文本时追加 MessageEvent；若无 Finish tool，按 profile 决定继续或完成。
7. response 含 tool calls 时逐项验证 schema，生成稳定 ActionEvent 和 tool_call_id。
8. 执行 PreToolUse hook、安全分析与 confirmation decision。
9. 对可执行 action 调度工具；把每个结果转成 ObservationEvent 或 typed AgentErrorEvent。
10. 按原 action 顺序追加结果，更新 cost/stats/stuck detector。
11. Finish action 位于 batch 中时丢弃其后 action；Finish 未阻断则完成或进入 critic refinement。
12. 无终止条件则下一 step。

模型异常、tool 异常和 protocol 异常必须分类，禁止把 Python traceback 当 Observation success。

## 并行工具

同一次模型 response 的多个 action 可以并行，但必须满足：

- action 先全部 durable，再 dispatch；
- 每个 action 一个独立 result slot；
- 只并行声明 `parallel_safe` 且资源集合不冲突的工具；
- 文件写、terminal session、conversation mutation 默认串行或资源加锁；
- executor 完成顺序不能改变 EventLog 的确定合并顺序；
- Finish 截断其后 action；
- cancel token 在 dispatch 前和工具内部都检查；
- 迟到结果只在 writer token 仍有效且 action 未终结时提交。

`设计综合`：给 ToolDefinition 增加 `resource_keys(args)`、`idempotency_class` 和 `cancel_mode`，避免只靠工具名称判断冲突。

## 确认与阻断

Action 路径：schema validate → hook → risk analyzer → confirmation policy → enforcement → execute。

- hook block：追加 `UserRejectObservation(rejection_source=hook)`；
- policy allow：进入 workspace enforcement；
- policy confirm：追加 durable request，状态 waiting_for_confirmation，停止派发；
- user reject：追加模型可见拒绝 observation；
- approve：重新验证 path、network、secret 和 writer token，再执行；
- amend：产生新 action/request id，不修改原 action；
- 断线：请求保持 pending，不自动批准。

SecurityAnalyzer 可以失败。失败策略由 profile 明确：安全 profile fail closed；开发 profile 可以带醒目标记降级，但不能冒充已分析。

## 终止与失败

终止来源：

- Finish tool 成功；
- profile 允许纯文本 final；
- 用户 pause/interrupt；
- max iteration、budget 或 deadline；
- stuck detector 命中；
- unrecoverable model/tool/state error；
- lease/ownership 丢失。

每个 run 恰有一个 `RunOutcome`：`completed`、`paused`、`failed`、`stuck`、`ownership_lost`。

Finish 之后同 response 的 tool call 不执行。Critic 要求继续时追加新的用户角色 feedback event，再进入下一 step，而不是撤销 Finish 历史。

## 取消与恢复

同步 `run()` 的 pause 只在 step 边界生效；异步 `arun()` 的 interrupt 必须取消 LLM await，并设置工具 cancellation token。

取消传播：Conversation → parallel batch → tool executor → workspace process/container/remote lease → child conversation。

工具线程可能晚于 async task 结束；token 必须保持可观察，不能在 `arun` finally 中过早替换。

中断后发现 orphan ActionEvent 时：

- 有 durable receipt：恢复/补 Observation；
- 明确未执行：追加 interrupted error；
- 外部副作用未知：追加 `unknown_effect`，要求人工确认；
- 禁止不带 idempotency key 自动重试。

## 重试和预算

- provider 429/5xx 使用有界指数退避，尊重 retry-after；
- invalid request、context shape、auth 不盲重试；
- context overflow 允许一次 condenser 后重试；
- tool schema failure 返回给模型修正，不执行；
- workspace transport 重试只针对只读或带 receipt/idempotency 的操作；
- iteration 每次模型 step 增一；cost/budget 以 provider usage 或保守估计累加；
- 子会话预算从父级分配，不能无限生成。

重试保持同 `causation_id`，每个 attempt 有不同 `attempt_id`。

## 伪代码

```python
async def run(conv, cancel):
    async with conv.writer_lease() as lease:
        await conv.prepare()
        while True:
            guard_limits_cancel_and_lease(conv, cancel, lease)
            view = await build_atomic_view(conv.active_branch())
            if conv.condenser.should_condense(view):
                await append(await conv.condenser.condense(view))
                continue
            response = await llm.complete(view.messages, conv.tools, cancel)
            dispatch = await agent.dispatch(response)
            await append_all(dispatch.events)
            if dispatch.final_text and not dispatch.actions:
                return await finish_by_profile(dispatch.final_text)
            batch = await prepare_actions(dispatch.actions)
            if batch.needs_confirmation:
                return await wait_for_confirmation(batch)
            results = await execute_parallel_safely(batch, cancel, lease.token)
            await append_results_in_action_order(results)
            if batch.has_finish and not batch.finish_blocked:
                return await finish_or_refine(batch)
```

## 实现检查

- 状态、终止、取消、重试均有 typed event 与黑盒测试。
- 系统事件一定先于首条用户事件。
- action/observation 在 context view 中不被压缩拆开。
- 并行 action 的持久化顺序可重放。
- confirmation 前无副作用，approval 后再做 enforcement。
- cancel 后不派发新工具，迟到结果不能复活已终结 run。
- resume 不重复 committed 副作用。

可执行 oracle 见 [acceptance-tests.md](acceptance-tests.md)。
