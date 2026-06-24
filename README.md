# RAG-KnowledgeSystem

生产级 RAG 系统，基于 LangChain + LangGraph + Qdrant + BGE-M3 构建。

## 技术栈

| 层级 | 技术选型 | 选型理由 |
|------|---------|---------|
| 框架 | LangChain + LangGraph | 市场主流 RAG 编排框架 |
| LLM | `init_chat_model()` 通用初始化 | 不绑定厂商，支持 deepseek/openai/anthropic/ollama 等 |
| Embedding | BAAI/bge-m3 | 免费、1024维、多语言SOTA、支持稀疏+稠密双向量 |
| 向量库 | Qdrant | Rust高性能，原生混合检索，Docker一键部署 |
| 重排序 | BAAI/bge-reranker-v2-m3 | 免费、C-MTEB排行榜第一 |
| 多路召回 | Dense + Sparse 单次查询 | BGE-M3双向量 + Qdrant原生融合，无需手动维护BM25 |
| Query重写 | Multi-Query + HyDE + Step-Back | LangChain官方推荐的Query增强手段 |
| 后端 | FastAPI | 高性能、类型安全、自动生成API文档 |
| 包管理 | uv | Rust编写，极速依赖解析 |
| 可观测性 | LangFuse | 开源可观测性方案 |
| 评测 | RAGAS | RAG专用评测框架 |

## 项目结构

```
RAG-KnowledgeSystem/
├── pyproject.toml                 # uv项目配置
├── .env.example                   # 环境变量模板
├── README.md
│
├── src/
│   ├── config/                    # 配置层
│   │   ├── settings.py            # Pydantic Settings 全局配置
│   │   └── constants.py           # 常量定义（文件类型、状态枚举）
│   │
│   ├── data_loader/               # 数据加载层（10种文件类型）
│   │   ├── base_loader.py         # 加载器抽象基类
│   │   ├── loader_registry.py     # 加载器注册中心（工厂模式）
│   │   ├── pdf_loader.py          # PDF（PyMuPDF + 表格提取）
│   │   ├── word_loader.py         # Word/docx
│   │   ├── excel_loader.py        # Excel/xlsx/csv
│   │   ├── ppt_loader.py          # PPT/pptx
│   │   ├── image_loader.py        # 图片OCR + 多模态LLM
│   │   ├── markdown_loader.py     # Markdown（保留层级结构）
│   │   ├── text_loader.py         # 纯文本/txt/log/rst
│   │   ├── html_loader.py         # HTML网页
│   │   ├── code_loader.py         # 代码文件（多语言语法感知）
│   │   ├── structured_loader.py   # JSON/YAML结构化数据
│   │   └── web_scraper.py         # 网页爬取（httpx + BeautifulSoup）
│   │
│   ├── splitting/                 # 文档分割层
│   │   ├── semantic_splitter.py   # 语义分割 + 递归分割 + 代码分割
│   │   └── splitter_factory.py    # 分割器工厂（自动识别文档类型）
│   │
│   ├── embedding/                 # 向量化层
│   │   ├── bge_embedding.py       # BGE-M3稠密向量 + 稀疏向量
│   │   ├── sparse_embedding.py    # 稀疏向量生成（BM25风格）
│   │   └── embedding_cache.py     # Embedding缓存（避免重复计算）
│   │
│   ├── ingestion/                 # 数据入仓库层
│   │   ├── document_store.py      # Qdrant向量库管理
│   │   ├── metadata_store.py      # SQLite元数据管理
│   │   └── pipeline.py            # 完整入库流水线（并行处理）
│   │
│   ├── retrieval/                 # 检索层
│   │   ├── vector_retriever.py    # 向量检索（dense + sparse）
│   │   ├── bm25_retriever.py      # BM25关键词检索
│   │   ├── hybrid_retriever.py    # 混合检索（RRF融合/加权融合）
│   │   ├── reranker.py            # 重排序（bge-reranker-v2-m3）
│   │   └── ensemble_retriever.py  # 融合检索器（多路召回+重排序）
│   │
│   ├── query_rewriting/           # Query改写层
│   │   ├── query_rewriter.py      # LLM驱动的Query重写/扩展
│   │   ├── query_decomposer.py    # 复杂问题分解（Multi-Query）
│   │   ├── hyde_generator.py      # HyDE（假设文档嵌入）
│   │   └── stepback_prompt.py     # Step-Back Prompting
│   │
│   ├── generation/                # 生成层
│   │   ├── rag_chain.py           # 核心RAG链（LangGraph StateGraph编排）
│   │   ├── context_builder.py     # 上下文构建与压缩
│   │   ├── prompt_templates.py    # Prompt模板管理（多风格）
│   │   └── response_synthesizer.py# 响应合成（compact/refine/tree_summarize）
│   │
│   ├── memory/                    # 对话记忆层
│   │   └── conversation_memory.py # 对话历史管理 + 问题压缩
│   │
│   ├── evaluation/                # 评测层
│   │   ├── retrieval_metrics.py   # 检索指标（MRR/NDCG/Precision/Recall）
│   │   └── ragas_eval.py          # RAGAS框架评测
│   │
│   ├── middleware/                 # 中间件
│   │   ├── rate_limiter.py        # 限流
│   │   ├── trace.py               # 请求追踪（X-Trace-ID）
│   │   └── guardrails.py          # 输入/输出安全护栏（防注入/PII/敏感信息）
│   │
│   └── api/                       # API层（FastAPI）
│       ├── main.py                # FastAPI入口 + 生命周期管理
│       ├── dependencies.py        # 依赖注入（单例模式）
│       ├── routes/
│       │   ├── chat.py            # 对话路由（支持流式SSE）
│       │   ├── document.py        # 文档管理路由（上传/入库/删除）
│       │   ├── retrieval.py       # 检索路由（dense/sparse/hybrid）
│       │   └── knowledge_base.py  # 知识库管理路由
│       └── schemas/
│           ├── request.py         # 请求数据模型
│           └── response.py        # 响应数据模型
│
├── scripts/                       # 运维脚本
│   ├── init_kb.py                 # 初始化知识库
│   └── reindex.py                 # 重建索引
│
└── tests/                         # 测试目录（预留）
```

