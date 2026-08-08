# Codex 公开源码地图与论断

## 目录

1. 证据规则
2. 固定研究快照
3. 架构与循环
4. 协议与客户端服务
5. 工具与执行
6. 状态与恢复
7. 安全与权限
8. 界面与测试
9. 官方文档
10. 不可公开验证的边界

## 证据规则

本文件只把可公开验证的事实绑定到固定 commit permalink。
链接固定到 `92fb33b7583ac909a21efaebcd2fad6e79643a6f`，避免 main 分支版本变化导致论断漂移。
目录链接证明模块存在与边界，具体行为优先引用文件或测试。
本 dossier 中标记为`设计综合`的 schema、SLO、伪代码和验收不是原产品内部实现声明。
不得从公开文件名反推私有服务、专有 prompt 或未公开线上架构。

## 固定研究快照

- 仓库：[openai/codex](https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f)
- Rust workspace：[codex-rs](https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs)
- 许可证：[Apache-2.0 LICENSE](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/LICENSE)
- 研究日期：2026-08-08
- 使用限制：可借鉴公开行为与架构，不复制品牌资产或不可验证材料。

## 架构与循环

| 公开论断 | 固定源码 |
|---|---|
| core session 被拆成 turn、step context、input queue、multi-agent 等模块 | [core/session](https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/session) |
| turn 运行逻辑有独立实现文件 | [session/turn.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/session/turn.rs) |
| 每步上下文有独立表示 | [step_context.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/session/step_context.rs) |
| 运行中输入队列有独立模块 | [input_queue.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/session/input_queue.rs) |
| thread runtime 有独立类型 | [codex_thread.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/codex_thread.rs) |
| turn 状态与 session 状态分开 | [state/turn.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/state/turn.rs)、[state/session.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/state/session.rs) |
| 压缩有独立实现与上下文窗口检查 | [compact.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/compact.rs)、[context_window.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/session/context_window.rs) |
| 多代理 session 路径公开存在 | [multi_agents.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/session/multi_agents.rs) |

这些来源支持“headless、多步、可取消 runtime”的蒸馏方向，但不证明本文伪代码逐行等同原实现。

## 协议与客户端服务

| 公开论断 | 固定源码 |
|---|---|
| app-server README 描述客户端协议与 API | [app-server/README.md](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/app-server/README.md) |
| 共享 protocol 定义协议类型 | [protocol.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/protocol/src/protocol.rs) |
| item 类型单独建模 | [items.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/protocol/src/items.rs) |
| capabilities 有显式类型和测试 | [capabilities.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/protocol/src/capabilities.rs)、[capabilities_tests.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/protocol/src/capabilities_tests.rs) |
| app-server 分离 thread 与 turn request processor | [thread_processor.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/app-server/src/request_processors/thread_processor.rs)、[turn_processor.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/app-server/src/request_processors/turn_processor.rs) |
| 服务端维护 thread state/status | [thread_state.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/app-server/src/thread_state.rs)、[thread_status.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/app-server/src/thread_status.rs) |
| 公开测试覆盖 start、fork、resume、rollback、steer 与 interrupt | [v2 test suite](https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/app-server/tests/suite/v2) |

本文 [protocol-state.md](protocol-state.md) 的 JSON 字段是可移植设计，不宣称复制公开 protocol 的 wire schema。

## 工具与执行

| 公开论断 | 固定源码 |
|---|---|
| 工具 registry 与 router 独立 | [registry.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/tools/registry.rs)、[router.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/tools/router.rs) |
| apply patch 有 parser 和 runtime | [apply-patch crate](https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/apply-patch/src)、[tool runtime](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/tools/runtimes/apply_patch.rs) |
| shell handler、spec 和 runtime 分离 | [shell handler](https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/tools/handlers/shell)、[shell runtime](https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/tools/runtimes/shell) |
| 统一 exec 支持 command 与 stdin continuation | [unified_exec handlers](https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/tools/handlers/unified_exec) |
| PTY 与 process group 有跨平台工具模块 | [utils/pty](https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/utils/pty/src) |
| 非交互 exec 有 JSONL 与人类输出处理器 | [exec event processors](https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/exec/src) |
| shell command parsing/safety 是独立 crate | [shell-command](https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/shell-command/src) |

