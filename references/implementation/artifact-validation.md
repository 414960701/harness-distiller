# Artifact 语义验证

## 目标

Artifact 只有在结构、语义、可打开性和产品要求通过后才能从 `validating` 进入 `ready`。文件存在、扩展名正确或 ZIP 可解压都不足以证明成品可用。

## 生命周期

```text
proposed -> producing -> produced -> validating
-> ready | invalid | quarantined
-> superseded | deleted
```

每次验证保存 validator 名称/版本、输入 hash、检查结果、预览 artifact 与错误。源文件变化后旧 validation 自动 stale。

## 通用检查

1. size/mime/magic 与扩展名一致；
2. hash、来源 tool call 和 workspace 路径可追溯；
3. 解析器无 repair/损坏警告；
4. 文档结构、链接、嵌入资源和关系完整；
5. 关键内容 oracle 满足；
6. 至少一种真实 renderer/viewer 可打开或渲染；
7. 预览与源 hash 绑定；
8. 无意外宏、外链、凭据、个人数据或隐藏内容。

## DOCX

- 解包 OOXML，验证 `[Content_Types].xml`、relationships 和引用部件；
- 用 python-docx/等价解析文本、表格、图片、页眉页脚；
- 用 LibreOffice headless 或目标 Office renderer 转 PDF；
- 检查修复提示、缺失字体、图片/表格溢出、空白页和目录域；
- 对模板任务断言标题、段落、表格、页数范围和必要字段。

## XLSX

- openpyxl/等价以 `data_only=false` 读取公式和 workbook 结构；
- 验证 sheet 名、named range、公式引用、合并单元格、数据验证和图表 source；
- 用 LibreOffice/Excel 自动化重算，再读取错误单元格；
- 检查 `#REF!/#DIV0!/#VALUE!`、隐藏 sheet、外部链接、日期/数字格式；
- 渲染关键 sheet 或导出 PDF，验证列宽、分页和可见性。

## PPTX

- 解析 OOXML 或 python-pptx，验证 slide/layout/master/media relationships；
- 断言 slide 数、标题、图表/图片、notes 与品牌字段；
- 用 LibreOffice/PowerPoint renderer 输出 PDF/图片；
- 检查文字越界、元素遮挡、空白/重复页、低分辨率图片和缺失字体；
- 对关键 slide 做结构断言，视觉比较只作补充。

## PDF

- 用 qpdf/等价做结构检查；
- 用 PyMuPDF/Poppler 渲染全部页面；
- 验证页数、页面尺寸、文本/表单/书签/链接和图片；
- 检查空白页、裁切、字体替换、不可选文本、损坏 xref；
- 若目标要求 PDF/A、签名或表单，使用专用 validator。

## 图片与网页 Artifact

图片验证维度、格式、alpha、色彩空间、可解码性和最小清晰度；网页/HTML 必须离线加载核心内容，检查断链、console error、无障碍和响应式关键宽度。截图不能替代 DOM/文件语义检查。

## 安全

解析和渲染不可信 artifact 时使用隔离 worker、资源上限和超时。禁用宏、外部数据连接和自动执行。validator 读取秘密时只返回脱敏结果。

## 四级

- runnable：magic/parse/open 与任务关键字段；
- usable：格式专用结构检查、真实 renderer、预览与错误反馈；
- productive：版本、视觉/语义回归、并行 worker、冲突；
- polished：隔离验证池、供应链锁定、合规/隐私、跨平台 viewer 矩阵。

## 版本锁定

在目标项目 decisions/lockfile 记录 validator 和 renderer 版本；本技能不锁死某个库版本，因为目标 OS/stack 不同。升级 parser/renderer 时对 golden artifacts 重跑并比较结果。

## 验收

- 故意损坏关系、公式、字体、xref 的 fixture 被判 invalid；
- 仅存在但打不开的文件绝不显示 Ready；
- 旧 preview 在源 hash 变化后 stale；
- validator 超时不阻塞整个 Agent，artifact 保持 validating/invalid；
- parser CVE 或坏文件不能逃出隔离；
- UI 显示具体检查、失败原因和重新生成动作。

