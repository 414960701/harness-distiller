---
name: harness-distiller
description: 蒸馏、设计、实现、复刻或升级完整的 AI Agent Harness，支持 Codex、Claude Code、QoderWork、OpenCode、OpenHands、AgentScope、LangGraph 等产品配方。用于把公开产品行为、官方文档与开源代码证据转成可执行的架构、协议、状态机、工具、权限、沙箱、上下文、持久化、界面和验收方案，并按“能跑、能用、顺手、好用”四级生成或原位升级 CLI、TUI、IDE、桌面、Web、SDK 或 headless Agent 工程。
---

# Harness Distiller（Agent Harness 蒸馏器）

把公开证据蒸馏成可实现、可验证、可升级的 Agent Harness。把产品名视为行为与能力配方，不复制品牌、专有提示词、受保护素材或无法验证的内部实现。

## 必须遵守

1. 区分 `code`、`official-doc`、`protocol`、`behavior`、`inference`；不得把闭源产品推断写成源码事实。
2. 四个成熟度等级共用同一协议、状态模型和模块边界；升级只增加能力与优化，不生成互不兼容的四套工程。
3. 先打通垂直切片：模型 → Agent loop → 一个读取工具 → 权限 → 执行 → 事件 → 状态 → 界面。
4. 保持 runtime headless；CLI、TUI、IDE、桌面与 Web 只通过版本化 command/event 协议交互。
5. 把 approval policy 与 sandbox enforcement 分开；用户批准不能代替 OS、容器、路径或网络强制边界。
6. 每项“已实现”都要有代码位置；每项“已验证”都要有可运行的测试或可重复行为证据。
7. 不把模型能调用 shell 当成“完整 Harness”。必须实现取消、失败、恢复、持久化、权限和界面状态重建。

## 按需读取

- 选择产品和检查目录完整度：读取 [references/catalog.md](references/catalog.md)。
- 选择等级或跨级升级：读取 [references/levels.md](references/levels.md)。
- 判断每个 capability 何时可标为 verified：读取 [references/capabilities.md](references/capabilities.md)。
- 判断证据可靠性：读取 [references/evidence.md](references/evidence.md) 和 [references/source-registry.md](references/source-registry.md)。
- 理解共享边界：读取 [references/architecture.md](references/architecture.md)。
- 开始落代码前：必须读取 [references/implementation/index.md](references/implementation/index.md)，再按其路由加载实现规范。
- 选择共享能力：读取 [references/knowledge/index.md](references/knowledge/index.md)，只加载蓝图选中的知识模块。
- 复刻某个产品：读取 `references/products/<product>/index.md`，并按索引指定顺序加载该产品的 13 篇 dossier。
- 新建工程：读取 [references/workflows/build.md](references/workflows/build.md)。
- 升级已有工程：读取 [references/workflows/upgrade.md](references/workflows/upgrade.md)。
- 验收工程：读取 [references/workflows/validate.md](references/workflows/validate.md)。

## 解析请求

从用户请求和目标仓库解析：

- `recipe`：一个产品、`hybrid` 或 `custom`；
- `level`：`runnable`、`usable`、`productive` 或 `polished`；
- `surfaces`：`cli`、`tui`、`ide`、`desktop`、`web`、`sdk`、`headless`；
- `execution`：`local`、`container`、`remote` 或组合；
- `stack`：优先沿用目标仓库；新项目按产品表面和安全要求选择；
- `providers`：模型提供商、本地模型与能力降级要求；
- `security`：个人、团队或企业威胁模型；
- `distribution`：源码、包、扩展、桌面应用或托管服务。

用户只说“做一个像 Codex/Claude Code/QoderWork 的产品”时，默认选择对应 recipe、`usable`、产品主表面加 `headless`，并把假设写入决策记录。

缺少其它选择时使用可回退默认值：`execution=local`、`security=personal`、`distribution=source`；Codex-like 默认 Rust + headless/TUI，Claude-Code-like 默认 TypeScript + headless/CLI，QoderWork-like 默认 TypeScript + Tauri/Rust executor + headless/Desktop，Aider-like 默认 Python + headless/CLI，OpenCode 默认 TypeScript/Bun + headless/TUI，OpenHands 默认 Python + TypeScript/React + headless/Web/SDK，AgentScope、LangGraph 与 Deep Agents 默认 Python + headless/SDK。Provider 未指定时先实现 provider-neutral contract、确定性 scripted fixture 和 OpenAI-compatible adapter 接口，不擅自绑定付费服务；真正联调前再要求用户提供 provider 配置。

