# 数学建模多 Agent 全流程工作台设计

日期：2026-07-10

## 1. 背景与决策

NotebookLM 当前已经具备资料管理、输出物、Skill 清单、Agent 运行记录和可检查的单 Agent 执行链路，但现有 Agent 主要执行“检索资料—单次生成—保存输出”。本设计将其扩展为面向数学建模比赛的可恢复工作流，使系统能够从题目和数据集出发，产出经过验证的代码、实验、图表、论文和 Git 提交。

首个 MVP 采用以下已确认决策：

1. 场景限定为数据驱动型数学建模，包括数据清洗、统计分析、预测、分类、评价和可视化。
2. 采用“状态机＋专业 Agent＋共享成果仓库”，不采用 Agent 自由讨论或单 Agent 动态切换角色作为核心架构。
3. 流程包含方案、实验执行、论文终稿和 Git 提交四个人工确认门禁。
4. Markdown 是可编辑论文中间稿，LaTeX 是正式源码，并自动编译 PDF。
5. 每道赛题拥有独立项目目录和独立 Git 仓库，避免成果混入 NotebookLM 应用源码仓库。
6. 最终成果保留代码、数据说明、图表、实验日志、依赖、论文源码、PDF 和复现说明。

## 2. 目标与非目标

### 2.1 产品目标

系统应让用户完成以下闭环：

```text
题目＋数据集＋比赛要求
  → 赛题解析
  → 数据体检
  → 候选模型与方案确认
  → 代码实现与执行确认
  → 可复现实验与结果验收
  → Markdown 论文
  → 事实一致性审稿
  → LaTeX/PDF
  → 成果打包
  → Git diff 与确认提交
```

用户必须能够检查每个阶段的输入、输出、Agent 行为、工具调用、失败原因、证据来源和审批记录。系统应在应用重启后从持久化状态继续，而不是重新生成已批准成果。

### 2.2 MVP 非目标

1. 不在首版覆盖运筹优化、微分方程、离散仿真、图论或机理建模。
2. 不在首版并行运行多个模型分支；数据结构保留未来并行能力。
3. 不让多个 Agent 进行无界自由对话。
4. 不允许未经用户批准的代码执行、论文定稿或 Git 提交。
5. 不自动执行 Git push、reset、clean、rebase、删除分支或远程仓库操作。
6. 不把 Docker 作为 MVP 的前置依赖；系统级沙箱是后续增强。
7. 不承诺自动生成的论文能够替代参赛者的学术判断或最终责任。

## 3. 总体架构

系统保留现有 React、TypeScript、FastAPI、SQLite 和本地文件架构，并新增“建模项目”领域。

```text
建模项目界面
    ↓
Modeling Project API
    ↓
Workflow Orchestrator（状态机与质量门禁）
    ↓
总控 / 建模 / 编程 / 论文 / 审稿 Agent
    ↓
Tool Runtime（数据分析、Python、LaTeX、Git）
    ↓
Artifact Store（结构化成果索引）
    ↓
独立项目目录与 Git 仓库
```

### 3.1 Modeling Project Service

负责创建项目、导入题目与数据、记录比赛要求、定位独立仓库、查询项目摘要，以及维护项目与现有 Sources、Outputs、Agents 的关联。

### 3.2 Workflow Orchestrator

状态机是流程状态的唯一真相来源。Orchestrator 负责：

1. 校验阶段进入和退出条件；
2. 创建角色任务；
3. 选择下一可运行任务；
4. 发起审批请求；
5. 验证审批内容哈希；
6. 处理失败、重试、回退和恢复；
7. 防止 Agent 自行跳过阶段。

### 3.3 Role Agents

各角色只完成专业任务，不能直接批准门禁。它们通过结构化成果和文件交接，而不是把聊天记录当作正式接口。

### 3.4 Tool Runtime

Tool Runtime 提供受限的数据读取、Python 执行、测试、图表检查、LaTeX 编译和 Git 操作。Agent 不能获得任意终端权限，所有可变更操作均绑定项目、任务、执行票据和内容哈希。

