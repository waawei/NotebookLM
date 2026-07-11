# 数学建模 Goal 跨会话进度账本

更新时间：2026-07-11

## 当前状态

```yaml
workflow: mathematical-modeling
current_phase: 5
phase_status: completed
current_task: "Task 6: Phase 5 Independent-Repository Checkpoint"
task_status: verified
baseline_commit: 1a6a55a7c95cfd26a6568dbfda66d19f3a688c49
worktree_path: "D:/develop/python/NotebookLM-mathematical-modeling-phase5"
last_verified_commit: 9de6eb81b634b1701413f42af010787690500c3d
last_verification: "Gate 5 passed: backend 238 passed/3 skipped/13 subtests; frontend 30 files/127 tests; production build passed; independent repository checkpoint passed"
next_action: "Stop after Phase 5 and wait for user review; do not start Phase 6"
```

## 启动前风险

- 本账本创建时，主工作区存在大量未提交改动。
- 未提交改动包含阶段 1 计划可能修改的后端配置、路由和前端模块文件。
- Phase 1 Goal 必须先重新运行 `git status --short` 并确认安全基线。
- 未经用户明确同意，不得 stash、reset、clean、覆盖或提交这些已有改动。

## 阶段总览

| 阶段 | 状态 | 计划 | Gate | 完成提交 |
| --- | --- | --- | --- | --- |
| 1 | completed | `2026-07-10-mathematical-modeling-phase1-foundation.md` | passed | Task 6 ledger commit |
| 2 | completed | `2026-07-10-mathematical-modeling-phase2-intake-planning.md` | passed | `09000b4` + completion ledger commit |
| 3 | completed | `2026-07-10-mathematical-modeling-phase3-experiments.md` | passed | `0a6e542` + `c72749f` + completion ledger commit |
| 4 | completed | `2026-07-10-mathematical-modeling-phase4-paper.md` | passed | Task 1 `34fea97` + `ee6ed66`; Task 2 `313e66c` + `b0c167b`; Task 3 `9d2e4cd` + `fc0205e`; Task 4 `4648b01` + `f38bbd2`; Task 5 `a645dda`; Task 6 `54f3fc8` + `8363a3e` |
| 5 | completed | `2026-07-10-mathematical-modeling-phase5-delivery-git.md` | passed | Task 1 `eab060d`; Task 2 `155d8e5` + `6e311ce`; Task 3 `d7099da`; Task 4 `b3906df`; Task 5 `cd59950`; Task 6 `64cb92d`; review fixes `9de6eb8` |
| 6 | not_started | `2026-07-10-mathematical-modeling-phase6-hardening.md` | pending | — |

## 当前阶段 Task 记录

### Phase 5 / Task 1: Reproducibility and Delivery Contracts

- 状态：verified
- 实际文件：`backend/services/delivery_contracts.py`, `backend/services/reproducibility_service.py`, `backend/tests/test_reproducibility_service.py`
- 失败测试：`DEBUG=false; PYTHONPATH=backend; python -m pytest backend/tests/test_reproducibility_service.py -q`，退出码 2；按预期缺少 `services.reproducibility_service`
- 聚焦验证：同一命令退出码 0，3 passed
- 相关回归：阶段 4 `test_phase4_traceability_checkpoint.py`、`test_latex_service.py`、`test_paper_gates.py` 退出码 0，9 passed
- 提交：`eab060d703eb7ac81ea3dcc77ebc7e6cebdb831c`
- 保留的用户改动：无；Phase 5 工作树从 `1a6a55a` 创建时干净
- 备注：检查 PDF、论文源、依赖锁定、复现命令、源代码、至少两个完成实验、实验四类证据、登记 artifact 哈希和 paper claim target；错误信息不包含文件内容或密钥。

### Phase 5 / Task 2: Delivery Manifest, Code Archive, and Output Link

- 状态：verified
- 实际文件：`backend/services/delivery_service.py`, `backend/services/output_service.py`, `backend/tests/test_delivery_service.py`, `backend/tests/test_modeling_output_link.py`
- 失败测试：`DEBUG=false; PYTHONPATH=backend; python -m pytest backend/tests/test_delivery_service.py backend/tests/test_modeling_output_link.py -q`，退出码 2；按预期缺少 `services.delivery_service`
- 聚焦验证：同一命令退出码 0，2 passed（既有 Pydantic 弃用警告）
- 提交：`155d8e5a034e2fcade694f10400e218daf891653`
- 保留的用户改动：无
- 备注：code.zip 只归档源代码、测试、论文和明确的复现/依赖文件；`data/raw` 默认排除。manifest 保留每项受限原始数据的路径、哈希、大小和 `restricted_raw_data` 原因。Outputs 使用项目与 manifest artifact 链接，不复制 PDF。

### Phase 5 / Task 3: Git Policy Scan and Reviewable Diff

- 状态：verified
- 实际文件：`backend/services/git_policy_service.py`, `backend/tests/test_git_policy_service.py`
- 失败测试：`DEBUG=false; PYTHONPATH=backend; python -m pytest backend/tests/test_git_policy_service.py -q`，退出码 2；按预期缺少 Git policy service
- 聚焦验证：同一命令退出码 0，2 passed、1 skipped（Windows host 不允许创建 symlink）
- 提交：`d7099da882222587d30143cca658a0e98e13500d`
- 保留的用户改动：无
- 备注：只接受显式项目相对路径，拒绝 secret、`.env`、虚拟环境、缓存、build 临时目录、超过 20 MiB 文件和外部 symlink；untracked text 使用统一 diff，二进制仅显示名称与 SHA-256，总输出最多 2 MiB。

### Phase 5 / Task 4: Approval-Gated Explicit Git Commit

- 状态：verified
- 实际文件：`backend/services/git_commit_service.py`, `backend/services/modeling_store.py`, `backend/services/modeling_gate_service.py`, `backend/tests/test_git_commit_service.py`, `backend/tests/test_commit_gate.py`
- 失败测试：commit service 初始聚焦测试退出码 2；Gate tests 初始 2 failed，因 packaging/committing 未执行交付与提交检查
- 聚焦验证：`DEBUG=false; PYTHONPATH=backend; python -m pytest backend/tests/test_git_commit_service.py backend/tests/test_commit_gate.py -q`，退出码 0，5 passed
- 提交：`b3906df0e34bd726cf3719c3e95be20807b28c70`
- 保留的用户改动：无
- 备注：审批 payload 绑定排序路径、每文件 hash、diff hash、manifest hash 和 subject；提交仅以参数数组调用 `git add --`、`git commit -m` 与 `git rev-parse HEAD`，从不调用 remote。提交前重建 payload，因此修改路径、内容或信息会失效。

### Phase 5 / Task 5: Delivery and Git API/UI

