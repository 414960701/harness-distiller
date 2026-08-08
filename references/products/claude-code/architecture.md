# Claude Code 架构蒸馏

## 证据声明

本篇不是 Claude Code 内部源码解析。完整 runtime 源码不可见；以下把官方行为规格与本仓库实现推断分开。

## 官方公开的架构行为

### Agentic loop

kind: official-doc / behavior

官方把一次任务描述为持续交织的三阶段：

1. gather context；
2. take action；
3. verify results。

用户可随时 interrupt 或 steer；不同任务可能只收集上下文，也可能反复编辑、运行测试和修正。

来源：https://code.claude.com/docs/en/how-claude-code-works

### 模型与工具

kind: official-doc

模型负责推理和选择动作，Claude Code harness 提供工具、上下文管理和执行环境。工具调用可触发权限决策、hook、sandbox 和 UI 事件；工具结果进入后续模型上下文。

### Session

kind: official-doc

CLI session 持续保存本地 transcript，可 continue、resume、rename、branch/fork。默认 transcript 位于 ~/.claude/projects/<project>/<session-id>.jsonl；官方明确提示该内部行格式可能随版本变化，外部集成应优先使用 export、headless output 或 hook/statusline 提供的路径。

来源：https://code.claude.com/docs/en/sessions

### 多种表面

kind: official-doc

同一产品能力出现在 CLI、IDE、Desktop、Web 和 Agent SDK，但各表面的 session history 不一定是同一存储。不能从“体验相似”推断它们共享某个未公开进程或数据库。

## 公开仓库能证明什么

kind: public-repo

仓库可证明 plugin manifest、skills、agents、commands、hooks 和 MCP 集成示例的公开格式，例如 plugin-dev、feature-dev、hookify、PR review toolkit。它不能证明闭源主循环、上下文管理器、sandbox 或 TUI 的内部模块结构。

来源：

- https://github.com/anthropics/claude-code
- https://github.com/anthropics/claude-code/tree/main/plugins

## 本仓库实现推断

kind: inference / design synthesis

为实现上述行为，推荐而非声称 Claude 内部采用：

- headless runtime：Agent loop、policy、execution、state；
- versioned protocol：Command、Event、Thread、Turn、Item；
- append-first event/session store；
- CLI、IDE、Desktop/Web adapter；
- hook bus 与 plugin loader；
- local/container/remote execution adapter。

替代解释：Claude Code 各表面可能共享部分代码、通过本地服务通信，或采用不同实现；公开资料不足以判断。因此生成器只能保证自身协议一致，不能写“复刻 Claude 内部架构”。

## 实现合同路由

架构篇不再重复实现状态枚举。完整 turn/run 状态机、转移守卫和循环伪代码见 [agent-loop.md](agent-loop.md)。

跨表面的 Command/Event/Item 与投影规则见 [protocol-state.md](protocol-state.md)。这些名称均为蒸馏设计，不是公开内部枚举。

持久化和崩溃恢复见 [persistence-recovery.md](persistence-recovery.md)；安全执行边界见 [workspace-execution.md](workspace-execution.md)。

## 架构不变量

- 用户 interrupt 必须最终产生可观察终态。
- tool use 与 tool result 一一配对，hook 拒绝也生成结构化结果。
- session resume 不盲目恢复 bypass permissions 等高风险临时状态。
- subagent 使用独立上下文和权限边界。
- hook/plugin 不直接越过 policy 与 sandbox。
- CLI、IDE、Desktop/Web 的差异由 capability 描述，不靠隐式分支。

## 验证策略

由于内部源码不可见，采用黑盒合同测试：官方示例流程、文档承诺、CLI headless 输出、公开 hook/plugin fixture。不可验证的性能、压缩算法或内部事件名不得设为“与 Claude 完全一致”的验收条件。

可执行 oracle 和故障注入矩阵统一维护在 [acceptance-tests.md](acceptance-tests.md)，避免架构文档和测试文档产生两套完成标准。