### 3.5 Artifact Store

SQLite 保存成果元数据、版本、哈希和来源关系；正文、代码、图表、日志和 PDF 保存于独立项目仓库。项目仓库是成果文件的权威来源，SQLite 是查询和流程索引。

## 4. 工作流状态机

### 4.1 主状态

```text
project_initialized
  → problem_parsing
  → data_profiling
  → model_planning
  → model_approval_pending
  → experiment_implementation
  → execution_approval_pending
  → experiment_running
  → result_validation
  → paper_drafting
  → consistency_review
  → final_approval_pending
  → packaging
  → commit_approval_pending
  → committing
  → completed
```

每个主状态都可附带 `blocked`、`failed` 或 `cancelled` 运行结果，但项目的持久化记录必须保留最后一个可恢复主状态。

### 4.2 阶段契约

#### 项目初始化

创建独立工作区和 Git 仓库，复制原始题目与数据，计算校验和，并将原始输入标记为只读。项目初始化成功后生成项目清单和初始 commit 候选，但不自动提交。

#### 赛题解析

提取子问题、目标变量、约束、评价方式、论文格式、交付要求和截止时间，生成 `problem/problem_spec.json`。若赛题存在无法安全推断的关键歧义，状态进入阻塞并请求用户说明。

#### 数据体检

执行只读分析，产出数据类型、缺失值、重复值、异常值、样本分布、相关性、潜在数据泄漏和数据质量报告。体检不修改 `data/raw`。

#### 候选方案设计与确认

建模 Agent 最多提出三个方案，分别说明假设、特征、算法、损失、评价指标、验证方法、风险、基线和所需图表。用户确认后，系统锁定方案版本及内容哈希。

#### 实验实现与执行确认

编程 Agent 生成 Python 源码、测试、依赖、实验配置和执行申请。审批卡必须展示文件差异、命令、输入输出路径、依赖变化、资源限制和网络需求。用户批准一个内容固定的实验批次后，运行器才可执行。

#### 实验运行与迭代

每次运行保存配置、随机种子、标准输出、标准错误、退出码、环境、指标、模型和图表。已完成实验不可覆盖。代码、依赖或命令发生变化时必须创建新实验批次并重新审批。自动返工最多三轮。

#### 结果验收

系统检查有效基线、训练验证隔离、指标方向、必要图表、可复现命令、数值有效性和结论证据。失败则退回实验阶段，不允许直接进入论文。

#### 论文草拟与一致性审稿

论文 Agent 先生成 Markdown，再转换为 LaTeX。论文数值和图表通过成果占位符引用，渲染时从 Artifact Store 解析。审稿 Agent 检查题目覆盖、公式与符号、实验事实、数据泄漏、过拟合、图表编号、参考文献和复现步骤。

#### 终稿、打包与提交

用户确认论文版本后，系统编译 PDF 并检查 LaTeX 错误、缺失引用和成果完整性。系统展示 Git diff、密钥扫描、受限数据检查和提交信息；用户确认后才允许 commit。

### 4.3 四个门禁

1. **方案门禁**：批准问题理解、模型方案、验证方案和预期产物。
2. **实验执行门禁**：批准确定的代码版本、命令、依赖和资源边界。
3. **终稿门禁**：批准 Markdown、LaTeX 和由成果占位符解析出的事实。
4. **Git 门禁**：批准文件清单、diff 摘要和 commit message。

审批绑定内容哈希。审批后任何相关内容发生变化，审批立即失效。

## 5. 独立项目目录与成果契约