- 状态：verified
- 实际文件：`backend/api/modeling.py`, `backend/tests/test_delivery_git_api.py`, `frontend/src/services/api.ts`, `frontend/src/components/DeliveryChecklist.tsx`, `frontend/src/components/GitCommitApprovalCard.tsx`, `frontend/src/views/ModelingProjectsView.tsx` 及对应测试
- 失败测试：API 初始 2 failed，缺少 delivery/git 路由与 commit service
- 聚焦验证：后端 `test_delivery_git_api.py test_delivery_service.py test_git_policy_service.py test_git_commit_service.py` 退出码 0，10 passed、2 skipped；前端 API/组件 3 files、11 tests passed，生产 build 退出码 0（保留既有 chunk-size warning）
- 提交：`cd59950531beafc19c0aebc8ecb0d93e1eb689d8`
- 保留的用户改动：运行时 `data/` 目录未跟踪且未暂存
- 备注：API 公开 check/build/list/review/request-commit/commit 与 porcelain status；UI 只从 status 选择、复核明确路径，展示 capped diff，并在审批 payload current 时允许审批和提交。

### Phase 5 / Task 6: Independent-Repository Checkpoint

- 状态：verified
- 实际文件：`backend/tests/test_phase5_delivery_checkpoint.py`, `backend/services/git_commit_service.py`
- 失败测试：第一次 checkpoint 失败，因 `git diff --cached --quiet` 的预期退出码 1 被通用 `check=True` 视为 subprocess 错误。
- 聚焦验证：`DEBUG=false; PYTHONPATH=backend; python -m pytest backend/tests/test_git_commit_service.py backend/tests/test_phase5_delivery_checkpoint.py -q`，退出码 0，4 passed
- 提交：`64cb92db5f9e5aff0bf44137b43a44e5efa5e54f`
- 保留的用户改动：运行时 `data/` 目录未跟踪且未暂存
- 备注：fixture 交付 manifest/code archive/论文源/依赖/复现命令/实验记录/受限数据条目齐全；secret 与超过 20 MiB 文件被 policy 拒绝；文件篡改使旧审批拒绝且不会提交；重新批准后产生一条批准信息的本地 commit，`git remote` 为空。

### Phase 5 Gate Compatibility Fix

- 状态：verified
- 根因：旧 `ModelingProjectsView` mock 未包含新 `checkDeliverables`，在 packaging 状态渲染时使组件崩溃。
- 红灯：完整前端 suite 1 failed、1 unhandled error；具体为 `modelingApi.checkDeliverables is not a function`。
- 绿灯：`ModelingProjectsView.test.tsx` 29 passed；完整前端 30 files、127 tests passed；`npm run build` 退出码 0。
- 提交：`2b5459147b94d72a8a4ed4d71a563fe18fd6b76c`

### Phase 5 Review Integrity Fixes

- 状态：verified
- 独立审查 P1：预暂存 index 内容可能混入批准提交；审批未校验实际 staged blob；delivery manifest 变更可绕过历史 artifact 校验。
- 修复：request/commit 均拒绝非空 index，`git add --` 后严格比对 cached paths 与 Git blob object IDs；可复现检查验证每个 artifact 路径的最新版本（包括 delivery manifest/archive）。
- 独立审查 P2：Delivery UI 未列出 manifest 文件与受限数据排除原因；Git UI 未显示 policy issues 或审批/当前 payload mismatch。
- 修复：DeliveryChecklist 读取 manifest artifact 并列出路径/hash/Git inclusion/exclusion；commit card 显示 issue/mismatch，选中路径必须刷新 review 才可申请审批。
- 验证：后端 `test_reproducibility_service.py test_delivery_service.py test_git_policy_service.py test_git_commit_service.py test_commit_gate.py test_delivery_git_api.py test_phase5_delivery_checkpoint.py` 退出码 0，18 passed、2 skipped；前端完整 30 files、127 tests；生产 build 退出码 0。
- 提交：`9de6eb81b634b1701413f42af010787690500c3d`

### Phase 5 Full Backend Gate Blocker

- 状态：blocked_pending_environment_diagnosis
- 现象：`DEBUG=false; python -m pytest tests -q` 从 `backend/` 执行时，runner 在约 25 秒后失去会话输出并留下 pytest 子进程；排除 `test_phase3_reproducibility_checkpoint.py` 后仍复现。
- 已排除：单独 `test_phase3_reproducibility_checkpoint.py` 退出码 0，1 passed；阶段 5 全部聚焦 backend 回归退出码 0，18 passed、2 skipped；阶段 4 Gate 聚焦回归 9 passed。
- 处理：已在每次诊断后终止仅由本次 pytest 启动的遗留 Python 子进程；未改动或删除仓库文件。必须在后续 Goal 回合继续诊断，当前不得将 Gate 5 或 Phase 5 标记为完成。

### Phase 5 Gate 5 Completion

- 状态：verified
- 完整后端：使用隐藏受控进程完成 `DEBUG=false; python -m pytest tests -q`，退出码 0，238 passed、3 skipped、13 subtests passed，耗时 123.88s；先前交互通道只是在长时间 venv/ensurepip fixture 执行时丢失输出，并非测试失败。
- 完整前端：`npm test -- --run` 退出码 0，30 files、127 tests passed；保留既有 `act(...)` 警告。
- 生产构建：`npm run build` 退出码 0；保留既有 Vite chunk-size warning。
- Git 审计：`git diff --check 1a6a55a..HEAD` 通过；无 tracked symlink；未执行 push 或 remote 修改。工作树仅保留测试生成、未跟踪且未暂存的 `data/`。
- 独立审查：P1 index/manifest/hash binding 与 P2 delivery/approval UI findings 均以 `9de6eb8` 修复并由 backend 18 passed、2 skipped及完整 Gate 复核。
- Gate 5：passed。Phase 6 维持 `not_started`。

### Phase 5 / Task 2 Review Fixes

- 状态：verified
- 独立审查发现：真实 `data_manifest.json` 的 `{files: [...]}` envelope 未解析、manifest 缺少 data manifest/实验四类证据、归档跟随外部 symlink 或敏感路径、重复构建使历史 delivery artifact hash 误报。
- 红灯：`test_delivery_service.py` 2 failed，重现缺失 raw-data entry 与审计证据。
- 绿灯：`test_delivery_service.py test_modeling_output_link.py test_reproducibility_service.py` 退出码 0，7 passed、1 skipped（symlink host 限制）。
- 提交：`6e311ce7ff67dcd216567e5b0720dfd49993e2cc`

### Phase 4 / Task 1: Paper Contracts, Claims, and Placeholder Resolution

- 状态：verified
- 预计文件：`backend/services/paper_contracts.py`, `backend/services/paper_claim_service.py`, `backend/services/paper_placeholder_service.py`, `backend/services/modeling_store.py`, `backend/tests/test_paper_placeholder_service.py`, `backend/tests/test_paper_claim_service.py`
- 实际文件：与预计文件一致
- 失败测试：`DEBUG=false; python -m pytest tests/test_paper_placeholder_service.py tests/test_paper_claim_service.py -q`，退出码 2；按预期缺少 paper services
- 聚焦验证：同一命令退出码 0，3 passed
- 相关回归：`DEBUG=false; python -m pytest tests/test_paper_placeholder_service.py tests/test_paper_claim_service.py tests/test_modeling_store.py tests/test_artifact_service.py tests/test_experiment_store.py -q`，退出码 0，12 passed
- 提交：实现 `34fea97`；独立审查修复 `ee6ed66`
- 保留的用户改动：无；Phase 4 工作树从 `aecdd1b` 创建时干净
- 备注：指标、图和表占位符均要求同项目已完成实验及已登记 artifact；解析前复核 metrics 文件 SHA-256，且 claim 集合在一个 SQLite 事务中替换。独立审查无遗留 P1/P2。

