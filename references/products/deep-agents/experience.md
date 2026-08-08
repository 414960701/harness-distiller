# Deep Agents 体验蒸馏

## 目录

- [事实：公开交互能力](#事实公开交互能力)
- [设计综合：长任务工作台](#设计综合长任务工作台)
- [建议事件](#建议事件)
- [投影、ACP 与断线](#投影acp-与断线)
- [黑盒体验场景](#黑盒体验场景)
- [非目标](#非目标)

## 事实：公开交互能力

官方文档提供 todo frontend、graph execution、subagent streaming、sandbox frontend、event streaming、一般 streaming、ACP、profiles 与 production 指南：

- https://docs.langchain.com/oss/python/deepagents/frontend/todo-list
- https://docs.langchain.com/oss/python/deepagents/event-streaming
- https://docs.langchain.com/oss/python/deepagents/frontend/subagent-streaming
- https://docs.langchain.com/oss/python/deepagents/frontend/sandbox
- https://docs.langchain.com/oss/python/deepagents/event-streaming
- https://docs.langchain.com/oss/python/deepagents/streaming
- https://docs.langchain.com/oss/python/deepagents/acp
- https://docs.langchain.com/oss/python/deepagents/profiles
- https://docs.langchain.com/oss/python/deepagents/going-to-production

## 源码观察

源码把 graph、message reducer、middleware、backends 和 profiles 分开：https://github.com/langchain-ai/deepagents/tree/d60560d695e8c436e11dee96965e7a1447409737/libs/deepagents/deepagents 。这适合让 frontend 投影 graph/todo/subagent/backend 事件；当前目录不从文档标题推断具体页面布局、视觉设计或云端专有能力。

## 设计综合：长任务工作台

Deep Agents 风格体验的重点不是聊天气泡，而是让长任务可观察、可 steering、可恢复：

- Todo 展示目标、状态、依赖、证据和阻塞，不展示私有 chain-of-thought。
- Graph execution 展示公开节点/阶段、重试和等待原因，不暴露内部敏感 state。
- Subagent 有独立 lineage、任务、预算和事件流，父视图可折叠汇总。
- Filesystem/sandbox 视图展示 logical roots、执行位置、变更和 artifacts。
- Approval 显示规范化 tool、参数、风险、scope 和有效期。
- 断线重连从 snapshot + sequence event 恢复，不把终端文本当状态。

## 建议事件

- `todo.created | todo.updated`
- `graph.node_started | graph.node_finished | graph.interrupted`
- `subagent.delegated | subagent.progress | subagent.returned`
- `backend.snapshot_changed | artifact.created`
- `tool.requested | tool.progress | tool.committed`
- `approval.requested | approval.resolved`
- `context.compacted`
- `turn.checkpointed | turn.resumed | turn.finished`

不同 surface 可隐藏事件，但不能改变 sequence、causation、终态或 policy 结果。

## 黑盒体验场景

1. 复杂仓库任务自动形成可编辑 todo，简单任务可直接执行而不强制计划。
2. agent 将独立调研委派给 subagent；父视图收到流式摘要和最终带 provenance 结果。
3. 大文件/输出写入 backend artifact；用户能展开、下载并定位来源。
4. 危险动作触发审批；修改批准 scope 后 runtime 使用 amend 后参数执行。
5. turn 在 graph interrupt 或远程 sandbox 断开后恢复，不重复已提交副作用。
6. ACP/前端断线重连后，以相同 sequence 重建 todo、subagent、approval 和 artifact 状态。

## 非目标

- 不复制 LangChain/Deep Agents 品牌和页面样式。
- 不把 LangSmith 或其他伴生服务默认算入纯 OSS 交付。
- 不把“创建很多 subagent”当作质量；必须用任务成功、冲突率、成本和取消正确性验收。

## 投影、ACP 与断线

Planning 在 0.7.5 是 opt-in；只有 capability snapshot 包含 `planning.todo` 时才显示 Todo，不能从模型文本猜计划状态。

投影至少保存 thread_id、turn_id、head_sequence、messages、todos、tool_calls、approvals、subagents 和 artifacts。

ACP 是独立 `deepagents-acp` 包，用于 agent-editor 集成；它不是核心 SDK，也不是供模型调用外部工具的 MCP。

断线恢复流程：先取 snapshot，再订阅 `sequence > head_sequence`；重复 event 按 event_id 去重，sequence gap 触发补拉。

取消与断线不同：取消向 model/tool/child/remote run 传播，断线可以让后台任务继续。UI 不投影 secret、header、private middleware state 或 chain-of-thought。

| 等级 | Surface 增量 | Oracle |
|---|---|---|
| `runnable` | SDK/headless 事件、Todo opt-in | 最终状态与 Todo revision 可重建 |
| `usable` | approval、sync child、skills/memory 来源 | steering/resume 正确 |
| `productive` | typed stream、async child、RAG/replay | 断线重连一致 |
| `polished` | sandbox 状态、协议协商、HA、SLO | 旧客户端与灾备通过 |
