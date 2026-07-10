# 数学建模工作流 Goal 循环执行手册

日期：2026-07-11

## 1. 用途

本手册用于在新的 Codex 会话中，以“一个阶段一个 Goal”的方式执行数学建模工作流。每个 Goal 只负责一个阶段，按对应计划中的 Task 顺序循环，达到阶段 Gate 后停止。下一阶段必须在用户检查后，以新的 Goal 启动。

官方建议 Goal 具有单一目标、明确停止条件、必读文件、验证证据、检查点和简短进度日志。本手册将这些要求固化为仓库内协议。参考：[OpenAI — Follow a goal](https://learn.chatgpt.com/codex/use-cases/follow-goals)。

## 2. 权威文件

每个阶段开始前必须完整阅读以下文件：

1. `docs/superpowers/execution/2026-07-11-mathematical-modeling-goal-loop.md`
2. `docs/superpowers/execution/2026-07-11-mathematical-modeling-goal-progress.md`
3. `docs/superpowers/specs/2026-07-10-mathematical-modeling-workflow-design.md`
4. `docs/superpowers/plans/2026-07-10-mathematical-modeling-roadmap.md`
5. 当前阶段对应的详细计划

阶段计划映射：

| 阶段 | 计划文件 |
| --- | --- |
| 1 | `docs/superpowers/plans/2026-07-10-mathematical-modeling-phase1-foundation.md` |
| 2 | `docs/superpowers/plans/2026-07-10-mathematical-modeling-phase2-intake-planning.md` |
| 3 | `docs/superpowers/plans/2026-07-10-mathematical-modeling-phase3-experiments.md` |
| 4 | `docs/superpowers/plans/2026-07-10-mathematical-modeling-phase4-paper.md` |
| 5 | `docs/superpowers/plans/2026-07-10-mathematical-modeling-phase5-delivery-git.md` |
| 6 | `docs/superpowers/plans/2026-07-10-mathematical-modeling-phase6-hardening.md` |

优先级如下：

```text
用户在当前 Goal 中的明确指令
  > 已批准的设计文档
  > 当前阶段详细计划
  > 路线图与本循环协议
  > 代码库既有惯例
```

若文件之间存在实质矛盾，不自行选择解释；记录矛盾并请求用户裁决。

## 3. Goal 功能准备

如果 `/goal` 未出现在斜杠命令列表，启用 Goal 功能：

```powershell
codex features enable goals
```

或者在 `config.toml` 中配置：

```toml
[features]
goals = true
```

官方控制命令：

```text
/goal                 查看当前 Goal
/goal pause           暂停
/goal resume          恢复
/goal clear           清除已经结束或不再需要的 Goal
```

不要在旧 Goal 尚未完成、暂停或清除时创建下一阶段 Goal。

## 4. 新会话启动前检查

### 4.1 工作区基线

运行：

```powershell
git status --short
git log -5 --oneline --decorate
```

检查规则：

1. 不覆盖、不重置、不暂存、不提交用户已有的无关改动。
2. 若未提交改动与当前阶段计划文件重叠，暂停实现并报告具体重叠文件。不得擅自 stash、reset 或丢弃。
3. 若当前阶段需要隔离执行，调用 `superpowers:using-git-worktrees`，基于用户确认的 commit 创建阶段工作树。
4. 不得假设当前 `HEAD` 包含脏工作区中的功能；若那些改动是阶段实现的必要基线，先由用户决定如何形成干净基线。
5. 在进度账本中记录 `baseline_commit`、`worktree_path` 和所有保留的脏文件。

当前仓库在本手册创建时存在多项未提交改动，而且其中包含阶段 1 可能修改的 `backend/main.py`、`backend/core/config.py`、`frontend/src/App.tsx`、`frontend/src/services/api.ts` 和 `frontend/src/store/useStore.ts`。因此首次 Goal 必须重新检查，不能直接假设可以安全开始阶段 1。

### 4.2 恢复已有进度

依次检查：

```powershell
Get-Content -Raw docs\superpowers\execution\2026-07-11-mathematical-modeling-goal-progress.md
git log --oneline --decorate --all -20
git status --short
```

然后：

1. 找到进度账本中的当前阶段和 Task。
2. 核对账本中的提交是否真实存在。
3. 对标记为 `verified` 的 Task 重新运行其最后一条聚焦验证命令。
4. 验证失败时，将 Task 恢复为 `in_progress`，不得跳过。
5. 从第一个没有可靠验证证据的 Task 继续。

## 5. 单阶段 Goal 契约

每个 Goal 必须满足以下约束：

### 5.1 唯一目标

只实现当前阶段计划，不提前实现下一阶段。可以完成当前阶段明确要求的兼容性修复，但必须记录原因和验证证据。

### 5.2 停止条件

仅在以下条件全部满足时宣告当前阶段完成：

1. 当前阶段所有 Task 已完成。
2. 每个 Task 的聚焦测试通过。
3. 阶段计划中的最终验证全部通过。
4. 路线图对应 Phase Gate 已满足。
5. 阶段相关改动已经按任务边界提交。
6. 进度账本记录了验证命令、结果和提交哈希。
7. 没有把用户已有无关改动纳入提交。

达到停止条件后结束 Goal，不自动进入下一阶段。

### 5.3 不得扩大的权限

Goal 的“持续执行”只表示持续推进当前目标，不扩大权限。以下操作仍需要明确授权：

- 删除、覆盖或移动用户文件；
- stash、reset、clean、rebase 或丢弃修改；
- 安装需要联网的新依赖；
- 修改远程仓库或 push；
- 使用新的外部服务、密钥或付费资源；
- 对计划之外的产品行为做重大选择。

## 6. Task 内循环

对当前阶段的每个 Task，严格执行下面的循环：

```text
读取 Task 全文
  → 检查依赖 Task 和现有实现
  → 写失败测试
  → 运行测试，确认因目标能力缺失而失败
  → 写最小实现
  → 运行聚焦测试
  → 运行相关回归测试
  → 检查 diff 和安全边界
  → 提交当前 Task
  → 更新进度账本
  → 选择下一个未验证 Task
```

### 6.1 每个 Task 开始时

1. 将账本中的 `current_task` 更新为 Task 编号和名称。
2. 将状态设为 `in_progress`。
3. 记录预计修改文件，和 `git status --short` 对比。
4. 若计划文件路径已因代码演进变化，先找到现有等价边界；不得静默创造第二套实现。
5. 使用计划指定的接口名，除非现有代码已存在更权威接口；发生变化时在账本记录映射。

### 6.2 测试驱动

实现功能或修复缺陷时调用 `superpowers:test-driven-development`：

1. 先写能够表达行为的失败测试。
2. 运行并确认失败原因正确。
3. 实现满足该测试的最小代码。
4. 运行聚焦测试和相关回归测试。
5. 不因测试难写而删除或弱化验收标准。

若遇到意外失败，先调用 `superpowers:systematic-debugging`，找出根因后再修改。不得用反复试错代替诊断。

### 6.3 提交边界

每个 Task 原则上对应一个可独立审查的提交。提交前：

```powershell
git status --short
git diff --check
git diff --stat
```

只 `git add` 当前 Task 明确修改的文件。禁止 `git add .` 和 `git add -A`。

提交后记录：

- commit hash；
- 聚焦验证命令及结果；
- 相关回归命令及结果；
- 未解决的警告；
- 下一 Task。

### 6.4 进度报告

每个 Task 提交后给出短报告：

```text
阶段：
完成 Task：
提交：
已验证：
剩余 Task：
阻塞：无 / 具体阻塞
```

不要只报告“正在处理”或“基本完成”。

## 7. 失败、暂停与恢复

### 7.1 可以自动处理

- 明确的代码错误；
- 测试暴露的局部回归；
- 格式、类型和静态检查问题；
- 计划内且不改变产品决策的小范围兼容修复。

### 7.2 必须暂停

- 当前工作区存在与本阶段重叠的未知改动；
- 需要新的用户选择或权限；
- 需要破坏性 Git/文件操作；
- 计划、设计与现有实现发生实质冲突；
- 无法安全确定应保留哪个行为；
- 外部服务、依赖源或工具不可用，且没有等价本地路径；
- 阶段目标只能通过明显扩大范围才能完成。

暂停时：

1. 保留可复现现场。
2. 更新进度账本的 `blockers`。
3. 写出已尝试方法和证据。
4. 指明用户需要做出的单一决定。
5. 使用 `/goal pause`，等待用户处理后 `/goal resume`。

不要把“需要用户输入”伪装成阶段完成。

### 7.3 连续失败

同一失败连续出现时：

1. 第一次：保存完整错误并定位失败层。
2. 第二次：验证先前根因假设，换用证据驱动的诊断。
3. 第三次：停止重复尝试，记录最小复现、环境、已排除原因和下一决策点。

## 8. 阶段 Gate 循环

所有 Task 完成后：

1. 调用 `superpowers:verification-before-completion`。
2. 逐条执行当前阶段计划最后一个 Checkpoint Task。
3. 执行路线图中的对应 Gate。
4. 运行完整后端测试、完整前端测试和生产构建，除非当前阶段计划明确缩小范围。
5. 调用 `superpowers:requesting-code-review` 做阶段级审查。
6. 修复审查发现后重新运行受影响验证和阶段 Gate。
7. 更新进度账本，将阶段标为 `completed`。
8. 输出阶段总结并停止 Goal。

通用验证命令：

```powershell
python -m pytest backend/tests -q
Set-Location frontend
npm test -- --run
npm run build
```

只有新鲜命令输出能够支持“通过”声明。不得用以前的结果、局部测试或主观判断替代。

## 9. 跨会话进度账本

可变状态保存在：

`docs/superpowers/execution/2026-07-11-mathematical-modeling-goal-progress.md`

更新规则：

1. 每个 Task 开始、提交、阻塞和阶段完成时更新。
2. 只记录事实，不复制大段日志。
3. 命令结果写通过数量、失败数量或退出码。
4. 提交哈希必须能由 `git show` 验证。
5. 新会话不得仅相信账本；必须复核 Git 和关键验证。
6. 账本随当前 Task 提交，或者用独立 `docs: update modeling goal progress` 提交。

## 10. 新会话通用启动提示词

在新会话中先打开仓库，然后粘贴以下提示词；将其中的阶段专用段落替换为第 11 节对应内容：

```text
/goal 完成数学建模工作流的当前单一阶段，不停止，直到该阶段详细计划中的全部 Task、最终 Checkpoint 和路线图 Phase Gate 均以新鲜验证证据通过，并且每个 Task 已按边界提交。禁止进入下一阶段。

开始前完整阅读：
1. docs/superpowers/execution/2026-07-11-mathematical-modeling-goal-loop.md
2. docs/superpowers/execution/2026-07-11-mathematical-modeling-goal-progress.md
3. docs/superpowers/specs/2026-07-10-mathematical-modeling-workflow-design.md
4. docs/superpowers/plans/2026-07-10-mathematical-modeling-roadmap.md
5. 当前阶段详细计划文件

先执行基线检查：git status --short、git log -5 --oneline --decorate，并核对进度账本。当前仓库可能存在与计划文件重叠的未提交修改；不得覆盖、stash、reset、clean 或提交用户已有改动。若重叠修改无法安全隔离，立即暂停并报告具体文件。

执行当前阶段时使用 superpowers:executing-plans；每个功能或修复使用 superpowers:test-driven-development；遇到意外失败先使用 superpowers:systematic-debugging；宣告 Task 或阶段完成前使用 superpowers:verification-before-completion；阶段 Gate 后使用 superpowers:requesting-code-review。

严格按 Task 顺序循环：失败测试 → 确认正确失败 → 最小实现 → 聚焦测试 → 相关回归 → 检查 diff → 仅暂存 Task 文件 → 提交 → 更新进度账本。不要重复已经由 Git 和新鲜验证确认完成的 Task。

每个 Task 后报告阶段、Task、提交、验证、剩余和阻塞。需要用户权限、重大选择、破坏性操作或范围扩张时暂停。阶段完成后停止 Goal，不自动进入下一阶段。
```

## 11. 阶段专用 Goal 提示词

以下提示词已经包含具体目标和停止条件，可以直接复制到全新会话。

### 11.1 阶段 1：项目基础

```text
/goal 实现 docs/superpowers/plans/2026-07-10-mathematical-modeling-phase1-foundation.md 中的阶段 1。按 Task 1 到 Task 6 顺序循环执行，直到建模状态机、SQLite 工作流元数据、独立仓库外工作区、项目服务与 API、前端建模入口全部实现；全部阶段 1 聚焦测试、完整后端测试、完整前端测试和生产构建通过；创建项目、推进一次、重启后仍处于 problem_parsing；路线图 Gate 1 满足。每个 Task 独立提交并更新 Goal 进度账本。禁止开始阶段 2。

必须先完整阅读 Goal 循环手册、Goal 进度账本、总体设计、路线图和阶段 1 计划。先检查脏工作区；当前已有改动可能与 backend/main.py、backend/core/config.py、frontend/src/App.tsx、frontend/src/services/api.ts 和 frontend/src/store/useStore.ts 重叠，无法安全隔离时暂停。执行时使用 executing-plans、test-driven-development、systematic-debugging、verification-before-completion 和 requesting-code-review。
```

### 11.2 阶段 2：赛题、数据与方案

```text
/goal 实现 docs/superpowers/plans/2026-07-10-mathematical-modeling-phase2-intake-planning.md 中的阶段 2。先验证阶段 1 Gate 和提交历史，再按 Task 1 到 Task 6 顺序循环执行，直到不可变赛题/CSV 导入、数据清单与 SHA-256、成果索引、审批记录、CSV 数据体检、结构化赛题解析、最多三个候选方案、模型审批 Gate 和对应前端完成；真实 UTF-8 题目与 CSV 能生成并登记 problem_spec.json、data_profile.json、data_report.md、model_plan.json 和 model_plan.md；修改已批准方案后推进返回冲突；路线图 Gate 2 满足。每个 Task 独立提交并更新 Goal 进度账本。禁止开始阶段 3。

必须先完整阅读 Goal 循环手册、Goal 进度账本、总体设计、路线图和阶段 2 计划。复核阶段 1 的关键测试，不重复已验证实现。执行时使用 executing-plans、test-driven-development、systematic-debugging、verification-before-completion 和 requesting-code-review。
```

### 11.3 阶段 3：实验执行

```text
/goal 实现 docs/superpowers/plans/2026-07-10-mathematical-modeling-phase3-experiments.md 中的阶段 3。先验证阶段 2 Gate，再按 Task 1 到 Task 6 顺序循环执行，直到实验契约、编程 Agent、项目虚拟环境、依赖安装命令、内容哈希执行票据、受限 Python 运行器、PID/超时/输出限制/密钥清除/默认断网、不可变实验、指标、图表、环境快照和实验 UI 完成；批准的基线与候选模型均可运行，固定随机种子复现指标，命令变化使审批失效；路线图 Gate 3 满足。每个 Task 独立提交并更新 Goal 进度账本。禁止开始阶段 4。

必须先完整阅读 Goal 循环手册、Goal 进度账本、总体设计、路线图和阶段 3 计划。安装或联网前遵循权限规则；未经批准不执行依赖下载。执行时使用 executing-plans、test-driven-development、systematic-debugging、verification-before-completion 和 requesting-code-review。
```

### 11.4 阶段 4：论文与审稿

```text
/goal 实现 docs/superpowers/plans/2026-07-10-mathematical-modeling-phase4-paper.md 中的阶段 4。先验证阶段 3 Gate，再按 Task 1 到 Task 6 顺序循环执行，直到论文契约、成果占位符解析、paper_claims、Markdown/LaTeX 论文 Agent、独立审稿 Agent、阻塞问题 Gate、最终论文内容哈希审批、禁用 shell escape 的 XeLaTeX 编译和论文工作台完成；所有实验数字和图表均能追溯到已完成实验；修改论文后旧审稿和审批失效；paper.pdf 成功生成；路线图 Gate 4 满足。每个 Task 独立提交并更新 Goal 进度账本。禁止开始阶段 5。

必须先完整阅读 Goal 循环手册、Goal 进度账本、总体设计、路线图和阶段 4 计划。若 XeLaTeX 不可用，先报告工具状态；不得伪造编译成功。执行时使用 executing-plans、test-driven-development、systematic-debugging、verification-before-completion 和 requesting-code-review。
```

### 11.5 阶段 5：交付与 Git

```text
/goal 实现 docs/superpowers/plans/2026-07-10-mathematical-modeling-phase5-delivery-git.md 中的阶段 5。先验证阶段 4 Gate，再按 Task 1 到 Task 6 顺序循环执行，直到复现检查、交付清单、代码归档、受限数据排除说明、Outputs 链接、Git 路径/密钥/大文件/符号链接扫描、可审查 diff、明确文件列表 add、内容哈希 commit 审批和提交 UI 完成；变更文件或提交信息后旧审批失效；独立建模项目仓库产生一个批准的 commit，且没有远程和 push；路线图 Gate 5 满足。每个 Task 独立提交并更新 Goal 进度账本。禁止开始阶段 6。

必须先完整阅读 Goal 循环手册、Goal 进度账本、总体设计、路线图和阶段 5 计划。禁止 git add .、git add -A、push、reset、clean、rebase、远程修改和任何未批准路径。执行时使用 executing-plans、test-driven-development、systematic-debugging、verification-before-completion 和 requesting-code-review。
```

### 11.6 阶段 6：恢复与端到端加固

```text
/goal 实现 docs/superpowers/plans/2026-07-10-mathematical-modeling-phase6-hardening.md 中的阶段 6。先验证阶段 5 Gate，再按 Task 1 到 Task 7 顺序循环执行，直到中断恢复、运行中 PID 安全终止、恢复历史、运行时能力诊断、路径/网络/资源/Git 对抗测试、固定 24 行赛题、确定性 Fake LLM、完整后端 E2E、前端 Gate 集成测试和用户文档完成；中断实验并重启后可从安全状态恢复；固定赛题能够从导入完成到可追溯 PDF 和批准的 Git commit；完整后端测试、完整前端测试和生产构建通过；路线图 Gate 6 满足。每个 Task 独立提交并更新 Goal 进度账本。阶段完成后停止 Goal，并报告整个六阶段项目状态。

必须先完整阅读 Goal 循环手册、Goal 进度账本、总体设计、路线图和阶段 6 计划。XeLaTeX 不存在时只允许计划中明确说明的单项 skip，其余论文和审批断言仍须执行。执行时使用 executing-plans、test-driven-development、systematic-debugging、verification-before-completion 和 requesting-code-review。
```

## 12. 阶段结束报告模板

```text
阶段：Phase N
状态：completed / blocked
完成 Task：
关键提交：
聚焦测试：
完整后端测试：
完整前端测试：
生产构建：
Phase Gate 证据：
保留的用户改动：
未解决警告：
下一步：停止当前 Goal，等待用户检查后在新会话启动 Phase N+1
```

阶段 6 的“下一步”改为：项目六阶段计划已经完成，等待最终验收或新的明确目标。

## 13. 用户操作速查

开始阶段：复制第 11 节对应提示词。

查看状态：

```text
/goal
```

临时暂停：

```text
/goal pause
```

继续：

```text
/goal resume
```

阶段完成并确认总结后：

```text
/goal clear
```

然后新建会话，复制下一阶段提示词。
