# Capability 验收定义

## 使用规则

蓝图中的 capability 只有同时具备实现路径、测试路径和下表 oracle 证据时才能标 `verified`。只创建接口标 `implemented`；只在计划中出现标 `selected`。

## runnable / 能跑

| Capability | verified 判定 |
|---|---|
| `runtime.agent-loop` | 无工具、单工具、多工具都能到唯一终态；最大步数、模型错误和自然结束有测试 |
| `model.adapter` | scripted fixture 与至少一个 provider-neutral contract suite 通过；流式文本/tool/error 可归一化 |
| `protocol.events` | thread/turn/item/tool 事件有 schema、sequence、golden fixture，并可重放最终投影 |
| `context.basic` | 按层装配系统/项目/用户/最近历史/显式文件；预算超限明确失败或裁剪；来源可追溯 |
| `tools.runtime` | ToolSpec/schema 校验、policy 前规范化、恰一个最终 ToolResult、大输出 artifact 化 |
| `tools.cancellation` | 模型流和前台进程可取消；进程树退出；取消/完成竞态只有一个终态 |
| `workspace.boundary` | canonical root containment、`..` 与 symlink escape 测试通过 |
| `filesystem.read` | 文本/二进制/大小/编码/权限错误有界处理，读取带 hash |
| `patch.apply` | base hash、冲突、跨文件失败和实际 diff 可验证，不覆盖用户并发改动 |
| `shell.foreground` | argv/cwd/env/timeout/output 有结构化合同；退出码、超时和错误可见 |
| `policy.basic-approval` | 写/执行等动作可 allow/deny/ask；approval 绑定规范化 action hash |
| `testing.smoke` | 至少一个真实 vertical slice 与模型/工具/权限失败 smoke case 通过 |

## usable / 能用

| Capability | verified 判定 |
|---|---|
| `state.persistence` | thread/turn/item/event 持久化；重启 resume；event 不丢不重；旧 fixture 可读 |
| `context.compaction` | 长历史压缩后保留目标/约束/变更/未决错误；不拆 tool call/result；原事件可审计 |
| `planning.steps` | step id/status/dependency/证据持久化；失败重规划与 steering 有测试 |
| `tools.mcp` | stdio 或 HTTP MCP 发现/调用/超时/断线/schema 变化；本地 policy 不被注解绕过 |
| `diff.review` | base/current/proposed 三方状态；stale/conflict、hunk 操作和实际应用结果一致 |
| `reliability.retry` | retryable 分类、jitter、retry-after、幂等键与 unknown-side-effect 不重试测试通过 |
| `testing.contracts` | model/tool/store/protocol adapter 共用合同套件，无网络可运行核心 fixtures |
| `testing.scenarios` | 产品 usable 黑盒任务、取消、拒绝、压缩、恢复和失败修复场景通过 |

## productive / 顺手

| Capability | verified 判定 |
|---|---|
| `rag.incremental-index` | 文件 hash/commit 驱动增量更新；rename/delete/ignore/ACL；陈旧命中注入前复核 |
| `context.stable-prefix` | 稳定指令/tool/sandbox 前缀 hash 可重复；动态状态追加；cache 指标证明收益 |
| `git.worktree` | 每任务隔离、dirty provenance、lease/cleanup、冲突和 handoff 测试通过 |
| `subagents.parallel` | 独立上下文/预算/权限/workspace；取消向下传播；结果 lineage；写冲突受控 |
| `hooks.lifecycle` | 顺序、超时、失败策略、递归限制、权限收紧和敏感字段脱敏有测试 |
| `policy.profiles` | path/tool/network/profile 规则优先级确定；deny 胜出；grant 有 scope/expiry |
| `state.checkpoints` | context/event/workspace 锚点一致；fork/rollback/崩溃恢复不重复副作用 |
| `observability.traces` | model/tool/policy/store trace 关联；脱敏；exporter 失败不阻塞 runtime |
| `evals.regression` | 固定 fixture、结构化 oracle、安全 gate、轨迹/cost 指标和版本 baseline |

## polished / 好用

| Capability | verified 判定 |
|---|---|
| `sandbox.enforced` | 真实 OS/容器边界；文件/进程/IPC/资源限制；sandbox 不可用时 fail closed；逃逸集通过 |
| `network.policy` | 默认 deny、域/IP/端口/redirect/private/DNS/Unix socket enforcement 与审计通过 |
| `policy.auto-review` | 只审查原本需要审批的动作；高风险/失败 fail closed；用户授权与规则可解释 |
| `plugins.lifecycle` | 安装/发现不等于授权；签名/身份、依赖、隔离、升级/回滚和坏插件恢复 |
| `execution.remote` | 认证、租约/fencing、路径映射、断线、receipt/idempotency 和能力证明 |
| `protocol.negotiation` | N/N-1 双向测试；未知可选字段忽略；必需语义协商；gap/reconnect |
| `deployment.migrations` | 数据/config/event/plugin schema 迁移可重复；kill-point、compat reader、回滚说明 |
| `deployment.signed-update` | 包/更新签名与来源验证、SBOM、灰度、失败回滚和 turn 中不热换 executor |
| `quality.accessibility-i18n` | 键盘/读屏/非颜色状态/200%缩放/reduced motion；本地化与时区格式测试 |
| `reliability.slo` | 成功/延迟/恢复/sandbox SLO、容量保护、告警、灾备演练和错误预算 |

## 产品附加闸门

共享 capability verified 不等于产品 parity 完成。还必须运行所选产品 `product-contract.md` 和 `acceptance-tests.md`；闭源不可确认项保持 `blocked-by-evidence`。

