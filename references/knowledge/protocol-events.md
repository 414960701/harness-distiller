# Protocol 与事件

## 职责与非目标

Protocol 为 headless runtime 与 CLI、IDE、桌面、SDK 定义版本化 command、response、event、error 与 capability negotiation。
它传递领域事实，不规定 UI 颜色、布局、模型 provider wire schema 或数据库物理表。
客户端只能提交 command，不能直接修改 thread/turn/item 投影。
事件是已发生事实，不能把瞬时 UI action 伪装成 durable event。

## 信封与对象

```text
CommandEnvelope {
  protocol_version, request_id, method, params,
  idempotency_key?, client_info, auth_context?
}
EventEnvelope {
  protocol_version, event_id, thread_id, turn_id?,
  sequence, type, payload, correlation_id?, causation_id?, timestamp
}
Error { code, message, retryable, safe_details?, request_id }
```

领域对象是 `Thread`、`Turn`、`Item`；`Event` 只表达它们的状态变化或增量。
thread 内 sequence 单调递增；event id 用于跨重连去重。
delta 可丢弃重建，completed item 必须包含 canonical 完整内容。
未知可选字段应忽略，未知强制 capability 必须拒绝初始化。

## 命令与生命周期

最小命令集：`initialize`、`thread.start/read/list`、`turn.start/interrupt`、`subscription.open/close`。
能用级增加 `thread.resume/fork`、`turn.steer`、`approval.resolve` 和进程输入。
所有有副作用 command 支持 idempotency key；同 key 不同参数返回 conflict。
command 被接受后的业务失败通过 terminal event 表达，不混同 transport error。
快照包含 `last_sequence`，订阅只应用更大的事件。

## 四级增量

| 等级 | 新增能力 | 不变量 |
|---|---|---|
| 能跑 | 进程内总线、基础 command/event | id、sequence、单终态 |
| 能用 | JSON-RPC/stdio/socket、重放、快照 | canonical event 与稳定 error code |
| 顺手 | 多客户端、断线续传、背压、steering | 至少一次投递和客户端去重 |
| 好用 | 远程认证、版本协商、限流、审计、SDK | capability gate 与兼容窗口 |

transport 可以更换，领域 event 与顺序语义不能随 transport 分叉。

## 直接升级与回滚

升级顺序：冻结 golden schema → 增加版本/能力握手 → 双读新旧字段 → 启用新事件 → 停止旧写入。
新增 event 必须让旧客户端能忽略或投影为通用 item。
破坏字段含义、枚举语义或顺序保证时提升 major，不能只改文档。
回滚服务端前停止写入新 major；历史未知 payload 原样保留，不做有损降级。
客户端回滚用 `after_sequence` 恢复，不允许以本地缓存覆盖服务端 head。

## 失败模式、背压与安全

- sequence gap：暂停投影并 resync，不能静默跳过；
- 重复事件：按 event id 去重，handler 必须幂等；
- 慢订阅者：有界队列溢出后发 resync_required，不阻塞 runtime；
- 中途断线：快照加尾部事件恢复，客户端断线默认不取消 turn；
- schema mismatch：初始化失败并返回支持版本，不无限重连；
- 恶意 payload：限制深度、大小、枚举和 artifact 引用；
- 跨 thread 读取：在 command handler 鉴权，订阅 token 不可复用；
- error detail：不得包含 secret、完整环境变量或未脱敏 provider payload。

## 可执行验收

- golden JSON/MessagePack fixture 在语言 SDK 间往返不丢字段；
- 重放 10 万事件与 snapshot+tail 得到相同投影 hash；
- 随机重复、丢弃 delta、重连后 transcript 与终态不变；
- sequence gap 触发一次 resync，无重复 tool card；
- 旧客户端遇到新 item 显示 generic item 且继续消费后续事件；
- 同 idempotency key 重复 turn.start 只创建一个 turn；
- 未认证或跨租户订阅不能观察 event 是否存在；
- 慢客户端被隔离，agent loop 延迟不随其队列增长。

## 证据与设计综合

`公开事实`：Codex app-server、Agent Client Protocol 与多个开源 runtime 展示了 command/notification 和增量事件边界。
`设计综合`：本信封字段与升级顺序是跨产品参考，不复制某一协议的品牌字段或 wire 格式。
持久化顺序见 [state-persistence.md](state-persistence.md)，表面投影见 [cli-tui.md](cli-tui.md) 与 [ide.md](ide.md)，观测字段见 [observability.md](observability.md)。
