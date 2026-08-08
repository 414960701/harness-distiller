# Aider-like 架构

## 目录

- [架构原则](#架构原则)
- [组件边界](#组件边界)
- [依赖方向](#依赖方向)
- [领域对象](#领域对象)
- [初始化顺序](#初始化顺序)
- [并发和一致性](#并发和一致性)
- [可替换接口](#可替换接口)
- [扩展边界](#扩展边界)

## 架构原则

Aider-like 的最小正确拆分是“交互壳 + Coder 编排 + 上下文编译 + 编辑协议 + 工作区执行 + Git 恢复”。不要把全部逻辑塞进一个 while loop，也不要先建设通用 agent 平台再寻找产品行为。公开源码中的 `Coder.create()` 按 edit format 选择具体子类，`Coder` 持有 IO、Repo、RepoMap、Commands、Model 和 Summarizer；这是可复刻的核心依赖图。

## 组件边界

| 组件 | 输入 | 输出 | 不负责 |
|---|---|---|---|
| CLI/IO | argv、stdin、确认答复 | 用户消息、渲染、审计输入 | 决定可写路径 |
| Session/Coder | 用户消息、配置、依赖 | turn 结果、reflection | provider 特有 HTTP |
| ModelAdapter | message chunks、model role | 流式文本/usage/error | 解释 edits |
| ContextCompiler | 文件、repo map、历史、约束 | 有序 message chunks | 写文件 |
| EditParser | assistant text、format | typed edits 或 parse error | 权限确认 |
| WorkspaceExecutor | typed edits、policy | file outcome | 生成模型文本 |
| GitRepo | 工作树、diff、commit policy | checkpoint/commit/undo outcome | 通用 sandbox |
| Validator | edited files、commands | lint/test outcome | 无限自动修复 |
| Persistence | events、history、cache | 恢复快照 | 把 cache 当真源 |

源码映射：`aider/coders/base_coder.py` 是编排器；`aider/coders/*_coder.py` 是编辑协议；`aider/repomap.py` 是符号图；`aider/repo.py` 是 Git facade；`aider/commands.py` 是斜杠命令；`aider/history.py` 是总结器；`aider/io.py` 是终端和确认边界。

## 依赖方向

```text
CLI/IO -> Session/Coder -> ContextCompiler -> ModelAdapter
                    |-> EditParser -> WorkspaceExecutor -> GitRepo
                    |-> Validator ------------------------|
                    |-> EventLog/History/Cache
```

依赖必须单向：edit parser 不可直接写磁盘；repo map 不可偷偷把文件加入可编辑集合；模型 adapter 不可自行批准 shell；渲染层只消费事件。这样才能对 parser、权限、落盘和恢复分别做故障注入。

## 领域对象

```yaml
Session:
  id: string
  root: absolute-path
  mode: code|ask|architect|help|context
  main_model: ModelRef
  weak_model: ModelRef
  editor_model: ModelRef|null
  edit_format: string
  chat_files: [relative-path]
  read_only_files: [relative-path]
  done_messages: [Message]
  cur_messages: [Message]
  aider_commit_hashes: [sha]
  config_snapshot: object

ChangeSet:
  id: string
  turn_id: string
  edits: [Edit]
  base_head: sha|null
  edited_paths: [relative-path]
  status: parsed|authorized|applied|validated|committed|failed
```

`chat_files` 表示可写候选而不是无条件写权限；`read_only_files` 只进入 context。`done_messages` 是可总结的历史，`cur_messages` 是当前文件快照之后的活跃对话。两者分离可以在文件变化后重新编译真值。

## 初始化顺序

1. 合并 CLI、环境变量、配置文件和 model metadata，冻结 `config_snapshot`。
2. 规范化 root；若启用 Git，发现 repo 并获取 HEAD/dirty 状态。
3. 校验初始文件：ignore、存在性、普通文件、read-only 分类。
4. 根据 model 默认或显式参数选择 edit format 和 Coder subclass。
5. 初始化 RepoMap、ChatSummary、Linter、Commands 和 ModelAdapter。
6. 可选读取 chat history；超过阈值时异步总结，但不得阻塞首屏。
7. 输出模型、format、repo、map、Git 和执行边界公告。

任何一步失败都应降级或明确终止：Git 不存在可进入无 Git 模式；repo map parser 不支持语言可仅列文件；主模型配置无效则启动失败；不能静默换模型。

## 并发和一致性

- 单 session 同时最多一个 `RUNNING` turn 和一个 workspace writer。
- history summarization 可以后台执行，但提交结果前比较输入消息快照；历史已变化则丢弃旧 summary。
- repo map cache 可并发读取，更新用单写者或文件锁；损坏时删除 cache 并重建。
- streaming 只改变显示，不得边 stream 边落盘；完整响应解析成功后再 apply。
- architect 和 editor 是串行子阶段，不是两个并发 agent。

## 可替换接口

```python
class ModelAdapter:
    def complete(self, request, cancel_token) -> ModelResult: ...

class EditFormat:
    def parse(self, text, workspace_snapshot) -> list[Edit]: ...
    def preview(self, edits) -> DiffPreview: ...

class Workspace:
    def authorize(self, edits) -> Authorization: ...
    def apply(self, edits, expected_hashes) -> ApplyOutcome: ...

class RepoIndex:
    def build(self, files, focus, token_budget) -> RepoMapResult: ...
```

接口返回 typed outcome，不以打印文本代表成功。所有路径进入 Workspace 前必须转为 root-relative canonical path。完整循环和状态见 [agent-loop.md](agent-loop.md) 与 [protocol-state.md](protocol-state.md)。

## 扩展边界

要加 sandbox、MCP 或 subagent，应作为共享 harness 的可选增强：sandbox 替换 Workspace/CommandRunner；MCP 通过显式 tool runtime 接入；subagent 通过新的 task graph 接入。它们不能伪装成 Aider 原生能力，也不能改变 Coder、ChangeSet、event 和 checkpoint 合同。
