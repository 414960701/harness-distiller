# Reliability

## 职责

为模型、工具、存储、事件传输和远程执行定义 timeout、retry、idempotency、backpressure、cancellation、circuit breaker 与 compensation。

## Operation contract

```yaml
Operation:
  id: string
  deadline: timestamp
  retry_policy: {max_attempts, backoff, retryable_codes}
  idempotency: idempotent|keyed|non_idempotent
  cancellation: cooperative|process_tree|unsupported
  side_effect: classification
  status: pending|running|succeeded|failed|cancelled|indeterminate
```

未知执行结果必须是 `indeterminate`，不能自动当失败重跑。

## 背压

限制 model streams、tool progress、event subscribers、background processes 和 subagents。队列满时返回 overloaded/retry-after，不无限占内存。慢 UI 不应阻塞 runtime 持久化。

## 四级增量

- runnable：deadline、有限重试、最大 steps；
- usable：取消、幂等、resume、outbox；
- productive：queue、checkpoint、circuit breaker、后台任务；
- polished：lease/fencing、容量保护、灾备、SLO 与多区域策略。

## 直接升级

先给动作加稳定 id 与副作用分类，再开放自动重试。引入分布式 worker 前增加 lease/fencing。回滚时保留 idempotency 记录，不能因降级清空。

## 失败模式

重试风暴、timeout 后进程继续、取消与完成竞态、迟到事件改变终态、队列饿死交互请求、circuit 永不恢复、恢复时重复外部发送。

## 验收

- 429/5xx 使用 jitter 并尊重 retry-after；
- Ctrl-C 杀完整进程树；
- timeout 与成功同时发生仍只有一个终态；
- 重复 command/tool receipt 不重复副作用；
- 慢 subscriber 不阻塞 turn；
- worker lease 过期后的迟到写被 fencing 拒绝；
- 磁盘/数据库不可用时 fail 明确且可恢复。

证据类型：设计综合；恢复算法见 `references/implementation/storage.md`。

