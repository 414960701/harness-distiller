# AgentScope Workspace 与执行

## 事实边界

固定源码中 `WorkspaceBase` 负责 backend、instructions、tools、MCP、skills 和 context/tool-result offload；`LocalWorkspace` 与多种 sandboxed workspace 分开；app 层 `WorkspaceManagerBase` 用 isolation policy 分配 workspace。由此只能证明可替换执行/资源抽象，不能证明任意 workspace 或 manager 自动具备 OS 安全隔离。

## 三个必须分开的对象

1. `WorkspaceDescriptor`：workdir、resources、tools、skills、MCP 与 artifact 位置。
2. `ExecutionBackend`：read/write/process/upload/download 等实际执行能力。
3. `EnforcementProfile`：host-process、filesystem-restricted、container、microVM/remote 等已验证边界。

LocalWorkspace 默认是 `host-process`。只有对应 backend 的逃逸测试通过，才可提升 enforcement label。

## Workspace schema

```json
{
  "workspace_id": "ws_01",
  "owner_scope": {"user_id": "u1", "agent_id": "a1", "session_id": "s1"},
  "manager_policy": "per_agent",
  "backend": {"kind": "local", "instance_id": "local:123"},
  "enforcement": {"kind": "host-process", "verified_at": null},
  "roots": [{"name": "project", "path": "/work/project", "mode": "rw"}],
  "capabilities": ["read", "write", "exec"],
  "resource_limits": {"timeout_ms": 30000, "output_bytes": 1048576},
  "lease": {"token_hash": "...", "expires_at": "2026-08-08T12:30:00Z"},
  "version": 3
}
```

Manager 的 `per_agent/per_user` 表示复用范围，不等价于内核隔离；复用 workspace 时必须清理 session secrets、临时进程和 pending outputs。

## ExecutionSpec

```json
{
  "execution_id": "exec_7",
  "tool_call_id": "call_7",
  "workspace_id": "ws_01",
  "workspace_version": 3,
  "operation": "process.spawn",
  "argv": ["python3", "-m", "pytest", "-q"],
  "cwd": "/work/project",
  "env_refs": ["secret:test-token"],
  "stdin_artifact": null,
  "network_policy_ref": "net-deny",
  "limits": {"wall_ms": 30000, "stdout_bytes": 1048576},
  "permission_decision_id": "dec_7",
  "idempotency_key": "call_7:sha256args"
}
```

Executor 只消费规范化 spec，不消费模型自由文本。执行前再次验证 lease、workspace version、resolved cwd/path、decision binding 和限额；批准后参数变化必须重做 permission。

## 路径与进程规则

- 相对路径以已批准 root/cwd 解析；canonicalize 后检查根边界。
- symlink、hardlink、`..`、大小写折叠、挂载点与临时目录各自测试。
- shell string 与 argv 分开；能用 argv 时不经 shell。
- 子进程进入自己的 process group，取消时先温和终止再强杀。
- stdout/stderr 分流、限长并可 offload；截断必须显式标记。
- 环境变量采用 allowlist 与 secret reference，不能复制宿主全部环境。

## MCP Gateway

Gateway 负责 server discovery、连接、tool/resource 规范化与调用路由，不是 permission 或 sandbox。导入时生成 `McpServerSnapshot{server_id,transport,tool_schemas,resource_schemas,version_hash,trust}`；每个 tool 仍走本地 permission。server tool list 变化只影响下一 capability snapshot，当前 reply 不静默换 schema。

远端调用强制 timeout、payload limit、credential scope、TLS/transport policy 和 trace。恶意 tool description 视为不可信数据，不能进入最高优先级指令。

## Skill 与资源管理

Skill 安装先在 staging 解包，防 zip-slip、大小/文件数炸弹与符号链接逃逸，再生成 manifest hash。启用 skill 只是把指令/资源/工具依赖加入 snapshot，不授予额外 filesystem/network 权限。资源删除或更新产生版本事件；旧 reply 继续引用旧 hash 或明确失败。

## Artifact 与 offload

大 context/tool result 变为 `ArtifactRef{uri,sha256,size,media_type,owner_scope,created_at,expires_at}`。模型收到有界摘要与读取方式。读取时验证 hash、scope 和 expiry；缺失返回结构化 error，不把空内容当成功。外部上传成功与 event commit 之间使用 pending/committed 两阶段或补偿清理。

## 外部执行与 HITL

`REQUIRE_EXTERNAL_EXECUTION` 表示 runtime 暂停并等待带 execution request id 的结果。外部结果必须验证调用参数 hash、提交者 identity、result schema 和一次性 continuation；不能让 channel 文本直接伪造 tool result。

## 失败与恢复

- backend 未启动：reply 进入可重试 workspace error，不自动切到更弱 LocalWorkspace。
- lease 过期：停止新执行，已运行进程进入 fenced 状态。
- MCP 断连：只重试幂等调用；副作用未知则人工确认。
- output 超限：保留截断摘要与 artifact；artifact 写失败则 tool result 为 partial/error。
- manager 重启：依据 workspace record 重新连接或创建新实例，旧 instance token 作废。

## 分级实现

- runnable：LocalWorkspace + 明示 host-process + 单 root + fake backend 测试。
- usable：offload、MCP、skills staging、lease/version、结构化 execution result。
- productive：remote manager、per-agent/user 分配、配额、artifact store、team workspace scope。
- polished：已验证 sandbox backend、网络/secret policy、fencing、逃逸测试与故障恢复。

## 验收 oracle

越界路径、symlink、超时、输出爆量、MCP schema 漂移、lease 过期、取消孤儿进程、skill archive 攻击均应 fail closed 或进入明确 partial/unknown 状态；任何失败不得通过 fallback 悄悄扩大权限。
