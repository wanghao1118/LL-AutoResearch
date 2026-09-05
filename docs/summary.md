# exp31_autoresearch 内容说明

## 项目用途

本目录是 **AutoDesign** 的主代码仓，用来把上游 AutoSearch 给出的 Motivation、Contribution 和可选 Benchmark 转换为论文级实验设计，并在通过 R0 门控后推进实现、执行、结果诊断和独立完整性审计。它强调 Skill-first：科学判断由五个 Agent Skills 完成，Python 包只承担状态推进、契约校验、本地命令执行和结果完整性检查。

## 主要内容

- `skills/`：AutoDesign 编排、实验设计、实验执行、结果科学诊断和完整性审计五个 Skill。
- `autodesign/`：状态机、设计契约、结果 cell 校验、目标对比和命令行薄运行层。
- `apps/thainker-autodesign/`：读取真实本地任务状态的 AutoDesign 操作台。
- `tests/`：设计契约、状态与结果比较的回归测试。
- `scripts/`：Skill 安装等辅助脚本。
- `assets/`：本地运行输入、日志和输出，不属于发布源码的核心组成。

## 当前状态与边界

AutoDesign 采用“先设计、再执行”的硬边界，并区分 claim-bearing 实验、机制 pilot 和工程 smoke。模拟目标只能用于预写决策阈值，不能冒充观测结果；GPU、SSH 和机器资源来自使用者的 `AGENTS.md` 或 `CLAUDE.md`，不由 Python 包内置。具体实验项目的真实结果应到相应 run 目录核对，而不是从本仓库的框架能力推断。
