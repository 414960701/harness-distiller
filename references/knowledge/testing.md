# Testing

## 职责与层次

测试证明实现符合领域合同，不只是函数能返回。使用：纯状态机单测、adapter contract、schema golden、executor security、record/replay、仓库 scenario、UI projection 和迁移测试。

## 测试目录

```text
tests/
  unit/          # reducer、policy、budget、normalizer
  contracts/     # model/tool/store/protocol adapters
  fixtures/      # provider streams、events、repos
  scenarios/     # 端到端任务
  security/      # 越界、注入、sandbox
  recovery/      # kill/restart/duplicate
  migrations/    # old schema fixtures
  surfaces/      # event projection/a11y
```

Provider fixture 保存归一化 stream，不保存秘密。外部 API live tests 与确定性离线 suite 分开。

## 关键合同

- 每个 ToolCall 恰一个最终 ToolResult；
- Turn 终态唯一；
- sequence 单调且可重放；
- approval 绑定 action hash；
- context 不拆 tool call/result；
- snapshot+events 得到确定 projection；
- idempotency key 不重复副作用。

## 四级增量

- runnable：unit + smoke vertical slice；
- usable：contracts + scenarios + basic security/recovery；
- productive：并发、故障注入、跨平台、UI/eval；
- polished：逃逸、负载、迁移矩阵、供应链、发布认证。

## 直接升级

每增加 capability，先添加失败 fixture，再实现。升级后运行所有低等级 suite。破坏性协议变更同时增加旧 fixture 和 adapter 测试。

## 失败模式

mock 掉真实 executor/policy、只测 happy path、测试依赖执行顺序、时间/随机数不受控、snapshot 每次盲目更新、live model 不锁版本、忽略 Windows/macOS/Linux 差异。

## 验收

1. 可在无网络模式运行核心 suite；
2. 每个外部 adapter 有同一 contract suite；
3. kill points 覆盖 tool intent/result 事务；
4. security suite 运行真实 enforcement；
5. UI fixture 能在断线/重复/gap 下重建；
6. 测试报告映射 blueprint capability。

证据类型：设计综合；完整矩阵见 `references/implementation/validation.md`。

