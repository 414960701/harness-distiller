# Observability

## 职责与非目标

让开发者和用户解释一次 turn 做了什么、为什么停下、耗费多少、哪里失败。Observability 不保存模型私有推理，也不允许日志成为第二套事实状态。

## 统一关联

所有事件与 trace 使用 `thread_id`, `turn_id`, `item_id`, `tool_call_id`, `trace_id`, `span_id`, `correlation_id`。UI timeline、内部 trace、eval replay 消费同一领域事件，避免三套互相矛盾的生命周期。

```yaml
Span:
  name: model.call|tool.execute|policy.decide|context.build|store.commit
  start/end: timestamp
  status: ok|error|cancelled
  attributes: bounded low-cardinality map
  links: [trace/span refs]
```

## 指标

- turn：成功率、终止原因、持续时间、恢复率；
- model：首 token、总延迟、tokens、cache hit、429/5xx；
- context：各层 token、压缩频率、检索命中；
- tool：队列/执行时间、错误、取消、approval 等待；
- policy：allow/deny/ask/amend、风险、过期；
- executor：sandbox failure、资源、网络阻断；
- product：任务完成、artifact validation、用户回退。

高基数字段放 trace/log，不放 metrics label。

## 脱敏

默认删除 secret、token、cookie、完整 prompt、文件全文、终端环境和个人数据。Tool 参数按 schema 标注敏感字段；未知对象采取 allowlist 序列化。调试模式仍不能记录原始凭据。

## 四级增量

- runnable：结构化日志、turn/tool id、错误类别；
- usable：trace、usage、context/tool 指标、用户 timeline；
- productive：成本画像、eval trace、告警与采样；
- polished：SLO、租户隔离、合规导出、事故回放与保留策略。

## 直接升级

先稳定事件 id，再引入 trace exporter；为旧事件补 projection，不改写事实。启用生产采样前验证脱敏。回滚 exporter 不应影响 runtime。

## 失败模式

日志泄密、指标基数爆炸、跨线程 trace 关联错误、时钟漂移、exporter 阻塞 agent loop、采样丢掉唯一失败轨迹。

## 验收

1. 从 trace 定位一次失败工具和对应 approval；
2. 关闭 exporter 仍能完成 turn；
3. secret corpus 不出现在日志/trace；
4. 重启恢复的 span 使用 link 而非伪造连续 parent；
5. 指标 label 基数有上限；
6. UI timeline 与事件回放结果一致。

证据类型：设计综合；产品映射见 Codex/QoderWork dossier 与 `references/implementation/protocol.md`。

