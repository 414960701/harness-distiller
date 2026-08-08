# Context Engine

## 职责与非目标

Context Engine 在 token、延迟、缓存、可信度和隐私预算内装配模型可见快照。
输入包括指令、项目规则、历史、文件、检索、记忆、计划、工具结果和运行状态。
它不执行模型、不授权工具、不把长期记忆当事实库，也不靠最后拼接顺序偶然解决冲突。
它不原地改写 durable 历史；选择、裁剪和压缩都产生可审计引用。

## Fragment 与 Snapshot

```text
ContextFragment {
  id, kind, content_ref, provenance, scope, trust,
  priority, token_estimate, sensitivity,
  valid_from, invalidation_key?, parent_id?
}
ContextSnapshot {
  id, thread_id, turn_id, step_no, model_capabilities,
  fragments[], tool_catalog_version, token_total,
  selection_trace, created_at
}
```

稳定前缀与动态后缀分开，便于 provider cache，但语义优先于命中率。
snapshot 建成后不可变；steering、规则变化和工具刷新进入下一 step。
每个 fragment 可追溯到用户、项目文件、工具、检索或摘要 item。

## 装配与压缩

装配顺序是：收集候选 → 按 scope/指令层级解冲突 → 安全过滤 → 预算选择 → 保持调用配对 → 序列化。
预算必须为 final response、工具 schema 和输出预留空间。
工具 call/result 不可被裁成孤立项；当前目标、未完成计划、修改文件和验证状态优先保留。
压缩产生 summary item、覆盖范围、原文 checkpoint 和质量指标。
压缩失败先做确定性裁剪；仍超限则返回明确错误，不无限递归。

## 四级增量

| 等级 | 新增能力 | 不变量 |
|---|---|---|
| 能跑 | 最近历史、显式文件、固定预算 | provenance 与不可变 snapshot |
| 能用 | 项目规则、分层预算、自动压缩 | 指令优先级和 tool pair 完整 |
| 顺手 | 增量选择、缓存前缀、分支上下文、RAG | selection trace 与失效机制 |
| 好用 | 学习型路由、敏感过滤、跨设备记忆、质量评测 | 可解释、可回放和用户可控 |

优化只能改变候选选择，不能绕过安全层级或丢失必要状态。

## 直接升级与回滚

先为所有 fragment 补 provenance 和 content hash，再上线自动选择或压缩。
直接升级好用时，以 shadow mode 记录新旧 snapshot 差异并运行任务 eval。
新的 summary schema 与旧 reader 双读；切换前保留原 rollout checkpoint。
回滚选择器只改变未来 snapshot，不重写已提交历史或删除摘要覆盖范围。
学习型路由故障时降级为确定性优先级与最近性策略。

## 失败模式与安全

- token 估算偏差：保留 margin，并对 provider overflow 做一次压缩恢复；
- 规则冲突：按来源层级和 scope 产生诊断，不按文本位置决定；
- 恶意仓库指令：标记低信任，不能提升权限或覆盖系统约束；
- 工具输出过大：外置 artifact，只注入有界摘要与引用；
- 过期文件/RAG：invalidation key 变化后禁止复用旧 snapshot；
- 摘要幻觉：保留原文引用，关键事实用结构化状态重新注入；
- 敏感内容：在进入 provider 前按 policy 过滤，缓存 key 不泄露明文。

## 可执行验收

- 同一候选集合和配置生成确定性 snapshot hash；
- 指令冲突 fixture 始终按层级解析并输出 selection trace；
- 上下文超限后压缩继续完成编辑，且 call/result 无孤立；
- 文件 hash 变化导致缓存 snapshot 失效；
- 100 MB 工具输出仅注入有界摘要，完整 artifact 可按权限读取；
- 恶意项目规则无法改变 sandbox、approval 或系统指令；
- 回滚到旧选择器后新 turn 可运行，旧 snapshot 仍可审计；
- 长任务 eval 比较压缩前后目标、计划、改动与待验证项的保留率。

## 证据与设计综合

`公开事实`：Codex、AgentScope、LangGraph 等公开实现均有上下文、压缩或状态装配模块。
`设计综合`：fragment schema、selection trace 和升级流程是跨 harness 的实现建议。
指令层级见 [instructions-prompts.md](instructions-prompts.md)，RAG 见 [rag-index.md](rag-index.md)，长期记忆见 [long-term-memory.md](long-term-memory.md)。
