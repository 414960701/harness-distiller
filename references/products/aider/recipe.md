# Aider-like 蒸馏配方

## 目录

- [默认蓝图](#默认蓝图)
- [四级能力矩阵](#四级能力矩阵)
- [直接升级规则](#直接升级规则)
- [Aider overlay capability](#aider-overlay-capability)
- [推荐交付顺序](#推荐交付顺序)
- [禁止替代](#禁止替代)

## 默认蓝图

产品差量：单 foreground Coder、显式 chat/read-only files、repo map、structured edit formats、Git auto/dirty commits、安全 undo、lint/test reflection、CLI modes，以及可选 architect/editor 双模型。

共享 required：`agent-loop`、`model-adapter`、`protocol-events`、`context-engine`、`patch-edit`、`filesystem`、`git-worktree`、`cli-tui`、`testing`、`reliability`。默认不选择 browser/desktop/web、MCP、dynamic subagents、long-term memory。polished 可把强 sandbox 和 headless protocol 作为增强，但要标明不是原生基线。

建议默认：`mode=code`、`auto_commits=true`、`dirty_commits=true`、`auto_lint=true`、`auto_test=false`、repo map 约 1024 tokens、streaming=true、shell 每次确认。

## 四级能力矩阵

| 子系统 | runnable（能跑） | usable（能用） | productive（顺手） | polished（好用） |
|---|---|---|---|---|
| loop | 单 code turn | reflection/retry/cancel | architect/editor | durable recovery/SLO |
| context | 显式文件 | repo map + summary | 增量 PageRank/cache | context manifest/eval |
| edits | whole 或 diff | 多 format + preview | model-format routing | property/fuzz tests |
| Git | 手动 checkpoint | auto/dirty commit | safe undo provenance | crash-safe journal |
| validation | 手动命令 | lint/test feedback | formatter/timeout | isolated runner |
| UX | plain CLI | modes/commands/stream | JSONL/token/cost | 多前端 event projection |
| security | root/read-only | confirmation/stale hash | policy audit | 强 sandbox enhancement |

等级是同一合同的字段和优化累积，不是四个独立产品。高等级必须包含低等级所有 oracle。

## 直接升级规则

任意低等级可直接升级到目标等级：

1. 先运行当前等级 acceptance baseline，保存 thread/config/HEAD 快照。
2. 执行 additive schema migration，旧 Turn/ChangeSet/Event id 不变。
3. 为已有 session 补默认字段：access、expected hash、checkpoint provenance、budget。
4. cache 版本变化只重建 cache，不迁移为真源。
5. 打开新能力 feature flag，先 shadow 生成 repo map/JSONL/policy outcome。
6. 运行目标等级和所有较低等级 oracle。
7. 失败时关闭 flag；数据库/工作区仍能由旧 runtime 只读或继续。

从 runnable 直升 polished 不可跳过 dirty provenance、bounded reflection 和 stale write；“已经有 sandbox”不能补偿编辑事务缺失。

## Aider overlay capability

以下 ID 必须原样进入蓝图；等级为最早可 `verified` 的阶段：

| capability ID | 等级 | 实现路径 | verified oracle |
|---|---|---|---|
| `context.explicit-files` | runnable | Session chat/read-only sets + ContextCompiler | 未加入文件全文不进 prompt；read-only edit 被拒 |
| `editing.structured-format` | runnable | EditFormat parser/preview/apply | malformed multi-file response 零写入 |
| `git.atomic-checkpoint` | runnable | base HEAD + GitCheckpoint | AI edit 前后产生可定位 checkpoint，commit fail 不伪成功 |
| `context.repo-map` | usable | tree-sitter tags + PageRank + token selector | 跨文件符号检索进入预算内 map，parser 缺失可降级 |
| `context.history-summary` | usable | ChatSummary + source hash | 超阈值总结且保留最新约束；过期 worker 不覆盖新历史 |
| `validation.lint-test` | usable | Validator + reflection budget | 非零输出反馈，用户接受后修复，次数有上限 |
| `modes.architect-editor` | productive | 串行 ArchitectCoder/EditorCall | 两个 model call；拒绝 proposal 时零写入；editor 不运行 shell |
| `models.role-routing` | productive | main/weak/editor ModelRef | summary/commit/editor 调到配置角色并分别计 usage |
| `git.undo-dirty-provenance` | productive | session commit set + safe undo | 非 session/dirty/merge/pushed HEAD 全拒绝且文件不丢 |
| `security.sandbox-enhancement` | polished | isolated Workspace/CommandRunner | root/网络/资源逃逸测试在内核边界失败；不能只测确认 |
| `protocol.headless-jsonl` | polished | Event serializer + `--output-format jsonl` | stdout 每行合法 event、seq 单调、无 ANSI、重放终态一致 |

逐项可执行步骤在 [acceptance-tests.md](acceptance-tests.md)。overlay 未实现的能力保持 `planned`/`implemented`，不能仅因文档存在标 `verified`。

## 推荐交付顺序

1. 建 Session、Turn、ChangeSet、Event 和 root-relative Workspace。
2. 实现 whole 或 strict diff 的 parse/simulate/apply，配模型 adapter。
3. 加 Git base checkpoint、diff preview 和 plain CLI，完成 runnable。
4. 加 tree-sitter repo map、history summary、ask/code modes、lint/test、确认，完成 usable。
5. 加多 format metadata、architect/editor、role routing、安全 undo、stale hash、流式事件，完成 productive。
6. 加 transaction journal、JSONL replay、强 sandbox adapter、故障注入和评测，完成 polished。

每步都以 vertical slice 交付，不先建设无法由用户路径验证的抽象平台。

## 禁止替代

- 仅列目录不能替代 repo map 的 symbol graph/ranking。
- 让模型输出自由 Markdown 再正则猜测不能替代 edit format parser。
- 自动保存 diff 文件不能替代 Git dirty/agent provenance 和安全 undo。
- prompt 说“不要运行危险命令”不能替代 policy/confirmation/sandbox。
- 两次普通 chat call 不能替代 architect proposal 到隔离 editor 的字段合同。
- GUI 成功动画不能替代 validation/commit outcome。
- 通用 tool-calling agent 即使能力更多，也不自动满足 Aider-like 行为。
