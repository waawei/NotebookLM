# 🚀 NotebookLM Clone - 快速启动指南

一个本地部署的智能文档问答系统，基于 RAG（检索增强生成）技术实现。

---

## 📋 项目结构

```
NotebookLM/
├── backend/                 # Python 后端
│   ├── api/                # API 路由
│   ├── core/               # 核心配置
│   ├── models/             # 数据模型
│   ├── services/           # 业务逻辑
│   ├── main.py             # 入口文件
│   └── requirements.txt    # Python 依赖
├── frontend/               # React 前端
│   ├── src/
│   │   ├── components/     # UI 组件
│   │   ├── services/       # API 调用
│   │   ├── store/          # 状态管理
│   │   └── main.tsx        # 入口文件
│   └── package.json        # Node 依赖
├── PROJECT_GOAL.md         # 项目目标和规划
└── 技术架构详解.md          # 技术原理详解
```

---

## 🛠️ 环境要求

### 必需
- **Python**: 3.10 或更高版本
- **Node.js**: 18.0 或更高版本
- **npm** 或 **yarn**

### 推荐
- **内存**: 至少 8GB RAM（运行 Embedding 模型）
- **存储**: 至少 5GB 可用空间

---

## 🚀 快速开始

### 第一步：克隆项目

```bash
# 已经在项目目录中，跳过此步
cd D:\develop\python\NotebookLM
```

### 第二步：配置后端

#### 1. 创建 Python 虚拟环境

```bash
cd backend

# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

**注意**：首次运行会自动下载 Embedding 模型（约 500MB），需要一些时间。

#### 3. 配置环境变量

```bash
# 复制配置文件
copy .env.example .env

# 编辑 .env 文件，填入你的 API Key
notepad .env
```

**重要**：必须配置 `LLM_API_KEY`

##### 获取 API Key 的方法：

**方案 A：通义千问（推荐，便宜）**
1. 访问 https://dashscope.console.aliyun.com/
2. 注册阿里云账号
3. 开通 DashScope 服务
4. 创建 API Key
5. 在 `.env` 中设置：
   ```
   LLM_PROVIDER=dashscope
   LLM_MODEL=qwen-turbo
   LLM_API_KEY=sk-xxxxx
   ```

**方案 B：OpenAI**
1. 访问 https://platform.openai.com/
2. 创建 API Key
3. 在 `.env` 中设置：
   ```
   LLM_PROVIDER=openai
   LLM_MODEL=gpt-3.5-turbo
   LLM_API_KEY=sk-xxxxx
   ```

#### 4. 创建数据目录

```bash
mkdir data
mkdir data\uploads
mkdir data\chroma_db
```

#### 5. 启动后端服务

```bash
python main.py
```

看到以下信息说明启动成功：
```
🚀 NotebookLM Clone API 启动中...
📊 向量数据库路径: ./data/chroma_db
🤖 LLM 提供商: dashscope
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**测试后端**：访问 http://localhost:8000 应该看到 `{"status": "running"}`

---

### 第三步：配置前端

#### 1. 打开新终端，进入前端目录

```bash
cd D:\develop\python\NotebookLM\frontend
```

#### 2. 安装依赖

```bash
npm install
```

#### 3. 启动前端服务

```bash
npm run dev
```

