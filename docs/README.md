# Auto-Bench Skill 对接说明

## 1. 交付对象

当前交付对象是：

```text
skills/auto-bench
```

它是一个可被 Codex 自动发现和调用的 Skill，不是 Web 系统、后台服务或独立应用。根目录原有的 `autobench/` pipeline 现在只作为 Skill 内 deterministic runtime 的开发来源。

Skill 已复制安装到：

```text
${CODEX_HOME:-$HOME/.codex}/skills/auto-bench
```

## 2. Skill 能力

| 能力 | 输入 | 输出 |
|---|---|---|
| Method-to-Benchmark | Introduction + Method | 任务画像、benchmark portfolio、指标和 route |
| Base adaptation | Method + train/development records | 改造方案、合成 records、deterministic verification |
| New benchmark design | 新 Method | construct、数据 schema、生成模块、指标、切分和质量门槛 |
| Paper comparison | sealed plan + paper evidence | Match/Partial/Mismatch、missing、extra、route error |
| Feedback iteration | automatic review | typed errors 和下一轮通用优化方向 |

Skill 不会只推荐一个 benchmark，除非 Method 确实只有一个原子评测构造。

## 3. Skill 文件

| 文件 | 作用 |
|---|---|
| `skills/auto-bench/SKILL.md` | 触发描述、工作流、route 决策和输出要求 |
| `skills/auto-bench/agents/openai.yaml` | Codex UI 名称、短描述和默认提示词 |
| `skills/auto-bench/scripts/run_auto_bench.py` | 可移植 matcher 与 workflow runner |
| `skills/auto-bench/scripts/review_plan.py` | sealed plan 与论文证据的自动核对 |
| `skills/auto-bench/scripts/autobench/` | 自包含 deterministic runtime |
| `skills/auto-bench/assets/benchmark_catalog.json` | 26 条 literature-grounded benchmark records |
| `skills/auto-bench/references/input-schema.md` | Introduction/Method 输入格式 |
| `skills/auto-bench/references/paper-evidence-schema.md` | post-match 论文证据格式 |
| `skills/auto-bench/references/output-contract.md` | Skill 最终输出结构和决策语义 |

Skill 文件夹中没有 README、安装指南、changelog 或其他冗余文件。

## 4. 使用边界

### 已有论文

1. 只提取 Introduction 和 Method；
2. 保存 matcher-visible JSON；
3. 运行 Skill 生成 sealed plan；
4. 再读取 Experiment、Evaluation、Dataset 和 table caption；
5. 建立 paper evidence JSON；
6. 运行 `review_plan.py` 自动比较；
7. 输出 fresh 或 feedback evidence class。

### 用户的新 Method

1. 提取创新点对应的评测构造；
2. 运行 matcher；
3. 对 catalog 覆盖部分给 direct portfolio；
4. 对部分覆盖任务给 base adaptation；
5. 对完全新任务给 new benchmark synthesis；
6. 自动论文核对标记为 `NOT_APPLICABLE`；
7. 直接交付 benchmark、数据、指标、baseline 和 kill threshold。

### 数据构造

- 只使用明确的 train/development records；
- test、hidden 和 holdout records 不作为 synthesis seed；
- 保留 source benchmark、source split、source record IDs 和 transformation；
- expected output 必须经过 deterministic verifier；
- 冻结 validation/test 后再调 Method。

## 5. 验证结果

### 结构验证

- `quick_validate.py skills/auto-bench`：通过；
- path privacy scan：通过；
- TODO 数量：0；
- 私有绝对路径数量：0；
- `SKILL.md`：123 行；
- Skill 文件：21 个；
- runtime Python 模块：13 个。

### 独立前向测试

Skill 被复制到临时目录，并从仓库外运行以下场景：

1. ReAct Introduction/Method：输出 direct portfolio；
2. 全新 robot manipulation Method：输出 `new_benchmark_synthesis`；
3. scientific experiment planning：输出 `base_benchmark_adaptation`；
4. interaction、compositional、counterfactual 三种 synthesis verification：全部 `PASS`；
5. ReAct plan 与论文证据自动核对：输出 `PARTIAL`，准确暴露 `PORTFOLIO_PRECISION_GAP`；
6. 所有执行退出码：0。

