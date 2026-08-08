# OpenHands-like Context 与 Tool Runtime

## 目录

- [上下文分层](#上下文分层)
- [View 不变量](#view-不变量)
- [Condenser](#condenser)
- [Prompt 与记忆](#prompt-与记忆)
- [Tool 定义](#tool-定义)
- [工具集合](#工具集合)
- [MCP Client Tool Skill Plugin](#mcp-client-tool-skill-plugin)
- [预算与缓存](#预算与缓存)
- [实现检查](#实现检查)

## 上下文分层

模型输入按来源和生命周期分层：

1. 静态 system prompt：agent 角色、通用工具规则，可跨 conversation cache；
2. 动态 system context：workspace/repo、时间、已授权 secret 描述、能力；
3. active branch：用户/agent message、Action、Observation；
4. condensation：旧区间摘要与保留锚点；
5. 按需 skill/plugin/MCP/tool schema；
6. 当前 run 的临时附件、path rules 和 hook feedback。

每段记录 `source`、`scope`、`digest`、`trust`、`token_estimate`。仓库文件、MCP 响应、skill 和 tool output 都是不可信数据。

## View 不变量

View 是 EventLog active branch 的确定投影：

- SystemPromptEvent 位于首条 user message 前；
- 同一 LLM response 的多个 ActionEvent 还原为一个 assistant tool-call message；
- 每个 ActionEvent 后有匹配 Observation/AgentError/UserReject；
- tool call 与 result 不能被 condenser 截断拆开；
- condensation request/result 作为原子批次；
- branch 切换后丢弃旧 View cache 或从共同祖先安全增量；
- unknown event 不进入模型，除非有显式 converter；
- streaming delta 不作为恢复后的模型真相。

View 构建后运行 property validators：tool-call matching、tool-loop atomicity、observation uniqueness、batch atomicity。违反即停止采样并报告 protocol error。

## Condenser

Condenser 接口：

```python
class Condenser(Protocol):
    def should_condense(self, view: View, budget: ContextBudget) -> bool: ...
    async def condense(self, view: View, boundary: AtomicBoundary) -> Condensation: ...
```

摘要至少保留：用户目标、已完成/待办、文件和 symbol、关键命令与结果、失败、决策、workspace 状态、未闭合确认、引用 event range/digest。

LLM summarizer 输出视为不可信，必须 schema validate。摘要不能声称未发生动作，也不能包含 secret。失败时退回更小的保留窗口、tool output offload 或明确 context exhausted。

原 EventLog 不删除；CondensationEvent 记录 covered ids、summary、token before/after、model/version 和 prompt digest。重放同事件得到相同 View；不要求再次调用模型。

## Prompt 与记忆

动态 context 通过 typed sections 组合，不把字符串散落在 tool executor。

- repo memory/AGENTS 只在 workspace scope 内；
- user memory 与 project memory 命名空间隔离；
- secret 只注入 executor credential channel，不注入 prompt 值；
- path rules 在首次触碰匹配路径时注入一次，并记录激活；
- invoked skill 和 trigger skill 分开记录；
- profile/model switch 从下一 step 生效并发出事件。

任何记忆都不能增加 tool、workspace、network 或 confirmation 权限。

## Tool 定义

```json
{
  "name": "terminal",
  "version": "1",
  "action_schema": "TerminalAction@1",
  "observation_schema": "TerminalObservation@1",
  "parallel_safe": false,
  "resource_policy": "terminal-session",
  "risk_tags": ["process", "filesystem", "network-possible"]
}
```

Tool registry 保存 spec 与 executor 分离。模型只看到 spec；runtime 绑定 executor。参数通过 discriminated union 校验，不允许额外字段静默穿透。

Tool result 必须返回 typed Observation，异常通过统一 adapter 转换。每个结果带 duration、truncation、artifact、workspace identity 和 receipt；用户文案不替代机器字段。

## 工具集合

`runnable`：Finish、Think、Terminal、FileEditor/apply_patch、Glob、Grep。

`usable`：Planning/Task tracker、MCP、client tool、git diff/change、model switch。

`productive`：Browser、skill invoke、plugin tools、delegate/child conversation、workflow。

工具名可因 provider 规范适配，但 canonical kind 和 event schema 不变。FileEditor 进行 workspace root 检查；Terminal 支持 session、stdin、timeout、cancel；Browser observation 包含 URL、结构化状态、截图 artifact 和 tab id。

## MCP Client Tool Skill Plugin

### MCP

连接有 start/ready/changed/error/closed 生命周期；server identity、tool digest、auth scope 进入 capability snapshot。运行中 tool list changed 在 step 边界 reconcile，不能改变当前 response 的 spec。

### Client Tool

Canvas 提供 client-side tool spec；SDK executor 只发 ActionEvent/ack，真正结果必须由已认证客户端回传并匹配 tool_call_id。无人订阅时 fail，不等待无限期。

### Skill

先加载元数据，触发或显式 invoke 后加载正文。校验名称、大小、frontmatter、source 和 precedence；skill 指令不能提升权限。

### Plugin

plugin 聚合 skills、MCP、hooks 和 agents。固定 ref/digest，安装与启用分开；合并优先级可解释，hooks 组合、同名 skill/tool 覆盖需记录 provenance。

## 预算与缓存

预算包括模型输入/输出、工具 output、附件、摘要和 reserve。必须为下一次 Observation 与最终回答保留空间。

静态 system prompt 使用稳定 cache key；动态 context 不污染共享 cache。父子 conversation 可显式共享 prompt cache shard，但不共享 secret 或 event history。

大 tool output 写 content-addressed artifact，View 只含摘要、digest 和读取句柄。截断同时保存原始 exit status，禁止模型把截断当完整输出。

## 实现检查

- 相同 active branch 和 capability snapshot 生成相同 View digest。
- condenser 不拆 action/observation，不删除审计事件。
- tools 变更只在 step 边界可见。
- client tool/MCP/plugin 的来源和 trust 可追踪。
- prompt、event、trace 和 artifact 中无 secret 值。
- skill/plugin/hook 输出不能改变 policy ceiling。
- model switch 后旧 response 不使用新 tool registry。

公开源码地图见 [sources.md](sources.md)，工作区强制边界见 [workspace-execution.md](workspace-execution.md)。
