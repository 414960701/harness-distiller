# AgentScope Context 与 Tool 蒸馏

## 事实：公开能力

官方文档为 Context 单列 overview、compress、offload 与 environment awareness：

- https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/context/overview
- https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/context/compress-context
- https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/context/offload-context
- https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/context/environment-awareness

Tool 文档区分 overview、manage tools、Python tool、MCP 与 skill；RAG 和 Long-Term Memory 也有独立页面：

- https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/tool/overview
- https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/tool/manage-tools
- https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/tool/python-tool
- https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/tool/mcp
- https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/tool/skill
- https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/rag
- https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/long-term-memory

## 源码观察

`context` 能力在当前源码树中主要由 agent/message/event/state 等组件协作，而 `tool`、`mcp`、`skill`、`rag`、`embedding` 与 `workspace` 有独立包：

- https://github.com/agentscope-ai/agentscope/tree/29b592358c2e983a0d10dd5227316b7a02d8c23a/src/agentscope

可据此判断“工具调用、MCP 传输、skill 组织、检索和 workspace 资源”并非同一层；不能据目录判断压缩算法质量、RAG 默认召回指标或长期记忆写入策略。

## 设计综合：Context 三段式

蒸馏实现保持共享 [context-engine](../../knowledge/context-engine.md) 合同，并增加三项 AgentScope 差量：

1. `context.compress`：预算触发后生成带 `covered_item_ids`、摘要模型、token 统计和恢复引用的新 item。
2. `context.offload`：大工具结果、文件和中间产物外置为 artifact；模型只收到有界摘要、MIME、hash、scope 和读取工具。
3. `context.environment`：把 workspace roots、平台、可用工具、时间和执行限制建模为有来源/失效条件的 fragment，不拼进不可审计的系统长字符串。

Context 组装顺序建议保持稳定：系统/组织指令 → 项目规则 → 工具与安全声明 → 计划与工作状态 → 相关历史/记忆/RAG → 当前输入。动态片段位于稳定前缀之后，以保留缓存能力。

## 设计综合：Tool 与 Resource 分离

- `ToolSpec` 描述可调用动作、schema、副作用、权限、timeout、取消和幂等。
- `ResourceRef` 描述文件、artifact、知识库、skill 包或远程对象，不自动赋予执行能力。
- `McpServerRef` 描述发现与调用连接；导入的 MCP tool 必须重新规范化名称、schema、风险和 scope。
- `SkillRef` 是指令、资源和工具依赖的可版本化集合，不可绕过 policy 注册隐藏工具。
- `ToolResult` 区分模型可见摘要、用户可见内容、artifact、错误与审计元数据。

## RAG 与 Long-Term Memory 边界

RAG 负责外部知识的 ingest/retrieve/rerank/citation；Long-Term Memory 负责主体化、可撤销、跨会话的事实或偏好。二者共享检索接口，但写入策略、权限、过期和删除语义不同。AgentScope 提供两类独立 building blocks 是设计证据，不代表应共享一张无类型向量表。

## 验证焦点

- 压缩后继续完成依赖早期细节的编辑，且能定位被覆盖 items。
- offload artifact 被删除、过期或越权时 fail closed。
- MCP schema 冲突、恶意描述和超大返回不会污染稳定前缀。
- skill 禁用后，其工具、指令和资源同时从下一 turn 的 capability snapshot 消失。
- RAG 结果带来源和当前版本；长期记忆支持纠错、撤销和跨项目隔离。

## 实现补充

- `ContextSnapshot` 固定 fragment provenance、scope、token budget 与 tool schema hash。
- `ToolkitSnapshot` 固定 tool name/schema/group/risk/source/version，当前 reply 内不静默漂移。
- Model wrapper 分开 chat、embedding、TTS capability；不伪造 provider 等价性。
- Plan Task 使用稳定 id、revision 与 `pending/in_progress/completed`，更新产生 event。
- Middleware hook 具有顺序、timeout、failure policy 与 mutation provenance。
- RAG chunk 保存 source/hash/span；LTM 保存 subject/scope/expiry/supersedes/tombstone。