```text
modeling-project/
├─ README.md
├─ problem/
│  ├─ original/
│  ├─ problem_spec.json
│  └─ requirements.md
├─ data/
│  ├─ raw/
│  ├─ interim/
│  ├─ processed/
│  └─ data_manifest.json
├─ analysis/
│  ├─ data_profile.json
│  ├─ data_report.md
│  └─ model_plan.md
├─ src/
│  ├─ prepare.py
│  ├─ features.py
│  ├─ train.py
│  ├─ evaluate.py
│  └─ visualize.py
├─ tests/
├─ experiments/
│  └─ exp-0001/
│     ├─ config.json
│     ├─ run.log
│     ├─ metrics.json
│     ├─ artifacts.json
│     └─ environment.json
├─ figures/
├─ tables/
├─ paper/
│  ├─ draft.md
│  ├─ main.tex
│  ├─ references.bib
│  └─ sections/
├─ deliverables/
│  ├─ paper.pdf
│  ├─ code.zip
│  └─ manifest.json
├─ .workflow/
│  ├─ state.json
│  ├─ approvals.json
│  ├─ artifact_index.json
│  └─ runs/
├─ requirements.txt
├─ reproduce.ps1
└─ .gitignore
```

### 5.1 不可变规则

1. `problem/original` 和 `data/raw` 导入后不可由 Agent 修改。
2. 已完成的 `experiments/exp-*` 不可覆盖；任何变化创建新实验编号。
3. `.workflow/approvals.json` 只能由审批服务写入。
4. 每个成果记录生成代码、实验、输入数据、内容哈希和被引用位置。
5. 论文 Agent 只能引用已登记成果，不能直接从非结构化日志中摘取数字。

### 5.2 数据提交政策

小型且许可允许的数据可提交。大型、敏感或受限数据默认不提交，只记录来源、许可、校验和、获取说明和预期路径。提交前的 `deliverables/manifest.json` 必须明确列出未包含的数据及复现要求。

### 5.3 成果验证

首版使用 JSON Schema 验证 `problem_spec.json`、实验配置、指标、成果索引、Agent 交接结果和交付清单。必需文件缺失、格式无效、哈希不符或引用断裂时，阶段不得完成。

## 6. Agent 角色与协作协议

### 6.1 总控 Agent

读取状态、检查输入、拆解任务、选择角色并生成审批摘要。可以建议状态转换，但不能修改专业成果或代替用户审批。

### 6.2 建模 Agent

根据赛题、数据报告、评价要求和实验结果设计假设、特征、算法、评价方案、敏感性分析、稳健性分析、消融和图表计划。不能执行代码，也不能把预期结果写成已验证事实。

### 6.3 编程 Agent

把已批准方案实现为 Python 源码、测试、依赖和实验配置。只能通过注册工具操作项目工作区，不能修改原始输入、审批记录或已完成实验。

### 6.4 论文 Agent

使用已批准方案、成果索引、图表、表格和文献编写 Markdown 与 LaTeX。实验事实使用以下形式的引用占位符：

```text
{{metric:exp-0007.validation_rmse}}
{{figure:artifact-0032}}
```

渲染器解析占位符，记录论文结论与实验成果之间的关系。

### 6.5 审稿 Agent

独立检查题目覆盖、假设、符号、公式、算法、指标、图表、数据泄漏、过拟合、摘要与结论、文献引用和复现步骤。它只提交带严重等级的问题清单，不能静默修改代码或论文。

### 6.6 统一交接结果

```json
{
  "status": "completed",
  "summary": "本轮完成内容",
  "artifacts_created": [],
  "artifacts_consumed": [],
  "issues": [],
  "recommended_transition": "result_validation",
  "requires_user_approval": false
}
```

Agent 不直接发起无限对话。同一阶段最多自动返工三轮；超过上限后进入阻塞，由总控 Agent 汇总证据和待决问题交给用户。

## 7. 安全执行与失败恢复

### 7.1 Python 执行

每个项目使用独立虚拟环境。运行器直接调用参数数组，不执行由 Agent 拼接的 shell 字符串。运行器必须：

1. 将工作目录限制在项目仓库；
2. 只允许声明过的读写路径；
3. 清除 API 密钥等敏感环境变量；
4. 默认禁止网络；
5. 禁止长期后台进程；
6. 设置超时、输出上限和进程树终止；
7. 拒绝绝对路径、路径穿越和项目外写入；
8. 将原始输入、审批记录和历史实验以只读方式暴露；
9. 将新依赖安装作为独立审批动作，并锁定准确版本。

