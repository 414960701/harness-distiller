# OpenCode-like Context、Provider 与工具

## 目录

- [StepContext](#stepcontext)
- [Provider 归一化](#provider-归一化)
- [Instruction 与上下文](#instruction-与上下文)
- [Tool registry](#tool-registry)
- [MCP](#mcp)
- [LSP](#lsp)
- [压缩与截断](#压缩与截断)
- [实现门禁](#实现门禁)

## StepContext

每个 provider step 生成不可变清单：

```yaml
StepContext:
  session_id: string
  model: {provider_id, model_id, variant}
  agent: string
  system: [string]
  messages: [normalized-message]
  tools: [{id, description, json_schema}]
  permission_rules_hash: string
  location: {directory, worktree, workspace_id}
  context_budget: {window, output_reserved, used}
  abort_signal: runtime-ref
```

工具、模型、permission 或 cwd 在 stream 中改变，只影响下一 step。这样 MCP 上线/下线、用户切模型和配置 reload 不会让当前 tool call 找不到原 schema。

## Provider 归一化

adapter 输出统一 LLMEvent：step-start、text/reasoning start/delta/end、tool-input delta/end、tool-result、usage、finish、error。adapter 负责：

- provider/model discovery、auth 与 option transform；
- tool JSON Schema 能力差异与名字规范化；
- media/tool-result 支持差异的安全降级；
- reasoning metadata、cache usage、cost 字段；
- API error 到 auth/rate-limit/context/content/output/network 的分类；
- provider-executed tool 与 host tool 的区分。

默认测试必须使用 scripted provider，不要求 OpenCode Zen/Go 或付费 key。模型目录缓存不可作为授权真值；不存在的 model 返回 typed not-found。

## Instruction 与上下文

按确定优先级收集全局配置、项目 `AGENTS.md`/rules、路径级 instruction、agent prompt、用户 system override。记录每个 instruction 的 source path/hash；路径越具体的规则只能在声明范围内应用。

message compiler 保留 user/assistant/tool 配对、最新约束、附件类型和 compaction marker。显式 `@file` 读取发生在 server，生成 FilePart source；二进制/media 依据 model 能力保留、转换说明或拒绝，不能把任意 data URL 无界送入模型。

## Tool registry

内置工具建议分 runnable 与增量：

| 阶段 | 工具 |
|---|---|
| runnable | read, glob, grep, edit/write 或 apply_patch, shell |
| usable | todo, question, task/subagent, webfetch, skill, MCP tools |
| productive | PTY/background, custom tools, plugin tools, LSP |

`ToolDef` 含 id、description、runtime schema、JSON Schema、permission name、effect class、output policy、execute。初始化后 registry 合并 builtin、配置目录 tool、plugin 与 MCP；冲突必须确定性拒绝或 namespace，不能静默覆盖。

执行顺序：decode schema → normalize path/command → permission ask → optional sandbox → execute → truncate/artifact → persist result。tool 返回结构化 title/output/metadata/attachments；超大输出存 artifact 并在结果中给 preview、path/hash、truncated=true。

## MCP

支持 local stdio 与 remote Streamable HTTP/SSE；每个 server 有 disabled/connecting/connected/failed 状态、timeout、transport finalizer。OAuth token 存凭证库，callback state 防 CSRF；工具、resource、prompt 通过 client name namespace。

MCP 暴露的 tool schema 必须复制后转换，不能让远端对象在 registry 中被原地修改。调用仍受本地 permission、timeout、abort、size 和 media allowlist。连接失败不删除 core tools；恢复后只在下一 step 进入 tool snapshot。

## LSP

LSP 默认可关闭。启用后按 extension、project root 和 prerequisites 惰性启动，维护 `(server_id, root)` 唯一 client；broken 状态需重试/重启策略。提供 diagnostics、hover、definition、references、symbols、call hierarchy 等 typed service。

文件 read/edit 后调用 `touchFile`/didOpen/didChange，并收集 diagnostics。LSP 输出是提示，不是文件真值；server 未安装、过慢、不同步时降级 grep/read/lint。下载 language server 属供应链动作，需要配置和校验。

## 压缩与截断

预算从 model context window 减去 output reserve、system、tool schemas 和附件。先截断单个 tool output，再 prune 足够旧的 completed outputs，最后 summary head，保留最近若干完整 turns 与未完成 plan/todo。

Compaction message 保存 summary、reason、tail boundary、source watermark/hash。并发新消息导致 watermark 变化时旧 summary 不得覆盖。skill/tool artifact 可列为 protected，但必须有总上限。

## 实现门禁

- 两个 provider fixture 对相同 tool loop 生成同一 canonical parts；
- schema-invalid tool 零执行；
- MCP 断线不漂移当前 step tools；
- LSP crash 不阻断 read/edit；
- context overflow 压缩后 tool pair 完整；
- tool output 截断仍保存 hash/artifact ref；
- prompt capture 可解释每段上下文来源且不含 secret。

固定实现证据见 [sources.md](sources.md) 的 provider、tool registry、MCP、LSP 与 compaction。
