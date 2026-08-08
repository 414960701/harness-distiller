# Claude-Code-like Workspace 与执行运行时

> 本篇把工作区、编辑、Bash、sandbox、权限和 trust 组合成可实现的执行合同。平台事实按官方文档标记；模块与 schema 为 `inference`。

## 目录

- [边界模型](#边界模型)
- [Workspace 身份](#workspace-身份)
- [Trust 与配置装载](#trust-与配置装载)
- [文件读取和编辑](#文件读取和编辑)
- [Bash 执行](#bash-执行)
- [权限求值](#权限求值)
- [Sandbox enforcement](#sandbox-enforcement)
- [网络与秘密](#网络与秘密)
- [Worktree 和并发](#worktree-和并发)
- [Hooks、MCP 和 Plugins](#hooksmcp-和-plugins)
- [升级与测试](#升级与测试)

## 边界模型

```text
Model intent
  -> Tool registry validation
  -> Path/command normalization
  -> Hook observation/policy input
  -> Permission evaluator
  -> Sandbox profile compiler
  -> Executor
  -> Change/output collector
  -> Redactor
  -> ToolResult
```

`inference`：顺序可在无副作用处优化，但 permission 与 sandbox 不能由 UI 或 prompt 替代。

### 三层区别

- instruction：告诉模型“应该怎么做”，可能被忽略。
- permission：决定某个意图是否允许、询问或拒绝。
- sandbox：操作系统层限制获准进程实际能做什么。

任何文档和界面都必须区分三层。

## Workspace 身份

```yaml
Workspace:
  id: string
  canonical_root: absolute_path
  device_inode_or_volume_id: string
  vcs_root: absolute_path|null
  trust_state: unknown|trusted|restricted|revoked
  writable_roots: [absolute_path]
  temp_root: absolute_path
  revision: string
```

- 启动时解析 realpath，保存 display path 与 canonical path。
- 不允许用 `..`、symlink、junction 或 bind mount 越出 root。
- trust 绑定 canonical identity，不只绑定可伪造路径字符串。
- cwd 改变不会自动扩大 writable roots。
- 多仓库 workspace 必须逐 root 声明权限。

## Trust 与配置装载

`official-doc/behavior`：项目可提供 CLAUDE.md、rules、hooks、MCP 和其他配置；其中可执行配置具有风险。

`inference`：把装载分两阶段。

1. 静态发现：只读文件名、hash、声明能力，不执行。
2. trust gate：用户确认后装载项目 hook、command、MCP process。

### 装载优先级

- managed policy：最高，项目不可覆盖。
- user config：用户跨项目选择。
- project config：受 trust gate。
- local config：本机项目覆盖，但仍受 managed deny。
- runtime default：没有规则时的安全默认。

CLAUDE.md/rules 是 context，不参与 permission precedence。

项目从 trusted 变更为新 canonical identity 时重新询问。

## 文件读取和编辑

### 读取合同

- 打开前 canonicalize 并检查 read policy。
- 限制单次字节数、总 context tokens 和二进制类型。
- 返回 path、revision/hash、encoding、range 和 truncation。
- secret matcher 在进入模型上下文前脱敏或拒绝。
- 读取失败保留 errno 类 reason code，不泄露不必要绝对路径。

### 编辑合同

```yaml
EditRequest:
  path: workspace_relative_path
  base_revision: sha256|string
  operations: [replace_range|apply_patch|write_new]
  expected_encoding: string
```

- 只接受 workspace-relative API，executor 内部再拼 canonical root。
- 写入前验证 base revision，冲突则返回 stale_revision。
- 写临时文件、fsync、atomic rename；不破坏权限位。
- 应用后重新读取并生成 diff/stat。
- checkpoint 在首次修改前捕获基线。
- 用户已有 dirty changes 不能被静默覆盖或 reset。

## Bash 执行

### ProcessSpec

```yaml
ProcessSpec:
  command_text: string
  argv: [string]|null
  cwd: workspace_relative_path
  env_allowlist: [string]
  timeout_ms: integer
  stdin_mode: closed|pipe|pty
  sandbox_requirement: required|preferred|none
  network_requirement: deny|allowlist|unrestricted
```

保留用户可见原命令，同时创建规范化 policy target；不得重写后悄悄执行不同命令。

### 生命周期

- spawn 前发 `tool.started` 之前必须完成授权和 profile compile。
- stdout/stderr 分离，chunk 有 sequence 和上限。
- 超出上限落 artifact，context 只保留头尾和摘要。
- cancel 先发送温和终止，再按期限 kill process group。
- PTY background job 有 owner；session 结束时处理孤儿进程。
- exit code、signal、timeout 和 sandbox violation 分别编码。

## 权限求值

`official-doc`：公开规则概念为 allow、ask、deny，并有 managed/user/project/local 等来源和 permission modes。

`inference`：求值先规范化 action，再按 deny 优先和管理锁计算。

```python
def decide(action, rules, mode):
    candidates = match(action, rules)
    if any(r.effect == "deny" and r.managed for r in candidates):
        return deny("managed_deny")
    if any(r.effect == "deny" for r in candidates):
        return deny("matched_deny")
    if mode == "plan" and action.has_side_effect:
        return deny("plan_mode")
    best = highest_precedence(candidates)
    return best.effect if best else safe_default(action)
```

精确 precedence 作为蒸馏实现选择，不声称是闭源内部算法。

持久 grant 保存 canonical matcher、scope、创建者、expiry，不保存自然语言解释作为规则。

## Sandbox enforcement

`official-doc`：macOS 使用 Seatbelt；Linux/WSL2 使用 bubblewrap，网络可经 socat 代理，可选 seccomp；native Windows 不支持同等 Bash sandbox。

### Capability 声明

```yaml
SandboxCapability:
  platform: macos|linux|wsl2|windows
  filesystem: enforced|partial|none
  network: enforced|proxy_only|none
  unix_socket_filter: enforced|partial|none
  hard_fail_supported: boolean
```

- `required` 但 capability 不足时必须 hard fail。
- `preferred` 降级时重新授权并醒目标记 unsandboxed。
- writable root 只含 workspace、session temp 和显式授权路径。
- deny root 至少覆盖用户凭证、SSH、cloud config 和其他 workspace。
- profile 以 immutable execution snapshot 编译，避免审批后配置漂移。

不得在 native Windows 上显示与 WSL2 相同的 hard-sandbox 结论。

## 网络与秘密

- 默认网络 deny；允许时按 domain/port/protocol 声明。
- DNS rebinding、IP literal、redirect 和代理绕过进入测试集。
- TLS 凭证和代理日志不得记录 token/query secrets。
- 环境变量使用 allowlist，常见 credential 变量默认移除。
- credential helper 通过窄接口提供，不把 secret 文本加入模型。
- MCP/OAuth token 存系统 keychain 或等价 secret store。
- 网络 allow 不等于外部 write 自动获批。

## Worktree 和并发

- 并行 Agent 默认使用独立 git worktree 或 copy-on-write workspace。
- 每个 run 记录 base commit、dirty patch 和 worktree path。
- merge 前做冲突检测和用户变更保护。
- checkpoint 只覆盖受控文件变更，不回滚 push、数据库和 API。
- 删除 worktree 前保存未合并 patch artifact。
- 同一路径并发编辑必须基于 revision compare-and-swap。

## Hooks、MCP 和 Plugins

Hook 是扩展代码，不是天然可信安全层。

- hook 输入是脱敏事件 snapshot。
- hook 声明 timeout、network、filesystem 和 fail mode。
- PreToolUse 可进一步 deny，不能覆盖 managed deny。
- MCP server/tool 独立标识、审批和 effect 分类。
- plugin manifest 声明 skills、agents、hooks、MCP 和最低协议。
- project plugin 首次执行走 trust gate。
- plugin uninstall 不删除历史 session 所需 schema 信息。

## 升级与测试

- 能跑：单 root、显式 ask、直接进程和能力警告。
- 能用：canonical path、规则作用域、平台 sandbox、atomic edit。
- 顺手：网络代理、secret policy、worktree、hook/plugin trust。
- 好用：remote microVM、组织 policy、signed plugin、持续攻击测试。

Oracle：symlink 指向 root 外时，read/edit/Bash 三条路径都不能越界。

Oracle：managed deny 在 project allow、hook allow 和 UI grant 下仍为 deny。

Oracle：sandbox unavailable 且 requirement=required 时，命令从未 spawn。

Oracle：cancel 后 process group 不留可写 workspace 的孤儿进程。

Oracle：编辑遇到 stale revision 时不覆盖用户的新内容。

Oracle：secret fixture 不出现在 model request、event log、hook input 和 UI transcript。
