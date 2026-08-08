# Deep Agents Context 与 Tool 蒸馏

## 目录

- [事实基线](#事实基线)
- [Context 分层](#context-分层)
- [Context Builder Schema](#context-builder-schema)
- [压缩与外置](#压缩与外置)
- [Filesystem Backend 合同](#filesystem-backend-合同)
- [Tool Runtime](#tool-runtime)
- [Skill、Memory 与 RAG](#skillmemory-与-rag)
- [Subagent 上下文隔离](#subagent-上下文隔离)
- [四级升级](#四级升级)
- [失败与验证](#失败与验证)

## 事实基线

官方文档分别说明 context engineering、models、tools、backends、memory、RAG、retrieval、skills、subagents 与 multimodal：

- https://docs.langchain.com/oss/python/deepagents/context-engineering
- https://docs.langchain.com/oss/python/deepagents/models
- https://docs.langchain.com/oss/python/deepagents/tools
- https://docs.langchain.com/oss/python/deepagents/backends
- https://docs.langchain.com/oss/python/deepagents/memory
- https://docs.langchain.com/oss/python/deepagents/skills
- https://docs.langchain.com/oss/python/deepagents/subagents
- https://docs.langchain.com/oss/python/deepagents/multimodal

## 源码观察

固定源码证据见 [sources.md](sources.md)。公开源码有 `_messages_reducer.py`、`_models.py`、`_tools.py`、`backends/`、`middleware/` 与 `profiles/`；不能仅凭文件名推断某种检索器或 provider 是默认实现。

## Context 分层

Deep Agents 配方把模型可见上下文做成以下层的预算投影：

1. 系统、组织和 profile 指令；
2. workspace 规则与 skill 指令；
3. todo/plan 与当前 subagent task；
4. 相关 thread items；
5. backend 文件摘要、RAG 结果和长期记忆；
6. 工具结果与 artifact refs；
7. 当前用户输入。

每个片段至少记录：

```json
{
  "fragment_id": "f-1",
  "kind": "system|memory|skill|todo|message|rag|tool|artifact",
  "source_uri": "workspace:///AGENTS.md",
  "trust": "user-controlled",
  "scope": "thread|project|user|org",
  "tokens": 420,
  "priority": 70,
  "digest": "sha256:...",
  "loaded_at": "..."
}
```

## Context Builder Schema

Builder 输入包括 model context window、reserved output、tool schemas、current task、fragments 与 budgets。

选择算法必须确定：

1. 固定 immutable system/policy；
2. 加当前用户输入与未完成 tool continuity；
3. 加当前 todo/subagent objective；
4. 按 scope/trust/relevance 选择 memory/skill/RAG；
5. 为近期 messages 和 tool result 留预算；
6. 超预算先外置大结果，再压缩旧历史；
7. 记录被纳入/排除原因。

模型不可见的 secret/policy internals 不因“priority 高”被加入 prompt。

## 压缩与外置

固定实现的 summarization middleware 可把旧 history 追加到 `/conversation_history/{thread_id}.md`，媒体单独外置并在 summary 中保留引用。

复刻不变量：

- summary 是派生投影，原始事实仍可回读；
- summary 带 source message IDs、cutoff 与 digest；
- summary 失败时保留原消息或明确失败，不静默丢弃；
- tool args 与大结果可先截短/外置，再做语义摘要；
- context overflow 有 clip/fallback，但不能伪造成功；
- private summarization state 不传播给 subagent。

消息 reducer 负责确定性合并事实账本；context builder 负责按来源、scope、token 和可信度选择投影。两者不得合并成“截断 messages 列表”。

## Filesystem Backend 合同

统一 backend 接口至少提供：

- logical URI 与 root/capability snapshot；
- list/read/write/patch/search/stat；
- artifact upload/download；
- snapshot 或变更集标识；
- cancellation、timeout、quota 与结构化错误；
- 本地、容器、远程实现的一致路径语义。

backend 是资源抽象，不是安全声明。每个写入和执行动作仍先经过 policy，并由 sandbox/executor 强制。

## Tool Runtime

ToolSpec 至少有 name、JSON schema、effect、permission class、backend requirement、timeout、result schema 和 idempotency。

ToolCall 流程：normalize -> validate -> policy -> interrupt? -> dispatch -> receipt -> result -> event。

大输出不得直接无限回灌 messages；使用 artifact + bounded preview。

Tool registry 在 turn 开始时冻结；MCP server 或 plugin 热变更只影响新 turn。

## Skill、Memory 与 RAG

- Tool 使用共享 schema、权限、副作用、幂等和结果外置合同。
- Skill 是可版本化指令/资源/工具依赖集合；启停后生成新的 capability snapshot。
- RAG 负责外部知识的检索、重排和引用，结果必须可回到当前源。
- Long-term memory 负责主体化、可撤销、带 scope 的跨会话信息。
- 大输出写入 backend/artifact，模型只接收有界摘要与引用，避免把 filesystem 变成无限 token 旁路。

必须修正一个边界：`deepagents==0.7.5` 没有内置通用 vector RAG pipeline。

RAG 通过 custom tool、MCP 或 middleware 接入，至少包含 retrieve、filter、rerank、citation、index version 与 injection handling。

三者区别：

| 能力 | 加载方式 | 典型 scope | 是否语义检索 |
|---|---|---|---|
| Skill | 索引元数据，按需读 SKILL.md | project/user | 否 |
| Memory | 启动时加载 AGENTS.md | user/project/org | 否 |
| RAG | query-time retrieve/rerank | corpus/index | 是 |

## Subagent 上下文隔离

父 agent 发出结构化 delegation：task、return schema、budget、deadline、allowed tools、backend roots、permission ceiling 和 context slice。子 agent 返回带 lineage 的 result/artifacts/events；父 agent 合并结果，不共享子 agent 的隐式可变消息列表。

## 验证焦点

- 同一任务切换 local 与 remote backend，logical URI 和事件保持一致。
- 工具大输出被 artifact 化，摘要丢失信息时可受控回读。
- skill 或 MCP tool 热变更不会影响已开始 turn 的 capability snapshot。
- 子 agent 看不到未委派文件、秘密、记忆和工具。
- RAG 陈旧、记忆冲突、恶意文件指令和多模态超预算都有确定降级行为。

## 四级升级

| 等级 | Context/Tool 增量 | Oracle |
|---|---|---|
| `runnable` | messages + bounded file tools | 不溢出并能回读 |
| `usable` | summary、skills、memory、sync child | provenance/scope 正确 |
| `productive` | RAG、artifact、async child、eval | 引用与隔离通过 |
| `polished` | multi-tenant memory、remote registry、migration | 删除/retention/SLO 通过 |

## 失败与验证

- memory source 不存在：记录来源错误，不用空内容冒充加载成功。
- skill frontmatter 恶意 YAML：安全解析且不执行代码。
- RAG citation 不可解析：不得把回答标 grounded。
- summary 丢失关键约束：golden query 可从原 history 回读纠正。
- unsupported media：用明确 placeholder，不触发 provider 400 循环。
- tool schema 改版：旧 turn 使用冻结 schema，新 turn协商新版本。
- child 请求超出 context/permission：父 ceiling 拒绝。
- 删除主体 memory：索引、store、artifact cache 同步清理。
- Context Builder 输出 trace 不包含原始 secret。
- 所有 oracle 见 [acceptance-tests.md](acceptance-tests.md)。