## 状态与恢复

| 公开论断 | 固定源码 |
|---|---|
| core 有 rollout 写入实现 | [rollout.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/rollout.rs) |
| session 有 rollout reconstruction 与测试 | [rollout_reconstruction.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/session/rollout_reconstruction.rs)、[tests](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/session/rollout_reconstruction_tests.rs) |
| state crate 包含 SQLite 与 migrations | [sqlite.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/state/src/sqlite.rs)、[migrations.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/state/src/migrations.rs) |
| state runtime 有 recovery 实现和测试 | [recovery.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/state/src/runtime/recovery.rs)、[recovery_tests.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/state/src/runtime/recovery_tests.rs) |
| rollout migration 被显式建模 | [rollout_migration.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/state/src/runtime/rollout_migration.rs)、[app-server migration tests](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/app-server/tests/suite/v2/rollout_migration.rs) |

本文推荐的 SQL schema、事务 marker 与 exactly-once 策略是设计综合。

## 安全与权限

| 公开论断 | 固定源码 |
|---|---|
| approval 有独立 core 模块和测试 | [approvals.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/tools/approvals.rs)、[tests](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/tools/approvals_tests.rs) |
| sandboxing 在 core tool 层有抽象 | [tools/sandboxing.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/tools/sandboxing.rs) |
| 配置层有 permissions 与 resolved profile | [permissions.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/config/permissions.rs)、[resolved_permission_profile.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/config/resolved_permission_profile.rs) |
| 仓库包含平台 sandbox crate | [sandboxing](https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/sandboxing)、[linux-sandbox](https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/linux-sandbox)、[windows-sandbox-rs](https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/windows-sandbox-rs) |
| 网络审批有独立实现与测试 | [network_approval.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/tools/network_approval.rs)、[tests](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/core/src/tools/network_approval_tests.rs) |

## 界面与测试

- TUI 源码：[codex-rs/tui/src](https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/tui/src)
- exec 测试：[codex-rs/exec/src tests](https://github.com/openai/codex/tree/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/exec/src)
- app-server mock model：[mock_model_server.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/app-server/tests/common/mock_model_server.rs)
- app-server rollout fixture：[rollout.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/app-server/tests/common/rollout.rs)
- turn steering 测试：[turn_steer.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/app-server/tests/suite/v2/turn_steer.rs)
- turn interrupt 测试：[turn_interrupt.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/app-server/tests/suite/v2/turn_interrupt.rs)
- thread resume 测试：[thread_resume.rs](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/codex-rs/app-server/tests/suite/v2/thread_resume.rs)

## 官方文档

- CLI：[Codex CLI](https://learn.chatgpt.com/docs/codex/cli)
- 安全：[Security](https://learn.chatgpt.com/docs/security)
- MCP：[Model Context Protocol](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)
- Skills：[Build skills](https://learn.chatgpt.com/docs/build-skills)
- 仓库 exec 文档：[docs/exec.md](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/docs/exec.md)
- 仓库 sandbox 文档：[docs/sandbox.md](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/docs/sandbox.md)
- 仓库 exec policy：[docs/execpolicy.md](https://github.com/openai/codex/blob/92fb33b7583ac909a21efaebcd2fad6e79643a6f/docs/execpolicy.md)

## 不可公开验证的边界

- 线上服务的私有拓扑、容量和调度策略；
- 私有模型权重、隐藏 reasoning 和服务端 system prompt；
- 未进入公开仓库的认证、风控、遥测或实验系统；
- 产品 UI 的未发布行为与内部路线图；
- 任何仅由截图、传闻或逆向猜测得出的内部实现。

遇到这些内容时只写能力目标或替代设计，并标记为`设计综合`。
本目录入口见 [index.md](index.md)，产品非目标见 [product-contract.md](product-contract.md)。