### Phase 4 / Task 2: Paper Writer Agent and Versioned Drafts

- 状态：verified
- 预计文件：`backend/services/paper_agent_service.py`, `backend/skills/modeling_paper_writer/skill.json`, `backend/tests/test_paper_agent_service.py`
- 实际文件：预计文件及 `backend/tests/test_skill_service.py`
- 失败测试：`DEBUG=false; python -m pytest tests/test_paper_agent_service.py -q`，退出码 2；按预期缺少 writer service
- 聚焦验证：`DEBUG=false; python -m pytest tests/test_paper_agent_service.py tests/test_skill_service.py -q`，退出码 0，5 passed
- 相关回归：`DEBUG=false; python -m pytest tests/test_paper_agent_service.py tests/test_paper_placeholder_service.py tests/test_paper_claim_service.py tests/test_skill_service.py -q`，退出码 0，10 passed
- 提交：`313e66c`
- 保留的用户改动：无
- 备注：编辑态 Markdown/LaTeX 保留 placeholder；带结果名的字面指标数值会被拒绝。

### Phase 4 / Task 3: Independent Review and Paper Gates

- 状态：verified
- 实际文件：`backend/services/review_agent_service.py`, `backend/services/modeling_gate_service.py`, `backend/services/modeling_store.py`, `backend/skills/modeling_reviewer/skill.json`, 及聚焦测试
- 聚焦验证：`DEBUG=false; python -m pytest tests/test_review_agent_service.py tests/test_paper_gates.py tests/test_paper_agent_service.py tests/test_paper_placeholder_service.py tests/test_paper_claim_service.py tests/test_skill_service.py -q`，退出码 0，19 passed
- 提交：实现 `9d2e4cd`；当前 claim/hash 审查修复 `fc0205e`
- 备注：审稿对完成实验、artifact SHA 和 paper_claims 逐项复核；编辑源修改后 review hash 不再匹配，最终 Gate 拒绝。

### Phase 4 / Task 4: Final Approval and Restricted XeLaTeX Compilation

- 状态：verified
- 实际文件：`backend/services/latex_service.py`, `backend/tests/test_latex_service.py`
- 聚焦验证：`DEBUG=false; python -m pytest tests/test_latex_service.py tests/test_phase4_traceability_checkpoint.py -q`，退出码 0，5 passed
- 提交：实现 `4648b01`；bibliography 审批绑定修复 `f38bbd2`
- 备注：构建树位于 `.workflow/build/paper`，XeLaTeX 两遍执行且固定 `-no-shell-escape -interaction=nonstopmode -halt-on-error`。审批 payload 包含 Markdown、LaTeX、可选 bibliography、claims 和通过 review hash。

### Phase 4 / Task 5: Paper API and Workbench

- 状态：verified
- 实际文件：`backend/api/modeling.py`, `backend/tests/test_paper_api.py`, `frontend/src/services/api.ts`, `frontend/src/components/PaperWorkspace.tsx`, `frontend/src/components/ReviewIssuesPanel.tsx`, `frontend/src/components/FinalPaperApprovalCard.tsx`, `frontend/src/views/ModelingProjectsView.tsx` 及对应测试
- 聚焦验证：后端 API 2 passed；前端 4 files / 12 tests passed，生产构建通过
- 提交：`a645dda`
- 备注：保存 Markdown 注册新 artifact 版本；后续 render/review/approval/compile 依据当前哈希自然使旧结果失效；PDF endpoint 仅从项目工作区 deliverables 路径响应。

### Phase 4 / Task 6: Phase 4 Traceability Checkpoint

- 状态：verified
- 实际文件：`backend/tests/test_phase4_traceability_checkpoint.py`
- 聚焦验证：`DEBUG=false; python -m pytest tests/test_review_agent_service.py tests/test_phase4_traceability_checkpoint.py tests/test_latex_service.py tests/test_paper_gates.py -q`，退出码 0，13 passed；完整后端 `DEBUG=false; python -m pytest tests -q`，退出码 0，219 passed、1 skipped、13 subtests
- 相关回归：前端 `npm test -- --run`，退出码 0，28 files/125 tests；`npm run build`，退出码 0（保留既有 Vite chunk-size warning）
- 提交：`54f3fc8`；Gate/审批绑定修复 `f38bbd2`、`bad2dde`、`e8e2bdb`、`8363a3e`
- 备注：真实 checkpoint 创建完成实验指标与图表、解析两个 claim、通过审稿、批准包含 Markdown/LaTeX/bibliography/claims/review hash 的精确 payload、两次 `-no-shell-escape` XeLaTeX 编译并检查 PDF；删除引用图表生成 blocking review，篡改 Markdown 或 bibliography 后旧 review/approval 失效。

### Phase 3 / Task 1: Experiment Contracts and Records

- 状态：verified
- 预计文件：`backend/services/experiment_contracts.py`, `backend/services/modeling_store.py`, `backend/tests/test_experiment_contracts.py`, `backend/tests/test_experiment_store.py`
- 实际文件：`backend/services/experiment_contracts.py`, `backend/services/modeling_store.py`, `backend/tests/test_experiment_contracts.py`, `backend/tests/test_experiment_store.py`
- 失败测试：`DEBUG=false; PYTHONPATH=backend; python -m pytest backend/tests/test_experiment_contracts.py backend/tests/test_experiment_store.py -q`，退出码 2；按预期因缺少 `services.experiment_contracts` 收集失败
- 聚焦验证：同一命令退出码 0，3 passed
- 相关回归：`DEBUG=false; PYTHONPATH=backend; python -m pytest backend/tests/test_experiment_contracts.py backend/tests/test_experiment_store.py backend/tests/test_modeling_store.py backend/tests/test_artifact_service.py backend/tests/test_approval_service.py -q`，退出码 0，11 passed
- 提交：实现 `5b5d6db`；审查修复 `5f69d1c`
- 保留的用户改动：无；Phase 3 工作树从 `6f534eb` 创建时干净
- 备注：Gate 2 以 Phase 2 完成工作树的新鲜检查点、后端、前端和构建证据复核；未开始 Phase 4。独立审查发现状态更新会清除未提供的运行字段，且存储层能绕过实验契约；新增先红后绿回归，状态更新仅修改明确字段，存储层验证实验 ID、配置与执行票据哈希。

### Phase 3 / Task 2: Code Generation Contract and Project Template

