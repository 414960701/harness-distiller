# Aider-like Coder loop

## 目录

- [状态与预算](#状态与预算)
- [主循环伪代码](#主循环伪代码)
- [上下文与模型阶段](#上下文与模型阶段)
- [编辑与验证阶段](#编辑与验证阶段)
- [architect/editor 阶段](#architecteditor-阶段)
- [重试、取消与终止](#重试取消与终止)
- [四级增量](#四级增量)

## 状态与预算

单个 turn 使用以下状态：

```text
CREATED -> PREPROCESSING -> COMPILING_CONTEXT -> MODEL_RUNNING
  -> PARSING_EDITS -> AWAITING_CONFIRMATION -> APPLYING
  -> COMMITTING -> VALIDATING -> COMPLETED
```

任一非终态可进入 `FAILED` 或 `CANCELLED`；`VALIDATING` 可在用户同意后产生 `REFLECTING -> COMPILING_CONTEXT`。ask/help 模式从 `MODEL_RUNNING` 直接进入 `COMPLETED`。architect 模式在首个 `MODEL_RUNNING` 后进入 `ARCHITECT_REVIEW -> EDITOR_RUNNING -> PARSING_EDITS`。

每轮冻结预算：

```yaml
TurnBudget:
  provider_retries: 6
  reflection_attempts: 3
  edit_parse_attempts: 2
  lint_fix_attempts: 2
  test_fix_attempts: 2
  command_timeout_ms: 120000
  max_wall_time_ms: 900000
  max_cost_usd: null
```

原 Aider 以 `max_reflections` 和 provider backoff 控制部分循环；蒸馏实现把所有预算显式化，避免不同错误共享一个模糊计数器。

## 主循环伪代码

```python
def run_turn(session, raw_input, cancel, budget):
    turn = new_turn(session, raw_input, budget)
    emit("turn.started", turn)
    snapshot = workspace.snapshot(session.root)

    try:
        message = preprocess(raw_input, session.commands)
        if message.command_result is not None:
            return finish_command(turn, message.command_result)

        while True:
            cancel.raise_if_cancelled()
            request = compile_context(session, turn, snapshot, message.text)
            result = complete_with_retry(session.main_model, request, cancel, budget)

            if session.mode in {"ask", "help", "context"}:
                append_messages(session, message.text, result.text)
                return complete(turn, assistant_text=result.text)

            if session.mode == "architect":
                result = run_editor_stage(session, result.text, cancel, budget)

            edits = edit_formats[session.edit_format].parse(result.text, snapshot)
            preview = edit_formats[session.edit_format].preview(edits)
            auth = authorize(session, edits, preview)
            if not auth.allowed:
                return complete(turn, assistant_text=result.text, edits=[])

            checkpoint_dirty_files(session, edits)
            outcome = apply_atomically(edits, snapshot.expected_hashes)
            if not outcome.ok:
                message = reflect_or_fail(turn, outcome.diagnostic, budget)
                snapshot = workspace.snapshot(session.root)
                continue

            commit = auto_commit_if_enabled(session, outcome.edited_paths, turn)
            validation = validate(session, outcome.edited_paths, cancel)
            emit_validation(validation)

            diagnostic = accepted_fix_diagnostic(validation)
            if diagnostic and budget.has_reflection_capacity():
                message = diagnostic
                snapshot = workspace.snapshot(session.root)
                continue

            update_history_after_files(session, result.text, commit, validation)
            return complete(turn, outcome, commit, validation)
    except Cancelled:
        return cancel_turn_at_safe_point(turn)
    except KnownFailure as error:
        return fail(turn, error)
```

关键 invariant：模型响应不会直接触发写入；完整 parse、preview、authorization、stale check 全部成功后才进入 apply。每次 reflection 重新读取工作区，因为上一次 edit 或外部进程可能改变真值。

## 上下文与模型阶段

`preprocess` 先区分斜杠命令；普通消息再检测文件名和 URL。文件 mention 只能建议加入 context，不能自动扩大可写权限。`compile_context` 的典型顺序为：system/editor prompt、示例、summarized done history、repo map、read-only contents、chat file contents、current messages、新用户消息。

模型请求记录：

```yaml
ModelCall:
  id: string
  turn_id: string
  role: main|architect|editor|weak
  request_hash: sha256
  model: string
  started_at: timestamp
  attempt: integer
  input_tokens: integer|null
  output_tokens: integer|null
  cost_usd: number|null
  finish_reason: stop|length|cancel|error
```

provider retry 只覆盖被 adapter 分类为 transient 的错误；指数退避有最大延迟和总预算。context exceeded 不按普通 transient 重放同一请求，而是触发 history summary、缩小 repo map 或要求用户 drop files。流式 chunk 只发 UI event；直到 provider 给出终止或本地检测到完整 response，才进入 parse。

## 编辑与验证阶段

编辑阶段严格分五步：

1. `parse`：format-specific 文本到 `Edit[]`，拒绝歧义、多重匹配和根外路径。
2. `preview`：在内存副本应用，生成 diff 和 post-image hash。
3. `authorize`：对新文件、未加入文件、删除和 shell 请求询问；read-only 一律拒绝。
4. `apply`：比较 expected hash，采用临时文件 + rename 或 journal 保证文件级原子性。
5. `checkpoint`：Git auto commit 成功后记录 commit hash；失败则结果为 `applied_uncommitted`。

malformed edit 的 diagnostic 应包含 format 名、失败块、匹配数量和纠正提示，但不能把敏感文件内容无界回显给模型。原 Aider 将这类错误放入 `reflected_message`；复刻应为 diagnostic 标识 `source=edit_parser`。

验证顺序与公开 Coder 一致：编辑完成并可先 auto commit；lint edited files；可再次 commit formatter/linter 造成的变动；运行建议 shell（逐项确认）；最后执行 auto-test。lint/test 出错时由用户决定是否反射修复。自动化 `--yes` 模式可以预先同意，但仍受 reflection 和 timeout 预算。

## architect/editor 阶段

architect 不是能写工作区的 agent。第一阶段使用 main model 和 architect prompt，仅产生方案文本。若 `auto_accept_architect=false`，必须询问“是否编辑文件”。第二阶段创建隔离的 editor call：

```yaml
EditorRequest:
  proposal: string
  chat_files_snapshot: [FileSnapshot]
  read_only_files_snapshot: [FileSnapshot]
  edit_format: editor-diff|editor-whole|other
  repo_map_tokens: 0
  shell_suggestions: false
  inherited_done_history: []
```

公开源码使用新的 Coder，清空 editor 的 `cur_messages`/`done_messages`，禁用 repo map、shell suggestion、cache warming，并把 architect content 当用户指令。复刻可用同等隔离；editor 不重新规划，也不递归产生新的 architect。

两次模型调用分别计费并关联同一 turn。editor 失败时保留 proposal 供用户重试或切回 code；不得把 proposal 当 edits 猜测应用。

## 重试、取消与终止

### 重试分类

| 错误 | 策略 | 幂等要求 |
|---|---|---|
| 429/临时 5xx/连接断开 | capped exponential backoff | 仅重发模型请求 |
| context exceeded | 重编译更小 context | request hash 必须变化 |
| output length | provider 支持 assistant prefill 时续写，否则失败 | 不 apply partial text |
| malformed edit | diagnostic reflection | 上次零写入 |
| stale workspace | 重新 snapshot 和请求 | 不覆盖外部修改 |
| lint/test fail | 用户确认后 reflection | 已完成 commit 可形成新 commit |
| Git commit fail | 不自动重放 edits | 标记未 checkpoint |

### 取消

Ctrl-C 第一次取消当前 model/command 或标记 turn 取消；短时间内第二次可退出 CLI。取消在 `APPLYING` 临界区到达时，先完成当前原子文件替换或回滚 journal，再发 `turn.cancelled`。子进程需按 process group 发送 TERM，宽限后 KILL，并记录 exit/signal。

### 终止条件

`COMPLETED`：问答已返回，或 edits 已应用且验证流程已结束（验证可失败，但 outcome 清楚）。`FAILED`：没有可继续的 bounded path，例如模型永久错误、parser budget 耗尽、授权策略拒绝必需修改、workspace conflict 无法重编译。`CANCELLED`：用户取消且没有未决 apply。`AWAITING_CONFIRMATION` 不是终态，重启后可恢复或按策略过期。

## 四级增量

| 等级 | loop 增量 |
|---|---|
| runnable | 单 code turn、一个 format、同步模型、parse-before-write、手动 diff/checkpoint |
| usable | ask/code、Git auto/dirty commits、lint/test reflection、历史总结、bounded retry/cancel |
| productive | architect/editor、多 format、streaming、cache、stale hash、后台 summarization、费用预算 |
| polished | 原子 journal、全事件审计、强 sandbox 可选、远程 workspace、故障注入与恢复 SLO |

直接从 runnable 升 polished 仍使用同一 Turn、ChangeSet 和 event id；只打开新阶段与字段，禁止另写一套“高级循环”。升级细则见 [recipe.md](recipe.md)。
