# Library AI Assistant

基于 RAG 的对话机器人及智能体开发平台

## 项目简介

构建一个基于 RAG（检索增强生成）技术的**对话机器人及智能体开发平台**，解决企业知识资产分散、信息检索效率低下的问题，提供从后端数据处理（以RAG为核心进行知识库维护）、混合搜索、智能路由到模型微调的全链路、生产级解决方案。

### 产品愿景

成为业界领先的**对话机器人及智能体开发平台**，不仅仅是一个应用，更是一个**高内聚、低耦合的开发脚手架和最佳实践集合**。

## 功能特性

### 后台知识库管理平台

- **知识库管理** - 创建、编辑、删除、克隆知识库，支持多 Embedding 模型切换
- **文档管理** - 批量上传 txt/pdf/docx/md 格式，自动解析、切分、向量化，支持版本管理
- **向量管理** - 自动生成向量，支持预览、去重、优化
- **系统管理** - 模型配置、系统参数、缓存配置
- **权限管理** - 用户管理、角色管理、RBAC 权限分配、JWT 认证
- **配置管理** - 回复速度、回答长度、检索参数、多轮上下文长度配置
- **对话日志** - 日志记录、查询筛选、数据分析、导出清理

### 对话机器人功能

- **智能问答** - 基于 RAG 的语义检索 + LLM 答案生成，支持多轮对话
- **语义理解** - 意图识别、问题重写、多知识库检索、语义纠错
- **答案增强** - 答案拼接、引用标注、Markdown 格式化、LLM 增强
- **对话规则** - 知识库兜底、敏感词过滤、规则配置、拒绝回答

## 技术栈

### 后端
- **Web 框架**: FastAPI (异步、高性能)
- **服务器**: Uvicorn (asyncio 驱动)
- **数据库**: SQLite + SQLAlchemy ORM
- **向量数据库**: ChromaDB (嵌入式，无需外部服务)
- **Embedding**: BAAI/bge-small-zh-v1.5 (384 维中文 Embedding)
- **文档解析**: python-docx / pypdf
- **文本切分**: LangChain Text Splitters (RecursiveCharacterTextSplitter)
- **认证**: python-jose (JWT Token)

### 前端
- **框架**: Vue 3 + Vite
- **UI 库**: Element Plus
- **HTTP**: Axios
- **路由**: Vue Router
- **Markdown**: markdown-it

## 项目结构

```
library-ai-assistant/
├── backend/                     # 后端服务
│   ├── main.py                  # FastAPI 入口
│   ├── requirements.txt         # Python 依赖
│   ├── .env                     # 环境变量配置
│   └── app/
│       ├── api/                 # API 路由
│       │   ├── auth.py          # 认证（登录/注册/用户信息）
│       │   ├── chat.py          # 智能问答
│       │   ├── knowledge.py     # 知识库管理
│       │   ├── documents.py     # 文档管理
│       │   └── logs.py          # 对话日志
│       ├── core/                # 核心配置
│       │   ├── config.py        # 应用配置
│       │   └── security.py      # 安全工具
│       ├── services/            # 业务服务
│       │   ├── llm_service.py       # LLM 调用
│       │   ├── rag_service.py       # RAG 检索与答案生成
│       │   ├── embedding_service.py # 向量生成
│       │   ├── vector_service.py    # ChromaDB 操作
│       │   ├── document_parser.py   # 文档解析
│       │   └── text_splitter.py     # 文本切分
│       ├── models/              # 数据模型
│       │   ├── models.py        # SQLAlchemy 模型
│       │   ├── schemas.py       # Pydantic 模型
│       │   └── database.py      # 数据库连接
│       └── data/                # 运行时数据
│           ├── library.db       # SQLite 数据库
│           ├── chroma/          # 向量库
│           └── uploads/         # 上传文件
├── frontend/                    # 前端项目
│   ├── package.json
│   └── src/
│       ├── main.js              # 入口文件
│       ├── App.vue              # 根组件
│       ├── api/index.js         # 接口封装
│       ├── router/index.js      # 路由配置
│       └── views/               # 页面组件
│           ├── LoginView.vue    # 登录/注册
│           ├── HomeView.vue     # 仪表盘
│           ├── ChatView.vue     # 智能问答
│           ├── KnowledgeView.vue # 知识库管理
│           ├── DocumentView.vue # 文档管理
│           └── LogView.vue      # 对话日志
├── docs/                        # 知识库文档
├── presentation/                # 答辩材料
└── README.md
```

## 环境要求

- Python 3.10 或 3.11
- Node.js 18.x 或 20.x
- 包管理：pip + npm

## 快速开始

### 1. 安装后端依赖

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `backend/.env` 文件，配置 LLM API Key：

```env
# LLM 配置（必须配置）
LLM_API_KEY=sk-your-api-key-here
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-plus

# 其他配置可保持默认
SECRET_KEY=your-secret-key-here
```

### 3. 启动后端服务

```bash
cd backend
python main.py
```

### 4. 安装前端依赖

```bash
cd frontend
npm install
```

### 5. 启动前端服务

```bash
cd frontend
npm run dev
```

### 6. 访问系统

| 地址 | 说明 |
|------|------|
| http://localhost:5173 | 前端界面 |
| http://localhost:8000/docs | API 文档（Swagger） |

## 默认账号

系统首次启动时会自动创建默认管理员账号：

| 用户名 | 密码 | 角色 | 权限 |
|--------|------|------|------|
| admin | admin123 | 管理员 | 全部功能 |

> 💡 新用户可通过登录页面的"立即注册"功能创建账号

## 权限说明

| 功能 | 管理员 | 普通用户 |
|------|--------|----------|
| 智能问答 | ✅ | ✅ |
| 仪表盘 | ✅ | ❌ |
| 知识库管理 | ✅ | ❌ |
| 文档管理 | ✅ | ❌ |
| 对话日志 | ✅（查看所有） | ❌ |

## 常见问题

### Q: LLM 不回复怎么办？

检查 `backend/.env` 中的 `LLM_API_KEY` 是否正确配置。

### Q: Embedding 模型加载失败？

首次运行会自动下载模型，如网络不佳可配置镜像：
```bash
export HF_ENDPOINT=https://hf-mirror.com
```

### Q: 如何切换 LLM 模型？

修改 `backend/.env` 中的配置：
```env
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL_NAME=deepseek-chat
LLM_API_KEY=sk-your-deepseek-key
```

### Q: 如何配置多知识库检索？

在知识库管理页面，可以为每个知识库设置检索权重。系统默认检索所有有权限的知识库，返回结果会标注来源知识库。

### Q: 如何查看对话日志？

管理员可在"对话日志"页面查看所有用户的对话历史，支持按用户、时间、关键词筛选。

## 开发规范

### 代码风格
- 后端遵循 PEP 8 规范
- 前端遵循 Vue 3 Composition API 最佳实践
- 使用有意义的变量和函数命名
- 重要逻辑添加注释

### Git 提交
- 使用中文提交信息
- 提交格式：`<类型>: <描述>`
- 类型：feat / fix / docs / style / refactor / test / chore

### API 设计
- RESTful 风格
- 统一响应格式：`{ code, message, data }`
- 错误处理：返回明确的错误信息
