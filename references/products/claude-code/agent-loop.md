# Claude-Code-like Agent Loop 实现合同

> 本文把 gather/action/verify 公开行为拆成可恢复状态机。状态名、队列和伪代码均为 `inference`，不声称等于 Claude Code 内部实现。

## 目录

- [行为目标](#行为目标)
- [输入与输出](#输入与输出)
- [状态机](#状态机)
- [循环伪代码](#循环伪代码)
- [Gather](#gather)
- [Action](#action)
- [Verify](#verify)
- [Steer 与 Interrupt](#steer-与-interrupt)
- [Plan 与 Tasks](#plan-与-tasks)
- [Subagents 与 Teams](#subagents-与-teams)
- [故障恢复](#故障恢复)
- [升级与测试](#升级与测试)

## 行为目标

`official-doc/behavior`：Claude Code 在收集上下文、采取动作、验证结果之间自适应循环，用户可以随时 steer 或 interrupt。

`inference`：不要实现为固定三步流水线；每次 observation 后由模型决定继续 gather、action、verify 或完成。

### 循环不变量

- 每个模型请求使用已提交的 context snapshot。
- 每个 tool call 在执行前经过 policy 和 hook。
- 每个 side effect 有 idempotency key 或明确不可重放标志。
- verify 使用真实 observation，不接受模型自报成功。
- cancel token 向模型流、hook、工具、子 Agent 和子进程传播。
- 完成事件只在未解决的必需 task 为零时产生。

## 输入与输出

```yaml
TurnInput:
  session_id: string
  turn_id: string
  user_items: [Item]
  mode: default | plan | accept_edits | restricted
  workspace_revision: string
  capability_snapshot: object
  deadline_at: timestamp|null
```

```yaml
TurnOutcome:
  status: completed | failed | cancelled
  answer_item_id: string|null
  changed_paths: [string]
  verification: [VerificationResult]
  unresolved_tasks: [string]
  usage: object
```

`inference`：不要把 bypass 类高风险模式作为持久化默认输入。

## 状态机

```text
queued -> preparing -> gathering -> reasoning
reasoning -> authorizing -> executing -> observing -> reasoning
reasoning -> verifying -> observing -> reasoning
reasoning -> compacting -> reasoning
reasoning -> awaiting_user -> reasoning
reasoning -> completed
any-active -> cancelling -> cancelled
any-active -> failed
```

附属运行可以处于 `backgrounded`，但其父 turn 必须持续可观察。

### 转移守卫

- `preparing -> gathering`：workspace trust 和 capability snapshot 已确定。
- `authorizing -> executing`：decision 为 allow 且 enforcement 已准备。
- `authorizing -> awaiting_user`：decision 为 ask。
- `authorizing -> observing`：decision 为 deny，生成拒绝 observation。
- `reasoning -> completed`：模型给出 final 且 completion gate 通过。
- `any -> compacting`：预算越阈值且没有不可分割 tool transaction。

## 循环伪代码

```python
async def run_turn(input):
    state = await recover_or_create(input)
    emit("turn.started", state.snapshot())
    while not state.terminal:
        check_cancel(state.cancel_token)
        ctx = context_engine.materialize(state)
        if ctx.requires_compaction:
            await compact_with_provenance(state, ctx)
            continue
        response = await model.stream(ctx, tools=registry.visible(state))
        await persist_model_items(response.items)
        for intent in response.intents:
            if intent.kind == "tool":
                decision = await policy.evaluate(normalize(intent), state)
                result = await dispatch_or_reject(intent, decision, state)
                await persist_observation(result)
            elif intent.kind == "question":
                await block_for_user(intent, state)
            elif intent.kind == "final":
                state.terminal = completion_gate(intent, state)
        await incorporate_pending_steering(state)
    emit_terminal_once(state)
    return project_outcome(state)
```

伪代码未展示真实 Claude 内部结构；实现者可用 actor、workflow engine 或普通 async loop。

## Gather

### 来源排序

1. 当前用户目标和 steer 消息。
2. managed、user、project 范围指令。
3. task/plan 和未解决验证状态。
4. 用户显式 mentions、IDE selection 和附件。
5. repository 搜索和文件片段。
6. tool observations、MCP resources 和 Web 内容。
7. auto memory；只能作为建议性上下文。

### Gather 约束

- 先搜索后读取，避免无边界遍历。
- 文件片段携带 path、revision、line range 和 trust。
- 大 tool output 持久化为 artifact，context 中只放摘要和引用。
- 外部内容标 prompt-injection trust，不能修改 policy。
- CLAUDE.md/rules 冲突时记录 provenance，不伪装安全层。

### Gather oracle

当用户问“为什么这样做”，trace 能列出产生决策的主要 context fragment。

## Action

### Tool intent 标准化

- 解析 canonical path，拒绝隐藏 traversal。
- Bash 保留原 argv/command，同时产生只用于策略匹配的规范化视图。
- MCP 标识 server、tool、tenant 和 write/read effect。
- 编辑记录 expected revision，避免覆盖并发变更。
- 外部写操作生成 idempotency key。

### 执行顺序

`PreToolUse hook -> permission decision -> sandbox compile -> execute -> PostToolUse hook -> observation`

任何 hook 都不能把 deny 变成 allow，也不能提升 sandbox capability。

## Verify

### 验证层次

- 语法/类型：最小静态检查。
- 定向测试：与改动相关的最小测试集。
- 回归：成熟等级允许时扩大测试。
- diff review：确认无意变更、秘密和生成物。
- 用户目标：逐项映射 acceptance criteria。

### VerificationResult

```json
{"command":"npm test -- x","status":"passed","exit_code":0,"artifact_id":"a1","revision":"git:abc+dirty","observed_at":"..."}
```

失败、超时、未运行必须彼此区分；final answer 必须如实呈现。

## Steer 与 Interrupt

`official-doc/behavior`：用户可在工作中追加方向或中断。

`inference`：steer 是高优先级 input item，不直接修改正在提交的 tool transaction。

- streaming 时 steer 可终止当前 model request 并带入下一次 reasoning。
- executing 时先请求取消；不可取消动作完成后再应用 steer。
- awaiting_permission 时 steer 可撤销待审批请求。
- background task 接收独立 cancel token。
- interrupt 必须产生一次且仅一次 cancelled 终态。

## Plan 与 Tasks

Plan mode 由 policy enforcement，而非仅用提示词约束。

```yaml
Task:
  id: string
  title: string
  status: pending|in_progress|blocked|completed|cancelled
  depends_on: [string]
  evidence_item_ids: [string]
```

同一时刻默认仅一个 task 为 in_progress；团队模式可由 scheduler 放宽。

plan 升为 execution 需要显式 mode transition event。

## Subagents 与 Teams

`official-doc`：subagent 有独立 context、prompt、tools 和权限；agent teams 可互相通信。

`inference`：父级签发 capability envelope：工具交集、权限上限、预算、deadline、workspace view。

- 子 Agent 不继承父 transcript 全量，只收到任务包。
- 子 Agent 默认不能再委派，除非 capability 明确允许。
- team message 作为事件保存并带 sender/recipient。
- 共享文件写入需要 worktree 隔离或冲突检测。
- 父 cancel 必须级联；子失败不自动让父 turn 失败。

## 故障恢复

- 模型断流：保存已确认 item，按 provider 规则重试，不拼接半个 tool call。
- 进程崩溃：从最后 committed event 恢复。
- tool 结果未知：标 `outcome_unknown`，先 reconcile，禁止盲目重放。
- compact 失败：回到原 context snapshot，不覆盖 transcript。
- hook 超时：按声明的 fail-open/fail-closed；安全 hook 默认 fail-closed。
- session schema 旧：迁移副本后再 resume。

## 升级与测试

- 能跑：同步 loop、前台工具、基础取消。
- 能用：事件化状态、resume、plan enforcement、compact。
- 顺手：background、subagent、steer queue、checkpoint。
- 好用：teams、remote worker、幂等恢复和 SLO。

关键 oracle：同一 committed event prefix 重放两次，投影视图相同，外部 mutation 不增加。

关键 oracle：用户 interrupt 后，不再出现新的非终止性 tool start。

关键 oracle：plan mode 中任何文件 revision 不改变。

关键 oracle：verify 失败时，final 不得声明任务已完全成功。
