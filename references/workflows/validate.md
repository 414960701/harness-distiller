# 验证工作流

## 1. 技能自身

运行：

```bash
python3 scripts/check_inventory.py
python3 scripts/validate_knowledge.py
python3 scripts/validate_dossier.py references/products/<product>
python3 scripts/validate_blueprint.py <target>/.harness-distill/blueprint.yaml
```

检查 Markdown 内部链接、Skill frontmatter、Python 编译与 `git diff --check`。

## 2. 静态合同

- blueprint recipe/level/surface/capability 合法；
- 产品 13 篇 dossier 齐全并满足深度闸门；
- command/event/domain schema 有版本和 golden fixture；
- capability 依赖闭包完整；
- tool、policy、error 和 state transition 没有无主分支；
- migration 有版本、fixture 和幂等保护。

## 3. 动态合同

- 正常模型/工具循环和自然终止；
- schema 错误、模型限流、工具异常、超时与取消；
- approval 接受、拒绝、缩小范围和过期；
- context 达阈值后的压缩、恢复和缓存稳定性；
- 进程崩溃后的 thread/turn/tool 恢复；
- UI 断线重连后用 snapshot/event 重建；
- provider/tool/plugin 不可用时明确降级。

## 4. 安全

- workspace 越界、符号链接、TOCTOU；
- shell 注入、进程树、环境秘密；
- 网络 allowlist、redirect、private IP、DNS rebinding；
- MCP/tool 虚假 read-only 注解；
- browser/computer prompt injection；
- approval 参数变化和 sandbox fail-open。

安全测试必须作用于真实 enforcement，不 mock 最关键边界。

## 5. 恢复与迁移

在 command 接收、model stream、tool intent、tool completion、result transaction、event outbox、checkpoint 和 migration 中间 kill 进程。验证终态唯一、事件不丢不重、外部副作用不重复、旧 session 可读。

## 6. 产品体验

按 `product-contract.md` 和 `acceptance-tests.md` 运行当前等级黑盒任务，覆盖启动、编辑/工作、长任务、受限动作、恢复、审查和主界面状态。闭源产品只比较公开行为，不宣称内部等价。

## 7. 完成报告

列出 `verified`、`implemented`、`deferred`、`blocked-by-evidence`。每项包含实现路径、测试路径、来源、已知差异和直接升级步骤。只有 `verified` 计入等级完成度。
