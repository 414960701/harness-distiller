# OpenCode-like Agent Loop

## 目录

- [循环单位](#循环单位)
- [状态机](#状态机)
- [单步算法](#单步算法)
- [工具生命周期](#工具生命周期)
- [重试与压缩](#重试与压缩)
- [取消与并发](#取消与并发)
- [终止条件](#终止条件)
- [故障注入点](#故障注入点)

## 循环单位

OpenCode 的可观察单位是 session 内的一次 prompt admission，内部可能执行多个 provider step 和工具。不要把每个 HTTP request、每个 tool call 或每段 token 当成独立 turn。canonical 实现用 `SessionDrain(session_id)` 串行消费已持久化 input。

每次 admission 先落库：用户 message ID、prompt parts、delivery、agent/model、location、时间。之后启动或唤醒 drain。API 可以立即返回 admitted receipt；等待型 API 只是订阅同一终态，不能启动第二套 loop。

## 状态机

```text
idle -> admitted -> preparing -> streaming
                         |          |
                         |          +-> awaiting_permission -> executing_tool
                         |                                ^          |
                         +-> compacting ------------------+          |
                                    |                               |
                                    +-------------------------------+
streaming/executing_tool -> retry_wait -> preparing
streaming/executing_tool -> cancelling -> cancelled
streaming -> completed | failed
```

`status` 是 projection，可由 durable events 重建。所有 terminal transition 只允许一次。`awaiting_permission` 不等于 idle；新输入按 delivery 规则处理。

## 单步算法

1. 事务读取 session、pending input、context epoch 和最新 completed projection。
2. 获取 single-writer lease；同进程可用 mutex，跨进程需 owner/epoch。
3. 冻结 `StepContext`：agent、model、system/instructions、messages、tools、permission rules、location、abort signal。
4. 若超预算，先执行 compaction；compaction 本身记录为 message/event。
5. 持久化 assistant message 与 `step.started`，随后调用 provider stream。
6. 将 provider chunk 归一成 text/reasoning/tool/start/finish/error LLMEvent。
7. processor 更新 typed Part：delta 可广播，完整值与 tool state 持久化。
8. tool call 先校验 schema，再 permission.ask，后 execute；结果送回同一步后续模型上下文。
9. provider 给出 stop/end-turn 时写 step finish、usage、cost、snapshot/diff。
10. 若还有 tool-result 需要模型继续，则下一 step；否则写终态并释放 lease。

伪代码：

```text
while budget.steps > 0 and not cancelled:
  ctx = freeze_step_context()
  if needs_compaction(ctx): compact_once(); continue
  stream = provider.stream(ctx)
  result = processor.consume(stream, execute_tool)
  if result == CONTINUE: continue
  if result == COMPACT: compact_once(); continue
  settle(result); break
```

## 工具生命周期

工具状态严格为 `pending -> running -> completed|error`。pending 保存 raw/parsed input；running 保存 start、title、metadata；completed 保存 output、attachments、end；error 保存稳定错误码和安全消息。

同一 `call_id` 的 execute 只能发生一次。provider 断流后若状态 completed，重试时把结果作为历史，而不是重跑。执行前记录 intent；有副作用工具在 productive 级增加 receipt/hash/idempotency key。

并行 tool call 只在声明 `parallel_safe` 且 path/effect scope 不冲突时开启。否则保持序列执行；shell、edit、write、apply-patch 默认不并行修改同一 workspace。

## 重试与压缩

重试策略分类：认证/内容过滤/参数错误不重试；429、明确 retryable、5xx、暂时网络故障可重试。优先使用 `retry-after-ms`/`retry-after`，否则指数退避并封顶。每次 retry 产生 RetryPart/status，取消可以中断等待。

context overflow 不直接做相同请求重试。先 prune 旧 tool output，再用专用 compaction prompt 总结旧 turns，保留最近 tail 与未完成状态。summary 失败时减小附件/工具输出或明确终止；不得删除最新用户输入。

## 取消与并发

`cancel(session_id)` 设置 durable/intention state，触发 provider abort，拒绝新 tool start，终止当前进程组和派生 background job。已经进入原子文件 rename/DB commit 的临界区要完成或回滚，再报告 cancelled。

同 session 第二个 foreground drain 返回 conflict 或加入 inbox；不同 session 可并发，但共享 workspace 写操作需要 workspace lease/冲突检查。父子 session 取消沿明确 parent/child 关系传播，不能靠标题匹配。

## 终止条件

- provider finish 为 stop/end-turn 且没有未结 tool；
- 用户取消或 server shutdown deadline；
- 非重试错误；
- step/retry/tool/elapsed budget 耗尽；
- 连续相同工具与输入达到 doom-loop 阈值；
- permission 拒绝后模型选择结束，或策略规定立即结束；
- compaction 仍无法满足 context window。

终态记录 `completed|failed|cancelled`、finish reason、error、usage、cost、最后 event seq。客户端显示只读取该记录。

## 故障注入点

测试需在 input admitted、step started、tool intent、process spawned、tool receipt、part completed、step ended、terminal committed、broadcast 前后 kill。恢复断言：sequence 单调、terminal 唯一、completed tool 不重跑、pending/running tool 进入可诊断 reconciliation、client 能 resync。

源码依据见 [sources.md](sources.md) 的 prompt、processor、retry、compaction 与 run-state；single-writer lease 的跨进程形式属于 `inference`。
