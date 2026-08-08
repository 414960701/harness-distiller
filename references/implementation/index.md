# 实现规范导航

## 为什么需要这一层

共享知识文档解释能力边界，产品 dossier 解释产品差量，但两者不足以直接约束代码。若没有实现规范，另一个模型很容易生成“能调用模型和 shell 的聊天壳”，却遗漏事件、恢复、审批范围、幂等、协议版本和 UI 重建。

本层补齐以下原缺口：

| 原缺口 | 后果 | 必读文档 |
|---|---|---|
| 领域对象没有字段级合同 | thread/turn/message/tool 混成一个数组 | [domain-model.md](domain-model.md) |
| command/event 没有 schema 与兼容规则 | UI 与 runtime 紧耦合，无法重连 | [protocol.md](protocol.md) |
| Agent loop 只有概念，没有状态和伪代码 | 取消、重试、steering、压缩产生竞态 | [agent-loop.md](agent-loop.md) |
| 上下文没有装配算法和预算 | 大仓库、长会话立即失控 | [context.md](context.md) |
| ToolSpec、结果和 artifact 不完整 | 工具只返回字符串，副作用无法恢复 | [tools.md](tools.md) |
| 权限与执行边界没有动作规范化 | approval 被误当 sandbox | [policy-execution.md](policy-execution.md) |
| 缺少数据库表、事务和恢复算法 | 重启后重复执行副作用 | [storage.md](storage.md) |
| 缺少 UI 状态模型 | 界面靠运行时内存和日志拼接 | [ui.md](ui.md) |
| Artifact 只有“文件存在”检查 | DOCX/XLSX/PPTX/PDF 损坏仍显示 Ready | [artifact-validation.md](artifact-validation.md) |
| 缺少分阶段文件清单 | 模型一次生成大量不可运行代码 | [delivery.md](delivery.md) |
| 缺少技术栈落地差异 | 语言选择随意、无法维护 | [stack-selection.md](stack-selection.md) |
| 缺少统一验收矩阵 | “看起来像”替代真正完整 | [validation.md](validation.md) |

## 读取规则

任何新建 Harness 必须读取：`domain-model`、`protocol`、`agent-loop`、`tools`、`policy-execution`、`storage`、`delivery`、`validation`。

同时读取 `references/capabilities.md`，用其逐能力 oracle 决定 selected、implemented 或 verified；不要自行降低判定标准。

再按能力读取：

- 长会话、代码索引、记忆：`context`；
- CLI/TUI/IDE/Desktop/Web：`ui`；
- 文档、表格、演示、PDF、图片或网页成品：`artifact-validation`；
- 新项目技术选型：`stack-selection`；
- 具体产品行为：所选产品目录 13 篇 dossier；
- 具体能力实现的边界和失败模式：`references/knowledge/<capability>.md`。

## 实现顺序

```text
domain types
  -> protocol schemas
  -> event store skeleton
  -> model adapter
  -> turn state machine
  -> one read tool
  -> policy + workspace executor
  -> one patch tool
  -> headless client
  -> persistence/recovery
  -> primary product surface
  -> context compaction
  -> extensions/subagents/remote
```

不得在 protocol、event store 和 policy 边界建立前先批量添加工具或界面。

## 质量标记

实现文档中的：

- `MUST`：缺失即不能称为完整；
- `SHOULD`：当前等级要求时必须实现，低等级可记录 deferred；
- `MAY`：产品差量或优化；
- `INVARIANT`：所有等级不得破坏。
