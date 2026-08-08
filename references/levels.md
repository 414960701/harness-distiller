# 成熟度等级与原位升级

## 四级模型

| 等级 | 中文名 | 目标 | 必须具备 |
|---|---|---|---|
| `runnable` | 能跑 | 一条可靠的端到端任务链 | 单 Agent loop、模型适配、文件读取、补丁或写入、命令工具、workspace 边界、基础审批、模型/进程取消、流式事件、烟雾测试 |
| `usable` | 能用 | 可连续完成真实仓库任务 | thread/turn/item 状态、会话恢复、计划、上下文预算与压缩、结构化 diff、MCP、配置、重试/取消、CLI/TUI 或 IDE 主表面、场景测试 |
| `productive` | 顺手 | 低摩擦、高吞吐的日常工具 | 增量索引、前缀缓存、后台任务、worktree、subagent、hooks、细粒度权限、检查点、观测与 eval、多个表面共享协议 |
| `polished` | 好用 | 产品级稳定、安全与可演进 | OS/容器强制沙箱、网络策略、自动审批审查、插件/技能生命周期、远程执行、协议协商、数据迁移、无障碍/国际化、发布更新与生产 SLO |

等级表示同一合同的实现深度，不表示四套产品。`usable -> polished` 可以直接升级，但必须按依赖拓扑执行中间迁移，不要求用户先运行 `productive` 版本。

## 不变量

所有等级共享：

- `Command`, `Event`, `Thread`, `Turn`, `Item`, `ToolSpec`, `ToolCall`, `ToolResult`, `PolicyDecision` 的稳定语义；
- 模型层、工具层、执行层、策略层、状态层、界面层的边界；
- capability id 与版本；
- 可取消的 turn 和幂等的持久化写入；
- 证据、决策和验证记录。

## 升级表示

在 `.harness-distill/blueprint.yaml` 中逐能力记录：

```yaml
capabilities:
  context.compaction:
    target_level: usable
    status: verified
    contract_version: 1
  execution.sandbox:
    target_level: polished
    status: implemented
    contract_version: 2
```

升级器比较能力级别，不比较产品名。产品配方只改变默认能力集合和验收场景。

## 直接升级算法

1. 验证当前 manifest 和数据库 schema。
2. 计算 `current < target` 的 capability delta。
3. 展开依赖，例如强制沙箱依赖 command normalization、workspace roots 和 policy decision。
4. 按 `schema -> protocol -> runtime -> surface -> migration cleanup` 排序。
5. 为每一项建立回滚点、兼容读取和验收场景。
6. 完成后仍运行当前等级以下的全部合同测试。

## 防止“伪升级”

以下不是等级提升：

- 只增加 prompt 长度；
- 换一个模型并宣称 agent 变强；
- 多放几个工具但没有权限、取消、错误语义；
- 新写一套 UI 绕过原事件协议；
- 用字符串黑名单冒充沙箱；
- 用摘要覆盖原历史而没有可审计的压缩边界。
