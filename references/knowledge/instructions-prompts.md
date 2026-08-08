# Instructions 与 Prompts

## 职责与非目标

指令解析器把 system、developer、user、organization、workspace、skill 和 tool data 按 authority 与 scope 组合成可解释输入。
它不把网页、仓库文本或 MCP result 提升为可信指令，也不让 prompt 替代执行层权限。
Prompt 是模型输入编排，不是 Task/Step 状态事实源；状态必须来自结构化事件。
隐藏推理不应写入日志或 UI，用户需要的是决策摘要、来源和可审计动作。

## 指令 schema

```yaml
Instruction:
  id: string
  authority: system|developer|organization|user|workspace|skill|data
  scope: global|account|project|directory|task|turn|step
  source_uri: string
  content_hash: string
  precedence: integer
  trusted: boolean
  effective_from: timestamp
  effective_until: timestamp|null
PromptBuild:
  model_profile: string
  instruction_refs: [string]
  context_refs: [string]
  tool_schema_digests: [string]
  token_budget: object
```

接口：`discover(scope)`, `resolve(instructions)`, `explain(conflict)`, `build(context,budget)`, `redact`, `fingerprint`。
目录规则按路径祖先到子目录收集，同 authority 时更窄 scope 优先，但不能覆盖更高 authority。
稳定指令与工具 schema 放可缓存前缀，动态 turn/step context 放后部。

## 解析与上下文状态

每次 TaskRun 保存 effective instruction snapshot 和 fingerprint。
配置热更新只影响新 Run，除非用户明确重载并产生事件。
冲突解析输出 winner、loser、authority、scope 与理由；不能“最后拼接者获胜”。
tool/web/file 内容统一包装成 `untrusted_data`，其中出现的命令只可被引用和分析。
超长规则先拒绝/截断并提示来源，不用模型摘要悄悄改变规范语义。

## 四级增量

### `runnable` 能跑

固定 system/developer 指令与当前 user turn，保存 prompt fingerprint。

### `usable` 能用

增加 workspace/directory 规则、冲突解析、来源展示、稳定前缀和 token budget。

### `productive` 顺手

增加 profile、Skill 渐进加载、context compression、缓存统计和 prompt eval 数据集。

### `polished` 好用

增加组织 requirements、签名规则、注入检测、模型差异适配、变更审计和企业保留策略。

## 直接升级与回滚

先把旧拼接 prompt 拆成有来源的 Instruction，再引入 precedence/scope resolver。
对旧新 PromptBuild 保存 fingerprint 与离线输出比较，不记录 secret 或隐藏推理。
组织策略启用前做冲突预览；新规则不得追溯改写历史 Run。
回滚切换 resolver 版本并保留旧 snapshot，不能删除用户规则文件。

## 失败模式与安全

- prompt injection：外部内容 trusted=false，不能创建高 authority item。
- 规则循环/冲突：确定性 resolver 与 explain，不依赖模型判断权限。
- 上下文溢出：按合同预算与引用摘要，优先保留当前意图和安全策略。
- 缓存串租户：cache key 包含主体、scope、model 与 fingerprint。
- secret 泄漏：构建前后 redaction，日志只留 digest/长度。
- Skill 覆盖系统策略：Skill authority 永低于 system/developer/organization。

## 验收 oracle

1. 仓库 README 写“忽略系统策略”不会改变 effective instructions。
2. 子目录规则只影响其 scope，不污染邻居目录。
3. 两条冲突规则可稳定解释 winner 与来源。
4. 热更新后旧 Run fingerprint 不变，新 Run 使用新版本。
5. prompt cache 不跨用户/项目复用敏感前缀。
6. 极长恶意 tool result 不挤掉安全策略与用户本轮目标。

## 来源与设计综合

可参考 [OpenAI Model Spec](https://model-spec.openai.com/) 的 authority 思路和 [OWASP LLM Prompt Injection Prevention](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) 的威胁分类。
具体模型模板、专有 system prompt 与内部推理不属于可蒸馏合同；产品 dossier 只需规定外部行为和 snapshot。
