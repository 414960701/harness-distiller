# Aider 证据与版本登记

## 目录

- [版本快照](#版本快照)
- [固定源码证据](#固定源码证据)
- [官方行为文档](#官方行为文档)
- [结论到证据映射](#结论到证据映射)
- [证据限制](#证据限制)

## 版本快照

复核日期：2026-08-08。GitHub API 的 `main` HEAD 为 `5dc9490bb35f9729ef2c95d00a19ccd30c26339c`，提交时间 2026-05-22T14:02:20Z；仓库约 48,043 stars，许可证为 Apache-2.0。星数只作热度快照，不是架构证据。

固定基线：

```text
repository: https://github.com/Aider-AI/aider
commit: 5dc9490bb35f9729ef2c95d00a19ccd30c26339c
docs: https://aider.chat/docs/
license: Apache-2.0
```

所有源码链接优先锁定该 commit；`main` 文档只用于发现，不作为不可变引用。

## 固定源码证据

### Coder 与循环

- [`Coder.create` 与 format subclass 选择](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L125-L201)（code）：切换 format 时会总结旧历史，继承文件、消息、commit hash、费用和 commands。
- [`Coder.__init__`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L299-L543)（code）：模型、Git、repo map、summarizer、lint/test 和消息字段。
- [`run_one` reflection loop](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L924-L945)（code）：`reflected_message` 驱动有上限的再请求。
- [`send_message` 的 provider retry、编辑、commit、lint/test](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L1419-L1624)（code）。
- [`apply_updates`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L2296-L2337)（code）：parse、dry-run preview、authorization、apply 和 malformed reflection。

### Context 与 repo map

- [`format_chat_chunks`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L1226-L1332)（code）：system、examples、done、repo、read-only、chat files、cur 的编排。
- [`ChatSummary`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/history.py#L7-L124)（code）：保留尾部、总结头部、递归收敛和模型 fallback。
- [`RepoMap.get_tags_raw`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/repomap.py#L279-L364)（code）：tree-sitter query 提取 definition/reference，必要时 Pygments 补 refs。
- [`RepoMap.get_ranked_tags`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/repomap.py#L365-L575)（code）：文件图、权重、personalization 和 PageRank。
- [`RepoMap.to_tree`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/repomap.py#L748-L784)（code）：按相关行渲染代码树并截断长行。

### 编辑、Git 和命令

- [coder format modules](https://github.com/Aider-AI/aider/tree/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders)（code）：whole、search/replace、udiff、patch、architect/editor 等实现。
- [`ArchitectCoder.reply_completed`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/architect_coder.py#L11-L49)（code）：architect 输出被传给新的 editor Coder，禁用 map 与 shell suggestions。
- [`allowed_to_edit` 与 dirty checkpoint](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L2175-L2243)（code）。
- [`auto_commit`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L2375-L2424)（code）。
- [`GitRepo.commit`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/repo.py#L131-L318)（code）：提交消息、attribution、hooks 和 commit outcome。
- [`/undo` safety checks](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/commands.py#L553-L655)（code）：会话 commit、merge、dirty、新文件和 pushed HEAD 检查。
- [`/run` 与 `/test`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/commands.py#L993-L1054)（code）。

## 官方行为文档

- [Chat modes](https://aider.chat/docs/usage/modes.html)（official-doc）：code、ask、architect、help 和 sticky/one-shot mode。
- [Edit formats](https://aider.chat/docs/more/edit-formats.html)（official-doc）：whole、diff、diff-fenced、udiff、editor variants。
- [Repository map](https://aider.chat/docs/repomap.html)（official-doc）：符号图、相关性和 token budget。
- [Git integration](https://aider.chat/docs/git.html)（official-doc）：auto commit、dirty commit、undo、attribution。
- [Linting and testing](https://aider.chat/docs/usage/lint-test.html)（official-doc）：edited-file lint、whole-project tests、错误反馈。
- [In-chat commands](https://aider.chat/docs/usage/commands.html)（official-doc）：文件、Git、运行、模式和历史命令。
- [Scripting](https://aider.chat/docs/scripting.html)（official-doc）：single-message CLI 和非稳定 Python API。
- [Configuration](https://aider.chat/docs/config.html)（official-doc）：CLI、env、`.aider.conf.yml`、dotenv 和 model settings。
- [Analytics/privacy](https://aider.chat/docs/more/analytics.html)（official-doc）：遥测行为必须单独配置，不属于离线核心。

## 结论到证据映射

| 结论 | 证据 | 强度 |
|---|---|---|
| Coder 是单 foreground turn，reflection 有上限 | `run_one`、`send_message` | code |
| edit format 是模型适配层，不只是显示格式 | `Coder.create`、coder modules、官方 edit docs | code + official-doc |
| repo map 使用 tree-sitter + dependency graph + PageRank | `repomap.py`、repo map docs | code + official-doc |
| architect/editor 是串行双模型，不是 subagent runtime | `architect_coder.py`、modes docs | code + official-doc |
| Git commit 是主要可逆边界 | `repo.py`、`commands.py`、Git docs | code + official-doc |
| lint/test 错误可进入 reflection | `send_message`、lint docs | code + official-doc |
| Aider 无通用 MCP/subagent/强 sandbox 合同 | 仓库入口、参数和 docs 的能力边界 | code absence + inference |

“缺少能力”属于全仓入口、参数、文档和 runtime 的联合检查，不是仅凭一次字符串搜索证明。它只约束本基线，不预测未来版本。

## 证据限制

- LiteLLM、provider SDK、tree-sitter language pack、GitPython 等依赖的内部实现不等于 Aider 自身合同。
- 官方 benchmark 说明 edit 成功率，不直接证明生产安全、sandbox 或恢复能力。
- Python scripting API 官方明确不保证兼容；蒸馏实现应暴露自己的稳定协议。
- `--yes` 会自动确认，但不把宿主执行变成安全执行。
- 浏览 URL、抓取网页或运行 shell 是局部功能，不等于 MCP/tool marketplace。
- 本 dossier 的 thread/turn/item/event 是兼容共享 harness 的蒸馏协议，属于 inference；原 Aider 主要使用 Python 对象和终端流。
