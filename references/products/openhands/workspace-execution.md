# OpenHands-like Workspace 与执行规格

## 目录

- [Workspace 合同](#workspace-合同)
- [能力模型](#能力模型)
- [Local Workspace](#local-workspace)
- [Container Workspace](#container-workspace)
- [Remote Workspace](#remote-workspace)
- [Terminal 与文件](#terminal-与文件)
- [Browser 与 Git](#browser-与-git)
- [生命周期和失败](#生命周期和失败)
- [实现检查](#实现检查)

## Workspace 合同

Workspace 是 agent 所有执行副作用的唯一入口，不是普通 cwd 字符串。

```python
class Workspace(Protocol):
    identity: WorkspaceIdentity
    capabilities: frozenset[str]
    async def execute(req: CommandRequest, cancel: Token) -> CommandResult: ...
    async def upload(req: UploadRequest) -> FileReceipt: ...
    async def download(req: DownloadRequest) -> FileReceipt: ...
    async def git_changes(path: LogicalPath) -> list[GitChange]: ...
    async def git_diff(path: LogicalPath) -> GitDiff: ...
    async def pause() -> None: ...
    async def resume() -> None: ...
    async def close() -> None: ...
```

`WorkspaceIdentity` 至少含 provider、runtime id、root、generation 和 policy digest。Conversation resume 必须验证 identity，不能悄悄绑定另一个目录。

## 能力模型

能力采用显式集合：`exec`、`file-upload`、`file-download`、`git`、`persistent-terminal`、`browser`、`pause-resume`、`network`、`snapshot`。

Tool registry 只暴露 workspace 支持且 policy 允许的工具。provider 缺能力返回 `unsupported_capability`，不能回退宿主执行。

路径先解析成 logical workspace path，再在 executor 内 canonicalize。拒绝 `..`、绝对路径逃逸、symlink 穿越、大小写/Unicode 绕过和 mount alias。

## Local Workspace

`公开事实`：SDK `LocalWorkspace` 直接调用宿主 command、复制文件和本地 git API；pause/resume 是 no-op。

因此 UI 与事件必须标 `execution_mode=local-host`。安全 profile 默认不选择 LocalWorkspace；用户显式选择后仍经过 path/confirmation，但不能声明容器隔离。

本地执行采用最小环境 allowlist、独立 process group、确定 cwd、timeout 和 output limit。不得继承全部宿主 env；token 通过短生命周期 credential channel 注入。

## Container Workspace

Docker/Apptainer provider 负责：

- 固定 image digest，不只用 floating tag；
- 创建非 root 用户、workspace mount、tmpfs 和资源限制；
- 健康检查后才返回 ready；
- 明确 network policy、DNS 和代理；
- pause/resume/cleanup 幂等；
- conversation close 或租约过期后清理；
- 输出 runtime id/image digest/cgroup limits 进入事件。

容器不是自动安全：privileged、docker socket、宽 host mount、host network 都会破坏隔离，polished 必须有逃逸测试。

## Remote Workspace

远程 adapter 使用 control API start/attach/pause/resume/stop，并维护：runtime id、lease/fencing token、endpoint、expiry、capabilities。

每个 mutation 带 idempotency key；网络超时后先查询 receipt，不能直接重发。runtime generation 改变时旧 terminal/browser handle 失效，并发出 replacement event。

远程 provider 不可用时 fail closed。禁止无提示切换到 LocalWorkspace。

## Terminal 与文件

CommandRequest：argv 或受控 shell string、cwd、env refs、timeout、pty、session id、stdin mode、output limit。

CommandResult：exit code、stdout/stderr inline 或 artifact、timeout、cancelled、duration、process/session id、receipt、truncation。

Terminal session 维持 cwd/env/shell state；不同 conversation 默认不同 session。cancel 终止进程树，reset 明确丢失 session state。

FileEditor/apply_patch：

- read 带 digest/revision；
- edit 使用 expected digest 或 context hunk；
- 写入采用 temp+fsync+rename；
- binary/encoding/large file 显式处理；
- 冲突返回 current digest 和定位信息；
- history/undo 不覆盖用户既有变更。

## Browser 与 Git

Browser 作为 workspace-associated service：tab id、URL、structured DOM/accessibility state、screenshot artifact、download 均绑定 conversation/runtime。跨域、下载、clipboard 和认证按 policy 控制。

Browser action 包含 navigate/click/type/scroll/tab/get-content；selector 使用观察返回的稳定 element ref，失效时返回 stale element，不猜坐标。

Git changes/diff 是只读投影；commit/push 走 Terminal 或独立高风险 tool。diff 记录 base/head、untracked、binary 和 rename；Canvas 刷新不能触发工作区修改。

## 生命周期和失败

状态：`provisioning -> ready -> busy/paused -> stopping -> stopped`，失败为 `failed`。

启动失败：保留诊断 artifact，回收部分资源。运行失败：区分 command nonzero、transport、runtime died、policy denied、timeout。close 重复调用安全。

Conversation pause 可选择只停 agent 或同时 pause workspace；二者在协议中分开。恢复前检查 runtime health、identity 和 terminal handles。

Workspace 失联时 action 进入 `unknown_effect` 或根据 receipt 判定；不得用错误字符串冒充失败已回滚。

## 实现检查

- Local、Docker、Remote 跑同一 workspace conformance suite。
- workspace 外写、symlink、mount、Unicode path 均被拒绝。
- timeout/cancel 清理整个进程树并闭合 Observation。
- remote transport 断开后 committed command 不重复。
- container profile 限制 CPU/memory/output/network，且有逃逸测试。
- browser/tab/session 不跨 tenant 或 conversation 泄漏。
- executor 失败产生 typed error，Conversation 仍可恢复或明确终止。

安全策略见 [safety-runtime.md](safety-runtime.md)，恢复见 [persistence-recovery.md](persistence-recovery.md)。
