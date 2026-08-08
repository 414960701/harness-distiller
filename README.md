# Harness Distiller

Harness Distiller 是一套面向 AI Agent Harness 的设计与实现知识库，也可以作为 Codex Skill 使用。它把公开产品行为、官方文档和开源代码证据，整理成可执行、可验证、可升级的架构与工程方案。

项目关注的不只是 Agent Loop，还覆盖协议、状态、上下文、工具、权限、沙箱、持久化、恢复、界面和验收，目标是帮助你从零构建或原位升级完整的 Agent Harness。

## 能做什么

- 按 `runnable`、`usable`、`productive`、`polished` 四级规划能力演进
- 生成统一的 Harness blueprint，而不是四套互不兼容的工程
- 复用 Codex、Claude Code、QoderWork、Aider、OpenCode、OpenHands、AgentScope、LangGraph、Deep Agents 等产品配方
- 为协议、运行时、权限、执行、存储、恢复和 UI 提供实现规范
- 用脚本检查知识模块、产品 dossier 和 blueprint 的完整性

## 目录

```text
SKILL.md                         Codex Skill 入口与工作流
agents/                          Agent 配置
assets/contracts/                Blueprint、事件与工具 JSON Schema
references/architecture.md       共享架构边界
references/implementation/       可直接落地的实现规范
references/knowledge/            共享能力知识模块
references/products/             产品 dossier、配方与验收测试
references/workflows/            新建、升级与验收流程
scripts/                         Blueprint 生成与一致性检查工具
```

## 作为 Codex Skill 安装

```bash
git clone https://github.com/414960701/harness-distiller.git \
  ~/.codex/skills/harness-distiller
```

安装后，可在 Codex 中用类似下面的请求触发：

```text
用 harness-distiller 帮我做一个 usable 级的 Codex-like TUI Agent。
```

也可以直接阅读 [SKILL.md](SKILL.md)，按其中的路由加载所需参考资料。

## 脚本

项目脚本只依赖 Python 标准库。

```bash
# 查看当前知识模块与产品 dossier 库存
python3 scripts/check_inventory.py

# 验证共享知识模块
python3 scripts/validate_knowledge.py

# 验证全部实现级产品 dossier
python3 scripts/validate_dossier.py

# 为目标工程生成 blueprint
python3 scripts/new_blueprint.py \
  --target /path/to/project \
  --recipe codex \
  --level usable

# 验证目标工程的 blueprint
python3 scripts/validate_blueprint.py /path/to/project
```

`check_inventory.py --strict` 会要求规划中的全部产品 dossier 都已完成；当前仓库在持续补全中，因此普通检查和严格检查的语义不同。

## 设计原则

- 明确区分源码事实、官方文档、协议、可观察行为和推断
- Runtime 保持 headless，各类界面只通过版本化 command/event 协议交互
- Approval policy 与真正的 sandbox enforcement 分离
- “已实现”必须能定位到代码，“已验证”必须有可重复的测试证据
- 优先打通可执行垂直切片，再逐级增加能力

## 贡献

欢迎提交 Issue 或 Pull Request。新增产品 dossier 时，请保持既有 13 篇文档结构，并运行相关校验脚本。

## 许可证

[MIT](LICENSE)
