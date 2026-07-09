# NotebookLM 深度复刻优化计划

## 🎯 目标

在 P0 功能基础上，进一步提升产品完成度，达到 NotebookLM 95%+ 的功能对齐。

---

## 📊 当前完成度分析

### 已完成功能 ✅
- ✅ P0: 引用编号系统 [1], [2]
- ✅ P0: 建议问题生成
- ✅ P0: 文档摘要生成
- ✅ P0: 对话历史持久化
- ✅ 基础 RAG 问答
- ✅ 多文档支持
- ✅ NotebookLM 风格 UI

### 核心差距分析
| 功能领域 | NotebookLM | 当前项目 | 差距 |
|---------|-----------|---------|------|
| 文档管理 | 10 种格式 | 3 种格式 | ⭐⭐⭐ |
| 对话体验 | 流式输出 | 一次性输出 | ⭐⭐ |
| 引用系统 | 可跳转 | 只显示 | ⭐⭐⭐ |
| 笔记功能 | 完整编辑器 | 无 | ⭐⭐⭐⭐ |
| 搜索功能 | 全文搜索 | 无 | ⭐⭐ |
| 导出功能 | 多格式 | 无 | ⭐⭐ |

---

## 🚀 优化阶段划分

### 🔥 Phase 1: 用户体验提升（1-2 天）
**目标：** 提升交互流畅度和视觉反馈

1. **流式输出（Streaming）** ⭐⭐⭐⭐⭐
   - 打字机效果显示回答
   - 实时引用卡片出现
   - 提升等待体验

2. **引用内容预览** ⭐⭐⭐⭐
   - 点击引用展开完整内容
   - 高亮显示匹配片段
   - 模态框显示源文档上下文

3. **更多文档格式支持** ⭐⭐⭐⭐
   - DOCX 文档解析
   - 网页 URL 抓取
   - Markdown 渲染优化

4. **加载状态优化** ⭐⭐⭐
   - 骨架屏（Skeleton）
   - 进度指示器
   - 更友好的错误提示

---

### 🎨 Phase 2: 功能完善（2-3 天）
**目标：** 补齐核心功能差距

5. **笔记功能** ⭐⭐⭐⭐⭐
   - Markdown 笔记编辑器
   - 笔记与对话关联
   - 笔记内插入引用
   - 笔记列表管理

6. **内联引用在回答中** ⭐⭐⭐⭐
   - 回答文本中显示 [1], [2]
   - 点击编号滚动到引用卡片
   - 引用编号高亮效果

7. **全文搜索** ⭐⭐⭐
   - 搜索文档内容
   - 搜索对话历史
   - 高亮搜索结果

8. **对话管理** ⭐⭐⭐
   - 对话列表侧边栏
   - 新建/删除对话
   - 对话重命名

---

### ✨ Phase 3: 高级特性（3-5 天）
**目标：** 实现差异化功能

9. **导出功能** ⭐⭐⭐
   - 对话导出为 Markdown
   - 对话导出为 PDF
   - 笔记导出

10. **多笔记本管理** ⭐⭐⭐
    - 创建多个笔记本
    - 笔记本切换
    - 笔记本共享

11. **暗色模式** ⭐⭐
    - 完整暗色主题
    - 主题切换动画
    - 系统主题跟随

12. **快捷键支持** ⭐⭐
    - Cmd/Ctrl + K 搜索
    - Cmd/Ctrl + N 新对话
    - Cmd/Ctrl + / 快捷键面板

---

## 🎯 Phase 1 详细实现计划

### 1️⃣ 流式输出（Streaming）

#### 优先级：⭐⭐⭐⭐⭐
#### 预计时间：4-6 小时

**用户价值：**
- 减少等待焦虑感
- 提升专业感
- 与 NotebookLM 体验完全一致

**技术实现：**

#### 后端修改
```python
# backend/api/chat.py
from fastapi.responses import StreamingResponse

@router.post("/ask-stream")
async def ask_question_stream(request: ChatRequest):
    """流式问答接口"""
    async def generate():
        # 1. 检索文档
        search_results = await chat_service.vector_store.search(...)
        
        # 2. 流式生成回答
        answer_chunks = []
        async for chunk in chat_service.llm_service.generate_stream(prompt):
            answer_chunks.append(chunk)
            yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
        
        # 3. 发送引用
        citations = chat_service._build_citations(search_results)
        yield f"data: {json.dumps({'type': 'citations', 'citations': [c.dict() for c in citations]})}\n\n"
        
        # 4. 结束信号
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

#### 前端修改
```typescript
// frontend/src/components/ChatInterface.tsx
const handleSubmitStream = async (question: string) => {
  const response = await fetch(`${API_BASE_URL}/api/chat/ask-stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, doc_ids: selectedDocIds }),
  })

  const reader = response.body?.getReader()
  const decoder = new TextDecoder()
  
  let answer = ''
  let citations: Citation[] = []

  while (true) {
    const { done, value } = await reader!.read()
    if (done) break

    const chunk = decoder.decode(value)
    const lines = chunk.split('\n')

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6))
        
        if (data.type === 'content') {
          answer += data.content
          // 实时更新消息
          updateMessage(answer, citations)
        } else if (data.type === 'citations') {
          citations = data.citations
          updateMessage(answer, citations)
        }
      }
    }
  }
}
```

**UI 效果：**
```
User: 这篇文档讲了什么？