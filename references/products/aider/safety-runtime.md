# Aider-like 安全与运行时边界

## 目录

- [威胁模型](#威胁模型)
- [真实 enforcement](#真实-enforcement)
- [确认与权限](#确认与权限)
- [Git undo 安全](#git-undo-安全)
- [宿主执行边界](#宿主执行边界)
- [故障与安全 oracle](#故障与安全-oracle)
- [增强路径](#增强路径)

## 威胁模型

输入不可信来源包括用户粘贴内容、仓库文件、网页内容、模型响应、生成的 shell 命令和测试输出。主要风险：路径穿越/符号链接逃逸、模型覆盖未授权文件、prompt injection 诱导运行命令、shell 数据破坏、secret 进入 prompt/日志、Git undo 吞掉用户修改、超长输出/进程耗尽资源。

保护资产包括工作区和 root 外文件、Git 历史、未提交用户修改、API key/环境变量、终端控制权、费用和网络访问。安全目标不是证明模型可信，而是让模型输出必须经过确定性 parser、policy 和 executor。

## 真实 enforcement

| 控制 | enforcement 点 | 仅提示是否足够 |
|---|---|---|
| root 边界 | canonical path + symlink resolve + Workspace deny | 否 |
| read-only | Workspace access map | 否 |
| ignore | repo/ignore matcher + policy | 否 |
| edit format | parser + in-memory applier | 否 |
| stale write | expected hash compare | 否 |
| shell approval | CommandRunner 前 confirmation record | 否 |
| undo provenance | session commit set + Git graph checks | 否 |
| secret redaction | prompt/log/event serializer | 否 |
| resource bounds | timeout/output/cost/reflection budgets | 否 |

system prompt 中“不要编辑某文件”只能作为 UX 辅助，不算 enforcement。`--yes` 只改变 confirmation decision，不关闭路径、read-only、stale hash 或 undo provenance 控制。

## 确认与权限

```yaml
ConfirmationRequest:
  id: uuid
  turn_id: uuid
  action: create_file|edit_unlisted|delete_file|run_shell|run_test|web_fetch|unsafe_git
  subject: string
  risk: low|medium|high
  rule_id: string
  options: [allow_once, allow_session, deny, deny_forever]
  expires_at: timestamp|null
```

同一 action/subject 可以在一轮分组确认，但批准不能跨 root、跨 action class 泛化。shell command 需展示准确文本并要求显式 yes；空输入不能视为同意。确认记录关联 changeset/command hash，内容变化后旧批准失效。

新文件、未加入文件需要确认；chat files 表示用户已选入编辑上下文，可以视为 session grant。read-only 是 deny rule。删除、根外访问、危险 Git 应为 high risk。自动化模式用预声明 grant 替代交互，grant 写明 path glob、action、expiry 和 actor。

## Git undo 安全

安全 `/undo` 必须逐项满足：

1. 当前 HEAD 存在且不是初始无 parent commit；
2. HEAD short/full hash 属于当前 session 的 `aider_commit_hashes`；
3. commit 只有一个 parent，不处理 merge；
4. commit 涉及的文件当前没有未提交修改；
5. 对每个目标，previous commit 中存在可恢复版本；
6. 若有 `origin/current_branch`，当前 HEAD 未等于 remote HEAD，即未确认已经推送；
7. 调用方提供的 expected HEAD 与当前一致。

满足后，逐文件 checkout 上一版本，再 soft reset HEAD~1；任何文件恢复失败必须停止并报告已恢复/未恢复集合。该公开行为对“commit 新建文件”较保守，会拒绝自动 undo；复刻若支持删除新文件，必须增加 trash/preimage 和单独高风险测试。

绝不自动建议或执行 `git reset --hard HEAD^`。用户原 dirty changes 的 checkpoint 和 agent edits 必须有不同 provenance。

## 宿主执行边界

Aider 基线没有通用 OS sandbox。文件编辑、Git、lint/test、`/run` 和 `/git` 在启动进程的宿主权限下运行；确认对误操作有帮助，但无法隔离恶意/被注入命令。它也没有通用 MCP capability negotiation 和动态 subagent runtime。

因此启动公告和 settings 必须显示：

```yaml
ExecutionBoundary:
  filesystem: host
  process: host
  network: host-or-command-dependent
  sandboxed: false
  mcp: false
  dynamic_subagents: false
```

不要因 subprocess 设置 cwd、Git 可 undo 或 Docker 安装选项就声称所有执行已隔离。用户自己在容器内启动 Aider，只能标为 `external_container`，隔离质量取决于容器配置。

## 故障与安全 oracle

- 模型输出 `../../.ssh/config`：parser 或 policy 拒绝，root 外文件 hash 不变。
- chat 中 read-only 文件出现 edit block：整个 block 拒绝，记录 rule id。
- symlink 从 root 指向外部：resolve 后拒绝，不能只检查字符串前缀。
- 模型在代码块建议 `rm -rf ...`：不得因代码块存在而运行；只有 typed shell suggestion + explicit confirmation 才进入 runner。
- confirmation 后命令被修改：command hash 不同，必须重新确认。
- malformed multi-file edit：没有任何文件变化。
- HEAD 不是当前 session commit：`/undo` 拒绝。
- agent commit 后用户修改其中一文件：`/undo` 拒绝且不丢用户修改。
- test 打印疑似 API key：event/log 持久化版本被 redaction，终端显示策略可配置。
- provider 连续错误：bounded retry 后失败，费用/attempt 可审计。

这些 oracle 必须在 host mode 和可选 sandbox mode 分别运行；sandbox oracle 不能用 host confirmation 测试替代。

## 增强路径

`polished` 可加入进程/文件/网络 sandbox、MCP 和远程 workspace，但保持同一 Workspace/Command/Event 合同：

- sandbox backend 使用 allowlisted mount、非 root 用户、CPU/memory/pid/time 限额和默认网络 deny；
- MCP tool 经过 ToolSpec 校验、policy 和确认，不把 server 文本当系统指令；
- subagent 若加入，使用独立 context/worktree 和 join，不把 architect/editor 改名冒充；
- remote workspace 的 commit/undo 仍要实现 expected HEAD 与 provenance。

这些能力应标 `enhancement`，默认 Aider 兼容配置保持关闭。`security.sandbox-enhancement` 只有真实隔离测试通过才能 `verified`。
