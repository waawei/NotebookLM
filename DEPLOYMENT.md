# 🚀 NotebookLM Clone - Windows 快速部署指南

## 📝 部署前检查清单

在开始之前，请确保：
- [ ] 已安装 **Python 3.10+** (https://www.python.org/downloads/)
- [ ] 已安装 **Node.js 18+** (https://nodejs.org/)
- [ ] 已获取 **LLM API Key** (推荐通义千问: https://dashscope.console.aliyun.com/)

---

## 🎯 三种启动方式

### 方式 1: 一键启动（推荐）

**适合**: 首次使用，希望快速体验

```bash
# 1. 进入项目目录
cd D:\develop\python\NotebookLM

# 2. 一键配置（首次运行）
双击 setup.bat

# 3. 配置 API Key
编辑 backend\.env 文件，填入你的 API Key

# 4. 一键启动
双击 start.bat
```

---

### 方式 2: 分步配置（推荐学习）

**适合**: 想了解每一步在做什么

#### 步骤 1: 配置后端

```bash
# 进入后端目录
cd D:\develop\python\NotebookLM\backend

# 运行配置脚本
双击 setup.bat

# 或者手动执行：
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
mkdir data\uploads
mkdir data\chroma_db
copy .env.example .env
```

#### 步骤 2: 配置 API Key

编辑 `backend\.env` 文件：
```env
LLM_PROVIDER=dashscope
LLM_MODEL=qwen-turbo
LLM_API_KEY=sk-your-actual-api-key-here
```

#### 步骤 3: 启动后端

```bash
cd D:\develop\python\NotebookLM\backend
双击 start_backend.bat

# 或者手动执行：
venv\Scripts\activate
python main.py
```

看到以下信息说明成功：
```
🚀 NotebookLM Clone API 启动中...
INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### 步骤 4: 配置前端

**打开新的命令行窗口**：

```bash
cd D:\develop\python\NotebookLM\frontend
双击 setup.bat

# 或者手动执行：
npm install --registry=https://registry.npmmirror.com
```

#### 步骤 5: 启动前端

```bash
cd D:\develop\python\NotebookLM\frontend
双击 start_frontend.bat

# 或者手动执行：
npm run dev
```

看到以下信息说明成功：
```
  VITE v5.0.8  ready in 500 ms
  ➜  Local:   http://localhost:3000/
```

---

### 方式 3: 命令行手动配置

**适合**: 有经验的开发者，喜欢完全掌控

#### 后端配置

```bash
cd D:\develop\python\NotebookLM\backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 安装依赖（使用清华镜像加速）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 创建数据目录
mkdir data
mkdir data\uploads
mkdir data\chroma_db

# 复制配置文件
copy .env.example .env

# 编辑配置（填入 API Key）
notepad .env

# 启动服务
python main.py
```

#### 前端配置

```bash
# 打开新的命令行窗口
cd D:\develop\python\NotebookLM\frontend

# 安装依赖（使用淘宝镜像加速）
npm install --registry=https://registry.npmmirror.com

# 启动服务
npm run dev
```

---

## 🔑 获取 API Key

### 方案 A: 通义千问（推荐）

**优势**: 中文效果好，价格便宜（约 0.01 元/次）

1. 访问 https://dashscope.console.aliyun.com/
2. 注册/登录阿里云账号
3. 点击"开通 DashScope"
4. 进入"API-KEY 管理"创建 Key
5. 复制 API Key 到 `.env` 文件

配置示例：
```env
LLM_PROVIDER=dashscope
LLM_MODEL=qwen-turbo
LLM_API_KEY=sk-xxxxxxxxxxxxx
```

### 方案 B: OpenAI

**优势**: 效果最好，但需要科学上网

1. 访问 https://platform.openai.com/
2. 注册并充值
3. 创建 API Key
4. 复制 API Key 到 `.env` 文件

配置示例：
```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo
LLM_API_KEY=sk-xxxxxxxxxxxxx
```

---

## ✅ 验证安装

### 1. 验证后端

访问 http://localhost:8000

应该看到：
```json
{
  "status": "running",
  "message": "NotebookLM Clone API is running"
}
```

访问 API 文档: http://localhost:8000/docs

### 2. 验证前端

访问 http://localhost:3000

应该看到 NotebookLM Clone 的主界面

---

## 🎮 开始使用

### 第一步：上传文档

1. 点击右上角"上传文档"按钮
2. 选择 PDF、TXT 或 Markdown 文件
3. 等待文档处理完成（状态变为"已完成"）

### 第二步：提问

1. 在左侧文档列表选择文档（点击文档卡片）
2. 在右侧输入框输入问题
3. 按 Enter 发送

### 第三步：查看引用

- 助手回答中会标注 [来源1]、[来源2]
- 底部显示具体的引用内容和来源

---

## 🐛 常见问题排查

### 问题 1: Python 版本太低

**错误**: `Python 3.10+ is required`

**解决**:
```bash
python --version  # 检查版本
# 如果低于 3.10，到官网下载最新版
# https://www.python.org/downloads/
```

### 问题 2: pip 安装慢

**解决**: 使用国内镜像

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题 3: npm 安装慢

**解决**: 使用淘宝镜像

```bash
npm install --registry=https://registry.npmmirror.com
```

### 问题 4: 端口被占用

**错误**: `Address already in use: 8000`

**解决**:
```bash
# 查找占用端口的进程
netstat -ano | findstr :8000

# 结束进程
taskkill /PID <进程ID> /F

# 或者修改端口
# backend\main.py 中修改 port=8000 为其他端口
```

### 问题 5: 模块导入错误

**错误**: `ModuleNotFoundError: No module named 'xxx'`

**解决**:
```bash
# 确认虚拟环境已激活
venv\Scripts\activate

# 重新安装依赖
pip install -r requirements.txt
```

### 问题 6: API Key 错误

**错误**: `Invalid API Key` 或 `Authentication failed`

**解决**:
1. 检查 `.env` 文件中的 API Key 是否正确
2. 确认 Key 没有过期
3. 检查账户余额是否充足

### 问题 7: 文档处理失败

**错误**: 文档状态显示"失败"

**解决**:
1. 查看后端命令行的错误日志
2. 检查文件是否损坏
3. 确认文件格式正确（PDF/TXT/MD）
4. 尝试更小的文件

### 问题 8: 前端无法连接后端

**错误**: 前端显示网络错误

**解决**:
1. 确认后端已启动（http://localhost:8000 能访问）
2. 检查防火墙设置
3. 查看浏览器控制台 (F12) 的错误信息

---

## 📊 性能优化建议

### 后端优化

1. **使用 GPU 加速** (如果有 NVIDIA 显卡):
   ```env
   EMBEDDING_DEVICE=cuda
   ```

2. **调整分块大小**:
   ```env
   CHUNK_SIZE=800  # 增大块大小，减少块数量
   CHUNK_OVERLAP=100
   ```

3. **增加检索数量**:
   ```env
   TOP_K_RESULTS=10  # 增加检索结果
   ```

### 前端优化

1. **生产环境构建**:
   ```bash
   npm run build
   # 输出在 dist/ 目录
   ```

2. **使用本地字体**（提升加载速度）

---

## 🔄 更新和维护

### 更新依赖

```bash
# 后端
cd backend
venv\Scripts\activate
pip install --upgrade -r requirements.txt

# 前端
cd frontend
npm update
```

### 清理数据

```bash
# 清理上传的文档
rd /s /q backend\data\uploads
mkdir backend\data\uploads

# 清理向量数据库（重置）
rd /s /q backend\data\chroma_db
mkdir backend\data\chroma_db
```

### 重启服务

```bash
# 关闭正在运行的服务窗口
# 重新运行 start.bat
```

---

## 📝 开发调试

### 查看后端日志

后端日志会直接输出在命令行窗口中

### 查看前端错误

浏览器按 F12 打开开发者工具，查看 Console 标签

### API 调试

使用 Swagger UI: http://localhost:8000/docs

可以直接在网页中测试 API

---

## 🎯 下一步

项目运行成功后，你可以：

1. **阅读技术文档**: 查看 `技术架构详解.md`
2. **查看项目目标**: 查看 `PROJECT_GOAL.md`
3. **开始开发**: 根据里程碑逐步添加功能
4. **提交代码**: 使用 Git 管理代码版本

---

## 📞 需要帮助？

1. 查看项目文档
2. 检查常见问题
3. 查看后端日志和浏览器控制台

---

**祝你搭建顺利！🎉**
