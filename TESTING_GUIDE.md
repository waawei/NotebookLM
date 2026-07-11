# NotebookLM Clone - P0 功能测试指南

## 🎯 目标

验证所有 4 个 P0 核心功能正常工作：

1. ✅ **引用编号系统** [1], [2], [3]
2. ✅ **建议问题生成**
3. ✅ **文档摘要生成**
4. ✅ **对话历史持久化**

---

## 🚀 快速开始

### 方法 1：一键启动所有服务

```bash
# 启动后端 + 前端
start-all.bat
```

### 方法 2：分步启动

```bash
# 终端 1：启动后端
start-backend.bat

# 终端 2：启动前端
start-frontend.bat
```

---

## 🧪 自动化测试

### 后端 API 测试

```bash
# 前提：后端已启动
python test_p0_features.py
```

或使用批处理脚本：

```bash
run-tests.bat
```

**测试内容：**
- ✅ 健康检查
- ✅ 文档列表（含摘要）
- ✅ 建议问题生成
- ✅ 对话回答（含引用编号）
- ✅ 对话历史持久化

---

## 🎨 前端手动测试

### 1. 访问应用

打开浏览器访问：**http://localhost:3000**

---

### 2. 测试：文档上传和摘要生成

**步骤：**
1. 点击左侧 Sidebar 的 **"Add source"** 按钮
2. 上传一个测试文档（PDF/TXT/MD）
3. 等待文档处理（状态从 `processing` → `completed`）

**验证点：**
- ✅ 文档卡片显示处理完成状态（绿色 ✓）
- ✅ **文档名下方显示 AI 生成的摘要**（2-3 句话）
- ✅ 显示 chunk 数量

**截图示例：**
```
┌─────────────────────────────┐
│ 📄 research_paper.pdf       │
│ This document discusses...  │  ← 摘要
│ AI models and their...      │
│ [✓ completed] [42 chunks]   │
└─────────────────────────────┘
```

---

### 3. 测试：建议问题生成

**步骤：**
1. 上传文档后，确保文档被选中（蓝色边框）
2. 查看对话界面中央

**验证点：**
- ✅ 显示 **"Suggested questions"** 标题（💡 灯泡图标）
- ✅ 显示 3-5 个智能生成的问题
- ✅ 点击任意问题，**自动填充到输入框**

**截图示例：**
```
        💡 Suggested questions

┌───────────────────────────────────────┐
│ What are the main topics covered in  │
│ this document?                        │
└───────────────────────────────────────┘

┌───────────────────────────────────────┐
│ Can you summarize the key findings?  │
└───────────────────────────────────────┘
```

---

### 4. 测试：引用编号系统

**步骤：**
1. 提交一个问题（可以使用建议问题）
2. 等待回答生成
3. 查看回答下方的 **"Sources"** 区域

**验证点：**
- ✅ 每个引用卡片**左上角显示蓝色圆形编号徽章**
- ✅ 编号从 [1] 开始递增 [1], [2], [3]...
- ✅ 显示文档名和相关性分数
- ✅ 显示引用片段内容

**截图示例：**
```
Sources

┌─────────────────────────────────────┐
│ [1] Document_abc123                 │ 95%
│ This section describes the method...│
└─────────────────────────────────────┘
     ↑ 蓝色圆形编号

┌─────────────────────────────────────┐
│ [2] Document_abc123                 │ 87%
│ The results show that...            │
└─────────────────────────────────────┘
```

---

### 5. 测试：对话历史持久化

**步骤：**
1. 进行 2-3 轮对话（提问 → 回答）
2. **刷新浏览器页面**（按 F5 或 Ctrl+R）
3. 观察对话历史

**验证点：**
- ✅ **对话历史完整保留**（所有问题和回答）
- ✅ 引用卡片正常显示
- ✅ 可以继续对话，**上下文连贯**
- ✅ 后端文件：`data/uploads/conversations/{conversation_id}.json` 存在

---

## 📊 测试结果检查

### 前端检查

打开浏览器开发者工具（F12）：

```javascript
// 检查 localStorage
console.log(localStorage.getItem('chat_messages'))
console.log(localStorage.getItem('conversation_id'))
```

### 后端检查

```bash
# 查看对话文件
dir backend\data\uploads\conversations

# 查看文档文件
dir backend\data\uploads
```

---

## ✅ 完整测试清单

### P0 功能验证表

| 功能 | 测试步骤 | 验证点 | 状态 |
|------|---------|--------|------|
| **文档摘要** | 上传文档 → 等待处理完成 | Sidebar 文档卡片显示摘要 | ⬜ |
| **建议问题** | 选中文档 | 对话界面显示 3-5 个建议问题 | ⬜ |
| **引用编号** | 提交问题 → 查看回答 | 引用卡片显示 [1], [2] 编号 | ⬜ |
| **对话持久化** | 对话 → 刷新页面 | 对话历史完整保留 | ⬜ |

