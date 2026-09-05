# The ThAInker Autodesign

一个中文多任务实验控制台。每个 `idea.md` 会创建独立任务、Codex thread 和 `assets/output/<run>` 目录；页面展示当前阶段、实时事件、产物与需要人工判断的方法修改断点。

也可以在“新建任务 → 接续已有任务”中输入已有的 `codex://threads/<thread-id>` 和原实验绝对路径。系统先读取该目录的 `AUTODESIGN_STATE.md`，只把任务登记为“已暂停”并展示现有状态；不会在导入时自动执行。用户之后明确点击“继续实验”，本地服务才会用原 thread、原工作目录和已有产物恢复。

## 两种运行方式

- 公开网页：用于查看和操作前端，不需要 ChatGPT 登录。由于公开网页不能直接启动用户电脑上的 Codex，本地服务未连接时会明确显示“演示模式”。
- 本地真实执行：网页连接本机 Node 服务，由 Codex SDK 在当前工作区使用 `gpt-5.6-sol` 和 `xhigh` 启动或恢复 `$run-autodesign`。

## 本地启动

在当前目录打开两个终端：

```bash
npm run dev:server
```

```bash
NEXT_PUBLIC_AUTODESIGN_API=http://127.0.0.1:4317 npm run dev
```

本地服务默认把当前仓库预填为新任务的实验项目目录，也可以在上传窗口中改成其他绝对路径。Codex 在所选项目目录内工作，每个 Idea 的实验产物写入该项目自己的：

```text
assets/output/thainker_<时间>_<任务编号>/
```

控制台本身的任务索引仍写到：

```text
assets/output/thainker-autodesign/tasks.json
```

例如上传 exp39 的 `idea.md` 时，将实验项目目录填写为 `/Users/yzb/Desktop/research/exp39`，Codex 就会读取 exp39 的相对路径和数据，产物也不会混入 exp31。

## 多任务与 GPU

前端可同时保存、查看和审核多个任务。服务默认一次执行一个完整 AutoDesign 任务，其余任务显示为“排队中”。只有各任务的 `command_plan.json` 明确采用互不重叠的单卡资源时，才把并发数设为 2：

```bash
AUTODESIGN_TASK_CONCURRENCY=2 npm run dev:server
```

这不会改变每个任务内部的 AutoDesign GPU 规则。

正式实验页面优先展示训练、预测、遮挡实验等真实完成数、当前实验单元和关键里程碑。SSH、文件查询和状态检查等底层命令不在页面展示；“关键实验节点”可展开查看较早记录。

“实验方案”页面读取当前任务的 Idea 与真实 `experiment_design.md`，顶部展示总体目标和核心贡献，随后按主实验、消融实验、Case Study、分析实验列出每项实验要回答的问题、比较与操作、主要展示指标、实验变体和对应贡献。设计完成或修订时，Codex 同步维护中文展示摘要 `frontend_plan.json`；该文件只负责前端呈现，不改变科学设计，也不写入模拟结果。

运行中的任务支持“自动安全暂停”。点击后，本地服务会立即写入持久暂停标记，禁止启动新的实验单元；当前单元自然结束后，服务会自动开启安全收尾回合，校验在途结果、记录精确恢复点并停止 Codex。只有这些动作完成后，页面才显示“已暂停”并开放“继续实验”。已经启动的实验单元和已有结果不会被直接杀掉或删除；本地服务在暂停过程中重启时，也会自动接着完成安全收尾。

## 人工断点

普通 preflight、smoke、执行、聚合与收集失败由 Codex 按边界修复规则自动处理。只有状态进入 `WAITING_FOR_METHOD_REVISION_APPROVAL` 时，页面才显示 Yes 或 No，并把所选决定与准确的 `Revision ID` 一起交回原 Codex thread。

在默认修改次数内：

- Yes：`APPROVE_MINIMAL_METHOD_REVISION`
- No：`REJECT_METHOD_REVISION`

达到修改次数上限时：

- Yes：`APPROVE_EXCEPTION_METHOD_REVISION`
- No：`ABANDON_IDEA`

## 接续已有 Codex 任务

接续功能需要两项信息：

- Codex 任务链接或 thread ID，例如 `codex://threads/01a03823-0593-7203-a379-c44be38c8d70`
- 该任务原来的实验目录，例如 `/Users/yzb/Desktop/research/exp40`

原目录必须保留 `AUTODESIGN_STATE.md`。导入和恢复是两个独立动作：导入只读取状态；“继续实验”才调用 Codex SDK 的 `resumeThread`。恢复时仍固定使用 `gpt-5.6-sol` 与 `xhigh`，并要求 Codex从第一个未完成阶段继续，不重跑已有效的昂贵阶段。

已有实验目录不要求自身是 Git 仓库。服务只对“接续已有任务”传递 SDK 的 `skipGitRepoCheck` 选项；新建任务仍保留默认 Git 工作区检查。