- 状态：verified
- 预计文件：`backend/requirements.txt`, `backend/services/modeling_code_agent_service.py`, `backend/skills/modeling_programmer/skill.json`, `backend/tests/test_modeling_code_agent_service.py`, `backend/tests/test_skill_service.py`
- 实际文件：`backend/requirements.txt`, `backend/services/modeling_code_agent_service.py`, `backend/skills/modeling_programmer/skill.json`, `backend/tests/test_modeling_code_agent_service.py`, `backend/tests/test_skill_service.py`
- 失败测试：`DEBUG=false; PYTHONPATH=backend; python -m pytest backend/tests/test_modeling_code_agent_service.py -q`，退出码 2；按预期因缺少 `services.modeling_code_agent_service` 收集失败
- 聚焦验证：`DEBUG=false; PYTHONPATH=backend; python -m pytest backend/tests/test_modeling_code_agent_service.py backend/tests/test_skill_service.py -q`，退出码 0，5 passed
- 相关回归：含建模角色、生命周期、成果、审批与实验契约的命令退出码 0，30 passed
- 提交：实现 `027f289`；审查修复 `7bc5289`
- 保留的用户改动：无
- 备注：依赖均以精确版本写入 `requirements.txt`；根据权限规则，未运行 `pip install` 或联网下载。代码 Agent 只接收模型审批当前哈希、限定源路径和相对参数数组，生成确定性配置、复现文件、源哈希和未批准执行票据。独立审查新增输入内容复核、配置纳入源哈希和完整 pipeline 输出要求；相应红绿回归已通过。

### Phase 3 / Task 3: Execution Policy and Approval Ticket

- 状态：verified
- 预计文件：`backend/services/execution_policy.py`, `backend/services/project_environment_service.py`, `backend/tests/test_execution_policy.py`, `backend/tests/test_project_environment_service.py`
- 实际文件：`backend/services/execution_policy.py`, `backend/services/project_environment_service.py`, `backend/tests/test_execution_policy.py`, `backend/tests/test_project_environment_service.py`
- 失败测试：`DEBUG=false; PYTHONPATH=backend; python -m pytest backend/tests/test_execution_policy.py backend/tests/test_project_environment_service.py -q`，退出码 2；按预期因缺少策略和环境服务收集失败
- 聚焦验证：同一命令退出码 0，4 passed
- 相关回归：含审批、实验契约、存储与代码 Agent 的命令退出码 0，15 passed
- 提交：实现 `8613d87`；审查修复 `40dbbd8`；账本 `a9fe6f2`
- 保留的用户改动：无
- 备注：依赖安装批次必须显式标记 `network_allowed: true` 且经过批准；本 Task 不执行安装或联网。独立审查新增相对路径穿越和非规范 pip 调用回归；策略解析所有路径到工作区内，且只允许规范依赖安装命令。

### Phase 3 / Task 4: Restricted Runner and Immutable Experiment Output

- 状态：verified
- 预计文件：`backend/services/restricted_runner.py`, `backend/services/environment_capture.py`, `backend/services/experiment_service.py`, `backend/tests/test_restricted_runner.py`, `backend/tests/test_experiment_service.py`
- 实际文件：`backend/services/restricted_runner.py`, `backend/services/environment_capture.py`, `backend/services/experiment_service.py`, `backend/services/modeling_store.py`, `backend/tests/test_restricted_runner.py`, `backend/tests/test_experiment_service.py`
- 失败测试：`DEBUG=false; PYTHONPATH=backend; python -m pytest backend/tests/test_restricted_runner.py backend/tests/test_experiment_service.py -q`，退出码 2；按预期因缺少运行器与执行服务收集失败
- 聚焦验证：同一命令退出码 0，3 passed
- 相关回归：受限执行、策略、环境、实验契约、存储、成果和审批的组合命令退出码 0，20 passed
- 提交：实现 `ffc7cc6`；审查修复 `3f182bd`
- 保留的用户改动：无
- 备注：运行器必须清除密钥、默认断网、限制输出和超时并终止进程树；执行服务只写入新实验目录并登记有效指标、日志、环境和声明成果。审查修复将当前代码、配置和输入哈希绑定到票据并执行前复核；原子领取 prepared 实验；保留多命令日志和退出码；成果登记失败回滚索引；默认断网拒绝解释器绕过并禁用 Python 进程创建入口。应用层隔离不声称提供系统级网络沙箱。

### Phase 3 / Task 5: Experiment Gates, API, and UI

- 状态：verified
- 预计文件：`backend/services/modeling_gate_service.py`, `backend/api/modeling.py`, `backend/tests/test_experiment_api.py`, `frontend/src/services/api.ts`, `frontend/src/services/api.test.ts`, `frontend/src/components/ExperimentApprovalCard.tsx`, `frontend/src/components/ExperimentApprovalCard.test.tsx`, `frontend/src/components/ExperimentRunPanel.tsx`, `frontend/src/components/ExperimentRunPanel.test.tsx`, `frontend/src/views/ModelingProjectsView.tsx`
- 实际文件：`backend/services/modeling_gate_service.py`, `backend/api/modeling.py`, `backend/services/modeling_code_agent_service.py`, `backend/tests/test_experiment_api.py`, `frontend/src/services/api.ts`, `frontend/src/components/ExperimentApprovalCard.tsx`, `frontend/src/components/ExperimentApprovalCard.test.tsx`, `frontend/src/components/ExperimentRunPanel.tsx`, `frontend/src/components/ExperimentRunPanel.test.tsx`, `frontend/src/views/ModelingProjectsView.tsx`
- 失败测试：后端 `test_experiment_api.py` 初始退出码 1，缺少结果 Gate 和 execute 端点；审查回归退出码 1，发现 Python 路径票据不一致与两个 baseline Gate 绕过
- 聚焦验证：后端初始 4 passed；审查修复后后端 9 passed；前端 `api` 与两个组件 11 passed，生产构建通过
- 相关回归：Task 5 后端组合命令退出码 0，17 passed；保留 Pydantic/PyPDF2 deprecation warnings；前端构建保留既有 Vite chunk-size warning
- 提交：实现 `6d0ad6b`；审查修复 `7e2183c`、`8346057`
- 保留的用户改动：无
- 备注：结果 Gate 需要已完成基线和候选模型、有效验证指标与登记图表或表格；API 将陈旧审批映射为 HTTP 409。审查修复将生成命令规范到项目 `.venv` Python、要求非 baseline 候选且 Pydantic 验证指标，并使审批卡显示输入哈希/依赖差异、运行面板 1500ms 轮询及图表成果 ID。前端验证使用已有本地依赖的临时目录连接，未下载包。

### Phase 3 / Task 6: Reproducibility Checkpoint

- 状态：verified
- 预计文件：无源文件变更；如验证暴露缺陷则按 TDD 修复
- 实际文件：`backend/services/modeling_code_agent_service.py`, `backend/tests/test_phase3_reproducibility_checkpoint.py`
- 失败测试：首次检查点退出码 1，因 `config.json` 票据哈希使用紧凑 JSON 而落盘为缩进 JSON；执行前内容复核正确拒绝
- 聚焦验证：修复后 `DEBUG=false; PYTHONPATH=backend; python -m pytest backend/tests/test_phase3_reproducibility_checkpoint.py -q`，退出码 0，1 passed
- 相关回归：完整后端 `192 passed, 1 skipped, 13 subtests`；完整前端 `25 files, 122 tests`；生产构建成功，保留既有 Vite chunk-size warning
- 提交：检查点与配置哈希修复 `0a6e542`
- 保留的用户改动：未跟踪 `data/` 为 API 测试生成的运行时目录，绝不暂存或提交
- 备注：创建并批准了基线、候选和同配置固定种子重跑；验证指标差异不超过 `1e-9`、原实验目录字节不变、图表已登记，篡改命令/票据后执行因审批不匹配被拒绝。未开始 Phase 4。

