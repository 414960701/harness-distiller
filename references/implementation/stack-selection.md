# 技术栈选择与落地差异

## 决策表

| 条件 | 首选 | 理由 |
|---|---|---|
| TUI/headless、强沙箱、单二进制 | Rust | 并发、类型、分发与系统边界强 |
| IDE/Desktop/Web、多前端 | TypeScript | UI/扩展生态、共享 schema 与 SDK |
| 研究框架、RAG/ML、快速服务 | Python | 模型/RAG 生态与开发速度 |
| QoderWork-like 桌面 | TypeScript + Tauri/Rust executor | UI 效率与本地安全边界分层 |
| Codex-like CLI | Rust runtime；可配 TS/Python 客户端 | headless core 与表面解耦 |
| Claude-like 多表面 | 强类型 headless runtime + 多客户端 | 产品内部未知，不依赖推断语言 |
| Aider-like CLI | Python | 与公开实现、tree-sitter/NetworkX、快速编辑迭代一致 |
| AgentScope / Deep Agents | Python | 与公开框架、RAG/模型生态和 SDK 使用方式一致 |

## 所有语言共同要求

- 从同一 JSON Schema/IDL 生成协议类型；
- domain、adapter、policy、executor、surface 使用接口边界；
- provider SDK 对象不穿透 domain；
- cancellation 使用结构化 token/context；
- 数据库迁移、event fixture 和协议兼容测试独立于 UI；
- shell/path/network 操作集中在 executor，不散落业务代码。

## TypeScript

推荐 workspace：`packages/protocol`, `core`, `model`, `tools`, `execution`, `state`, `sdk`, `cli`, `desktop`, `ide`。启用 `strict`、discriminated unions、运行时 schema 校验。Node/Bun 进程管理必须显式杀进程树；桌面高风险执行放到 Tauri/Rust sidecar 或隔离服务。

避免：只依赖 TS 类型而不校验外部 JSON；把 Electron main process 作为无限权限工具；让 React store 成为权威状态。

## Rust

推荐 crates：`protocol`, `core`, `model`, `tools`, `policy`, `executor`, `state`, `app-server`, `tui`, `cli`。使用 enum 表达状态、`serde` schema、`tokio` cancellation、事务数据库与 trait adapter。平台 sandbox 分 crate，避免 `cfg` 逻辑污染 core。

避免：跨 await 持有全局锁；错误字符串充当协议；TUI 直接引用 mutable session internals。

## Python

推荐 packages：`protocol`, `runtime`, `models`, `tools`, `policy`, `execution`, `state`, `server`, `cli`。使用 Pydantic/等价 schema、asyncio structured concurrency、明确 transaction/session scope。CPU/不可信工具放 worker/process/container。

避免：任意 dict 贯穿全栈；async task 无所有者；在 web server 进程内直接运行不可信 shell；pickle 持久化协议对象。

## 混合栈

只在边界收益明确时使用：例如 TS UI + Rust executor、Python RAG service + Rust core。跨语言接口必须走版本化协议，不共享数据库内部表或 FFI 任意对象。先完成单进程 vertical slice，再拆服务。

## 选择输出

在 decisions.md 记录：选择、替代方案、产品表面、团队能力、安全边界、分发、性能、调试和迁移成本。不得只写“因为熟悉”。
