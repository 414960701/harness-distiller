# Model Adapter

## 职责与非目标

Model Adapter 把 provider 特有请求、流、工具调用、usage、缓存和错误映射为统一但不失真的接口。
它负责能力协商和字段转换，不负责上下文选择、工具执行、业务重试策略或展示。
统一接口不是“最小公分母”；provider 独有能力通过 capability 与 extension 字段保留。
adapter 不得伪造模型支持的模态、上下文窗口、structured output 或缓存语义。

## 接口与 schema

```text
ModelCapabilities {
  modalities, max_context_tokens, tool_calling,
  parallel_tool_calls, structured_output, reasoning_summary,
  prompt_cache, resumable_stream, usage_reporting
}
ModelRequest {
  request_id, model, context_snapshot, tool_catalog_version,
  response_schema?, reasoning?, cache?, deadline, idempotency_key?
}
ModelDelta = Text | ReasoningSummary | ToolCallStart |
  ToolArgumentsDelta | Usage | Completed | ProviderExtension
ModelError { category, retryable, retry_after?, safe_detail, provider_code? }
```

工具参数增量必须按 call id 聚合并在执行前做完整 JSON/schema 校验。
request 绑定不可变 snapshot，adapter 不在流中悄悄追加新上下文或工具。
原始响应可在受控调试存储中引用，但进入事件前必须脱敏和规范化。

## 错误与终止映射

稳定类别至少包括：authentication、permission、rate_limited、unavailable、timeout、context_overflow、invalid_request、content_blocked、protocol、cancelled。
provider 的 stop reason 映射为 `final_text`、`tool_calls`、`length`、`blocked`、`cancelled` 或 `unknown`。
收到 completed 后的 delta 视为协议错误并记录，不改变已提交终态。
partial stream 是否可续传由 capability 决定；不支持时关闭旧 item，再发新请求。

## 四级增量

| 等级 | 新增能力 | 不变量 |
|---|---|---|
| 能跑 | 一个 provider、文本、单工具调用 | request/delta/error 稳定类型 |
| 能用 | 多 provider、流式、usage、限流退避 | snapshot 与 call id 不变 |
| 顺手 | 路由、fallback、缓存、多模态、结构化输出 | capability gate 和无损 extension |
| 好用 | 区域/租户策略、成本质量自适应、合规审计 | 可解释选择、稳定错误和 trace |

新 provider 只新增 adapter 和 fixtures，不修改 agent loop 领域对象。

## 直接升级与回滚

先冻结 provider-neutral golden fixtures，再引入 capability negotiation，最后启用路由或 fallback。
直接升级好用时，旧 model id 必须解析到稳定 alias 或显式迁移。
fallback 只在没有未确认 partial output、或 provider 支持 continuation 时自动发生。
回滚时关闭新 capability flag，继续保留未知 extension 原文，避免破坏历史重放。
缓存 key 版本变化采用双读或自然失效，不把旧缓存误当新模型响应。

## 失败模式与安全

- 参数 delta 断包：等待闭合或以 protocol error 结束，不能执行半个 JSON；
- provider 重复 delta：按 response/item offset 去重；
- 无 tool id：生成本地 id 时保留原始关联并限制重试；
- 429/503：遵守 retry-after、jitter 和 turn deadline；
- fallback 模型能力更弱：重新协商或拒绝，不能静默丢工具；
- 日志泄露 prompt/密钥：分层脱敏，认证头永不进入事件；
- 模型别名漂移：记录解析后的 provider/model revision 以便审计。

模型输出、tool arguments 和 usage 都是不可信输入，必须做大小、类型和数值边界校验。

## 可执行验收

- 将相同 fixture 经两个 provider adapter 转成等价 canonical delta；
- 在每个字节边界拆分工具 JSON，聚合结果一致且只执行一次；
- 注入重复、乱序、completed 后 delta，adapter 返回稳定 protocol error；
- 429 按 fake clock 退避且 interrupt 能立即取消等待；
- context overflow 触发上层压缩信号，不在 adapter 偷裁消息；
- fallback 遇到不支持图片或工具时被 capability gate 阻止；
- redaction test 确认事件、日志和 error detail 无 API key；
- usage 缺失、延迟或修正时，账单投影保持可解释。

## 证据与设计综合

`公开事实`：OpenAI、Anthropic 等公开 API 及多个开源 harness 都提供流式、工具调用和不同错误语义。
`设计综合`：这里的 canonical schema 与 fallback 约束用于跨 provider 移植，不复制任何厂商 wire protocol。
上下文选择见 [context-engine.md](context-engine.md)，预算观测见 [performance-cost.md](performance-cost.md)，协议投影见 [protocol-events.md](protocol-events.md)。