首版实现应用层限制。Docker 或系统级隔离作为后续纵深防御，不影响现有工具接口。

### 7.2 LaTeX 与 Git

LaTeX 只能在 `paper/` 中编译，结果写入 `deliverables/`，并禁用 shell escape。

Git 工具仅开放 `status`、`diff`、对明确文件列表执行 `add`，以及使用已批准消息执行 `commit`。不开放 push、reset、clean、rebase、删除分支和修改远程仓库。提交前检查密钥、超大文件、临时文件和受限数据。

### 7.3 失败分类

系统使用稳定错误类别：

- `input_error`：题目或数据缺失；
- `schema_error`：成果格式无效；
- `code_error`：语法、导入或测试失败；
- `experiment_error`：训练失败、指标异常或数值不稳定；
- `resource_error`：超时、内存或磁盘超限；
- `latex_error`：编译、字体或引用错误；
- `policy_error`：越权路径、危险命令或未批准操作；
- `external_error`：依赖源或模型服务不可用。

错误记录所属阶段、是否可重试和建议恢复动作，但不返回密钥或不必要的系统路径。修改代码、依赖或命令后的重试必须重新审批。状态、任务和日志持久化，使应用重启后可继续执行。

## 8. 前端建模工作台

现有导航新增“建模项目”。主界面使用三栏布局：

```text
项目与阶段列表 │ 当前阶段主工作区 │ 证据、日志与审批检查器
```

### 8.1 左侧项目列表

展示当前阶段、完成比例、最近 Agent、待审批事项、阻塞或失败标记、截止时间和最近 commit。支持创建、暂停、恢复和归档项目。

### 8.2 中间阶段工作区

顶部显示阶段进度，主体提供赛题、数据、方案、代码、实验、论文和交付视图。界面只突出当前合法动作，并通过统一审批卡完成批准、要求修改或回退。

### 8.3 右侧检查器

展示 Agent 输入和摘要、成果来源、论文引用位置、执行日志、审稿问题、错误分类和审批历史。

### 8.4 审批卡

审批卡展示本阶段变化、目标状态、覆盖文件或命令、风险和自动检查结果。批准绑定内容哈希，相关内容变化后自动失效。

### 8.5 与现有模块集成

1. Sources 提供参考论文、规则和背景资料。
2. Agents 保留底层运行记录，建模项目展示业务流程。
3. Outputs 可收录最终论文和图表，但独立项目仓库仍是完整成果来源。
4. Settings 增加 Python、LaTeX、Git 和运行资源状态。

## 9. 后端数据模型与 API

### 9.1 SQLite 实体

- `modeling_projects`：项目、仓库路径、状态、截止时间和版本；
- `workflow_transitions`：状态转换、原因、触发者和时间；
- `workflow_tasks`：角色任务、输入、输出要求、重试次数和状态；
- `project_artifacts`：成果 ID、类型、相对路径、哈希、来源和版本；
- `experiment_runs`：实验、配置、执行票据、进程状态、资源和指标路径；
- `approval_requests`：门禁类型、内容哈希、风险和待批准动作；
- `approval_decisions`：决定、操作者、意见和时间；
- `paper_claims`：论文结论位置及其指标、图表和实验引用；
- `project_commits`：diff 摘要、提交信息、commit hash 和清单版本。

现有 `agent_runs` 与 `agent_steps` 继续使用，并关联项目、任务和阶段。

### 9.2 API

```text
POST   /api/modeling/projects
GET    /api/modeling/projects
GET    /api/modeling/projects/{id}
POST   /api/modeling/projects/{id}/inputs
POST   /api/modeling/projects/{id}/advance
POST   /api/modeling/projects/{id}/rollback

GET    /api/modeling/projects/{id}/tasks
POST   /api/modeling/projects/{id}/tasks/{task_id}/run
GET    /api/modeling/projects/{id}/runs

GET    /api/modeling/projects/{id}/artifacts
GET    /api/modeling/projects/{id}/artifacts/{artifact_id}

GET    /api/modeling/projects/{id}/approvals
POST   /api/modeling/projects/{id}/approvals/{approval_id}/decide

GET    /api/modeling/projects/{id}/experiments
POST   /api/modeling/projects/{id}/experiments/{exp_id}/execute

POST   /api/modeling/projects/{id}/paper/render
POST   /api/modeling/projects/{id}/paper/compile
GET    /api/modeling/projects/{id}/deliverables

GET    /api/modeling/projects/{id}/git/diff
POST   /api/modeling/projects/{id}/git/commit
```

