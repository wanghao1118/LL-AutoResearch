# AutoDesign 对接说明

## 1. 当前结论

当前分支为 `fix/AutoDesign`。分支只保留以下生产范围：

1. 七个 Skill；
2. 状态、结果完整性、本地命令和远端 GPU 的薄运行包；
3. Skill 安装、卸载与一个端到端 demo；
4. 四组核心回归测试；
5. 一个最小输入 fixture、远端配置示例、文档和可视化。

方法路线、baseline、训练范式、证据语义和论文 claim verdict 全部由 Skill/Codex 处理。Python 不再承担研究决策。

## 2. 最终文件边界

### 2.1 生产代码

| 路径 | 保留原因 |
| --- | --- |
| `autodesign/cli.py` | 统一暴露薄运行命令 |
| `autodesign/io.py` | 小型 JSON 和文本读写 |
| `autodesign/runner.py` | 执行本地五阶段 command plan |
| `autodesign/skillflow.py` | 初始化、推进、恢复和验证运行状态 |
| `autodesign/skillresults.py` | 校验 schedule/result cells 并聚合 |
| `autodesign/remote_gpu.py` | 可选 SSH、Conda、GPU、收集与恢复 |
| `autodesign/__init__.py`、`__main__.py` | Python package 与 CLI 入口 |

共 `8` 个 Python 文件、`2,414` 行。

### 2.2 Skills

| Skill | 单一职责 |
| --- | --- |
| `run-autodesign` | 编排与恢复 |
| `autodesign-method-router` | 方法路线和 R0 |
| `autodesign-evidence-designer` | contribution-complete evidence plan |
| `autodesign-implementer` | 生成可运行实验项目 |
| `autodesign-executor` | 五阶段本地或远端执行 |
| `autodesign-result-scientist` | 结果完整性、科学诊断、完整 tuning Prompt 与下一轮路由 |
| `autodesign-integrity-auditor` | 独立最终审计 |

### 2.3 运维与验证

| 路径 | 保留原因 |
| --- | --- |
| `scripts/install_autodesign_skills.sh` | 安装和验证七个 Skill |
| `scripts/uninstall_autodesign_skills.sh` | 删除完整 Skill 套件 |
| `scripts/run_skill_first_demo.sh` | 唯一端到端 fixture |
| `tests/test_skill_suite.py` | Skill 完整性和最小分支边界 |
| `tests/test_skillflow.py` | 状态机和失效传播 |
| `tests/test_skillresults.py` | cell 完整性与聚合 |
| `tests/test_remote_gpu.py` | 远端命令和五阶段合同 |
| `assets/input/demo_input.json` | demo 的最小自然语言输入 |
| `configs/remote_gpu.example.json` | 可复制的远端配置 |
| `configs/remote_agent_policy.template.md` | 可复制的远端 Agent 约束 |
| `environments/autodesign-gpu.yml` | 远端控制环境 |

`configs/*.local.*`、`assets/output/` 和 `assets/logs/` 是本机运行状态，均被 Git 忽略，不属于分支交付。

## 3. 已删除内容

| 内容 | 删除原因 |
| --- | --- |
| 旧 `src/autoresearch/` | AutoSearch/AutoBench 应用，不属于 AutoDesign |
| 顶层 `prompts/` 和 `autodesign/templates/` | 旧 renderer 和重复模板已删除；当前完整 tuning Prompt 的唯一生产副本位于 result-scientist Skill references |
| `examples/` | 一次性旧 schema 与三类迁移验证 fixture，不是生产入口 |
| `scripts/audit_idea_type_validation.py` | Round 25 一次性验收脚本 |
| `scripts/compare_user_blind_routes.py` | Round 22 一次性盲测比较脚本 |
| 单 Skill 安装/卸载 wrapper | 与完整七 Skill 安装器重复 |
| 盲测和 worker 临时输入 | 已完成迁移，不是用户入口 |
| Python、pytest、Ruff 缓存 | 生成物，不属于源码 |

历史实验输出没有加入分支；本机 gitignored 证据仍保留在 `assets/output/` 和 `assets/logs/`。

## 4. 当前执行合同

### 4.1 自然语言入口

```text
使用 $run-autodesign 处理 assets/input/demo_input.json，运行目录使用 assets/output/my_run；完成方法路线、证据设计、项目实现、五阶段执行、结果诊断和完整性审计。
```

### 4.2 五阶段顺序

```text
preflight → smoke → experiment → aggregate → collect
```

三个会阻止错误结论的边界：