看到以下信息说明启动成功：
```
  VITE v5.0.8  ready in 500 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

#### 4. 访问应用

打开浏览器，访问 http://localhost:3000

---

## 📝 使用指南

### 1. 上传文档

- 点击右上角 **"上传文档"** 按钮
- 选择 PDF、TXT 或 Markdown 文件（最大 10MB）
- 等待文档处理完成（状态变为 "已完成"）

### 2. 开始提问

- 在左侧文档列表点击选择文档（可多选）
- 在右侧对话框输入问题
- 按 Enter 发送（Shift+Enter 换行）

### 3. 查看引用

- 助手回答会标注 [来源1]、[来源2] 等
- 底部会显示引用的具体文档和内容

---

## 🐛 常见问题

### 问题 1：后端启动失败

**错误**：`ModuleNotFoundError: No module named 'xxx'`

**解决**：
```bash
# 确认虚拟环境已激活
pip install -r requirements.txt
```

### 问题 2：下载 Embedding 模型慢

**错误**：长时间停在下载模型

**解决**：
- 使用国内镜像：
  ```bash
  pip install sentence-transformers -i https://pypi.tuna.tsinghua.edu.cn/simple
  ```
- 或者手动下载模型后放到缓存目录

### 问题 3：LLM API 调用失败

**错误**：`LLM 调用失败`

**解决**：
- 检查 `.env` 文件中的 `LLM_API_KEY` 是否正确
- 确认 API Key 有余额
- 检查网络连接

### 问题 4：前端无法连接后端

**错误**：前端显示网络错误

**解决**：
- 确认后端已启动（http://localhost:8000 能访问）
- 检查防火墙设置
- 查看浏览器控制台的错误信息

### 问题 5：文档处理失败

**错误**：文档状态显示 "失败"

**解决**：
- 检查文档格式是否正确
- 查看后端日志的错误信息
- 确认文件未损坏

---

## 🔧 开发指南

### 后端开发

#### 运行后端（开发模式）

```bash
cd backend
python main.py
# 代码修改会自动重载
```

#### API 文档

启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

#### 添加新功能

1. 在 `services/` 中实现业务逻辑
2. 在 `api/` 中添加路由
3. 在 `main.py` 中注册路由

### 前端开发

#### 运行前端（开发模式）

```bash
cd frontend
npm run dev
# 代码修改会自动热重载
```

#### 构建生产版本

```bash
npm run build
# 输出在 dist/ 目录
```

#### 添加新组件

1. 在 `src/components/` 创建组件文件
2. 在 `App.tsx` 中引入使用
3. 使用 Zustand store 管理状态

---

## 📦 项目依赖说明

### 后端核心依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| fastapi | 0.104.1 | Web 框架 |
| sentence-transformers | 2.2.2 | Embedding 模型 |
| chromadb | 0.4.18 | 向量数据库 |
| langchain | 0.1.0 | RAG 框架 |
| PyPDF2 | 3.0.1 | PDF 解析 |
| openai | 1.3.0 | LLM API |

### 前端核心依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| react | 18.2.0 | UI 框架 |
| typescript | 5.2.2 | 类型检查 |
| vite | 5.0.8 | 构建工具 |
| tailwindcss | 3.3.6 | CSS 框架 |
| zustand | 4.4.7 | 状态管理 |
| axios | 1.6.2 | HTTP 客户端 |

---

## 🎯 下一步计划

根据 `PROJECT_GOAL.md` 的规划：

### Week 1-2: MVP 开发
- [x] 项目骨架搭建
- [ ] 完善文档上传功能
- [ ] 优化 RAG 问答效果
- [ ] 添加错误处理

### Week 3-4: 功能扩展
- [ ] 多文档关联分析
- [ ] 对话历史持久化
- [ ] 引用溯源优化
- [ ] UI/UX 改进

### Week 5-6: 高级功能
- [ ] 自动生成学习指南
- [ ] 流式输出
- [ ] 性能优化
- [ ] 部署方案

---

## 📚 学习资源

- **RAG 原理**：查看 `技术架构详解.md`
- **项目目标**：查看 `PROJECT_GOAL.md`
- **FastAPI 文档**：https://fastapi.tiangolo.com/
- **React 文档**：https://react.dev/
- **LangChain 文档**：https://python.langchain.com/

---

## 🤝 贡献指南

这是一个学习项目，欢迎改进和建议！

### 提交代码

1. Fork 项目
2. 创建分支：`git checkout -b feature/your-feature`
3. 提交代码：`git commit -m 'Add some feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 提交 Pull Request

---

## 📄 许可证

MIT License

---

## 💡 技术支持

遇到问题？

1. 查看 `技术架构详解.md` 了解技术细节
2. 检查 GitHub Issues
3. 查看后端日志和浏览器控制台

---

**祝你开发顺利！🎉**

## Mathematical Modeling Workflow

The Modeling workspace is a gated, local workflow for turning a problem statement and CSV data into reproducible experiments, a reviewed paper, delivery artifacts, and an approved commit in the project's independent Git repository.

### Requirements

- Python 3.10 or later and Node.js 18 or later.
- Git must be available for the delivery and commit stages.
- Configure a writable `MODELING_WORKSPACE_ROOT` outside the application source tree. Each project receives its own workspace and Git repository there.
- XeLaTeX is required only to compile the final PDF. Paper drafting, review, final-paper approval, delivery validation, and Git approval remain available when it is not installed.

The Modeling page displays runtime readiness for the workspace, Python, Git, and XeLaTeX. A missing workspace disables all project write actions. A missing Python disables experiment preparation and execution. A missing Git disables Git review and commit actions. A missing XeLaTeX disables only PDF compilation.

### User Flow

1. Create a project, import a `.txt`, `.md`, or `.pdf` problem statement, and import `.csv` data.
2. Parse the problem, profile the data, and create a model plan. Approve the plan before preparing experiments.
3. Prepare each experiment, review the command, dependency lock, input hashes, timeout, output cap, and network policy, then approve execution before running it.
4. Validate results, generate and review the paper, resolve blocking review issues, request final approval, and compile the PDF when XeLaTeX is available.
5. Build delivery artifacts, review the exact Git diff, request and approve a commit, refresh the review immediately before committing, then commit only the approved files.

There are four approval gates: model plan, experiment execution, final paper, and Git commit. Changing the approved plan, execution payload, paper claims, selected Git paths, diff, file hashes, delivery manifest, or commit message invalidates the relevant approval.

### Data and Recovery

- Original inputs are copied into the project workspace with a SHA-256 manifest and are treated as immutable evidence.
- Generated code is constrained to approved project-relative paths. Experiment execution removes sensitive environment variables, denies network access by default, and applies output, timeout, and child-process limits.
- On backend startup, interrupted running work is recorded and returned to a safe prior workflow state. The Modeling page shows a recovery notice with the interrupted run; dismissing it hides the notice but preserves recovery history.
- The project repository is local-only. Delivery commands never push, reset, clean, rebase, change remotes, or check out branches.

### Fixture Verification

Run the deterministic 24-row sales forecasting workflow test from the repository root:

```powershell
$env:DEBUG = 'false'
$env:PYTHONPATH = 'backend'
python -m pytest backend/tests/test_modeling_workflow_e2e.py -q
```

The fixture uses deterministic Fake LLM responses, compares baseline and linear-regression experiments, verifies traceable paper claims and delivery evidence, and produces an approved local Git commit. When XeLaTeX is unavailable, only the compilation case is skipped with the explicit `xelatex is not installed` reason.
