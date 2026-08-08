# Codex-like 分级验收测试

## 目录

1. 测试原则与环境
2. Runnable / 能跑
3. Usable / 能用
4. Productive / 顺手
5. Polished / 好用
6. 安全套件
7. 故障注入
8. 协议与界面一致性
9. 出厂门禁

## 测试原则与环境

本文件是`设计综合`，将产品合同转成黑盒验收，不声称是 Codex 官方测试清单。
每一级包含前一级全部测试；升级不是替换测试集。
测试只依赖公开协议、文件系统结果、事件 trace 和用户可见界面，不依赖私有 prompt。

固定测试环境至少包含：

- 临时 git 仓库，含未提交用户修改、symlink 和大文件 fixture；
- scripted model server，能发送文本、多工具、坏参数、断流和超限；
- fake clock、deterministic ids 和可控 executor；
- Linux/macOS/Windows 至少一个真实 sandbox，其他平台可在 CI 分片；
- stdout/stderr、JSONL trace、rollout、SQLite 和 workspace 快照采集器；
- 每个 crash point 可强制 kill runtime，而非优雅关闭。

通过条件：结果正确、终态唯一、事件可重放、无越权副作用、无泄密。

## Runnable / 能跑

### R1 读改测闭环

给定一处可复现单元测试失败，模型读取文件、应用 patch、运行目标测试并报告结果。
断言只修改预期文件，patch 前后 hash 与 diff 事件一致。
断言 trace 至少包含 user、tool call/result、agent final 和 turn completed。

### R2 多步工具循环

scripted model 依次请求 read、shell、patch、shell，再返回文本。
断言 runtime 发起至少三次模型 step，而不是提前结束。
断言每个 call id 只有一个 completed result。

### R3 工具错误恢复

第一次读取不存在文件，第二次搜索正确路径并继续。
断言错误作为 tool result 回到模型，不把整个 runtime 异常退出。

### R4 基础权限

尝试写工作区外路径与运行需要审批的命令。
断言越界写被 enforcement 拒绝；approval deny 反馈模型并正常收尾。

### R5 中断

运行持续输出的子进程，发送 interrupt。
断言进程树终止、turn interrupted、没有后续新工具、终态恰一次。

### R6 Headless 合同

同一任务分别成功、模型失败、权限拒绝和超时。
断言稳定退出码、stdout/stderr 分离、JSONL 每行合法且最终事件存在。

## Usable / 能用

### U1 崩溃恢复

在 tool result 持久化后、terminal 前 kill runtime，再 resume。
断言 transcript 不丢失，已完成副作用不重复，turn 被恢复或明确中断。

### U2 长上下文压缩

注入超过阈值的历史、未完成计划、失败命令和待验证文件。
断言压缩后仍可完成任务，原 rollout 可审计，tool pair 不孤立。

### U3 PTY continuation

启动需要 stdin 的命令，发送两段输入并 resize。
断言 offset 有序、重复 request id 不重复写入、退出码准确。

### U4 审批恢复

在 approval pending 时断开客户端并重启 app-server。
断言请求仍可见、过期策略生效、一次 resolution 只执行一次工具。

### U5 多表面等价

用 TUI 与 headless 消费同一 scripted fixture。
断言 canonical item 序列、工具结果和 turn 终态等价。

### U6 MCP 失效

MCP 在列工具后离线。
断言已有 step snapshot 不漂移；调用失败可分类；核心工具继续工作。

## Productive / 顺手

### P1 多客户端重连

两个客户端订阅同一 thread，其中一个在 1000 个 delta 中断线。
断言用 sequence 补洞，无重复 card，无事件阻塞 runtime。

### P2 Steering 竞态

分别在 sampling、approval、写工具临界区发送 steering。
断言每次 accepted/queued 语义明确，输入不丢失，不修改已批准参数。

### P3 Worktree 隔离

两个任务在独立 worktree 并行修改同名文件。
断言 cwd、branch、diff、进程和 cleanup 完全隔离。

