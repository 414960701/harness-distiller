# Aider-like CLI 体验

## 产品形态

默认是 terminal-first 前台会话。首屏必须公告版本、main/weak/editor model、edit format、Git root/文件数、repo map token 预算、auto commit/lint/test、执行边界和帮助入口。透明配置比隐藏“智能选择”更重要。

提示符显示 active mode：code 可用普通 `>`，ask/architect/help/context 使用前缀。流式 Markdown 只渲染模型回复；文件应用、commit、lint/test 和确认用独立状态行，避免把执行结果误认为模型声称。

## CLI modes

| mode | 行为 | 写文件 |
|---|---|---|
| code | 解决任务并按 edit format 生成修改 | 是，需授权 |
| ask | 讨论代码、方案和问题 | 绝不 |
| architect | main model 提方案，editor model 转 edits | 是，两阶段 |
| help | 回答产品配置/排错 | 绝不 |
| context | 分析应加入哪些文件/上下文 | 绝不 |

`/ask text`、`/code text`、`/architect text` 是单消息 override，下一条回 active mode；`/chat-mode architect` 是 sticky。切换 format 时旧 assistant edit syntax 应总结或隔离，防止模型模仿错误格式。

architect 的交互序列：展示 proposal；若未 auto-accept，询问“Edit the files?”；展示 editor 模型/format；解析并 preview edits；写入后展示 commit/validation。UI 不能把 architect proposal 当已完成修改。

## 命令分组

文件与上下文：`/add`、`/read-only`、`/drop`、`/ls`、`/map`、`/map-refresh`、`/tokens`、`/clear`、`/reset`。

Git 与执行：`/diff`、`/commit`、`/undo`、`/git`、`/lint`、`/test`、`/run`。

模型与模式：`/model`、`/weak-model`、`/editor-model`、`/chat-mode`、`/ask`、`/code`、`/architect`、`/help`、`/context`。

会话与输入：`/load`、`/save`、`/paste`、`/editor`、`/multiline-mode`、`/copy-context`、`/exit`。

命令 parser 支持 completion 和 quoted paths，但执行前转换 typed Command。`/run` 和 `/git` 显示准确命令、cwd、风险；output 可选择加入 chat。未知命令给相近建议，不把它当普通用户消息发送模型。

## 文件选择体验

chat files 列表持续可见或可用 `/ls` 查询；read-only 以不同标记显示。用户在消息中提到 repo 文件时，产品可建议加入，而不是静默读取/编辑。模型请求编辑未加入文件时，显示路径和 diff preview 后确认。

repo map 更新较慢时显示进度；首次大型 repo scan 说明只需一次。map disabled/degraded 必须展示，不应默默给模型空仓库信息。`/tokens` 按 system/history/map/read-only/chat/current 分类展示使用量，并给 `/drop`、`/clear` 建议。

## 变更与反馈

每轮结束展示：edited paths、diff summary、commit hash/message、lint/test outcome、费用/tokens 和 `/undo` hint。Git commit 失败时用醒目状态 `changes applied, not checkpointed`；validation 失败但用户拒绝修复时显示失败，不把 turn 整体渲染成成功。

malformed edit 展示简短 parser diagnostic 和自动 reflection 次数；详细内容可在 verbose 模式查看。provider retry 显示原因类别和下次 delay，但不刷屏重复 traceback。context exceeded 提供具体 token breakdown。

确认统一显示 action、subject、risk、scope 和选项。默认 Enter 不等于允许高风险 shell；`--yes` 启动时明确公告自动确认范围。

## headless 与脚本

`--message`/`--message-file` 执行单轮并退出；exit code 区分成功、validation failed、no-change、policy denied、provider failure 和 internal failure。人类 Markdown 输出之外，polished 等级提供 `--output-format jsonl`：每行一个 [protocol-state.md](protocol-state.md) Event，stdout 不混入 spinner/ANSI，诊断走 stderr 或 event。

```json
{"type":"turn.started","thread_id":"...","turn_id":"...","seq":1}
{"type":"workspace.file_applied","item_id":"...","payload":{"path":"src/a.py"}}
{"type":"turn.completed","payload":{"commit_sha":"abc123","validation":"passed"}}
```

同一 idempotency key 不能重复 apply。Python embedding API 若提供，必须自己 version；官方 Aider 的 Python scripting API 不保证稳定，复刻不能把内部对象暴露当长期协议。

## 可访问性与可观察性

- `--no-stream` 输出确定、适合日志和屏幕阅读器。
- `--no-pretty` 去除颜色/Markdown/动画；所有状态仍有纯文本标签。
- Ctrl-C 第一次取消当前 turn/command，第二次短间隔退出；取消结果明确。
- stdout/stderr/output truncation 有标记并可保存安全 sidecar。
- tokens、cost、duration、reflection、provider attempts 形成 usage report。
- telemetry 默认/opt-out 行为遵循部署说明；secret 永不作为 analytics 属性。

## 四级体验增量

| 等级 | 体验增量 |
|---|---|
| runnable | 单轮 code、文件列表、diff、清楚错误 |
| usable | modes、斜杠命令、streaming、confirm、Git/lint/test 状态 |
| productive | architect/editor、completion、token/cost、cache/map 进度 |
| polished | JSONL、TUI/GUI 投影、恢复提示、无障碍、远程 workspace、政策中心 |

所有等级消费同一 event；升级不另写一套 UI 真源。