### Phase 2 / Task 6: Phase 2 Real-Data Checkpoint

- 状态：verified
- 预计文件：`backend/tests/test_modeling_phase2_checkpoint.py`
- 实际文件：`backend/tests/test_modeling_phase2_checkpoint.py`
- 失败测试：不适用；Task 6 为真实纵向验证，无生产实现预期
- 聚焦验证：临时运行目录下 `DEBUG=false; PYTHONPATH=backend; python -m pytest backend/tests/test_modeling_phase2_checkpoint.py -q`，退出码 0，1 passed；保留既有 Pydantic/PyPDF2 deprecation warning
- 相关回归：最终完整 Gate 2 回归在隔离临时运行目录通过：后端 170 passed、1 skipped、13 subtests passed；前端 23 files、120 passed；生产构建和 `git diff --check` 通过；工作树在收尾文档修改前干净。本机 pandas 2.3.2 与 requirements 固定的 2.2.2 API 兼容；未联网安装依赖。
- 提交：检查点 `79d7d35d8e184efdcf5dde6debbeaf44edc6fb0c`；审查强化 `7fd4fa881c04d8285044546b4f3884949bf48771`
- 保留的用户改动：无；Task 6 开始时工作树干净
- 备注：使用真实 UTF-8 题目和 CSV 字节、实际 SQLite/外部 Git 工作区及确定性 Fake LLM；验证题目/CSV 原始字节与只读位、双 manifest SHA-256、缺失值/重复行、数值 target/分类 category、2 个候选、五个命名成果逐一对应 registry relative_path 与当前 SHA、hash-bound approval、篡改后 API 409 和恢复后 Gate 2。初审要求强化 schema 和 registry 关联，已补充；应用仓库 clean checkpoint 在账本提交后以外部 `git status --short` 新鲜验证。最终状态仅推进至 Phase 2 出口 `experiment_implementation`，未实现或运行 Phase 3。

### Phase 2 / Task 5: Phase 2 API and Approval UI

- 状态：verified
- 预计文件：`backend/api/modeling.py`, `backend/tests/test_modeling_intake_api.py`, `frontend/src/services/api.ts`, `frontend/src/services/api.test.ts`, `frontend/src/components/ModelingInputPanel.tsx`, `frontend/src/components/ModelingInputPanel.test.tsx`, `frontend/src/components/ModelPlanApprovalCard.tsx`, `frontend/src/components/ModelPlanApprovalCard.test.tsx`, `frontend/src/views/ModelingProjectsView.tsx`, `frontend/src/views/ModelingProjectsView.test.tsx`
- 实际文件：`backend/api/modeling.py`, `backend/services/approval_service.py`, `backend/tests/test_modeling_intake_api.py`, `frontend/src/services/api.ts`, `frontend/src/services/api.test.ts`, `frontend/src/components/ModelingInputPanel.tsx`, `frontend/src/components/ModelingInputPanel.test.tsx`, `frontend/src/components/ModelPlanApprovalCard.tsx`, `frontend/src/components/ModelPlanApprovalCard.test.tsx`, `frontend/src/views/ModelingProjectsView.tsx`, `frontend/src/views/ModelingProjectsView.test.tsx`
- 失败测试：后端 `backend/tests/test_modeling_intake_api.py` 退出码 1，5 failures，缺少 InputUploadKind、upload/parse/decide 与全部 Phase 2 路由；前端 API/组件命令退出码 1，缺少两个组件与 `uploadInput`；视图命令退出码 1，4 failures，缺少三个阶段动作和审批卡
- 聚焦验证：初始后端 intake API 5 passed、前端 API/组件 13 passed、建模视图 26 passed；审查修复后 Phase 2 聚焦后端 40 passed、1 skipped，聚焦前端 41 passed，生产构建通过
- 相关回归：Phase 2 聚焦后端 37 passed、1 skipped；聚焦前端 39 passed；生产构建通过；完整后端 163 passed、13 subtests passed、1 skipped；完整前端 23 files、117 passed；保留既有 deprecation 与 Vite chunk-size warning
- 提交：实现 `12d450e6db238b787e3c1b6dc172a93a3aff3d61`；审查修复 `c1935a46f40a961ac12b3c930bb7fccd5b4fdd58`、`76f0ef959e51250556c81c0e1cea6aa96f98c2bb`
- 保留的用户改动：无；Task 5 开始时工作树仅有本账本更新；`frontend/node_modules` 为指向 Phase 1 本地依赖的 ignored junction，不联网安装
- 备注：实现 multipart 输入、parse/profile/plan 动作、成果/审批查询与 hash-bound 决策；前端审批修改意见必填并发送 API 返回的精确 payload_hash。独立审查发现跨项目审批、无界 multipart、后期仍可上传、旧 pending 审批、异步证据竞态和哈希标签混淆；新增跨项目/超限/状态、最新审批、乱序响应回归，实施 project ownership、MAX+1 有界读取与关闭、仅初始化态 intake、generation guard，并分别显示 artifact SHA-256 与 approval payload hash。复审继续发现审批错误码、早拒绝未关闭文件、切换项目等待期旧卡和卡片本地状态继承；新增 400/404/409、所有早拒绝 close、evidenceProjectId 回归并以 approval_id key 渲染。最终复审无 Critical/Important，结论 Ready。

### Phase 2 / Task 4: Structured Problem and Model-Plan Agents