- R0 必须是实际执行记录，不能由设计文本自行填写通过；
- scheduled cells 与 observed cells 必须精确相等；
- 聚合器不产生科学 claim verdict，最终由 result scientist 和 integrity auditor 判断。
- 每轮诊断必须生成 `result_route.md`；开放的 iteration 或 execution-required tuning 必须执行并重新诊断后才能进入最终审计。

### 4.3 项目代码依赖

研究推理不依赖项目 Python。完整自动执行仍使用薄层：

```text
skillflow.py    状态事实
skillresults.py 结果完整性
runner.py       本地命令
remote_gpu.py   可选远端执行
```

通用单阶段执行器已经放在 `autodesign-executor` Skill 内，因此离开当前仓库仍可记录本地阶段；只有统一 CLI、确定性摄取和远端控制需要安装本 package。

## 5. 实验推进历程

### Round 21：从工程化单体迁移到七 Skill

**设计动机**

旧实现把研究空间压入大型 JSON schema，增加新方法族时要同时修改 prompt、validator、pipeline 和测试，限制 Codex 对方法路线的自主判断。

**具体方案与关键参数**

将方法路由、证据设计、实现、执行、结果诊断和完整性审计拆为六个 worker Skill；`run-autodesign` 只编排。Markdown 保存研究推理，JSON 只保存执行事实。

**结果数据**

形成七个可安装 Skill 和 canonical run artifact contract。

**核心发现/失败原因**

完全删除代码会失去命令失败恢复和结果完整性；问题不是代码存在，而是研究决策和执行保障混在同一层。

**推导出的下一步洞察**

用独立盲测比较 Skill-first 与旧 schema，而不是继续主观讨论架构。

### Round 22：Luna Max 双路线盲测

**设计动机**

验证 Skill-first 是否真的减少上下文和 schema 修复成本。

**具体方案与关键参数**

用户在两个独立任务中使用 `gpt-5.6-luna`、max reasoning，分别运行 Skill-first Markdown 与旧单体 schema。

**结果数据**

Route A 使用 `215,006` tokens、`880` 秒、`18,052` 输入字节，形成 `9` claims 和 `36/36` evidence obligations。Route B 使用 `324,727` tokens、`1,153` 秒、`92,569` 输入字节，严格 validator 发现 `23` 个错误。

**核心发现/失败原因**

旧 schema 虽然外形字段齐全，仍出现 fairness、test axis、调度和 figure series 对不齐。不同 validator 的 PASS/FAIL 不能直接当成模型质量分数。

**推导出的下一步洞察**

固定 Skill-first Markdown 为研究规划入口，薄代码只保留执行和 provenance。

### Round 23：真实 worker handoff

**设计动机**

盲测只证明设计输出，需要验证 implementer、executor 和 result scientist 能接真实数据。

**具体方案与关键参数**

对已有 STeP `50` 条 source records 做 provenance replay，执行五阶段并保持数值不变。

**结果数据**

五阶段全部 exit `0`，`50/50` cells、`200` aggregates、`4/4` 文件 byte-equal。

**核心发现/失败原因**

发现 portable runner 仍把 smoke 硬编码为第一阶段，导致 smoke 清除 preflight。分支已改为从 `STAGES[0]` 派生。

**推导出的下一步洞察**

worker 链已经闭合，可以删除旧 Python 研究 pipeline。

### Round 24–25：薄代码与三类方法族

**设计动机**

确认删除旧决策层后，Skill 仍能处理 train-free、SFT/DPO 和 RL/agent-environment 三类不同机制。

**具体方案与关键参数**

Python 包缩为状态、执行、摄取和远端运行；三类 fixture 分别实现 inference-time controller、checkpoint training/reload 和实际 reset/step/Q-learning。

**结果数据**

Python 从 `18` 文件、`7,249` 行缩为 `8` 文件、`2,170` 行。三类运行分别完成 `46/46`、`48/48`、`48/48` cells，并通过工程完整性审计。

**核心发现/失败原因**

研究方向已经不依赖 Python，但一次性迁移脚本、旧 Prompt 和验证 fixture 仍留在工作树，容易让人误以为它们是生产依赖。

**推导出的下一步洞察**

执行一次基于引用关系的分支清理，只保留生产代码、Skill 和必要回归。

### Round 26：最小分支清理

**设计动机**

用户要求直接看到当前 Skill 真正依赖哪些代码，删除已完成迁移后不再使用的文件。

**具体方案与关键参数**

保留 `8` 个薄运行 Python 文件、七 Skill、三个运维脚本、四个测试文件、一个输入 fixture 和远端执行示例；删除旧 Prompt、模板副本、examples、一次性比较/审计脚本、重复 wrapper、临时输入与缓存。安装和 demo shell 统一改为 Linux/macOS 均可用的 Bash。

**结果数据**