## 核心处理流程

```
用户 Query
    │
    ▼
┌──────────────────────────────────┐
│  1. Query 重写层（LLM驱动）       │
│  ├── Multi-Query：多角度改写       │
│  ├── Query Decompose：子问题分解   │
│  ├── HyDE：生成假设文档           │
│  └── Step-Back：回溯背景问题      │
└──────────────┬───────────────────┘
               │ 多个改写 Query
               ▼
┌──────────────────────────────────┐
│  2. 多路召回层（并行执行）         │
│  ┌─────────┐   ┌─────────┐      │
│  │Dense检索 │   │Sparse检索│      │
│  │(BGE-M3)  │   │(BGE-M3)  │      │
│  └────┬────┘   └────┬────┘      │
│       └──────┬──────┘            │
│              ▼                   │
│        RRF / 加权融合             │
└──────────────┬───────────────────┘
               │ Top-K 候选文档
               ▼
┌──────────────────────────────────┐
│  3. 重排序层                      │
│  bge-reranker-v2-m3 Cross-Encoder │
│  精排 + 阈值过滤                  │
└──────────────┬───────────────────┘
               │ Top-N 精排结果
               ▼
┌──────────────────────────────────┐
│  4. 上下文构建层                  │
│  去重 → 相关性过滤 → 元数据注入   │
│  → 长度压缩 → 格式化              │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│  5. 响应合成层                    │
│  LLM + RAG Prompt（多风格可选）   │
│  支持 compact / refine /         │
│  tree_summarize 三种模式          │
│  引用标注 + 流式输出              │
└──────────────────────────────────┘
               │
               ▼
            用户回答
```

## 数据层支持的文件类型

| 类型 | 扩展名 | 解析方案 |
|------|--------|----------|
| PDF | `.pdf` | PyMuPDF + RapidOCR(扫描件) + UnstructuredIO(复杂布局) + 图片提取 |
| Word | `.docx` `.doc` | python-docx |
| Excel | `.xlsx` `.xls` `.csv` | openpyxl + pandas |
| PPT | `.pptx` `.ppt` | python-pptx |
| 图片 | `.png` `.jpg` `.jpeg` `.bmp` `.tiff` | pytesseract OCR + 多模态LLM |
| Markdown | `.md` | 自定义解析器（保留层级结构） |
| 纯文本 | `.txt` `.log` `.rst` | 直接读取 |
| HTML | `.html` `.htm` | BeautifulSoup + Html2Text |
| 代码 | `.py` `.js` `.ts` `.java` `.go` `.rs` 等 | 语法感知分割器 |
| JSON/YAML | `.json` `.yaml` `.yml` | 结构化文档加载器 |

## 快速开始

### 1. 环境准备

```bash
# 安装 uv（如未安装）
pip install uv

# 克隆项目
git clone <repo-url>
cd RAG-KnowledgeSystem

# 创建虚拟环境并安装依赖
uv sync

# 复制环境变量配置
cp .env.example .env
# 编辑 .env 填入你的 LLM API Key
```

### 2. 启动 Qdrant

```bash
# Docker 方式（推荐）
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest

# 或使用内存模式（测试用）
# 在 .env 中设置 QDRANT_USE_MEMORY=true
```

### 3. 配置 LLM

编辑 `.env` 文件：

```env
# 方案1：硅基流动（免费，推荐个人开发者）
LLM_PROVIDER=openai
LLM_MODEL=deepseek-ai/DeepSeek-V3
LLM_API_KEY=your_siliconflow_api_key
LLM_BASE_URL=https://api.siliconflow.cn/v1

# 方案2：DeepSeek官方
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
LLM_API_KEY=your_deepseek_api_key

# 方案3：Ollama本地部署
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:14b
LLM_BASE_URL=http://localhost:11434
```

### 4. 初始化知识库

