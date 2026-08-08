# AgentScope 产品蒸馏索引

## 产品定位

本目录把 AgentScope 2.x 蒸馏成可交给其他大模型执行的实现 dossier。目标不是复刻品牌或页面，而是复现其公开的 Agent/Model/Context/Tool/Plan/Permission/Middleware/RAG/Long-Term Memory/Workspace 构件，以及从单 Agent 到 Service、Team、Channel 的部署路径。

研究快照：

- status: implementation-ready
- retrieved: 2026-08-08
- stable baseline: `v2.0.6`
- commit: `29b592358c2e983a0d10dd5227316b7a02d8c23a`
- repository: https://github.com/agentscope-ai/agentscope
- license: Apache-2.0
- GitHub API stars: 28713（抓取时动态快照，不是质量承诺）

## 事实边界

- **官方事实**：`2.0.6dev` 文档把上述十类 building blocks 分页，并公开 Agent Service、Agent Team、Workspace Manager 与 Channel。
- **源码事实**：固定 commit 中存在 Agent ReAct loop、Message/Event、PermissionEngine、Workspace 与 app/message-bus/storage/channel 等实现。
- **设计综合**：本 dossier 为复刻仓库补充 thread/turn/item 外层协议、幂等键、事务和测试 oracle；这些是可靠 harness 所需合同，不声称是 AgentScope 原字段。
- **禁止推断**：permission decision、LocalWorkspace、MCP Gateway 都不自动等于 OS sandbox。只有明确选择并验证 bubblewrap/container/remote sandbox backend，才能声明对应隔离等级。

## 十三篇导航

1. [sources.md](sources.md)：固定版本、源码地图、dev 文档边界与论断矩阵。
2. [product-contract.md](product-contract.md)：可观察行为、能力合同、非目标与 SLO。
3. [architecture.md](architecture.md)：组件、信任边界、service/team/channel 拓扑。
4. [agent-loop.md](agent-loop.md)：ReAct 状态机、终止、取消、重试和 HITL。
5. [protocol-state.md](protocol-state.md)：thread/turn/item/event 与 AgentScope message/event 映射。
6. [context-tools.md](context-tools.md)：Model、Context、Tool、Plan、Middleware、RAG、LTM。
7. [workspace-execution.md](workspace-execution.md)：Workspace、backend、MCP gateway 与执行规范。
8. [safety-runtime.md](safety-runtime.md)：permission mode/rule/tool check 与 enforcement。
9. [persistence-recovery.md](persistence-recovery.md)：state、service storage、事务、恢复和迁移。
10. [experience.md](experience.md)：SDK、service、team、channel 的事件投影体验。
11. [recipe.md](recipe.md)：四级差量、直接升级顺序与生成仓库结构。
12. [acceptance-tests.md](acceptance-tests.md)：分级黑盒、安全、故障注入和 oracle。

十三篇包含本索引。实现模型应按以上顺序阅读，不能只读取配方。

## 复刻仓库最低结构

- `protocol/`：命令、事件、schema、版本与 golden fixtures；
- `runtime/`：agent actor、model adapter、context assembler、middleware pipeline；
- `tools/`：tool registry、permission check、MCP/skill adapter；
- `executor/`：workspace、backend、artifact 与 sandbox adapter；
- `state/`：session、reply、event log、checkpoint、迁移；
- `service/`：API、message bus、team、channel、workspace manager；
- `surfaces/`：CLI/Web/channel projection；
- `tests/`：scripted model、fake tool/backend、恢复和等级验收。

## 给生成模型的硬约束

- 先选 `runnable | usable | productive | polished`，再展开该等级及以前的 capability。
- 核心 loop 只依赖 adapter；不得在 agent 类里硬编码模型厂商、Redis、Web 框架或容器 SDK。
- 每个工具调用都经过规范化、permission decision、execution boundary、result commit 四阶段。
- Event 必须可重放；channel 不得直接持有进程内 Agent 对象。
- dev 文档与固定 tag 冲突时，以固定源码为事实，dev 页面仅标记未来/开发中能力。
- 未配置强制 sandbox 时必须显示 `enforcement=host-process` 或等价降级状态。

## 完成判定

只有在 [acceptance-tests.md](acceptance-tests.md) 对应等级全部通过，能力才可标记 `verified`。文档存在、接口可调用或 demo 成功均不足以升级。闭源服务行为、内部提示词、官方视觉和未固定的 `main` 行为不在复刻承诺内。