最终回归结果记录在 `assets/output/minimal_branch_delivery/VERIFICATION.txt`；分支树和删除项展示在 `docs/autodesign-direction-review.html`。

**核心发现/失败原因**

生产依赖现在可直接从顶层目录看清：`skills/` 是研究层，`autodesign/` 是薄运行层。历史证据保留为本机 gitignored 产物，不进入分支。

**推导出的下一步洞察**

下一次新 Idea 直接从 `$run-autodesign` 和 `assets/input/demo_input.json` 的形状启动；不再恢复任何已删除旧入口。

### Round 27：补齐结果微调 Prompt 与复诊闭环

**设计动机**

最小分支清理把完整 `result_tuning_prompt.md` 当成重复模板删除了，但 result-scientist 只保留了摘要规则；同时诊断状态固定指向最终审计，iteration/tuning 尚未执行时可能提前进入 audit。

**具体方案与关键参数**

把用户源的完整 `153` 行结果微调 Prompt 放入 `autodesign-result-scientist/references/`，只在 route=`tuning` 后加载。新增 `result_route.md`、条件工件 `result_tuning.json` 和 `next_round.md`；把 `RESULT_DIAGNOSIS_READY` 的下一步改为 `run-autodesign`，由编排器分发 owner Skill，并要求执行、摄取和重新诊断后才关闭 route。

**结果数据**

当前 `21` 项完整单元测试通过，端到端 demo 的五阶段全部 exit `0`，结果为 `4/4` cells，七个 Skill 全部安装并通过 `quick_validate.py`。工程化交付快照的 `41` 项测试也在独立解包目录通过，用于功能矩阵对照。

**核心发现/失败原因**

迁移缺失的不是新的研究阶段，而是“诊断决定之后真正执行 tuning/iteration 并复诊”的控制回路。只把完整 Prompt 复制进 Skill 仍不够；必须显式记录 route、owner、execution requirement 和 closure condition。

**推导出的下一步洞察**

继续保持研究判断在 Skill、执行事实在薄代码。后续不恢复大 schema；在正式交付前应把当前工作树形成独立 Git 提交，否则 `fix/AutoDesign` 与 `codex/autodesign` 的 branch ref 仍无法表达功能差异。

### Round 28：执行记录、远端预检与状态机缺陷修复

**设计动机**

多命令 stage、全流程续跑、失败证据保存、旧远端 run、审计状态推进和 Markdown 状态解析存在八个可复现缺陷。单命令 demo 全绿没有覆盖这些真实工作流。

**具体方案与关键参数**

portable runner 按 `command_plan.json` 追加同一 stage 的命令记录，并在失败重试时只替换失败命令及其后缀；本地 `run-local --stage all` 直接比较当前计划并复用未变化的成功 stage 前缀。被拒绝的乱序请求不再写回 `execution_record.json`。远端 validate 在 deploy 前要求 `generated_project/`、五阶段 command plan、非空 experiment schedule 和有效 result contract。本机 remote run 已从旧 `exp34_step_r0` 切换到完整的 Skill-first run。状态机新增宽松 Markdown 表格解析、`skill-repair-state`、审计 PASS 门和进行中状态的 last-completed 映射。

**结果数据**

修改前复现器得到 `BUG_BASELINE status=FAIL observed=8/8`。修改后逐项验证得到 `BUGFIX_VERIFICATION status=PASS fixed=8/8`；完整回归增加到 `31` 项。端到端 demo 仍为五阶段 exit `0`、`4/4` cells、最终 `COMPLETE`。真实本机 remote 配置验证为 `PASS`，`remote-all --dry-run` 包含五个项目 stage；把配置临时指回旧 run 时在 `validate` 阶段立即 `FAIL`，不会进入 deploy。

**核心发现/失败原因**

问题集中在“单 stage 单命令”的隐含假设和“文件存在即可推进”的弱门控。旧测试只验证顺序主路径，没有验证同 stage 追加、失败后乱序请求、计划中途变化和审计 FAIL。

**推导出的下一步洞察**

执行层需要验证最小事实合同，但不重新引入研究设计 schema。之后新增 runner 行为时，必须同时覆盖成功前缀、失败证据、计划变化、拒绝尝试和资源消耗前预检。

## 6. 验证命令

```bash
python3 -m unittest discover -s tests -v
.venv/bin/ruff check .
python3 -m compileall -q autodesign skills scripts tests
bash scripts/run_skill_first_demo.sh assets/output/skill_first_demo
bash scripts/install_autodesign_skills.sh
python3 -m autodesign remote-validate configs/remote_gpu.local.json
python3 -m autodesign remote-all configs/remote_gpu.local.json --dry-run
```