```bash
# 将文档放入 data/raw/ 目录
mkdir -p data/raw
cp /path/to/your/documents/* data/raw/

# 初始化（首次运行会自动下载BGE-M3模型，约2GB）
uv run python scripts/init_kb.py --data-dir ./data/raw
```

### 5. 启动服务

```bash
uv run python -m src.api.main
# 或
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

访问 API 文档：http://localhost:8000/docs

## API 接口

### 对话

```bash
# 普通对话
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "question": "什么是RAG系统？",
    "enable_query_rewriting": true,
    "enable_reranking": true,
    "prompt_style": "detailed"
  }'

# 流式对话
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "解释一下向量检索的原理"}'
```

### 文档管理

```bash
# 上传文件
curl -X POST http://localhost:8000/api/v1/documents/ingest/upload \
  -F "file=@document.pdf"

# 入库整个目录
curl -X POST http://localhost:8000/api/v1/documents/ingest/directory \
  -H "Content-Type: application/json" \
  -d '{"directory": "./data/raw", "recursive": true}'

# 删除文档
curl -X DELETE http://localhost:8000/api/v1/documents/ \
  -H "Content-Type: application/json" \
  -d '{"file_path": "./data/raw/document.pdf"}'
```

### 检索

```bash
# 混合检索（RRF融合）
curl -X POST http://localhost:8000/api/v1/retrieval/search \
  -H "Content-Type: application/json" \
  -d '{"query": "RAG系统架构", "top_k": 10, "rerank_enabled": true}'

# 仅向量检索
curl -X POST http://localhost:8000/api/v1/retrieval/dense \
  -H "Content-Type: application/json" \
  -d '{"query": "RAG系统架构"}'

# 仅稀疏检索
curl -X POST http://localhost:8000/api/v1/retrieval/sparse \
  -H "Content-Type: application/json" \
  -d '{"query": "RAG系统架构"}'
```

### 知识库管理

```bash
# 查看知识库信息
curl http://localhost:8000/api/v1/knowledge-base/info

# 初始化空集合
curl -X POST http://localhost:8000/api/v1/knowledge-base/init

# 查看文档列表
curl http://localhost:8000/api/v1/knowledge-base/documents
```

## 环境变量说明

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_PROVIDER` | `deepseek` | LLM提供商 |
| `LLM_MODEL` | `deepseek-chat` | 模型名称 |
| `LLM_API_KEY` | - | API密钥 |
| `LLM_BASE_URL` | - | 自定义API地址 |
| `EMBEDDING_MODEL_NAME` | `BAAI/bge-m3` | Embedding模型 |
| `EMBEDDING_DEVICE` | `cpu` | 运行设备 (cpu/cuda) |
| `QDRANT_HOST` | `localhost` | Qdrant地址 |
| `QDRANT_PORT` | `6333` | Qdrant HTTP端口 |
| `QDRANT_USE_MEMORY` | `false` | 内存模式 |
| `CHUNK_SIZE` | `1024` | 文档分块大小 |
| `CHUNK_OVERLAP` | `200` | 分块重叠字符数 |
| `RETRIEVAL_TOP_K` | `20` | 检索返回数量 |
| `RERANK_TOP_N` | `5` | 重排序返回数量 |
| `BM25_WEIGHT` | `0.3` | BM25检索权重 |
| `DENSE_WEIGHT` | `0.7` | 向量检索权重 |

## 开发指南

### 添加新的文件类型加载器

1. 在 `src/data_loader/` 下创建新的 loader 文件
2. 继承 `BaseDocumentLoader`，实现 `lazy_load()` 和 `supports()` 方法
3. 使用 `@loader_registry.register(extensions=[".xxx"])` 装饰器注册
4. 在 `src/data_loader/__init__.py` 中导入

```python
from src.data_loader.base_loader import BaseDocumentLoader
from src.data_loader.loader_registry import loader_registry

@loader_registry.register(extensions=[".xlsx"])
class MyCustomLoader(BaseDocumentLoader):
    def lazy_load(self):
        # 实现加载逻辑
        yield Document(page_content=..., metadata=...)

    @classmethod
    def supports(cls, file_path):
        return file_path.suffix.lower() == ".xlsx"
```

### 切换 LLM 提供商

只需修改 `.env` 中的三个变量即可：

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
LLM_API_KEY=sk-xxx
```

支持的 provider：`deepseek`, `openai`, `anthropic`, `ollama`, `together`, `fireworks` 等。

### 调整检索策略

在 `ensemble_retriever.py` 中可配置：
- `hybrid_method`: `"rrf"`（推荐）或 `"weighted"`
- `dense_weight` / `sparse_weight`: 加权融合的权重
- `rerank_enabled`: 是否启用重排序
- `rerank_threshold`: 重排序过滤阈值

## 依赖安装

```bash
# 基础安装
uv sync

# 带OCR支持
uv sync --extra ocr

# 带所有文档格式支持（包括unstructured）
uv sync --extra all-docs

# 开发模式（含测试工具）
uv sync --group dev
```

## License

MIT
