# AutoResearch 三模块工作台

一个网页入口分别进入 Auto Search、Auto Design 和 Auto Writing。三个模块保留各自的完整前端、后台任务管理器、提示词、Schema、科学约束和独立启动方式。

## 启动

在仓库根目录使用 Python 3.11+：

```bash
python3 -m workbench --port 8760
```

本机已有环境可直接使用：

```bash
.venv/bin/python3 -m workbench --port 8760
```

Windows PowerShell：

```powershell
$env:AUTORESEARCH_PYTHON = "C:\path\to\python.exe"
.\run_workbench.ps1 -Port 8760
```

打开 [工作台](http://127.0.0.1:8760/)。工作台服务和三个模块只依赖 Python 标准库；模型调用需要已安装并登录的 Codex CLI。PDF 编译使用 Auto Writing 原有的编译器发现逻辑，支持 Tectonic、latexmk、XeLaTeX 或 pdfLaTeX。

| 参数 | 默认值 | 作用 |
| --- | --- | --- |
| `--host` | `127.0.0.1` | 对外监听地址 |
| `--port` | `8760` | 唯一浏览器入口端口 |
| `--workspace` | 当前目录 | 新建 Auto Design 任务的默认工作目录 |
| `--data-dir` | `<workspace>/assets/output/workbench` | 三模块任务索引与运行数据根目录 |

首页的连接状态来自真实健康接口。没有任务时显示空状态；打开页面和切换模块均不启动研究任务。浏览器切换不停止后台任务，退出服务则应先在模块内完成停止或安全暂停。

## 保留的功能

| 模块 | 浏览器入口 | 完整功能 |
| --- | --- | --- |
| Auto Search | `/auto-search/` | 新建方向调研、论文与 Weakness 提取、Idea 生成、可选独立评审、进度与日志、取消、调研文件夹删除、分板块阅读 Idea、人工通过或废弃及撤销核验 |
| Auto Design | `/auto-design/` | 新建任务、文本或文件输入 Idea、仅设计或完整流程、旧运行导入、R0 与正式执行、暂停恢复、Revision ID 审核、执行日志、结果表、诊断与独立审计、报告和产物文件浏览 |
| Auto Writing | `/auto-writing/` | 新建与修改资料、删除项目、Introduction 调研、Related Work 规划与调研、六章节逐步生成、任务停止、依赖与失效状态、参考文献调研与插入、路径约束、模板 ZIP 上传、LaTeX 适配、PDF 编译与 ZIP/PDF 下载 |

Auto Search 的 Weakness 直达 Idea 和批量生成命令仍保存在模块目录，原有 `src/autoresearch` CLI 也完整保留。单模块用法见 [Auto Search](../auto_search/README.md)、[Auto Design](../auto_design/README.md)、[Auto Writing](../auto_writing/README.md)。

模块之间继续通过明确的输入文档衔接：在 Auto Search 查看 Idea，将其内容或文件交给 Auto Design；再将实验说明和真实结果资料上传到 Auto Writing。此次整合统一入口和导航，模块切换不会自动选定 Idea、触发下一阶段或更改研究设置。

## 数据与运行结构

```text
assets/output/workbench/
  auto_search/                 调研运行目录
  auto_design/tasks.json       实验任务索引
  auto_writing/                写作项目与上传、生成文件
```

Auto Design 的具体运行产物仍写入用户选定工作目录下的 `assets/output/auto_design/<task-id>/`；工作台索引记录其实际路径。现有独立模块的数据不自动复制到工作台；接续已有 Auto Design 实验使用页面里的导入功能。工程验收数据和日志写入 `assets/logs/workbench/`，不进入正常任务索引，也不提交到 Git。

服务在一个 Python 进程内启动三个绑定到 `127.0.0.1` 临时端口的原模块 HTTP 服务，由公共入口按路径前缀转发请求。GET、HEAD、POST、PUT、DELETE、查询参数、上传请求体和二进制下载均由原模块处理；原 32 MB 请求上限保留。只在模块主页注入共享导航，生成的 HTML 报告维持原内容和相对资源路径。

前端只为 API 和下载地址增加模块前缀，因此独立启动时仍使用原路径。桌面与 390px 窄屏均可使用统一导航和原模块侧栏。

Auto Writing 默认传入 `--ignore-user-config`，与另外两个模块保持一致，避免本机全局 Codex 配置解析失败；不修改全局配置。确需读取自定义全局配置时设置 `CODEX_IGNORE_USER_CONFIG=0`。模型、推理强度、CLI 路径和 LaTeX 编译器仍由各模块原有参数控制。

## 验收记录

2026-09-05，Python 3.12 环境：

- 完整测试：**234 passed、4 skipped、3 subtests passed**。4 项跳过来自原 Auto Search 测试依赖的历史调研目录缺失；另有原依赖产生的 5 条 SWIG 弃用警告。
- 新增 HTTP 整合测试使用真实服务、文件与任务管理器，仅在模型调用边界使用明确标注的工程 fixture，覆盖各模块工作流、隔离存储、上传编辑、人工审核、取消、恢复与二进制下载。
- 三模块分别通过各自真实 Codex CLI 适配器返回预期结构；此项验证连接与调用兼容性，不代表科研输出质量验收。
- Auto Writing 原编译函数使用真实 `latexmk` 成功生成 **15,582 bytes** 的最小 PDF，并成功打包 LaTeX ZIP。
- 浏览器确认首页、三模块导航、调研表单、实验任务创建、写作文件上传与项目创建、六章节展示、依赖提示、下载链接和 390px 窄屏。页面宽度均为 390px，无横向溢出；控制台无 error/warn。
- Ruff 检查新增 Python 代码通过；五个新增或修改的 JavaScript 文件语法检查通过。

没有启动远端 GPU、科研训练或正式数据集评估。模型服务、网络和实际科研输入带来的运行结果仍以各模块执行日志及科学契约为准。

复现自动测试：

```bash
python3 -m pip install -e '.[dev]'
PYTHONPATH=auto_search python3 -m pytest --import-mode=importlib tests auto_design/tests auto_search/tests auto_writing/tests workbench/tests -q
```

本机验收文件：

| 路径 | 内容 |
| --- | --- |
| `assets/logs/workbench/tests-final.log` | 完整回归结果 |
| `assets/logs/workbench/cli-smoke/summary.json` | 三模块真实 CLI 与 LaTeX 验收汇总 |
| `assets/logs/workbench/cli-smoke/` | 原始提示、返回、事件、编译日志与最小 PDF/ZIP |
| `assets/logs/workbench/ui-qa/` | 独立界面测试服务、任务与工程 fixture |
| `assets/logs/workbench/server.log` | 正常工作台服务日志 |