---

## 🐛 常见问题

### Q1: 建议问题不显示？

**原因：** 文档未处理完成或未选中

**解决：**
1. 确保文档状态为 `completed`
2. 点击文档卡片选中（蓝色边框）
3. 刷新页面重试

### Q2: 引用编号不显示？

**原因：** 前端类型未更新或缓存问题

**解决：**
```bash
# 清除前端缓存重新启动
start-frontend-clean.bat
```

### Q3: 对话历史丢失？

**原因：** localStorage 被清除或浏览器隐私模式

**解决：**
1. 检查浏览器是否为隐私模式
2. 检查 localStorage 权限
3. 后端对话文件应该仍然存在

### Q4: LLM API 调用失败？

**原因：** API 密钥未配置或额度用完

**解决：**
1. 检查 `backend/core/config.py` 中的 API 配置
2. 确认 API 密钥有效
3. 查看后端日志错误信息

---

## 📝 配置文件

### 后端配置

**文件：** `backend/core/config.py`

```python
# LLM 配置
LLM_PROVIDER = "openai"  # 或 "dashscope"
LLM_API_KEY = "sk-your-api-key"
LLM_BASE_URL = "https://api.openai.com/v1"  # 或自定义
LLM_MODEL = "gpt-4"
```

### 前端配置

**文件：** `frontend/src/components/ChatInterface.tsx`

```typescript
const API_BASE_URL = 'http://localhost:8000'
```

---

## 📈 性能指标

### 预期响应时间

- 文档上传：< 2 秒
- 文档处理（含摘要生成）：10-30 秒（取决于文档大小）
- 建议问题生成：5-10 秒
- 对话回答：5-15 秒
- 对话历史加载：< 1 秒

---

## 🎉 测试完成标准

所有 4 个 P0 功能均正常工作即视为完成：

1. ✅ 文档摘要自动生成并显示
2. ✅ 建议问题智能生成并可点击
3. ✅ 引用显示带编号 [1], [2], [3]
4. ✅ 对话历史刷新后保留

---

## 📞 需要帮助？

查看详细实现文档：
- [功能对齐清单](FEATURE_ALIGNMENT.md)
- [P0 功能总结](P0_FEATURES_SUMMARY.md)
- [项目 README](README.md)

---

**祝测试顺利！🚀**

## Mathematical Modeling Release Checks

Run these commands from the repository root before releasing a modeling workflow change:

```powershell
$env:DEBUG = 'false'
$env:PYTHONPATH = 'backend'
python -m pytest backend/tests -q

Set-Location frontend
npm test -- --run
npm run build
```

The backend suite includes interruption recovery, runtime redaction, adversarial path/network/resource/Git controls, the deterministic 24-row fixture, and full workflow E2E coverage. XeLaTeX may be absent only when the affected compilation test is skipped with `xelatex is not installed`; paper rendering, review, approval, delivery, and Git assertions must still pass.

### Modeling Manual Audit

1. Start the backend with a writable `MODELING_WORKSPACE_ROOT`, create a modeling project, and confirm the runtime panel reports workspace, Python, and Git as ready.
2. Import a problem and CSV, then progress through model approval, two execution approvals, paper review, final approval, delivery build, and Git approval.
3. During one prepared or running experiment, stop the backend process. Restart it using the same database and confirm the recovery notice identifies the interrupted work and the project returns to a safe state before preparing a new experiment.
4. Before committing, verify the review displays the intended files and commit message. Change a selected file or the delivery manifest, refresh the diff, and confirm the approved commit action disappears until a new approval is obtained.
5. Inspect the project workspace: `git remote -v` must be empty. Inspect `deliverables/manifest.json`, the persisted artifact records, and paper claims; every paper metric and figure claim must resolve to registered evidence.

### Capability Expectations

- Workspace unavailable: all modeling write controls are disabled.
- Python unavailable: experiment preparation and Run are disabled.
- Git unavailable: Git review, approval, and commit controls are disabled.
- XeLaTeX unavailable: only Compile is disabled; paper review and final approval remain available.

### Focused Commands

```powershell
$env:DEBUG = 'false'
$env:PYTHONPATH = 'backend'
python -m pytest backend/tests/test_modeling_recovery_service.py backend/tests/test_modeling_runtime_status.py backend/tests/test_modeling_security_regression.py backend/tests/test_modeling_workflow_e2e.py -q

Set-Location frontend
npm test -- --run src/components/ModelingRuntimeStatus.test.tsx src/components/ModelingRecoveryBanner.test.tsx src/views/ModelingWorkflow.integration.test.tsx
```
