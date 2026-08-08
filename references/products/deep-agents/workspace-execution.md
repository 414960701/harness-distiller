# Deep Agents Workspace 与 Execution 规范

## 目录

- [职责分离](#职责分离)
- [Backend Schema](#backend-schema)
- [逻辑路径](#逻辑路径)
- [文件工具合同](#文件工具合同)
- [执行合同](#执行合同)
- [Sandbox 与权限](#sandbox-与权限)
- [Artifact 与大输出](#artifact-与大输出)
- [四级升级](#四级升级)
- [失败与安全](#失败与安全)
- [验收](#验收)

## 职责分离

`BackendProtocol` 是资源访问抽象，`SandboxBackendProtocol` 额外提供执行；两者都不自动等于安全策略。

实现必须分开：

| 层 | 职责 | 不负责 |
|---|---|---|
| Workspace | root、logical URI、版本/快照 | OS 隔离 |
| Backend | list/read/write/edit/delete/search/transfer | 用户授权 |
| Policy | allow/deny/ask/amend | 系统调用强制 |
| Executor | command/process/timeout/output | 业务级审批 |
| Sandbox | filesystem/process/network/secret/quota enforcement | 模型判断 |
| Artifact store | 大对象、digest、retention | agent loop |

## Backend Schema

```json
{
  "backend_id": "b-1",
  "kind": "state|filesystem|store|composite|sandbox|remote",
  "root_uri": "workspace:///",
  "capabilities": ["ls", "read", "write", "edit", "glob", "grep"],
  "supports_delete": false,
  "supports_execute": false,
  "snapshot_id": "s-1",
  "limits": {"read_lines": 2000, "output_bytes": 102400},
  "trust_domain": "thread-local"
}
```

固定版本协议返回 `ReadResult/WriteResult/EditResult/DeleteResult/LsResult/GrepResult/GlobResult`，执行返回 `ExecuteResponse`。

复刻可以使用语言无关 schema，但需保持错误、截断和部分成功语义。

## 逻辑路径

- agent 可见路径统一 POSIX 绝对路径；
- logical path 与 host/container/provider path 分离；
- `..`、`~`、NUL 和编码歧义在边界拒绝；
- symlink 解析后再次验证 sandbox root；
- CompositeBackend 按最长、无歧义 route 选择后端；
- 每次 route 解析写入 backend_id 和 snapshot_id；
- backend 切换不改变模型看到的 logical URI；
- artifact URI 不直接暴露临时签名 URL；
- Windows host 仍在协议层使用 POSIX path；
- root `/` 表示虚拟 root，不推断为宿主 `/`。

## 文件工具合同

### `ls`

返回 path、is_dir、size、modified_at；permission deny 的条目不得泄漏名称。

### `read_file`

- offset 为 0-indexed，显示 gutter 可为 1-indexed；
- 非正 limit 返回空窗口而不是读取全文件；
- 文本、base64 binary 和 multimodal 明确区分；
- 超长行、媒体和不支持的 block 有确定降级；
- 返回 next_offset/total_lines 时数值一致。

### `grep`

- pattern 是 literal，不是 regex；
- `max_count` 是全局 cap；
- timeout 时返回错误或 partial + truncated；
- permission 过滤后不能泄漏 denied match 数量或路径。

### `glob`

- pattern 与 base path 分开；
- absolute pattern 不得绕过 permission predicate；
- 结果稳定排序并有 cap。

### `write/edit/delete`

- write 的 overwrite 语义明确；
- edit 默认要求 old_string 唯一，除非 replace_all；
- recursive delete 评估整个 subtree 的 deny/interrupt overlap；
- mutation 产生 digest、previous snapshot 和 new snapshot；
- backend 失败不能伪装为成功 ToolMessage。

## 执行合同

```json
{
  "call_id": "c-1",
  "backend_id": "sandbox-1",
  "command": "pytest -q",
  "cwd": "workspace:///repo",
  "timeout_seconds": 120,
  "env_refs": [],
  "network_profile": "deny",
  "resource_profile": "small",
  "idempotency_key": "turn/c-1"
}
```

`ExecuteResponse` 至少有 combined output、exit_code 与 truncated。

命令确实运行后，即使 exit code 非零，transport status 也可能是 success；业务判断必须读取 exit_code。

超大输出写入 artifact，模型只得到 head/tail、digest、path 和回读方法。

## Sandbox 与权限

固定版本有一个关键限制：filesystem permissions 不支持控制通用 `execute` 命令。

因此生产复刻必须：

1. 对文件工具执行 path policy；
2. 对 execute 单独执行 command/cwd/network/secret policy；
3. 在 sandbox 内强制 mount、UID、进程、网络和资源限制；
4. 不因 sandbox provider 不可用回退到 `LocalShellBackend`；
5. 明示 `LocalShellBackend` 使用宿主 shell，不是隔离环境；
6. 限制 child process env 继承，secret 使用按调用注入；
7. 对 custom/MCP tool 注册独立 effect descriptor；
8. 保留 approval 参数 hash，并对 amend 后参数重新评估。

## Artifact 与大输出

Artifact 字段：

| 字段 | 说明 |
|---|---|
| artifact_id | 稳定身份 |
| logical_uri | backend 无关路径 |
| digest | 内容寻址与篡改检测 |
| media_type | 展示/解析选择 |
| size | quota 与下载提示 |
| producer_call_id | lineage |
| validation | parser/build/test 结果 |
| retention | thread/project/org policy |

conversation history offload 与普通产物使用不同 namespace；模型压缩历史不得污染用户仓库。

## 四级升级

| 等级 | Workspace/执行增量 | Oracle |
|---|---|---|
| `runnable` | StateBackend、基础文件工具、无 shell | 虚拟文件读写一致 |
| `usable` | Filesystem/Store/Composite、path permission | route 与 deny 测试通过 |
| `productive` | artifact、大输出、RAG adapter 与 backend receipt | 截断和恢复测试通过 |
| `polished` | 强 sandbox、remote backend、lease、quota、迁移、SLO | 逃逸失败且 provider 故障不破坏 logical URI |

## 失败与安全

- symlink 从允许 root 指向 secret：解析后拒绝。
- glob absolute pattern 越权：按真实 search root 触发 deny/interrupt。
- recursive delete 包含 denied descendant：整次拒绝。
- execute 超时：杀进程树并标记是否可能有残留副作用。
- output 超 cap：保留完整 artifact 或明确截断，不静默丢失。
- upload batch 部分失败：逐文件响应，不回滚成功项为假失败。
- backend route 中途变化：当前 turn 使用冻结 snapshot。
- remote backend 断线：只在幂等或有 receipt 时重试。
- sandbox capability 不满足：配置或调度时 fail closed。
- malicious file/skill：作为不可信上下文，不能提升权限。

## 验收

1. 同一 corpus 在 State、Filesystem、Store backend 的 `ls/read/grep/glob` oracle 一致。
2. Composite route 切换后 logical URI 和 artifact lineage 不变。
3. deny path 不出现在 search/list/error/trace 中。
4. `edit_file` 0/1/N occurrence 分别得到确定结果。
5. symlink、`..`、absolute glob、recursive delete 测试全部 fail closed。
6. 非执行 backend 不暴露 execute；执行 backend 暴露且 timeout 生效。
7. shell 非零 exit code 可机器读取，不能仅解析文本。
8. sandbox 无网络时 DNS、HTTP、redirect 都失败。
9. secret 只在批准调用可见，stdout/trace 自动脱敏。
10. 大输出可通过 artifact digest 完整回读并验证。
11. cancellation 清理进程树、临时文件和 remote lease。
12. 任一失败都进入结构化 ToolResult 和事件，而不是只写日志。
