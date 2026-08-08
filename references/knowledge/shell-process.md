# Shell 与进程

## 目录

- [职责](#职责)
- [非目标](#非目标)
- [接口与 Schema](#接口与-schema)
- [生命周期](#生命周期)
- [取消与后台](#取消与后台)
- [四级增量](#四级增量)
- [直接升级与回滚](#直接升级与回滚)
- [失败模式与攻击面](#失败模式与攻击面)
- [可执行验收](#可执行验收)
- [来源与设计综合](#来源与设计综合)

## 职责

Shell/Process 把获准的执行意图转换为可取消、可限额、可审计的本地、容器或远程进程，并结构化回传 stdout、stderr、退出和副作用状态。

执行器必须消费 permission decision 与 sandbox profile，但仍自行验证 cwd、env、network 和平台 capability。

## 非目标

- 不让模型风险解释替代权限求值。
- 不把命令字符串静态分类当 OS 隔离。
- 不保证任意 shell command 幂等或可回滚。
- 不把进程退出 0 等同于任务验证通过。
- 不默认把父进程完整环境传给子进程。

## 接口与 Schema

```yaml
ProcessSpec:
  id: string
  argv: [string]|null
  shell_text: string|null
  cwd_uri: string
  env_delta: {set: object, unset: [string]}
  stdin: closed|pipe|pty
  timeout_ms: integer
  network_intent: deny|allowlist|unrestricted
  sandbox_requirement: required|preferred|none
  idempotency: pure|idempotent|unknown
```

```yaml
ProcessResult:
  status: succeeded|failed|cancelled|timed_out|denied|outcome_unknown
  exit_code: integer|null
  signal: string|null
  output_ref: string|null
  changed_workspace: boolean|unknown
  sandbox_report: object
  duration_ms: integer
```

argv 与 shell_text 互斥；确需管道、重定向或 expansion 时才使用 shell_text，并按原文向用户展示。

## 生命周期

`received -> normalized -> authorized -> profile_ready -> spawned -> running -> draining -> terminal`

terminal 只提交一次；迟到 output 带 late 标记，不复活 cancelled run。

output chunk 含 stream、sequence 和 bytes；超过上下文上限写 artifact，不能阻塞进程造成死锁。

## 取消与后台

- cancel 先停止输入，再向整个 process group/job object 发温和信号。
- grace period 后强制 kill，并继续 drain pipe 到期限。
- background process 有 owner、lease、heartbeat 和 cleanup policy。
- session 崩溃后先 reconcile pid/worker lease，不盲目重复未知命令。
- remote executor 用 fencing token 阻止旧 worker 继续写事件。

## 四级增量

### runnable / 能跑

前台 argv、cwd、timeout、输出上限、基础 allow/ask/deny。

### usable / 能用

PTY/stdin、process group 取消、env allowlist、sandbox report 和 crash reconciliation。

### productive / 顺手

后台会话、并发、artifact 输出、resource usage、容器和结构化命令模板。

### polished / 好用

远程 executor、CPU/memory/pid 配额、worker fencing、平台等价测试和完整审计。

## 直接升级与回滚

历史 shell string 迁移时保留原文，能安全解析才补 argv；不可伪造结构化参数。

先稳定 process id/event/result schema，再把 executor 从 local 切 container/remote；UI 不依赖本机 pid。

回滚远程执行时等待或明确 orphan 现有 job，不能本地重放；background metadata 保留为只读审计。

## 失败模式与攻击面

- shell quoting、命令 substitution 和换行隐藏真实动作。
- cwd symlink 或 mount 在审批后改变。
- 环境变量、argv、`/proc` 或错误日志泄露秘密。
- 子进程逃出父 cancel，产生 zombie/orphan。
- stdout/stderr 背压让进程永久阻塞。
- PTY 控制字符欺骗审批或覆盖终端内容。
- timeout 与正常 exit 竞态造成双终态。
- sandbox 不可用时静默 unsandboxed 执行。
- 包管理器、Git helper 或编译器产生隐蔽网络/子进程。

## 可执行验收

- 参数含空格、引号、换行和 Unicode 时，argv fixture 原样到达子进程。
- fork 多层子进程后 cancel，所有后代在期限内终止，无 zombie。
- 产生超大 stdout/stderr 时无死锁，chunk sequence 连续，完整输出可从 artifact 取回。
- secret env 默认未继承，结果/事件/terminal 不出现 secret。
- sandbox requirement=required 且不可用时 spawn 计数为零。
- timeout/exit/cancel 三方竞态始终只有一个 terminal event。
- 崩溃发生在外部写之后时，resume 标 outcome_unknown 并先 reconcile。
- Windows job object 与 Unix process group 分别运行等价取消套件。

## 来源与设计综合

进程语义参考 POSIX process groups/signals、Windows Job Objects、PTY 和容器 runtime 公共接口；统一状态机为设计综合。

- POSIX process groups：https://pubs.opengroup.org/onlinepubs/9699919799/functions/setpgid.html
- Windows Job Objects：https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects
- OCI runtime spec：https://github.com/opencontainers/runtime-spec

工具 envelope 见 [../implementation/tools.md](../implementation/tools.md)，policy/enforcement 边界见 [../implementation/policy-execution.md](../implementation/policy-execution.md)，sandbox 细节见 [sandbox.md](sandbox.md)。

平台缺失的信号、PTY 或隔离能力必须显式降级，不允许 UI 假装等价。
