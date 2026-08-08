# 共享知识导航

每个知识点独立维护一篇文档。读取产品 `recipe.md` 后，只加载其 `required` 与当前等级新增模块。共享知识解释单项能力，`references/implementation/` 解释跨能力的字段、算法和事务；二者缺一不可。

| 组 | 模块 | 首版状态 |
|---|---|---|
| 内核 | [agent-loop](agent-loop.md), [model-adapter](model-adapter.md), [protocol-events](protocol-events.md), [context-engine](context-engine.md), [tool-runtime](tool-runtime.md), [planning](planning.md), [middleware-hooks](middleware-hooks.md), [state-persistence](state-persistence.md) | drafted |
| 执行安全 | [workspace](workspace.md), [filesystem](filesystem.md), [shell-process](shell-process.md), [patch-edit](patch-edit.md), [sandbox](sandbox.md), [permission-policy](permission-policy.md), [network-secrets](network-secrets.md), [browser-computer](browser-computer.md), [git-worktree](git-worktree.md) | drafted |
| 知识扩展 | [rag-index](rag-index.md), [long-term-memory](long-term-memory.md), [mcp](mcp.md), [skills-plugins](skills-plugins.md), [subagents](subagents.md), [instructions-prompts](instructions-prompts.md) | drafted |
| 产品表面 | [cli-tui](cli-tui.md), [ide](ide.md), [desktop-web](desktop-web.md), [diff-review](diff-review.md), [notifications-input](notifications-input.md), [auth-settings](auth-settings.md) | drafted |
| 质量运维 | [observability](observability.md), [evals](evals.md), [testing](testing.md), [reliability](reliability.md), [performance-cost](performance-cost.md), [deployment-update](deployment-update.md) | drafted |

## 单篇完整度要求

每篇最终必须包含：

1. 职责、边界与明确非目标；
2. 输入、输出、状态、schema 或接口合同；
3. runnable/usable/productive/polished 四级同架构增量；
4. 从低等级直接升级的迁移顺序与回滚点；
5. 失败模式、安全风险和反例；
6. 可执行验收、故障注入或测试 oracle；
7. 公开来源、版本或明确的设计综合标记。

`drafted` 表示已描述边界但仍可能缺少字段级合同或充分源码锚点；`implementation-ready` 表示上述七部分齐全；`verified` 还要求主要论断可追溯且验收场景已在生成工程运行。不得因篇幅长就标记为 verified。
