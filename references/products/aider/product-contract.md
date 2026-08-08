# Aider-like 产品合同

## 目录

- [用户承诺](#用户承诺)
- [行为合同](#行为合同)
- [领域 schema](#领域-schema)
- [非目标与边界](#非目标与边界)
- [证据与判定](#证据与判定)
- [失败语义](#失败语义)

## 用户承诺

用户在一个本地代码库启动产品、选择模型与文件、用自然语言描述修改。产品提供足够的仓库结构上下文，让模型返回受约束的 edit；在真正写入前检查路径和确认；写入后展示结果、建立 Git 恢复点并运行可选验证。用户可以问代码而不修改，也可以让 architect 先设计、editor 后落盘。

该合同强调“可审查、可逆的仓库编辑”。Aider-like 不是任意桌面自动化器，不默认运行长时间后台任务，也不承诺进程级隔离。

## 行为合同

### 会话与文件

1. root 在会话创建后不可隐式漂移。
2. chat file 的完整内容进入 prompt；repo 中其他文件只通过 repo map 或显式加入进入。
3. read-only file 可以提供上下文但永不成为 edit target。
4. ignore 文件默认不加入；新文件和未加入文件写入前需要确认，除非用户已明确授予自动确认。
5. ask/help/context 模式不得写工作区；code/architect 才能产生 ChangeSet。

### 模型与编辑

1. main model 负责回答/方案；weak model 可负责总结和 commit message；editor model 只在 architect 模式存在。
2. model metadata 决定默认 edit format、repo map、token limits；用户显式配置优先。
3. assistant 自由文本不能直接执行；必须由当前 format parser 生成 typed edits。
4. parse 失败不产生部分写入；错误可反馈给模型一次或多次，但受 reflection budget 限制。
5. architect 输出先作为文本计划；得到确认后才传给 editor，editor 的 edits 仍走同一授权/应用路径。

### Git 与验证

1. 若目标文件已有用户 dirty change 且启用 dirty commits，先单独 checkpoint。
2. AI edits 成功后可自动 commit，记录 hash 到当前 session 的 `aider_commit_hashes`。
3. lint 针对 edited files；test 针对配置的项目命令。非零退出码是失败结果而不是进程崩溃。
4. 用户接受后，lint/test 错误作为 reflection message；循环不得无限执行。
5. `/undo` 只操作当前 session 记录的最后一个 Aider commit，并执行安全检查。

## 领域 schema

```yaml
ModelRef:
  provider: string
  name: string
  role: main|weak|editor
  edit_format: string
  max_input_tokens: integer|null
  max_output_tokens: integer|null

Edit:
  path: relative-path
  operation: create|replace|delete|whole-file
  anchor: string|null
  replacement: string|null
  expected_sha256: string|null

TurnResult:
  turn_id: string
  state: completed|failed|cancelled|awaiting_confirmation
  assistant_text: string
  changeset_id: string|null
  edited_files: [relative-path]
  commit_sha: string|null
  lint: ValidationOutcome|null
  test: ValidationOutcome|null
  error: ErrorEnvelope|null
```

```yaml
ValidationOutcome:
  kind: lint|test|command
  command: string
  exit_code: integer|null
  stdout: string
  stderr: string
  timed_out: boolean
  truncated: boolean
```

稳定标识必须由 runtime 生成，不能让模型自报。`expected_sha256` 用于防止生成响应期间文件被外部修改；不匹配则拒绝 apply 并要求重新编译上下文。

## 非目标与边界

- **非强 sandbox**：Aider 基线在 host filesystem 和 host shell 上工作；确认提示不是 syscall isolation。
- **非 MCP host**：没有通用 MCP server discovery、schema negotiation、resource/prompt contract。
- **非 subagent scheduler**：architect/editor 是固定两阶段角色，不具有动态派生任务、独立 workspace、mailbox 或 join。
- **非 durable cloud task**：主交互依赖前台进程；Git/history 提供局部恢复，不等于分布式 exactly-once。
- **非 IDE clone**：GUI、浏览器、watch 等可选入口不改变 terminal-first 核心。
- **非秘密复刻**：prompt 和公开源码可研究，provider 私有行为与服务端数据不可推断。

若高级等级加入 sandbox/MCP/subagent，必须标为“增强型 Aider-like”，并保留上述 Coder 合同和默认关闭状态。

## 证据与判定

行为证据来自 [sources.md](sources.md) 的官方文档和固定 commit。蒸馏实现的 thread/turn/event、expected hash、事务 journal 是为了让别的大模型可以稳定实现，属于 `inference`，不可说成原项目字段。

判定一个实现是否“像 Aider”，优先看以下可观察行为：

- 文件上下文是显式集合，其他仓库内容以相关 repo map 注入；
- 模型输出采用可解析 edit format；
- Git 自动提交和安全 undo 是默认工作流；
- lint/test 错误可以继续对话修复；
- modes 在同一历史上切换，而非开启不相关会话；
- 产品透明披露模型、format、repo map 和 Git 状态。

仅有 chat + shell tool、仅生成 unified diff、或仅把整个 repo 塞入 prompt，都不足以满足合同。

## 失败语义

| 故障 | 必须结果 | 禁止结果 |
|---|---|---|
| 模型超时/限流 | bounded retry，最终 `failed` | 无限睡眠或重复 apply |
| context exceeded | 总结/减小 map 后重试或明确失败 | 静默丢最新用户约束 |
| malformed edit | 零写入，返回 parse diagnostic | 猜测并写入半个 patch |
| stale file hash | `workspace_conflict`，重新读取 | 覆盖外部修改 |
| lint/test fail | 保存 outcome，询问是否修复 | 把非零码当成功 |
| commit fail | edits 保留、标记 uncheckpointed | 宣称可 undo |
| cancel | 停止模型/命令；apply 临界区结束后报告 | 伪装成 completed |
| cache corrupt | 删除并重建 cache | 阻止用户访问 repo |

安全 oracle 和端到端验收见 [acceptance-tests.md](acceptance-tests.md)。