- 状态：verified
- 预计文件：`backend/services/modeling_contracts.py`, `backend/services/modeling_role_service.py`, `backend/services/modeling_agent_run_service.py`, `backend/services/modeling_gate_service.py`, `backend/services/modeling_project_service.py`, `backend/skills/modeling_problem_parser/skill.json`, `backend/skills/modeling_planner/skill.json`, `backend/tests/test_modeling_role_service.py`, `backend/tests/test_modeling_agent_run_service.py`, `backend/tests/test_modeling_gate_service.py`, `backend/tests/test_skill_service.py`
- 实际文件：`backend/services/modeling_contracts.py`, `backend/services/modeling_role_service.py`, `backend/services/modeling_agent_run_service.py`, `backend/services/modeling_gate_service.py`, `backend/services/modeling_project_service.py`, `backend/skills/modeling_problem_parser/skill.json`, `backend/skills/modeling_planner/skill.json`, `backend/tests/test_modeling_role_service.py`, `backend/tests/test_modeling_agent_run_service.py`, `backend/tests/test_modeling_gate_service.py`, `backend/tests/test_skill_service.py`
- 失败测试：临时运行目录下执行 `DEBUG=false; PYTHONPATH=backend; python -m pytest backend/tests/test_modeling_role_service.py backend/tests/test_modeling_agent_run_service.py backend/tests/test_modeling_gate_service.py backend/tests/test_skill_service.py -q`；完整输出为 3 个预期收集错误，缺少 `modeling_agent_run_service` 与 `modeling_gate_service`（首轮 PowerShell finally 覆盖退出码，已修正后续命令保存真实退出码）
- 聚焦验证：初始命令退出码 0，10 passed；审查修复后角色/生命周期/Gate/API/Skill 命令退出码 0，27 passed、1 个 unittest subtest passed；保留既有 deprecation warning
- 相关回归：初始 Task 1–4 服务、Phase 1 状态/项目/Agent store 联合命令退出码 0，54 passed、1 skipped；审查修复后退出码 0，71 passed、1 skipped、1 个 unittest subtest passed；保留既有 deprecation warning
- 提交：实现 `a96fa93bb6e50dedce8647d7de7ae5e4d5d02a9a`；审查修复 `c5dc9a965816e9ac9be0d18fa7a6a692665f1152`、`cccda858053f5c73f4eeb7fac18ba727b235ec44`
- 保留的用户改动：无；Task 4 开始时工作树仅有本账本更新
- 备注：复用现有 `DocumentMetadataStore` Agent run/step 持久化和 `LLMService.generate(prompt)`；Gate 在推进前检查必需成果及当前文件内容哈希绑定的模型审批。独立审查发现生产 API 未接 Gate、真实重试不能累计、跨 store 生命周期不一致、输入成果未复核、输出/成果/审批失败无补偿、错误可能泄密；新增真实三次角色失败、API 409、输入篡改、敏感 provider 错误、各登记/审批/完成失败回归，并完成 fail-closed Gate 接线、任务复用、生命周期补偿、SHA/边界/结构复核、原子输出与全链路回滚、安全错误摘要。复审继续发现 start 失败绕过摘要及 run 状态更新失败覆盖安全错误，新增先红后绿回归与一次重试/吞掉基础设施细节；最终复审无 Critical/Important，结论 Ready。剩余 Minor：永久 Agent store 故障可能保留 stale run、真实 PDF 未测、源哈希到读取有窄 TOCTOU。

### Phase 2 / Task 3: Deterministic CSV Profiling

- 状态：verified
- 预计文件：`backend/requirements.txt`, `backend/services/data_profile_service.py`, `backend/tests/test_data_profile_service.py`
- 实际文件：`backend/requirements.txt`, `backend/services/data_profile_service.py`, `backend/tests/test_data_profile_service.py`
- 失败测试：`DEBUG=false; PYTHONPATH=backend; python -m pytest backend/tests/test_data_profile_service.py -q`，退出码 1；按预期因 `services.data_profile_service` 不存在而出现 1 个收集错误
- 聚焦验证：同一命令初始退出码 0，3 passed；审查修复后退出码 0，8 passed、1 个符号链接测试因 Windows 权限 skip
- 相关回归：聚焦测试加 `backend/tests/test_modeling_input_service.py backend/tests/test_artifact_service.py backend/tests/test_modeling_store.py`，实现提交前退出码 0，19 passed；审查修复后退出码 0，24 passed、1 skipped
- 提交：实现 `cff1080c16151ee759470ace277518984701c60a`；审查修复 `c9c78d42f9da7ced5352456ca67211c4cbbef668`
- 保留的用户改动：无；Task 3 开始时工作树仅有本账本更新
- 备注：本机 pandas 为 2.3.2，pip 缓存无计划固定的 2.2.2；先以兼容 API 完成 TDD 并在 requirements 固定 2.2.2，不未经授权联网安装。独立审查发现非有限统计、源成果篡改/逃逸和双输出/登记半成品风险；新增极值、缺失/错后缀/哈希、符号链接、写入与两次登记失败回归，实施当前源 SHA/边界复核、非有限值归一为 null、原子输出与成果记录补偿回滚。复审无剩余 Critical/Important，结论 Ready；同路径哈希复核与 pandas 再打开之间仍有极窄 TOCTOU，被评为 Minor。

### Phase 2 / Task 2: Immutable Input Import and Manifests

- 状态：verified
- 预计文件：`backend/services/modeling_input_service.py`, `backend/tests/test_modeling_input_service.py`
- 实际文件：`backend/services/modeling_input_service.py`, `backend/tests/test_modeling_input_service.py`
- 失败测试：`DEBUG=false; PYTHONPATH=backend; python -m pytest backend/tests/test_modeling_input_service.py -q`，退出码 1；按预期因 `services.modeling_input_service` 不存在而出现 1 个收集错误
- 聚焦验证：同一命令初始退出码 0，6 passed；审查修复后退出码 0，11 passed
- 相关回归：聚焦测试加 `backend/tests/test_artifact_service.py backend/tests/test_modeling_store.py`，实现提交前退出码 0，11 passed；审查修复后退出码 0，16 passed
- 提交：实现 `24b4e924cb103b39c213ae3e9bc8766a7762b0c2`；审查修复 `6b9c4c82498b887cce7b59fe4966a36e39111dca`
- 保留的用户改动：无；Task 2 开始时工作树仅有本账本更新
- 备注：严格限制问题输入 `.pdf/.md/.txt`、数据输入 `.csv`，拒绝路径逃逸、重复名称和超限内容；原始输入写入后只读并记录 SHA-256 清单。独立审查发现宿主 OS 相关路径校验和失败后孤儿 raw/manifest；新增路径风格、登记失败回滚重试、畸形 manifest 写前失败回归，改为显式跨平台 basename 校验、独占 raw 创建和原子 manifest 替换/恢复。复审无剩余 Critical/Important，结论 Ready；并发导入 manifest 更新序列化仍为 Minor 加固项。

### Phase 2 / Task 1: Artifact and Approval Persistence

- 状态：verified
- 预计文件：`backend/services/modeling_contracts.py`, `backend/services/modeling_store.py`, `backend/services/artifact_service.py`, `backend/services/approval_service.py`, `backend/tests/test_artifact_service.py`, `backend/tests/test_approval_service.py`
- 实际文件：`backend/services/modeling_contracts.py`, `backend/services/modeling_store.py`, `backend/services/artifact_service.py`, `backend/services/approval_service.py`, `backend/tests/test_artifact_service.py`, `backend/tests/test_approval_service.py`
- 失败测试：`DEBUG=false; PYTHONPATH=backend; python -m pytest backend/tests/test_artifact_service.py backend/tests/test_approval_service.py -q`，退出码 1；按预期因 `services.artifact_service` 与 `services.approval_service` 不存在而出现 2 个收集错误
- 聚焦验证：同一命令初始退出码 0，4 passed；审查修复后审批聚焦套件 3 passed
- 相关回归：聚焦测试加 `backend/tests/test_modeling_store.py backend/tests/test_modeling_project_service.py`，实现提交前退出码 0，11 passed；审查修复后退出码 0，12 passed；保留既有 Pydantic deprecation warning
- 提交：实现 `480714e5162f719a2461310293a34e26a3c6dbc7`；审查修复 `84e2af0aef74ee4397442bf4174d8c3f4c2d3a53`
- 保留的用户改动：无；Phase 2 隔离工作树基线为 `3b9b8f3`，创建时干净
- 备注：Phase 1 提交历史已核对；新鲜复核后端建模纵向套件 23 passed、前端聚焦套件 45 passed、生产构建通过。Gate 复核生成的未跟踪 `data/` 已经用户授权后清理。Task 1 回归首次运行又因默认相对 `UPLOAD_DIR` 生成 `data/notebooklm.db`；根因已追踪到 `DocumentMetadataStore` 默认路径，后续测试通过临时环境目录隔离。独立审查发现历史 approved 决策会在后续 changes_requested 后仍被接受；新增先红后绿回归并要求请求当前状态为 approved。复审无剩余 Critical/Important，结论 Ready。并发注册同一路径时版本分配仍可能竞争，被审查评为 Minor 持久化加固项，不阻塞当前顺序计划。

