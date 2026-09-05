# AutoResearch 开发交接

当前分支为 `test-v1`，已将 Auto Search、Auto Design、Auto Writing 整合到 [同一个工作台](http://127.0.0.1:8760/)。完整说明见 [workbench/README.md](../workbench/README.md)。启动命令为 `.venv/bin/python3 -m workbench --port 8760`，任务在各自模块内明确启动。

此前的独立 Auto Design 已提交并推送到 GitHub：`49da8d80c738259bad1fb7b88668b945606878b7`，远端分支 [auto_design](https://github.com/wanghao1118/LL-AutoResearch/tree/auto_design)。该分支基于 `main` 的 `01615b8`；旧 `autodesign` 分支 `af51260` 是科学规则和运行工具的迁移来源。以下 Round 1、Round 2 记录其重构过程，Round 3 记录三模块整合。

## 当前代码与运行方式

- 新模块位于 [`auto_design/`](../auto_design/README.md)，不需要安装 AutoDesign Skills、React、Node 或 Codex SDK。
- Python 编排在 `orchestration.py`；CLI 调用和日志在 `codex_runner.py`；普通提示词位于 `prompts/`，路径注入在 `prompting.py`。
- 原有状态、结果单元校验、均值与样本标准差、设计目标对比和五阶段执行工具已迁入模块，原科学约束保持有效。
- 网页支持新建、仅设计、完整执行、旧运行导入、暂停、恢复、方法修改批准和真实结果浏览。
- 原仓库 `src/autoresearch` 与打包配置保持原样；旧分支和用户安装的 Skills 未修改。

本机使用已有 Python 3.11+ 虚拟环境启动：

```bash
.venv/bin/python3 -m auto_design serve --port 8767
```

访问 [本地 AutoDesign](http://127.0.0.1:8767/)。任务索引位于 `assets/output/auto_design/tasks.json`，服务日志位于 `assets/logs/auto_design_server.log`。启动服务不自动启动实验。

## 验证与产物

- 原 AutoResearch 测试和新模块测试合计 **139 passed**；测试记录：`assets/logs/auto_design_refactor/tests.log`。原依赖还输出 5 条 SWIG 类型弃用警告。
- Ruff 和 JavaScript 语法检查通过。
- 完整工作流测试用工程 fixture 覆盖设计、实际本地测试命令、结果摄取、诊断、独立审计和最终完成。
- 额外覆盖了仅设计不启动实验、暂停不继续派发、阶段内成功命令不重复运行、服务重启不自动重跑、Revision ID 匹配、拒绝后重新批准、已批准决定持续有效、修改次数上限、未关闭 iteration 不进入最终审计、HTTP 接口及真实子进程日志。
- 真实 Codex CLI 连接验收通过，返回 `outcome: completed`、`summary: CLI连接验收通过`、`next_action: none`。完整命令、时间、退出码和事件记录位于 `assets/logs/auto_design_refactor/cli-smoke-isolated/`。
- 浏览器确认了首页、任务表单、任务详情和空结果展示，控制台无 error/warn。界面验收任务明确标注“界面工程验收（不运行实验）”，全部放在 `assets/logs/auto_design_refactor/ui-qa/`，没有进入正常任务索引。
- 本轮没有启动科研模型训练、远端 GPU 实验或数据集评估，没有产生可用于科研结论的观测结果。

## 实验推进历程

### Round 1：统一系统组成方式

**设计动机。** Auto Search 与 Auto Writing 采用 Python 网页系统驱动 Codex CLI，而旧 AutoDesign 使用 Skills 和 Node/React 控制台。用户要求新建与另外两个模块并列的 `auto_design` 分支，统一工程结构。

**具体方案与关键参数。** 从 `main` 创建新分支，将旧分支的确定性工具迁入 `auto_design/`，把五个 Skills 的研究规则转成普通提示词，Python 根据持久化状态派发独立 CLI 调用。默认端口 8767；一个活动任务；编排模型默认延续 `gpt-5.6-sol`、`xhigh`。实验科学模型、数据、split、metrics、seeds 和 budget 仍由接受的设计决定。

**结果数据。** 139 项测试通过；真实 CLI 返回预期结构；原生网页接通本地真实 API。无科研实验结果。

**核心发现与失败原因。** 本机原全局 `config.toml` 在 CLI 启动时产生 `invalid type: map, expected a boolean in features`，已采用与 Auto Search 相同的 `--ignore-user-config` 隔离方式，保留当前登录认证，并未修改全局配置。失败日志保存在 `cli-smoke/`。新增完整流程测试曾因工程 fixture 漏写 `schema_version` 被正确拦截，补齐后通过。暂停接入暴露了阶段内命令恢复需求，已保留成功命令前缀以避免重复昂贵工作。

**下一步洞察。** 工程结构已经统一。后续若继续整合，应在三个模块之间增加明确的 Idea 选择、写作交接和真实结果更新入口。当前仍沿用文件交接；不需要先统一一套大型前端框架或重写科学契约。

### Round 2：统一三个模块的前端风格

**设计动机。** 用户查看 Auto Search 与 Auto Writing 的原版页面后，要求 AutoDesign 使用同样的视觉风格。

**具体方案与关键参数。** 复用 Auto Writing 的 The ThAInker Logo，以及两模块共有的字体、颜色、间距和控件样式。桌面顶栏为 70px、侧栏为 322px，主背景为 `#f4f6f7`，侧栏为 `#eef1f2`，主操作色为 `#087d70`。首页改为居中的实验入口；任务详情、状态标签、结果表、新建与导入弹窗使用统一样式。760px 以下采用可展开的侧栏，表单内容可滚动，底部操作保持可见。修改集中在 `auto_design/web/index.html`、`styles.css`、`app.js` 和品牌图片；Python 服务及实验编排没有改动。

**结果数据。** JavaScript 语法检查通过；浏览器确认首页、新建弹窗、已有任务概览、结果页和 390px 窄屏菜单可以使用。窄屏页面宽度与文档宽度均为 390px，没有页面横向溢出；控制台没有 error/warn。复用上一轮明确标注的界面验收任务，没有启动生成或实验，正常任务索引仍为空。

**核心发现与失败原因。** 原版 AutoDesign 的侧栏品牌、大标题和绿色底色与另外两个模块不同；统一顶栏品牌、灰色工作区和紧凑控件后，三个模块的外观已对齐。完整任务名称、路径和结果仍保留换行显示。

**下一步洞察。** 当前工程组成和视觉风格均已统一，后续可围绕真实任务继续打通三个模块间的文件交接。界面预览仍使用 [本地 AutoDesign](http://127.0.0.1:8767/)。

### Round 3：在 test-v1 整合完整三模块

**设计动机。** 用户要求先推送当前 `auto_design`，再新建 `test-v1`，把三个模块放入同一个前端入口，点击模块进入相应功能，保留全部能力。

**具体方案与关键参数。** 推送并核对 `auto_design` 远端提交后，从该提交创建 `test-v1`。完整引入 `origin/auto_search` 的 `3d28a34` 和 `origin/auto_writing` 的 `8aae3dc` 下对应模块，包括提示词、Schema、命令行入口、前后端和测试。新建 `workbench/`，公共端口为 8760，按 `/auto-search/`、`/auto-design/`、`/auto-writing/` 转发到三个原模块 HTTP 服务；模块页共享导航，原业务处理器和任务管理器继续工作。请求体、查询参数、PUT 编辑、DELETE、文件及 ZIP/PDF 下载均透传，HTML 报告不注入导航。默认运行数据位于 `assets/output/workbench/`，Auto Design 实际产物目录保留原约定。新增 `run_workbench.ps1`，原独立启动方式继续保留。

**结果数据。** 原仓库、三个模块及新增整合测试共 **234 passed、4 skipped、3 subtests passed**，耗时 18.83 秒。跳过项均来自原测试依赖的历史调研目录缺失，5 条 warning 来自原 SWIG 依赖。三个真实 Codex CLI 适配器均成功返回预期结构。Auto Writing 使用真实 `latexmk` 生成 15,582 bytes 的最小 PDF，并生成 LaTeX ZIP。浏览器验证了模块跳转、调研表单、仅设计任务创建、写作文件上传与创建、六章节及依赖提示、下载链接；工作台与三模块在 390px 下均无页面横向溢出，控制台没有 error/warn。Ruff 和五个 JavaScript 文件语法检查通过。日志见 `assets/logs/workbench/tests-final.log`、`cli-smoke/summary.json` 和 `ui-qa/`。工程 fixture 与正常任务分离，本轮没有科研实验结果。

**核心发现与失败原因。** 页面原先使用根路径 API，直接合并会使请求和下载进入错误模块，现按模块前缀统一生成地址，并保留单模块运行路径。跨模块完整流程测试还暴露了 Auto Search 在英文 Idea 中漏读 `Root-Cause Analysis` 与 `Cause` 的问题，现同时识别中英文标题。Auto Search 健康接口原先固定声称 CLI 已配置，现根据实际发现结果返回。Auto Writing 原先读取本机不兼容的全局 Codex 配置，现默认与其他模块一样隔离该配置，并保留 `CODEX_IGNORE_USER_CONFIG=0` 的显式选项。首次整合测试另有一处工程 fixture 把拒绝修改后的正确状态 `paused` 写成 `waiting_review`，已纠正预期；业务拒绝语义没有改变。

**下一步洞察。** 统一入口已能复用完整原功能，未引入第二套业务状态。实际使用可从调研模块选择 Idea，再通过文档交给实验模块，最后将真实实验说明和产物上传到写作模块。若将来增加“一键交接”，应明确传递用户选中的 Idea 和真实结果文件，继续保留各阶段的显式启动及科学批准边界；本轮不自动发起这些研究步骤。