### 安装验证

- 仓库源文件与安装副本 `diff -qr`：一致；
- 安装副本官方 validator：通过；
- 安装副本 `run_auto_bench.py --help`：退出码 0。

## 6. 实验推进历程

### Round 1 — Auto-Bench 原型

1. **设计动机：** 验证是否能从论文 Introduction/Method 自动恢复 benchmark。
2. **具体方案与关键参数：** 建立 task profile、26 条 benchmark catalog、多维兼容度和三类 route。
3. **结果数据：** matcher、portfolio、adaptation 和 synthesis pipeline 可运行。
4. **核心发现/失败原因：** 单 benchmark 推荐覆盖不了多任务论文，必须使用 portfolio。
5. **下一步洞察：** 加入 coverage-first ranking、task-balanced triangulation 和 route。

### Round 2 — Blind evaluation

1. **设计动机：** 防止模型看到论文 benchmark 名称后产生虚假高准确率。
2. **具体方案与关键参数：** worker 只接收 Introduction/Method 和公开 catalog；post-run 再加载论文 evidence。
3. **结果数据：** 三套 fresh suite 均保留 baseline 和 feedback regression；worker leakage checks 通过。
4. **核心发现/失败原因：** benchmark recall 高不等于 route 正确，catalog 外任务族也必须计入。
5. **下一步洞察：** 自动比较需要同时检查 recall、precision、unmodeled task family 和 route。

### Round 3 — 自动论文核对

1. **设计动机：** 消除重复的人工作答和 scope-bound submission。
2. **具体方案与关键参数：** 增加 Match/Partial/Mismatch evaluator 与 6 类 typed errors。
3. **结果数据：** Suite 003 feedback v3 达到 `3 Match / 2 Partial / 0 Mismatch`，route accuracy `1.0000`。
4. **核心发现/失败原因：** feedback regression 只证明已揭示论文上的修复，不能当作 fresh 泛化证据。
5. **下一步洞察：** 强制 evidence class，并让新 fresh suite 决定泛化状态。

### Round 4 — 从系统定位纠正为 Skill

1. **设计动机：** 用户明确交付目标是可复用 Skill，而不是独立系统。
2. **具体方案与关键参数：** 使用官方 `init_skill.py` 创建 `auto-bench`；只保留 SKILL.md、agents、scripts、references 和 assets。
3. **结果数据：** 生成 21 个 Skill 文件、13 个 runtime 模块、2 个 executable 和 26 条 catalog records。
4. **核心发现/失败原因：** 原 README、completion dashboard 和仓库 pipeline 属于开发原型，不是最终产品形态。
5. **下一步洞察：** 将仓库入口、安装、触发词和验证全部围绕 `skills/auto-bench` 表达。

### Round 5 — Skill 安装与独立前向测试

1. **设计动机：** 确认 Skill 离开当前仓库后仍可由另一个 Codex task 使用。
2. **具体方案与关键参数：** 把 Skill 复制到临时目录和 Codex skills 目录，运行 match、run、review_plan 和官方 validator。
3. **结果数据：** 所有执行退出码为 0；安装副本与仓库源一致；三种 synthesis verification 全部 `PASS`。
4. **核心发现/失败原因：** ReAct forward test 仍发现两个额外推荐，自动核对正确输出 precision gap，而不是隐藏问题。
5. **下一步洞察：** 后续优化直接修改 Skill runtime 和 SKILL.md，并用新的 unseen paper forward test，不再扩建独立系统 UI。

## 7. 下一步

1. 使用新 Codex task 通过 `$auto-bench` 做一次真实隐式触发测试；
2. 选择未参与当前规则设计的论文；
3. 保存 sealed plan；
4. 自动抽取 paper evidence 并运行 `review_plan.py`；
5. 根据 typed errors 更新 Skill；
6. 重新运行官方 validator、路径隐私和独立临时目录测试。
