# AutoDesign 远端 GPU Agent 运行约束

以下内容会原样拼接到远端 Agent 的运行提示词中。请把所有 `TBD` 替换成服务器上的实际值，并与 `configs/remote_gpu.local.json` 保持一致。

## 强制资源

- 仅使用 GPU：`GPU_INDEXES_TBD`
- 需要的 GPU 数量：`GPU_COUNT_TBD`
- 最大并行实验数：`1`
- 单次命令最长运行秒数：`86400`

## 强制目录

- 允许根目录：`/REMOTE/ALLOWED_ROOT_TBD`
- Git 仓库目录：`/REMOTE/ALLOWED_ROOT_TBD/exp31_autoresearch`
- 实验工作目录：`/REMOTE/ALLOWED_ROOT_TBD/exp31_autoresearch`
- 代码、配置、缓存、日志、checkpoint 与结果均放在允许根目录内。
- 远端 Agent 执行任何命令前先确认 `pwd` 位于允许根目录内。

## 代码同步

- 代码传输模式由 `configs/remote_gpu.local.json` 的 `transfer.mode` 决定，可选 `git` 或 `rsync`。
- Git 模式：AutoDesign 控制源码由远端 clone 或 pull。
- rsync 模式：本机增量同步 AutoDesign 控制源码到仓库目录，排除 `.git`、`.venv`、本机配置、日志和结果目录。
- 两种模式都会把当前 run 的 `generated_project` 单独 rsync 到实验工作目录；同步前该目录及其环境文件必须已经由 `materialize-code` 生成。
- 分支：`codex/autodesign`
- 更新方式：`git fetch`、`git checkout`、`git pull --ff-only`。
- 远端存在未提交的跟踪文件修改时停止 pull，并在记录中报告具体文件。
- 实验结果、日志和 checkpoint 不提交到源码分支，保存在配置指定的 result 路径。
- 结果回收使用 rsync 增量下载到本机 `assets/output/remote_gpu/results`。

## Conda 环境

- Conda 可执行文件：`/REMOTE/CONDA_BIN_TBD`
- 环境名：`autodesign-gpu`
- 环境定义：`environments/autodesign-gpu.yml`
- 首次运行执行 `conda env create`；已有环境执行 `conda env update --prune`。
- 控制环境完成后，继续读取实验工作目录内 `implementation_manifest.environment_file` 指定的 Conda YAML，更新同一个环境以安装真实实验依赖。
- 所有 smoke、experiment、aggregate 命令均通过 `conda run -n autodesign-gpu` 执行。

## 执行与记录

- 每次运行记录 Git commit、Conda 环境、`CUDA_VISIBLE_DEVICES`、完整命令、开始/结束时间、stdout、stderr 与 exit status。
- `CUDA_VISIBLE_DEVICES` 必须等于本文件声明的 GPU 列表。
- 先执行 smoke；smoke exit status 为 0 后再启动完整实验。
- 运行失败时保留已有日志、checkpoint 和结果文件，修复后从项目支持的恢复入口继续。
- 主实验、消融、case study 与 interesting experiment 使用同一份已经通过 coverage gate 的设计。

## 用户补充约束

- `USER_RULE_TBD`
