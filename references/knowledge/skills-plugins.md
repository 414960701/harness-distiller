# Skills 与 Plugins

## 职责与非目标

Skill 是渐进披露的过程知识与支持资源；Plugin 是可安装、版本化的能力包，可包含 skills、tools、hooks、connectors 和应用元数据。
Skill 告诉 Agent“如何做”，不自动获得“允许做什么”；执行权限仍由本地 policy 和用户 grant 决定。
Plugin 不是任意启动脚本，安装成功也不等于启用、授权或信任。
MCP server 的互操作合同见 [MCP](mcp.md)，指令优先级见 [Instructions 与 Prompts](instructions-prompts.md)。

## Manifest 与运行 schema

```yaml
PluginManifest:
  id: reverse-dns-or-package
  version: semver
  publisher: string
  integrity: sha256|signature
  engine_range: string
  contributes: {skills: [], tools: [], hooks: [], connectors: []}
  permissions: [filesystem, network, secrets, computer_use]
SkillDescriptor:
  name: string
  description: string
  entrypoint: SKILL.md
  invocation: explicit|slash|auto
  support_paths: [relative_path]
  content_hash: string
```

状态分为 `discovered → installed → enabled → authorized`，更新为独立 `update_available → staged → activated|rolled_back`。
发现阶段只读短 metadata；触发后完整读取 `SKILL.md`，再按其链接按需加载资源。
解析支持文件时以 plugin/skill root 为边界，拒绝绝对路径、`..` 和符号链接逃逸。

## 调用与冲突

显式用户调用优先于自动匹配；自动匹配基于描述、scope 和当前目标，不执行资源正文来“判断”。
多个 Skill 命中时返回候选与原因，冲突不可静默按安装顺序解决。
每个 TaskRun 固定 descriptor、版本与 hash，运行中更新只影响新 Run。
Skill 输出的是计划/上下文候选；工具调用仍进入统一 policy、Hook 和审计链。
Plugin contribution 使用命名空间，禁止覆盖核心工具或其他 publisher 的同名能力。

## 四级增量

### `runnable` 能跑

支持本地固定 instructions 与显式读取一个 `SKILL.md`，无自动安装。

### `usable` 能用

增加发现、显式/斜杠调用、支持资源、manifest validation 和启用/停用。

### `productive` 顺手

增加可信来源安装、自动匹配、依赖解析、staged update、能力页面与版本快照。

### `polished` 好用

增加签名市场、SBOM、管理员 allow/deny、细粒度权限、沙箱、灰度更新、兼容矩阵与审计。

## 直接升级与回滚

先把现有 instructions 包装为无执行权限的 SkillDescriptor，再生成 manifest 与 hash。
安装器启用前必须完成路径、manifest、签名和 engine range 校验。
更新先进入 staging，对触发、资源引用、工具 schema 和权限差异跑 contract tests。
回滚恢复旧包与 capability snapshot；数据库迁移必须提供 down/read-compatible 路径。
跨级升级不得把“已安装”迁移成“已授权”，新权限逐项确认。

## 失败模式与安全

- trigger 冲突：显示候选、来源和最终选择。
- 上下文爆炸：metadata 常驻，正文/资源按需并有 token budget。
- 路径穿越：所有引用相对 root canonical resolve。
- 恶意脚本：默认不可执行；执行 contribution 在独立 worker 和 policy 下运行。
- 依赖混淆：锁定 publisher、version、integrity 与 registry origin。
- 升级失败：旧版本保持可激活，TaskRun 不混用版本。
- 指令注入：资源/网页/tool result 不提升为 system/developer 指令。

## 验收 oracle

1. 两个同名 Skill 不会静默选错，显式命名可稳定调用。
2. Skill 引用 `../secret` 或 symlink 时读取被拒。
3. 安装含 network permission 的 Plugin 不会自动获得网络访问。
4. 运行中更新后当前 Run 仍使用旧 hash，新 Run 使用新 hash。
5. 回滚恢复旧触发与工具 schema，不丢用户配置。
6. 恶意支持文件中的“忽略策略”只作为不可信内容。

## 来源与设计综合

包格式可综合 [VS Code Extension Manifest](https://code.visualstudio.com/api/references/extension-manifest) 与 [npm package integrity](https://docs.npmjs.com/cli/v10/configuring-npm/package-lock-json) 的公开实践。
各产品的 Skill 目录、Hook 类型、市场 UI 和安装方式由产品 dossier 决定；共享层只规定生命周期、版本和权限不扩张。
