# LangGraph 执行循环

## 目录

- [循环状态](#循环状态)
- [初始化](#初始化)
- [Superstep](#superstep)
- [Task 执行](#task-执行)
- [更新与路由](#更新与路由)
- [重试与错误](#重试与错误)
- [中断与恢复](#中断与恢复)
- [取消与终止](#取消与终止)
- [参考伪代码](#参考伪代码)
- [实现陷阱](#实现陷阱)

## 循环状态

运行时至少维护：compiled graph、input/output channels、channel values、channel versions、versions seen、step、task table、pending writes、checkpoint config、stream sinks、durability、retry/timeout policy、interrupt set、cancel token、Store/Runtime context。

这些是 durable graph loop，不等同于 LLM 的“思考-工具”循环。模型节点只是 task 的一种实现。

## 初始化

1. 校验 config、thread id、checkpoint namespace 与 durability。
2. 若给出 checkpoint id，加载该历史点；否则加载 thread head。
3. 应用迁移与 pending writes，恢复 task result/error/interrupt。
4. 对普通 input 写入 input channels；对 `Command(resume/update/goto)` 走 control path。
5. 保存或安排 input checkpoint，产生初始 stream/state snapshot。
6. 计算第一批可运行 task，并检查 recursion/superstep limit。

无 checkpointer 可执行无状态图，但 interrupt、历史、time travel 和跨调用 thread state 不成立。

## Superstep

每一 superstep 遵守不可打乱的三阶段：

- **Plan**：比较 channel version 与 node 的 versions seen，构造 pull/push tasks。
- **Execution**：所有选中 task 读取本步起始快照，并发执行，写入各自 buffer。
- **Update**：只对已成功/可提交 task 的 writes 调用 channel reducer，原子推进版本。

同一步 task A 的 write 不能被 task B 读到。若要顺序可见，必须进入下一步或合并成同一 node。

## Task 执行

- task identity 由稳定 id、name、path 与触发来源构成。
- 调用前冻结 retry、timeout、runtime context、writer 与 child namespace。
- node 返回普通 mapping 时转换为 channel writes。
- node 返回 `Command` 时拆出 state update、goto/Send、parent target 与 resume。
- `Send` 创建下一步动态 task，参数可不同于全局 state。
- custom stream 在 task 执行中发出，但 durable state 只在 update 阶段生效。
- task 的外部副作用不能仅依赖内存中的“已经调用”布尔值。

## 更新与路由

- 按 channel 收集 update；空 update、单 update、多 update 分别执行 channel 合同。
- reducer 应具有可测试的顺序/交换/结合约束；不要假设所有 reducer 都交换。
- 成功 update 后增加 channel version，并记录触发 node 已见版本。
- branch/conditional edge 根据已提交结果生成下一步触发。
- waiting edge 等所有指定前驱满足后再调度 join node。
- `Command(goto=...)` 增加动态目标，但不会隐式取消同一步已计划任务。
- `Command.PARENT` 必须跨 namespace 冒泡给最近父图处理。

## 重试与错误

- retry policy 根据异常类型、attempt、backoff、jitter 和 max attempts 判定。
- 失败尝试产生的未提交 writes 必须丢弃；下一 attempt 使用同一 committed 输入。
- task timeout 与 run timeout 分开；timeout 之后迟到 writes 不得提交。
- retry exhaustion 形成结构化 task error，按 error handler 或 graph failure 处理。
- sibling task 是否取消取决于失败类别；interrupt 与普通 error 不得混淆。
- checkpoint/persistence 错误不能伪装成 node 错误。
- 对外部 non-idempotent action 的自动重试必须带 idempotency key/receipt，否则进入人工 reconcile。

## 中断与恢复

- `interrupt(value)` 首次执行抛出内部 control exception，并持久化 pending interrupt。
- interrupt id 应对同一 task/path/call position 稳定。
- 客户端用 `Command(resume=value)` 或 id→value mapping 恢复。
- 恢复时节点从开头重跑；scratchpad 按调用顺序返回已消费 resume value。
- 节点内多个 interrupt 不能在重构后改变调用顺序，否则历史 resume 可能错配。
- interrupt 之前的副作用必须幂等、缓存结果或移到 interrupt 后。
- subgraph interrupt 向父图 surface，但 child namespace 与 state 必须保留。

## 取消与终止

终止类别至少分：

- `completed`：没有下一 task，输出 channels 可投影；
- `interrupted`：存在待恢复 interrupt，thread 仍可继续；
- `failed`：不可处理错误或 retry exhaustion；
- `cancelled`：外部取消已传播到 task/child；
- `limit_exceeded`：recursion/superstep 上限；
- `indeterminate`：设计综合层无法确认外部副作用是否提交。

取消 token 必须向并行 task 与子图传播；迟到 task result 不能写入已取消 run。取消不是 retry，除非调用者显式开始新 run。

## 参考伪代码

```text
loop = restore_or_initialize(input, config)
while true:
  tasks = plan(loop.channels, loop.versions_seen, loop.pending_sends)
  if tasks.empty: return COMPLETED
  if step_limit_hit: return LIMIT_EXCEEDED
  results = run_concurrently(tasks, retry, timeout, cancel)
  persist_task_writes_if_enabled(results)
  if results.has_interrupt: checkpoint(); return INTERRUPTED
  if results.has_unhandled_error: checkpoint_error(); return FAILED
  writes = collect_committable_writes(results)
  apply_channel_reducers_atomically(writes)
  checkpoint_according_to_durability()
  emit_structured_step_events()
```

## 实现陷阱

- 直接共享 mutable state 会破坏 BSP 与 replay。
- 用日志推测 pending task 会丢失 task identity。
- 在 reducer 中执行网络调用会令 replay 不确定。
- 把 interrupt 当错误重试会反复请求审批。
- `async` durability 不等于副作用 exactly-once。
- checkpoint 成功与 UI 收到事件是两个独立确认面。
- 同步与异步实现若使用不同 reducer 顺序，会产生不可迁移状态。
