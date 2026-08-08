# Deep Agents Agent Loop 实现规范

## 目录

- [目标与边界](#目标与边界)
- [组装算法](#组装算法)
- [运行状态机](#运行状态机)
- [Middleware 调用](#middleware-调用)
- [Todo 与委派](#todo-与委派)
- [终止取消重试](#终止取消重试)
- [伪代码](#伪代码)
- [四级升级](#四级升级)
- [失败注入](#失败注入)
- [实现检查表](#实现检查表)

## 目标与边界

Deep Agents 自身负责组装，LangChain `create_agent` 与 LangGraph 负责实际 graph loop。

复刻时必须保留这一边界：

- 产品层定义 profile、middleware、backend、subagent 与 prompt；
- runtime 层定义 model/tool 节点、reducer、superstep、checkpoint 与 interrupt；
- executor 层定义文件、shell、网络和外部服务副作用；
- surface 层只消费版本化 snapshot/event。

不要把 `graph.py` 的 middleware 列表误写成自研调度算法。

## 组装算法

固定版本主 agent 的逻辑顺序是：

1. 解析 model 与 harness profile；
2. 规范化用户 tools 和 profile tool description override；
3. 默认 backend 为 `StateBackend()`；
4. 分类 inline subagents 与 async subagents；
5. 编译 declarative subagent 的独立 middleware；
6. 必要时加入 general-purpose subagent；
7. 组装 main core stack；
8. 插入 user middleware；
9. 追加 profile、prompt caching、memory、HITL 等 tail；
10. 应用 exclusion 与最终 tool exclusion；
11. 合并 middleware state schema/private fields；
12. 调用 `create_agent(...).with_config(...)`。

主栈的核心次序为：

```text
Skills? -> Filesystem -> SubAgent? -> Summarization
        -> PatchToolCalls -> AsyncSubAgent?
        -> user middleware
        -> profile extras -> prompt caches -> Memory? -> HITL?
        -> final tool exclusion?
```

`TodoListMiddleware` 不在默认核心栈；需要 planning 时把它作为 user/profile middleware 显式插入。

## 运行状态机

```text
CREATED
  -> READY
  -> MODEL_PENDING
  -> MODEL_STREAMING
  -> TOOL_ROUTING? --------------------------+
  -> POLICY_PENDING                          |
  -> WAITING_APPROVAL? -> POLICY_RESOLVED    |
  -> TOOL_RUNNING -> TOOL_COMMITTED/FAILED --+
  -> CONTEXT_COMPACTING? --------------------+
  -> MODEL_PENDING | COMPLETED | FAILED | CANCELLED | INDETERMINATE
```

状态不变量：

- 每次 transition 有单调 `sequence`；
- 每个 model/tool/subagent attempt 有稳定 ID；
- `COMPLETED/FAILED/CANCELLED` 为终态；
- `WAITING_APPROVAL` 必须已有 durable continuation；
- `TOOL_COMMITTED` 后重放不得重复副作用；
- `INDETERMINATE` 只用于无法确认外部提交结果。

## Middleware 调用

每个 middleware 描述符至少包含：

```json
{
  "id": "filesystem",
  "version": "0.7.5-compatible",
  "name": "FilesystemMiddleware",
  "position": 20,
  "hooks": ["before_model", "wrap_tool_call"],
  "mutates": ["tools", "messages"],
  "state_schema": ["files"],
  "timeout_ms": 30000,
  "failure_mode": "closed"
}
```

组装时必须检测：

- 重名 middleware 是原位替换还是重复注册；
- core middleware 不可被 profile exclusion 移除；
- user middleware 插入点不能越过 final tool exclusion；
- private state annotation 解析失败时发出高优先告警；
- hook 超时、异常和修改内容进入 trace；
- turn 开始后不热变更当前 capability snapshot。

## Todo 与委派

### Todo

Todo 状态建议使用：

```json
{"id":"t1","content":"验证恢复","status":"in_progress","depends_on":[],"evidence":[]}
```

`write_todos` 每次提交完整列表或有版本号的 patch；同一 model batch 内不得并发写两份相互覆盖的列表。

### 同步 subagent

同步 `task`：

1. 校验 `subagent_type`；
2. 从父 state 移除 `messages/todos/structured_response/private`；
3. 用 task description 建立全新 HumanMessage；
4. 在独立 context window 中运行；
5. 提取 structured response 或最后非空 AIMessage；
6. 用原 tool call ID 返回 ToolMessage；
7. 只合并允许的 state 字段。

### 异步 subagent

异步 task 使用远程 `thread_id/run_id`，状态至少有 running/success/error/cancelled。

主 agent 不应启动后立即忙轮询；返回 task ID，由用户或调度器稍后 check/update/cancel。

## 终止取消重试

终止原因枚举：

- `completed`：模型产生最终回答且没有未结工具；
- `budget_exhausted`：达到 model/tool/token/wall-clock/recursion 预算；
- `cancelled`：用户或父级 cancellation token 生效；
- `policy_denied`：目标不可继续且没有替代方案；
- `failed`：不可恢复异常；
- `indeterminate`：外部副作用状态未知。

取消传播顺序：frontend -> turn -> model stream -> tool -> sync child -> remote run。

重试分类：

| 错误 | 重试主体 | 规则 |
|---|---|---|
| model rate limit | runtime middleware | 指数退避、抖动、总预算 |
| tool 参数错误 | model | 返回结构化 ToolMessage |
| read-only timeout | runtime | 同 call ID 可重试 |
| write timeout before dispatch | runtime | 安全重试 |
| write timeout after dispatch | recovery | 查 receipt，否则 indeterminate |
| policy deny | 不重试 | 只有参数或 scope 改变后再评估 |

## 伪代码

```python
def run_turn(spec, input, ids, cancel):
    snapshot = freeze_capabilities(spec)
    state = load_or_create(ids.thread_id)
    emit("turn.started", snapshot=snapshot)
    while not terminal(state):
        enforce_budgets(state)
        cancel.raise_if_set()
        request = build_context(state, snapshot)
        response = call_model_with_middleware(request)
        if response.is_final:
            return commit_final(state, response)
        for call in response.tool_calls:
            normalized = normalize(call, snapshot)
            decision = evaluate_policy(normalized)
            if decision.ask:
                checkpoint_before_interrupt(state, normalized, decision)
                return interrupt(decision.request)
            receipt = dispatch_with_receipt(normalized, decision, cancel)
            append_tool_result(state, receipt)
        maybe_compact(state)
        checkpoint(state)
```

同步子 agent 可在一个 model batch 中并行，但只有在 workspace/副作用域不冲突时允许。

## 四级升级

| 等级 | Loop 增量 | 回归 oracle |
|---|---|---|
| `runnable` | 单 graph、Todo opt-in、step/time 预算 | 读文件→工具→最终回答 |
| `usable` | checkpoint、HITL、同步 subagent、取消 | 重启后从审批点恢复 |
| `productive` | async subagent、重试/fallback、typed event、压缩 | 故障注入不重复提交 |
| `polished` | 分布式 lease、远程执行、SLO、迁移 | 多实例竞争仅一方提交 |

直接跨级升级仍按 state/event -> recovery -> policy -> subagent -> remote/service 顺序迁移。

## 失败注入

- 在 model 首 token 前、流中和结束后断开。
- 在 tool dispatch 前、外部提交中、receipt 持久化后崩溃。
- 在 middleware 修改 tools 后抛出异常。
- 在 approval 产生后杀死进程。
- 在同步 subagent 返回前取消父 turn。
- 让远程 async run 返回未知状态或迟到成功。
- 让 summary 模型溢出或 backend history 写失败。
- 让 Todo 同一 batch 出现两次写入。
- 让 loop 达到 recursion limit 和 wall-clock limit。

## 实现检查表

- [ ] 默认 planning 行为与 0.7.5 一致，或差异已配置化。
- [ ] middleware 顺序写入 turn snapshot。
- [ ] 状态、终止、取消、重试均有稳定枚举。
- [ ] 每次副作用有 call ID、attempt、receipt。
- [ ] child cancellation 和 late-result suppression 有测试。
- [ ] interrupt 前 checkpoint 已 durable。
- [ ] frontend 只显示公开 plan/action，不显示隐式推理。
- [ ] 每级测试链接到 [acceptance-tests.md](acceptance-tests.md)。