`advance` 不接受任意目标状态，只请求状态机检查退出条件。执行、编译和 commit 需要有效审批令牌，并保证幂等。文件访问只接受成果 ID，不接受前端提供的任意本地路径。

## 10. 测试策略

### 10.1 单元和契约测试

1. 状态机合法转换、非法跳转、回退、重试上限和恢复；
2. JSON Schema、内容哈希、不可变实验和论文引用解析；
3. Agent 返回缺字段、无效 JSON、空输出和矛盾建议；
4. 审批内容变化后的令牌失效；
5. 成果依赖关系和交付清单完整性。

### 10.2 安全和集成测试

1. 路径穿越、绝对路径、危险命令和项目外写入；
2. 敏感环境变量清除、网络默认关闭和依赖审批；
3. 运行成功、超时、测试失败、依赖缺失、进程终止和日志截断；
4. LaTeX 占位符替换、无依据数字拦截、交叉引用和编译失败；
5. Git 超大文件、密钥、受限数据、空提交和重复提交。

### 10.3 前端和端到端测试

测试阶段显示、审批卡、内容变化后的重新审批、失败恢复和项目重载。端到端测试使用固定的小型赛题和 CSV，完成从导入到 PDF 和 commit 的真实闭环。

## 11. MVP 验收标准

固定回归赛题必须能够：

1. 创建独立目录与 Git 仓库；
2. 导入题目、要求和数据；
3. 生成赛题规范和数据报告；
4. 提出并批准候选方案；
5. 生成代码和执行申请；
6. 经批准后运行基线及至少一个候选模型；
7. 保存可复现配置、日志、指标、图表和环境；
8. 根据真实成果生成 Markdown；
9. 通过论文与实验一致性检查；
10. 经确认后生成 LaTeX 并编译 PDF；
11. 生成交付清单和复现说明；
12. 展示 Git diff 并经批准完成 commit；
13. 重启应用后继续未完成项目并查看全部历史。

论文数值无法追溯、代码无法复现、PDF 编译失败、审批内容变化或成果清单不完整时，系统必须阻止提交。

## 12. 实施阶段

本文件是覆盖完整闭环的总体设计。为控制单次变更范围，每个阶段使用独立实现计划、独立验收和独立提交；书面复核通过后首先只为阶段 1 编写实现计划。后续阶段以已经稳定并经过测试的状态机、成果契约和 API 为前置条件，不在一个超大计划中同时实现。

### 阶段 1：建模项目基础

项目实体、独立工作区、状态机、成果索引、项目列表和阶段页。完成后可以创建项目并持久化推进一个不执行代码的模拟流程。

### 阶段 2：赛题、数据与方案

输入导入、题目解析、数据体检、建模 Agent 和方案审批。完成后可以从真实 CSV 生成可审核方案。

### 阶段 3：实验执行

编程 Agent、执行申请、受限运行器、实验记录、指标和图表。完成后可以经审批运行基线与候选模型。

### 阶段 4：论文与审稿

Markdown、成果占位符、论文 Agent、审稿 Agent、LaTeX 和 PDF。完成后可以从已登记实验生成可追溯论文。

### 阶段 5：交付与 Git

交付清单、复现检查、Git diff、审批 commit 和 Outputs 关联。完成后形成独立、可复现的参赛成果仓库。

### 阶段 6：稳定性与回归

恢复、资源限制、安全测试、固定赛题端到端回归和界面完善。

每个阶段都必须通过相关后端测试和前端构建，并交付一条可演示的纵向链路。阶段 1 完成并验收后，再分别为阶段 2 至阶段 6 编写实现计划。
