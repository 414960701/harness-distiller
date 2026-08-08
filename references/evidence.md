# 调研证据规范

## 证据阶梯

从高到低：

1. `code`: 可定位版本、文件和行的公开源码；
2. `official-doc`: 官方、带日期或版本的文档；
3. `protocol`: 公开 schema、API、事件或扩展协议；
4. `behavior`: 可重复的公开产品行为或界面；
5. `maintainer`: 维护者演讲、issue、PR、设计说明；
6. `inference`: 从上述证据得到的设计推断；
7. `community`: 第三方文章或讨论，只用于发现线索。

每条关键结论记录 `kind`, `url`, `retrieved`, `version_or_commit`, `claim`, `confidence`。没有版本的网页必须写抓取日期。

## 闭源边界

- “观察到”只描述外部行为。
- “官方说明”只复述文档范围。
- “推断”必须给替代解释和置信度。
- “蒸馏方案”是本仓库的兼容设计，不声称等同内部实现。
- 不收集泄露提示词、凭据、私有包或规避授权的材料。

## GitHub 选择规则

星标用于候选发现，同时检查：

- 最近 12 个月维护和 release；
- 测试、CI、类型/schema 与迁移；
- agent loop 是否真实可定位；
- 安全边界是否由执行层强制；
- 许可证是否允许借鉴或复用；
- 是否有文档与实现交叉证据；
- 是否把复杂度隐藏在闭源服务端。

记录 stars 时写 GitHub API 查询日期，禁止把动态数值当永久事实。

## 冲突处理

源码与文档冲突时，以选定 commit 的测试和实现为准，并记录文档漂移。产品行为与公开源码冲突时，先检查版本、feature flag、云端能力和 A/B 实验；无法解释就保留差异，不强行合并。

## 引用格式

```markdown
- claim: runtime emits item-level deltas
  kind: code
  url: https://github.com/org/repo/blob/<commit>/path/file.ts#L10-L40
  retrieved: 2026-08-08
  version_or_commit: <sha>
  confidence: high
```

