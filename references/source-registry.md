# 来源登记与热度快照

抓取日期：2026-08-08（Asia/Shanghai）。Stars 来自当日 GitHub REST `stargazers_count`，只用于发现线索，会随时间变化。

## 开源编码 Harness

| 产品 | 仓库 | Stars | License/边界 | 代码快照 |
|---|---|---:|---|---|
| Codex | https://github.com/openai/codex | 104,637 | Apache-2.0 | `92fb33b7583ac909a21efaebcd2fad6e79643a6f` |
| Claude Code | https://github.com/anthropics/claude-code | 140,591 | 无 SPDX；不是完整产品源码，主要为安装、插件、示例与 issues | 不作为内部实现证据 |
| Aider | https://github.com/Aider-AI/aider | 48,023 | Apache-2.0 | `5dc9490bb35f9729ef2c95d00a19ccd30c26339c` |
| OpenCode | https://github.com/anomalyco/opencode | 194,888 | MIT | `fe82a1b6ca4f535beb973b0867017e3f639f85ed` |
| Cline | https://github.com/cline/cline | 65,831 | Apache-2.0 | `71536e55aab762900dfbfd09a55194b204677e8c` |
| Roo Code | https://github.com/RooCodeInc/Roo-Code | 24,354 | Apache-2.0 | `b867ec9145750d0ae1ff7f02d35406e9bf2a0b16` |
| OpenHands Canvas | https://github.com/OpenHands/OpenHands | 83,432 | MIT | `4470813ce58f5ac384e3d367d34518e10106526b` |
| OpenHands SDK | https://github.com/OpenHands/software-agent-sdk | 组成同一产品证据集 | MIT | `c7e270aae43a6e9bcc8723d27b85c680ab38e156` |

OpenHands 的前端和 Agent/Conversation/Condenser/Tool/Workspace/agent-server 分属两个仓库，但在产品目录中合并为一个配方。

## 通用 Agent Framework

| 产品 | 仓库 | Stars | 备注 |
|---|---|---:|---|
| AgentScope | https://github.com/agentscope-ai/agentscope | 28,707 | building blocks 边界完整 |
| LangGraph | https://github.com/langchain-ai/langgraph | 39,131 | Python 1.2.10 `41341457342327166d72fc11952ab28fb61ec0bf`；JS 1.4.9 `5f9915234a5dca861ef01180fde28e52f42c6e15` |
| Deep Agents | https://github.com/langchain-ai/deepagents | 27,483 | 基于 LangGraph 的产品化 harness 层，必须独立目录 |
| AutoGen | https://github.com/microsoft/autogen | 60,297 | 已进入 maintenance；后继参考 Microsoft Agent Framework |
| CrewAI | https://github.com/crewAIInc/crewAI | 56,748 | crew/flow DSL |
| OpenAI Agents SDK | https://github.com/openai/openai-agents-python | 28,471 | runner/handoff/guardrail/tracing |
| LlamaIndex | https://github.com/run-llama/llama_index | 51,446 | RAG、workflow、memory、eval |
| Letta | https://github.com/letta-ai/letta | 24,146 | stateful agent 与 memory hierarchy |

## 一级文档入口

### Codex

- 官方 app-server 协议：https://learn.chatgpt.com/docs/app-server
- 官方 approvals 与 sandbox：https://learn.chatgpt.com/docs/agent-approvals-security
- 源码 turn loop：https://github.com/openai/codex/blob/main/codex-rs/core/src/session/turn.rs
- 源码 context history：https://github.com/openai/codex/blob/main/codex-rs/core/src/context_manager/history.rs
- 源码 tool router：https://github.com/openai/codex/blob/main/codex-rs/core/src/tools/router.rs
- prompt caching 设计：https://developers.openai.com/cookbook/examples/prompt_caching_201#42-stabilize-the-prefix

### Claude Code

- How it works：https://code.claude.com/docs/en/how-claude-code-works
- Context：https://code.claude.com/docs/en/context-window
- Permissions：https://code.claude.com/docs/en/permissions
- Sandboxing：https://code.claude.com/docs/en/sandboxing
- Sessions 与 checkpoint：https://code.claude.com/docs/en/sessions 、https://code.claude.com/docs/en/checkpointing
- Hooks/Skills/Plugins：https://code.claude.com/docs/en/hooks 、https://code.claude.com/docs/en/skills 、https://code.claude.com/docs/en/plugins

### AgentScope

- Agent：https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/agent/overview
- Context：https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/context/overview
- Permission：https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/permission-system/overview
- Middleware：https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/middleware
- Plan/RAG/Memory/Workspace：
  - https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/plan
  - https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/rag
  - https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/long-term-memory
  - https://docs.agentscope.io/versions/2.0.6dev/en/building-blocks/workspace/overview

### Durable runtime、RAG 与 Memory 标杆

- LangGraph persistence：https://docs.langchain.com/oss/python/langgraph/persistence
- LangGraph interrupts：https://docs.langchain.com/oss/python/langgraph/interrupts
- Deep Agents context/backends/permissions/subagents：
  - https://docs.langchain.com/oss/python/deepagents/context-engineering
  - https://docs.langchain.com/oss/python/deepagents/backends
  - https://docs.langchain.com/oss/python/deepagents/permissions
  - https://docs.langchain.com/oss/python/deepagents/subagents
- LlamaIndex Workflows：https://developers.llamaindex.ai/python/llamaagents/workflows/
- Letta stateful agents：https://docs.letta.com/concepts/stateful-agents/
- Letta context hierarchy：https://docs.letta.com/v1-sdk/memory/context-hierarchy/

## 使用规则

引用实现时优先换成带 commit 的 permalink；`main`/`dev` URL 只作为入口。产品 recipe 若依赖此表未覆盖的新结论，必须先把来源补入自己的文档或 `.harness-distill/evidence.md`。