## 生成流程

1. 检查仓库、技术栈、现有指令、dirty changes 和可用运行环境。
2. 在 [references/catalog.md](references/catalog.md) 确认产品为实现级；计划中但未完成 13 篇 dossier 的 recipe 不得生成产品复刻，先补 dossier 或显式改用 `hybrid/custom`。再运行 `scripts/new_blueprint.py` 创建 `.harness-distill/blueprint.yaml`。
3. 读取产品 `index.md`、`product-contract.md`、`recipe.md`、`acceptance-tests.md`。
4. 按 recipe 加载实现规范和共享知识文档，建立 capability 依赖闭包。
5. 写 `.harness-distill/evidence.md`，记录论断、URL、日期、版本/commit、证据类型和置信度。
6. 写 `.harness-distill/decisions.md`，记录架构选择、闭源推断、非目标、风险和回滚点。
7. 先实现协议、状态骨架和一个可执行垂直切片；保存并重放其事件 trace。
8. 按 `schema → protocol → runtime → executor/policy → surface → migration` 顺序补齐能力。
9. 同时添加 contract、scenario、security、recovery、migration 和产品黑盒测试。
10. 运行 `scripts/validate_blueprint.py`、目标仓库检查和产品 `acceptance-tests.md`。
11. 只把具有实现位置和测试证据的 capability 标为 `verified`。

## 生成物最低合同

目标工程必须包含等价边界：

```text
.harness-distill/
  blueprint.yaml       # 选择、等级、能力、状态和合同版本
  evidence.md          # 公开证据与推断边界
  decisions.md         # 架构决策、非目标、风险和迁移
src/
  protocol/            # command/event/error/schema/capability negotiation
  runtime/             # turn 状态机、取消、重试、预算、steering
  model/               # provider adapter 与能力协商
  context/             # 指令、检索、记忆、预算、压缩、缓存
  tools/               # schema、registry、router、lifecycle、artifact
  policy/              # allow/deny/ask/amend 与审批范围
  execution/           # workspace、文件、shell、patch、网络、sandbox
  state/               # thread/turn/item/event/checkpoint/migration
  surfaces/            # CLI/TUI/IDE/Desktop/Web adapter
tests/
  contracts/           # 协议、provider、tool 与存储合同
  scenarios/           # 真实任务闭环
  security/            # 越界、注入、秘密、网络和逃逸
  recovery/            # 崩溃、重复投递、断线和迁移
```

允许按语言惯例改名，但不得合并掉策略与强制执行、领域状态与 UI 投影、模型历史与持久事实之间的边界。

## 完整性闸门

满足以下全部条件才称为选定等级的完整 Harness：

- blueprint、产品合同和实现位置一致；
- runnable 的 thread/turn/item/event trace 可持久化并重放；usable 起支持分页与进程重启恢复；polished 再要求跨版本迁移；
- tool call/result 原子配对，取消、超时和迟到结果语义明确；
- 选择 context 压缩后，不破坏工具调用原子性、指令层级和审计范围；
- 受限动作先由策略决策，再由真实执行边界强制；
- UI 可用 snapshot + event 重建，不依赖 runtime 内存对象；
- usable 及以上的崩溃恢复不会重复不可逆副作用；
- 产品 `acceptance-tests.md` 的当前等级场景通过；
- 交付说明列出未支持行为、证据缺口和直接升级路径。

## 跨级升级

直接从任意低等级升级到高等级时：

1. 验证当前 blueprint、协议和数据库 schema；
2. 计算 capability delta 并展开中间依赖；
3. 先迁移 schema，再扩协议、runtime、执行器和界面；
4. 保持旧配置和旧事件至少一个兼容迁移边界；
5. 为不可逆外部动作建立 checkpoint、幂等键或人工确认；
6. 运行所有低等级回归和新等级验收；
7. 测试通过后再更新 capability 状态。
