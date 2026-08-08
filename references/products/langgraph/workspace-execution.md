# LangGraph Workspace 与执行边界

## 目录

- [事实边界](#事实边界)
- [Workspace 合同](#workspace-合同)
- [Executor 合同](#executor-合同)
- [Graph 集成](#graph-集成)
- [副作用与恢复](#副作用与恢复)
- [子图隔离](#子图隔离)
- [失败语义](#失败语义)
- [验收](#验收)

## 事实边界

LangGraph core 执行 Python/JS callable，不提供 workspace、shell、Git、patch、容器或远程 worker。使用普通 node 直接调用 `subprocess` 是应用代码行为，不是框架的 sandbox 保证。

因此本页除“graph 如何调用 node”外均为完整 coding harness 的设计综合。

## Workspace 合同

- 每个 run 绑定 `workspace_id`、logical root、revision、owner tenant、lifecycle。
- graph state 只保存 logical URI、digest、revision 和 artifact metadata，不保存任意大文件内容。
- path normalization 在 model/tool 参数进入 filesystem 前完成。
- 所有 read/write/glob/grep/patch 都禁止越过 logical root，并检测 symlink escape。
- write 使用 expected revision/CAS，避免并行 task lost update。
- patch 记录 base digest、result digest、hunks、actor task 和 rollback ref。
- workspace snapshot 与 graph checkpoint 是不同资源，但用 receipt 互相引用。
- thread fork 时声明复用、copy-on-write 或新建 workspace，不能默认猜测。

## Executor 合同

- executor 输入：command/argv、cwd logical URI、env allowlist、stdin ref、timeout、resource/network profile。
- executor 输出：exit code、stdout/stderr artifact、start/end、usage、signal、receipt。
- process id 只作诊断；稳定身份使用 execution id。
- output 超限时 offload artifact 并保留 head/tail/digest/truncated 标志。
- timeout/cancel 要清理完整进程树，而非只取消等待 coroutine。
- 本地、container、remote executor 实现同一 contract；安全 profile 不允许隐式降级。
- network 与 secret injection 是 executor policy，不是 graph state 字段。

## Graph 集成

推荐把一次 effect 拆成多个 node/阶段：

1. `prepare_action`：规范化参数，计算 effect/idempotency key；
2. `authorize_action`：permission policy，必要时 `interrupt`；
3. `dispatch_action`：写 outbox/intent，再调用 executor；
4. `record_receipt`：持久化外部 receipt；
5. `reduce_result`：将小型结果写入 channel，artifact 留引用；
6. `verify_artifact`：运行测试或语义检查。

这些阶段可在一个 node 内实现，但 durable boundary 与 receipt 仍要可观察。

## 副作用与恢复

- interrupt 节点会从头重跑；审批前不得先执行 effect。
- retry policy 不能无条件覆盖 non-idempotent executor action。
- action intent、external commit、receipt、state checkpoint 是四个时间点。
- intent 无 commit 可安全 retry；receipt 已有则复用结果；commit 未知则 `indeterminate`。
- Git commit/checkpoint 可做 workspace rollback 点，但不能代表远程 API 回滚。
- `pending_writes` 能保存成功 task result，不自动确认宿主外部世界状态。
- time travel 重放默认不重放外部 effect；必须选择 simulate/reuse/re-execute policy。

## 子图隔离

- child graph 获得显式 workspace view：read-only、branch、subdir 或独立 snapshot。
- child permission ceiling 不超过 parent；`Command.PARENT` 也不能提升权限。
- 并行 `Send` task 写相同文件时使用 CAS、merge queue 或冲突失败。
- child artifact 带 parent run/task lineage，最终合并由父图显式确认。
- parent 取消向 child executor 传播；迟到 receipt 进入 reconcile，不直接写 parent state。
- checkpoint namespace 不能替代 OS/filesystem 隔离。

## 失败语义

- path denied、sandbox unavailable、timeout、nonzero exit、output overflow、revision conflict 分型返回。
- 工具/执行失败写入结构化 item；不得把 stderr 文本冒充成功 state update。
- checkpointer 成功但 workspace write 失败时，graph 进入可恢复失败并保留 intent。
- workspace write 成功但 checkpoint 失败时，依 receipt reconcile，而非盲重试。
- cancel 后进程仍存活是安全失败，应阻断 polished 发布。
- remote executor 断连时，只有 provider receipt/status API 能解除 `indeterminate`。

## 验收

- `../`、absolute path、symlink、case-folding 与 Unicode normalization 不逃逸。
- 同 base revision 的并行 patch 只有一个提交或得到确定 merge。
- killpoint 覆盖 intent 前后、external commit 前后、receipt 前后、checkpoint 前后。
- resume 不重复已批准且已 receipt 的动作。
- timeout/cancel 后进程树、临时 credential 和 lease 均清理。
- local/container/remote 的成功与失败 envelope 符合相同 schema。
- snapshot + event projection 能定位 artifact、execution、task 与 checkpoint lineage。