### Task N: Task 名称

- 状态：pending / in_progress / verified / blocked
- 预计文件：
- 实际文件：
- 失败测试：命令与预期失败
- 聚焦验证：命令、退出码、通过/失败数量
- 相关回归：命令、退出码、通过/失败数量
- 提交：commit hash
- 保留的用户改动：
- 备注：

### Task 1: Pure Workflow State Machine

- 状态：verified
- 预计文件：`backend/services/modeling_state.py`, `backend/tests/test_modeling_state.py`
- 实际文件：`backend/services/modeling_state.py`, `backend/tests/test_modeling_state.py`
- 失败测试：`DEBUG=false; python -m pytest tests/test_modeling_state.py -q`，退出码 1，预期失败 `ModuleNotFoundError: No module named 'services.modeling_state'`
- 聚焦验证：`DEBUG=false; python -m pytest tests/test_modeling_state.py -q`，退出码 0，4 passed；review fix 后退出码 0，5 passed
- 相关回归：`DEBUG=false; python -m pytest tests/test_config_defaults.py -q`，退出码 0，1 passed，保留既有 Pydantic deprecation warning
- 提交：实现 `029e5ef8eaf5b4ef607e603de0b97b5f6f287316`；review fix `640372ed3e444e005f7150c887f71da728bcbd02`
- 保留的用户改动：无；隔离工作树启动时 `git status --short` 为空
- 备注：基线验证使用 `DEBUG=false`，因为当前 shell 环境存在 `DEBUG=release`；Task 1 初始 review 指出测试需覆盖导出常量和 rollback 拒绝路径，已补充并验证；re-review 剩余问题为账本未指向 review fix commit，本次已更正

### Task 2: Modeling Metadata Store

- 状态：verified
- 预计文件：`backend/services/modeling_store.py`, `backend/tests/test_modeling_store.py`, `backend/services/document_metadata_store.py`, `backend/tests/test_agent_store.py`
- 实际文件：`backend/services/modeling_store.py`, `backend/tests/test_modeling_store.py`, `backend/services/document_metadata_store.py`, `backend/tests/test_agent_store.py`
- 失败测试：`DEBUG=false; python -m pytest tests/test_modeling_store.py tests/test_agent_store.py -q`，退出码 1，预期失败 `ModuleNotFoundError: No module named 'services.modeling_store'`；`DEBUG=false; python -m pytest tests/test_agent_store.py -q`，退出码 1，2 failed（缺少 `project_id` 返回字段和 `create_agent_run(project_id=...)` 支持）
- 聚焦验证：`DEBUG=false; python -m pytest tests/test_modeling_store.py tests/test_agent_store.py -q`，退出码 0，9 passed；review fix 前退出码 1，预期失败 raw JSON 字段泄漏；review fix 后退出码 0，10 passed，保留既有 Pydantic deprecation warning
- 相关回归：`DEBUG=false; python -m pytest tests/test_agent_service.py tests/test_agents_api.py -q`，退出码 0，8 passed，保留既有 Pydantic/PyPDF2 warnings；`DEBUG=false; python -m pytest tests/test_modeling_state.py -q`，退出码 0，5 passed
- 提交：实现 `935ec1ec08b3b5b846d86ea1b532dd208d0b2141`；review fix `24c7d8d3c9bf24736ed6a0c989bd19f4be0e7e74`
- 保留的用户改动：无；Task 2 开始时 `git status --short` 为空
- 备注：Task 2 review 指出 `list_tasks()` 不应泄漏内部 JSON 字段，并要求旧 `agent_runs` schema 迁移回归；已补充测试并修复任务输出形状

### Task 3: Safe Workspace and Project Service

- 状态：verified
- 预计文件：`backend/services/modeling_workspace.py`, `backend/services/modeling_project_service.py`, `backend/core/config.py`, `backend/tests/test_modeling_workspace.py`, `backend/tests/test_modeling_project_service.py`
- 实际文件：`backend/services/modeling_workspace.py`, `backend/services/modeling_project_service.py`, `backend/core/config.py`, `backend/tests/test_modeling_workspace.py`, `backend/tests/test_modeling_project_service.py`
- 失败测试：`DEBUG=false; python -m pytest tests/test_modeling_workspace.py tests/test_modeling_project_service.py -q`，退出码 1，预期失败 `ModuleNotFoundError` for `services.modeling_workspace` and `services.modeling_project_service`
- 聚焦验证：`DEBUG=false; python -m pytest tests/test_modeling_workspace.py tests/test_modeling_project_service.py -q`，退出码 0，5 passed；review fix 前 `DEBUG=false; python -m pytest tests/test_modeling_workspace.py tests/test_modeling_project_service.py tests/test_modeling_store.py -q` 退出码 1，4 failed（partial workspace、store failure cleanup、None rollback reason、missing transition_state）；review fix 后退出码 0，11 passed，保留既有 Pydantic deprecation warning
- 相关回归：`DEBUG=false; python -m pytest tests/test_config_defaults.py tests/test_modeling_store.py -q`，退出码 0，3 passed；review fix 后 `DEBUG=false; python -m pytest tests/test_config_defaults.py tests/test_agent_store.py -q`，退出码 0，9 passed，保留既有 Pydantic deprecation warning
- 提交：实现 `88d43699e3a20e21c44aad73757f791e8c368a7a`；review fix `087c51955ea6d0bcc74c9ee56ebde5fd5d7b8ffe`
- 保留的用户改动：无；Task 3 开始时 `git status --short` 为空
- 备注：Task 3 review 指出 workspace/git 初始化失败、store create 失败和 transition 两步写入存在部分状态风险；已补充回归，workspace cleanup 仅允许删除 workspace root 下的已创建项目目录，service create 失败会清理已创建 workspace，advance/rollback 使用 store 单事务 `transition_state`

### Task 4: Modeling REST API

- 状态：verified
- 预计文件：`backend/api/modeling.py`, `backend/main.py`, `backend/tests/test_modeling_api.py`
- 实际文件：`backend/api/modeling.py`, `backend/main.py`, `backend/tests/test_modeling_api.py`
- 失败测试：`DEBUG=false; python -m pytest tests/test_modeling_api.py -q`，退出码 1，预期失败 `ModuleNotFoundError: No module named 'api.modeling'`
- 聚焦验证：`DEBUG=false; python -m pytest tests/test_modeling_api.py tests/test_agents_api.py -q`，退出码 0，9 passed；保留既有 Pydantic、PyPDF2 与 FastAPI `on_event` deprecation warnings
- 相关回归：包含 `backend/tests/test_agents_api.py`，退出码 0，9 passed
- 提交：实现 `1ce74cab1216d0e8b48df1a707aa5470ee52c6d9`
- 保留的用户改动：无；隔离工作树在开始与提交后均为空
- 备注：直接导入 API 会初始化既有 `DocumentMetadataStore`，聚焦套件耗时约 29 秒；终端的早期流输出为空并非卡死。已通过等待子进程并读取完整输出确认结果。Post-Gate review 发现 `GET /projects/{id}/tasks` 和 `/runs` 会将服务层缺失项目 `ValueError` 传播为 500；先新增缺失项目的 404 回归，`DEBUG=false; python -m pytest tests/test_modeling_api.py -q` 预期失败 1 项，之后只在两个端点映射为 404。修复后同一命令退出码 0，7 passed（保留既有 Pydantic、PyPDF2 和 FastAPI deprecation warnings）；review-fix 提交 `1e67945`。

