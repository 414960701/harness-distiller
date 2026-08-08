# Evals

## 职责与非目标

衡量 Harness 在任务正确性、工具效率、安全、恢复和产品行为上的稳定性。Eval 不是只让另一个模型给最终文本打分，也不以 benchmark 均值掩盖高风险失败。

## Case schema

```yaml
EvalCase:
  id: string
  fixture: repo/environment image
  prompt: string
  allowed_actions: []
  forbidden_actions: []
  oracle:
    tests: []
    file_assertions: []
    event_assertions: []
    policy_assertions: []
  budgets: {time, tokens, cost, steps}
  product_contract_refs: []
```

先运行确定性 oracle，再用模型 judge 评价难以结构化的可读性。Judge prompt/version 与原始证据必须记录。

## 评测维度

- outcome：测试、构建、artifact 是否正确；
- trajectory：是否选对文件/工具、是否重复、是否越权；
- safety：是否请求必要审批、是否泄密；
- durability：崩溃/重连后是否继续且不重复副作用；
- UX：状态、错误、进度和恢复是否可理解；
- cost：tokens、调用、wall time、cache 与无效工作；
- parity：产品公开合同是否满足。

## 四级增量

- runnable：5–10 个 smoke fixture；
- usable：合同与真实仓库回归集；
- productive：多模型、多平台、故障注入、轨迹分析；
- polished：持续基准、红队、shadow、canary 与发布 gate。

## 直接升级

保留旧 case 和 baseline；新增维度而非替换成功定义。环境 image、依赖和模型版本锁定。发现数据污染时标记 case，不静默删除失败。

## 失败模式

测试泄漏进训练/上下文、judge 偏见、环境漂移、只跑成功任务、忽略安全违规、用平均分隐藏不可接受的尾部、对闭源行为写臆测 oracle。

## 验收

1. 同 fixture 可重放并得到稳定结构化 oracle；
2. 故意越权的 agent 即使完成任务也判失败；
3. 崩溃恢复 case 检查事件与副作用次数；
4. judge 结果可追到 prompt/version；
5. 产品 parity 只引用公开合同；
6. 发布 gate 对 critical safety failure 一票否决。

证据类型：设计综合；代码评测参考各开源产品 `sources.md` 的 eval/benchmark 路径。

