# Auto Design 重构交接

本轮将 AutoDesign 改为与 Auto Search、Auto Writing 同类的独立网页模块：原生前端、Python 服务、Codex CLI 分阶段调用。当前分支为 `auto_design`，基线是仓库 `main` 的 `01615b8`；旧 `autodesign` 分支 `af51260` 仅作为科学规则和运行工具的迁移来源。

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