### Task 5: Frontend API, Navigation, and Project View

- Status: verified
- Planned and actual files: `frontend/src/services/api.ts`, `frontend/src/services/api.test.ts`, `frontend/src/store/useStore.ts`, `frontend/src/store/useStore.test.ts`, `frontend/src/i18n.ts`, `frontend/src/components/ModuleNav.tsx`, `frontend/src/components/ModuleNav.test.tsx`, `frontend/src/App.tsx`, `frontend/src/views/ModelingProjectsView.tsx`, `frontend/src/views/ModelingProjectsView.test.tsx`
- RED evidence: `Set-Location frontend; npm test -- --run src/services/api.test.ts src/views/ModelingProjectsView.test.tsx src/components/ModuleNav.test.tsx src/store/useStore.test.ts` exited 1 as expected: missing `modelingApi`, `setSelectedModelingProjectId`, Workflow navigation entry, and ModelingProjectsView module.
- GREEN evidence: the same focused command exited 0 with 4 files and 26 tests passed; `Set-Location frontend; npm test -- --run` exited 0 with 21 files and 89 tests passed; `Set-Location frontend; npm run build` exited 0.
- Review: independent Task 5 review found no actionable findings.
- Commit: implementation `335c892`.
- Notes: production build retains the pre-existing Vite chunk-size warning only; no task files were dirty after the implementation commit. Post-Gate review found the controls only respected in-flight requests: `project_initialized` could still roll back and `completed` could still advance. First, `ModelingProjectsView.test.tsx` added initialization, completion, and `problem_parsing` legality regressions; `npm test -- --run src/views/ModelingProjectsView.test.tsx` failed 2 assertions as expected. The view now derives availability from the backend state machine's fixed states and rollback set; the same command exited 0 with 6 passed and `npm run build` exited 0. Review-fix commit `6de550c`.

### Task 6: Phase 1 Vertical Verification

- Status: verified; no production-code changes were required.
- Modeling backend suite: from `backend`, `DEBUG=false; python -m pytest tests/test_modeling_state.py tests/test_modeling_store.py tests/test_modeling_workspace.py tests/test_modeling_project_service.py tests/test_modeling_api.py -q` exited 0 with 22 passed in 28.09s.
- Entire backend suite: from `backend`, `DEBUG=false; python -m pytest tests -q` exited 0 with 114 passed and 12 subtests passed in 28.91s. The repository-root Gate command also exited 0 with the explicit import path, `DEBUG=false; PYTHONPATH=backend; python -m pytest backend/tests -q`, with 114 passed and 12 subtests passed in 42.21s.
- Frontend: `Set-Location frontend; npm test -- --run` exited 0 with 21 files and 89 tests passed; `Set-Location frontend; npm run build` exited 0. The build keeps the pre-existing Vite chunk-size warning only.
- Cold restart: an isolated temporary runtime and SQLite database created `Sales Forecast`, advanced it once to `problem_parsing`, stopped the first backend process and confirmed port release, then restarted with the same database. The project remained visible as `problem_parsing`; its external workspace contained `.git`, `problem/original`, `data/raw`, `experiments`, `paper`, `deliverables`, and `.workflow/runs`.
- Cleanup: temporary server processes were stopped and ports released. A root-level test invocation created an untracked relative `data/` directory; it was verified as this run's generated SQLite/Chroma data and removed. The source worktree was clean before this ledger update.
- Gate 1: passed. Phase 2 is `not_started` and is not started by this Goal.
- Commit: this docs-only Task 6 ledger commit.

### Post-Gate Task 4/5 Review Fixes

- 状态：verified；仅修复 Phase 1 review findings，未开始 Task 6 或 Phase 2 工作。
- 后端：缺失项目的 task/run 列表现在统一为 `404 Modeling project not found`；TDD 红灯后 `tests/test_modeling_api.py` 7 passed；提交 `1e67945`。
- 前端：已知状态机状态驱动 Advance/Rollback 可用性，未知状态也保守地禁用动作；初始化、完成态和 `problem_parsing` 回归 6 passed；生产构建通过；提交 `6de550c`。
- 覆盖强化：re-review 要求逐一覆盖所有声明状态，新增 16 状态表驱动断言；`npm test -- --run` 退出码 0，21 files、108 passed，`npm run build` 退出码 0；提交 `e698df6`。
- 账本：本次文档提交记录上述发现、红绿证据和提交。

## 验证历史

| 时间 | 阶段/Task | 命令 | 结果 | 提交 |
| --- | --- | --- | --- | --- |
| 2026-07-11 | 规划基线 | `git show --stat bd167bf` | 六阶段计划提交存在 | `bd167bf` |
| 2026-07-11 | Phase 2 / Gate 2 | `python -m pytest backend/tests -q`; `npm test -- --run`; `npm run build`; `git diff --check` | 后端 170 passed、1 skipped、13 subtests；前端 120 passed；构建与 diff 检查通过；最终只读审查无 Critical/Important | `09000b4` |
| 2026-07-11 | Phase 4 / Gate 4 | `DEBUG=false; python -m pytest backend/tests -q`; `npm test -- --run`; `npm run build`; phase traceability checkpoint | 后端 219 passed、1 skipped、13 subtests；前端 28 files/125 tests；构建通过；实际 XeLaTeX 禁用 shell escape 生成并验证 PDF | `8363a3e` |

## 阻塞项

1. 已处理：Phase 1 开始前的 Reviva 工作台改动已整理为实现、文档截图和基线记录提交。

## Goal 运行历史

| Goal | 会话 | 开始 | 结束 | 结果 |
| --- | --- | --- | --- | --- |
| Phase 1 | 尚未创建 | — | — | pending |
| Phase 2 | 当前会话 | 2026-07-11 | 2026-07-11 | completed; Gate 2 passed; Phase 3 not started |
| Phase 4 | 当前会话 | 2026-07-11 | 2026-07-11 | completed; Gate 4 passed; Phase 5 not started |

## 更新规则

1. Task 开始时更新当前状态和 Task 记录。
2. Task 提交后写入验证证据与 commit hash。
3. 阻塞时记录具体条件、已尝试方法和用户决策点。
4. 阶段 Gate 完成后更新阶段总览，并把下一阶段从 `blocked_by_phase_N` 改为 `not_started`。
5. 不删除历史验证和 Goal 运行记录；需要纠正时追加说明。
