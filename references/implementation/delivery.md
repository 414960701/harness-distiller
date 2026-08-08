# 分阶段交付计划

## Phase 0：蓝图与证据

生成：blueprint、evidence、decisions、威胁模型、产品合同、目录树。不得写大批业务代码前跳过。

退出条件：产品 recipe、等级、surface、stack、provider、execution、安全边界和 non-goals 已确定。

## Phase 1：协议与状态骨架

实现 domain types、JSON Schema、event envelope、thread/turn/item repository、append-only 本地 trace writer、内存 projection store、headless command client。runnable 可用 JSONL/等价顺序日志，不要求此时引入完整数据库。

退出条件：golden schema 通过；进程退出后仍能从落盘 trace 重建 ThreadView；截断尾记录可诊断且不会伪造完成事件。

## Phase 2：最薄垂直切片

实现一个 model adapter、turn loop、file.read、基础 policy、workspace root、agent message streaming。

退出条件：真实模型或确定性 fixture 完成“读取文件并回答”，取消和模型错误有明确终态。

## Phase 3：真实编码闭环

实现 patch.apply、process.exec、git status/diff、approval、artifact、change set、测试命令。

退出条件：完成真实 fixture bugfix；越界写被阻止；diff 可审查；测试失败可反馈修复。

## Phase 4：持久化与长任务

实现数据库、outbox、resume、checkpoint、compaction、plan、PTY continuation、故障恢复。

退出条件：在 model/tool/transaction 各关键点 kill 进程后恢复，不重复不可逆副作用。

## Phase 5：产品主表面

按 recipe 实现 Codex TUI、Claude-style CLI/IDE、QoderWork Desktop 等主表面。只消费协议事件。

退出条件：产品黑盒 runnable/usable 场景通过；断线重连能重建。

## Phase 6：扩展与生产优化

加入 MCP、skills、plugins、hooks、subagents、worktree、remote executor、memory/RAG、observability/evals。

退出条件：productive/polished capability 有实现位置和测试；供应链、权限与兼容策略成立。

## 每阶段交付记录

```yaml
capability: tools.patch
status: verified
implementation:
  - src/tools/patch.ts
contracts:
  - tests/contracts/patch.spec.ts
scenarios:
  - tests/scenarios/fix_fixture_bug.spec.ts
evidence:
  - .harness-distill/evidence.md#codex-apply-patch
known_gaps: []
```

没有 implementation 与 test 路径的 capability 不得标 verified。
