# Aider-like 验收测试

## 目录

- [测试夹具](#测试夹具)
- [runnable](#runnable)
- [usable](#usable)
- [productive](#productive)
- [polished](#polished)
- [故障与安全](#故障与安全)
- [升级与判定](#升级与判定)

## 测试夹具

建立临时 Git repo：`src/main.py` 调用 `src/math.py:add`，`tests/test_math.py` 验证结果；`notes.md` 为 read-only；`.env` 被 ignore；另建 root 外 `sentinel.txt`。fake provider 能返回 whole/diff、malformed、429、length、architect proposal 和 editor edits。fake linter/tester 可控制 exit、timeout 和输出。

每个用例断言：filesystem hashes、Git HEAD/dirty、Turn state、Item/Event 序列、provider call role/次数、stdout/JSONL。验证命令必须可在 CI 非交互运行；confirmation 由 scripted IO 提供。

## runnable

### R1 `context.explicit-files`

步骤：只把 `src/main.py` 加 editable，把 `notes.md` 加 read-only，不加入 `src/math.py`；捕获模型 request。Oracle：request 含 main 与 notes 全文，不含 math 全文；access manifest 正确。让模型编辑 notes，结果 `permission_denied`，所有 hash 不变。通过后 capability 可 `verified`。

### R2 `editing.structured-format`

步骤：provider 返回对 main 的唯一 SEARCH/REPLACE；再返回一个首块有效、第二块 ambiguous 的多文件响应。Oracle：第一次精确修改并生成 preview；第二次 parser diagnostic 包含 ambiguous，两个文件都不变，没有 `workspace.file_applied`。验证 format 名和 source span 可审计。

### R3 `git.atomic-checkpoint`

步骤：记录 base HEAD，执行 AI edit；再注入 commit failure。Oracle：正常路径新 commit 的 parent 等于 base、path set 正确；失败路径明确 `applied_uncommitted`，不把 hash 加 session commit set，不提示安全 `/undo`。若实现 transaction journal，kill 后亦不出现半个 ChangeSet。

### R4 mode write barrier

步骤：在 ask 模式让 provider 返回看似合法 edit block。Oracle：只产生 assistant message，不调用 parser/apply，文件和 HEAD 不变。code 模式同响应才可进入 edit pipeline。

## usable

### U1 `context.repo-map`

步骤：只加入 main，用户提到 `add`；index 扫描整个 repo，预算设小。Oracle：map 含 math 的 `add` 定义/签名且 token 不超预算；低 rank 内容被排除；修改 math 后 cache invalidated。移除语言 parser 时降级文件列表并发 `repo_map.degraded`，turn 仍完成。

### U2 `context.history-summary`

步骤：构造超过 soft limit 的 12 轮历史，最后两轮含未解决约束；启动 summary 后追加新消息。Oracle：正常 summary 保留 recent tail、目标/约束且总 token 收敛；旧 worker 的 source hash 不匹配时结果丢弃；weak 失败可 fallback main；全失败保留原历史。

### U3 `validation.lint-test`

步骤：edit 后 linter exit 1 输出错误，scripted confirmation 允许修复，第二响应修好；测试再配置持续失败。Oracle：lint diagnostic 进入下一 model request；修复产生新 change/commit；持续测试不超过 budget，最终 validation failed 可见，不无限循环。

### U4 dirty separation

步骤：用户先修改 main 未提交，AI 再修改同文件。Oracle：用户 dirty change 先形成 `user_dirty` checkpoint，AI edit 后形成 `agent_edit`；两个 commit path/diff 不混淆，最终内容同时保留。

### U5 retry/cancel

步骤：fake provider 先两次 429 再成功；另一次在 stream 中 cancel。Oracle：backoff attempts 有上限且只 apply 一次；cancel 响应没有 parse/apply，turn=`cancelled`，CLI 可继续下一轮。

## productive

### P1 `modes.architect-editor`

步骤：main/architect 返回 proposal，分别测试用户拒绝和允许。Oracle：拒绝时 editor 未调用且零写入；允许时第二调用 role=editor、history empty、map tokens=0、shell suggestions=false，只有 editor edit 进入 parser。两个调用 usage 分开。

### P2 `models.role-routing`

步骤：配置 main=A、weak=W、editor=E，触发普通回答、summary、commit message、architect edit。Oracle：调用日志分别为 A/W/W/A+E；任一角色不可用时按配置 fallback 或明确失败，不静默换成未知模型；usage 按 role 汇总。

### P3 `git.undo-dirty-provenance`

步骤：依次测试 HEAD 非 session commit、session merge commit、已推送 HEAD、目标有新 dirty change、正常单 parent agent commit。Oracle：前四种 `/undo` 拒绝且文件/HEAD hash 不变；正常路径恢复 previous content、soft reset、移除正确 commit。新建文件策略必须明确测试。

### P4 stale workspace

步骤：模型请求进行中外部修改 target。Oracle：expected hash 不匹配，原响应零写入，外部内容保留；系统重读并请求新 edit 或失败为 `workspace_conflict`。

### P5 mode/format switch

步骤：先用 whole 格式对话，再切 diff。Oracle：旧 assistant whole 示例不作为活跃 imitation context，done history 被总结/隔离；新响应只由 diff parser 接收。

## polished

### H1 `security.sandbox-enhancement`

前置：必须真实启用隔离 backend。步骤：命令尝试读 root 外 sentinel、写 root 外、访问被禁网络、fork bomb/超 CPU/内存。Oracle：内核/容器/VM enforcement 拒绝；sentinel hash 不变；资源进程被限额终止；event 标 boundary=sandbox。只弹确认或返回 prompt 拒绝不通过。

### H2 `protocol.headless-jsonl`

步骤：`--output-format jsonl --no-stream` 执行 edit + lint + commit，捕获 stdout。Oracle：每个非空行可 JSON parse 且符合 Event schema；thread seq 严格递增；无 ANSI/spinner/人类散文；重放 events 得到相同 turn terminal state、edited path、commit sha 和 validation outcome。

### H3 crash recovery

步骤：在 journal prepared、第一文件 replace、files applied before commit 三点 kill -9。Oracle：重启分别清理、完整回滚/阻止写入、识别 applied_uncommitted；没有静默 partial success，重复 command 不产生第二次 edit/commit。

### H4 cache/migration

步骤：截断 tag cache、用旧 DB schema 启动、迁移中断再重启。Oracle：cache 可重建；migration 幂等且有 backup/checksum；核心 thread/Git 不丢。

## 故障与安全

- path `../../sentinel.txt`、absolute path、symlink escape：全部拒绝，sentinel hash 不变。
- read-only/ignored target：即使 `--yes` 仍拒绝。
- malformed edit、provider partial length：不得应用 partial response。
- shell suggestion 未确认、confirmation 后 command hash 改变：runner 不启动。
- command timeout：process group 结束，outcome `timed_out=true`，输出有 truncation 标志。
- commit message model 失败：确定性 fallback 或 uncommitted，不能丢 edit。
- test 输出伪 secret：持久 event 已 redacted。
- reflection/provider retry 耗尽：turn failed/completed-with-validation-failure，不再调用模型。

## 升级与判定

每个等级运行本级和所有较低等级测试。直接 runnable→polished：先在旧数据上跑 R1-R4，migration 后跑 U/P/H 全集；旧 thread id、Git commit 和 event seq 不重置；关闭新 flag 后基础 code/edit/Git 仍可用。

Capability 只有满足 [recipe.md](recipe.md) 同名行及本文件对应 oracle 才可从 `implemented` 改为 `verified`。`security.sandbox-enhancement` 未启用真实隔离时保持 planned，即便其它 polished 项通过。`protocol.headless-jsonl` 必须以机器解析和重放验证，截图不算证据。