### P4 子代理

父任务创建两个子代理，其中一个超时、一个成功。
断言 parent id、独立上下文、权限收窄、取消传播与结果回传正确。

### P5 Fork 与 rollback

在 checkpoint fork 后分别修改两支，再执行 conversation rollback。
断言父支不变、子支独立、workspace 未被错误 reset。

### P6 Hook 与 skill

让 hook 失败、skill 文件损坏、恶意指令请求提权。
断言失败策略可见，扩展不能绕过 policy/sandbox，核心会话可恢复。

## Polished / 好用

### O1 协议迁移

用旧 schema 创建 session，再由新版本迁移并连接旧客户端。
断言迁移可重跑，未知字段可忽略，破坏能力通过协商拒绝。

### O2 远程 exactly-once effect

远程 command 执行成功后在 receipt 返回前断网。
断言重连按 idempotency key 查询，不重复执行副作用。

### O3 Managed policy

组织 deny、项目 ask、用户 allow 同时配置。
断言 deny precedence，客户端和模型不能覆盖 managed constraint。

### O4 可访问性与大负载

在窄终端、无颜色、screen reader 模式回放 10 万事件。
断言关键信息不只靠颜色，首屏和交互满足 SLO，内存有界。

### O5 生产可观测性

注入 provider、sandbox、storage 和 client 各类故障。
断言 metrics 能区分 turn 成功率、审批延迟、恢复率、sandbox failure，日志无 secret。

## 安全套件

- 路径：`../`、绝对路径、Unicode 混淆、symlink swap、mount boundary；
- 命令：shell 注入、嵌套 shell、环境变量泄漏、恶意 PATH；
- 网络：默认拒绝、域 allowlist、重定向、DNS rebinding、代理绕过；
- 进程：孙进程逃逸、daemonize、fork bomb、资源耗尽、取消竞态；
- 配置：恶意 AGENTS.md、MCP 输出、skill 和 hook 尝试改变权限；
- 数据：prompt、tool output、rollout、artifact、telemetry 中的密钥脱敏；
- Git：脏工作区、恶意 submodule、工作区外 git dir、push/force 操作；
- 服务：未认证订阅、跨 thread 读取、重放 approval、伪造 event sequence。

安全失败必须证明没有目标副作用，而不只是 UI 显示 denied。

## 故障注入

在以下边界逐一 kill -9 并恢复：

1. turn started append 前后；
2. model stream 第一个 delta 后；
3. tool intent durable 后；
4. process spawn 后、receipt 前；
5. patch rename 后、result 前；
6. result append 后、index commit 前；
7. compaction checkpoint 前后；
8. terminal durable 后、broadcast 前；
9. migration 每个 batch 后；
10. remote lease 获得后、heartbeat 前。

每个 case 断言：恢复可重入、终态不重复、sequence 不倒退、副作用不重复、损坏可诊断。

## 协议与界面一致性

golden trace 需要覆盖所有命令、事件、错误 code 和 unknown enum。
对 canonical trace 生成 TUI snapshot、headless JSONL 和 IDE projection。
断言三者状态相同；展示差异只能来自显式 capability 或 presentation rule。
随机丢弃 delta 后用 completed item 重建，最终 transcript 必须一致。
sequence gap 必须触发 resync，客户端不得悄悄跨过。

## 出厂门禁

每级发布需保存机器可读报告：commit、平台、sandbox adapter、模型 fixture、通过数和 waiver。
waiver 必须有 owner、到期日、风险和用户可见限制；安全越界不得 waiver 为通过。
Runnable 失败则不能称为 Codex-like harness。
Usable 失败则不得默认开启 resume。
Productive 失败则不得宣称稳定多客户端、worktree 或子代理。
Polished 失败则不得宣称企业级安全、远程 exactly-once 或跨版本兼容。

产品合同见 [product-contract.md](product-contract.md)，状态与故障恢复见 [persistence-recovery.md](persistence-recovery.md)。
公开测试源码入口见 [sources.md](sources.md)。
