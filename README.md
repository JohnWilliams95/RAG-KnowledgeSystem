# RAG-KnowledgeSystem

基于 LangChain + LangGraph + Qdrant + BGE-M3 构建的金属冶炼领域 RAG 知识库问答系统，支持多格式文档解析、语义分块、混合检索与智能问答。

## 效果展示
<img width="1920" height="1032" alt="RAGKnowledg1" src="https://github.com/user-attachments/assets/5f924797-3c82-4249-a8ca-6b6602ceb440" />
<img width="1920" height="953" alt="RAGKnowledg2" src="https://github.com/user-attachments/assets/e99bafe6-0c26-4135-bf06-6211497af74e" />

<img width="1920" height="953" alt="RAGKnowledg3" src="https://github.com/user-attachments/assets/2ff476e9-d532-4b58-88f2-3e168b459f00" />

## 技术栈

| 层级 | 技术选型 | 选型理由 |
|------|---------|---------|
| 框架 | LangChain + LangGraph |  RAG 编排框架，支持有状态工作流 |
| Embedding | BAAI/bge-m3（本地部署） | 1024维、多语言SOTA、支持稀疏+稠密双向量 |
| 向量库 | Qdrant（本地部署） | Rust高性能，原生混合检索，数据持久化 |
| 重排序 | BGE-Reranker-v2-m3（本地部署） | Cross-Encoder 精排，提升检索准确率 |
| 多路召回 | Dense + BM25 + RRF 融合 | BGE-M3双向量 + rank_bm25 + Qdrant原生融合 |
| Query重写 | Multi-Query + HyDE + Step-Back + QueryDecomposition | 多策略查询增强，提升检索覆盖率 |
| 后端 | FastAPI | 高性能、类型安全、自动生成API文档 |
| 前端 | React | 高性能、流式输出 |
| 评测 | RAGAS + 自建评估指标 | RAG专用评测框架 + 多维度检索指标 |
| 包管理 | uv | Rust编写，极速依赖解析 |

## 项目结构

```
RAG-KnowledgeSystem/
├── pyproject.toml                 # uv项目配置
├── .env                           # 环境变量配置
├── README.md
│
├── backend/
│   ├── src/
│   │   ├── config/                    # 配置层
│   │   │   ├── settings.py            # Pydantic Settings 全局配置
│   │   │   └── constants.py           # 常量定义（文件类型、状态枚举）
│   │   │
│   │   ├── data_loader/               # 数据加载层（31种文件类型）
│   │   │   ├── base_loader.py         # 加载器抽象基类
│   │   │   ├── loader_registry.py     # 加载器注册中心（工厂模式）
│   │   │   ├── pdf_loader.py          # PDF（PyMuPDF + RapidOCR + 表格/图片提取）
│   │   │   ├── word_loader.py         # Word/docx（python-docx）
│   │   │   ├── excel_loader.py        # Excel/xlsx/csv（pandas + openpyxl）
│   │   │   ├── ppt_loader.py          # PPT/pptx（python-pptx）
│   │   │   ├── image_loader.py        # 图片OCR（RapidOCR + 多模态LLM）
│   │   │   ├── markdown_loader.py     # Markdown（保留层级结构）
│   │   │   ├── text_loader.py         # 纯文本/txt/log/rst
│   │   │   ├── html_loader.py         # HTML网页（html2text + BeautifulSoup）
│   │   │   ├── code_loader.py         # 代码文件（多语言语法感知）
│   │   │   ├── structured_loader.py   # JSON/YAML结构化数据
│   │   │   └── web_scraper.py         # 网页爬取（httpx + BeautifulSoup）
│   │   │
│   │   ├── splitting/                 # 文档分割层
│   │   │   ├── base_splitter.py       # 分割器抽象基类
│   │   │   ├── semantic_splitter.py   # 语义分割（BGE-M3 embedding）
│   │   │   ├── recursive_splitter.py  # 递归分割（LangChain）
│   │   │   ├── fixed_splitter.py      # 固定长度分割
│   │   │   ├── paragraph_splitter.py  # 段落分割
│   │   │   ├── heading_splitter.py    # 标题分割（Markdown/RST）
│   │   │   ├── code_splitter.py       # 代码分割（语法感知）
│   │   │   └── splitter_factory.py    # 分割器工厂（自动识别文档类型）
│   │   │
│   │   ├── embedding/                 # 向量化层
│   │   │   ├── bge_embedding.py       # BGE-M3稠密向量 + 稀疏向量
│   │   │   ├── sparse_embedding.py    # 稀疏向量生成（BM25风格）
│   │   │   └── embedding_cache.py     # Embedding缓存（SHA256哈希索引）
│   │   │
│   │   ├── ingestion/                 # 数据入库层
│   │   │   ├── document_store.py      # Qdrant向量库管理
│   │   │   ├── metadata_store.py      # SQLite元数据管理
│   │   │   └── pipeline.py            # 完整入库流水线（并行处理）
│   │   │
│   │   ├── retrieval/                 # 检索层
│   │   │   ├── vector_retriever.py    # 向量检索（dense + sparse）
│   │   │   ├── bm25_retriever.py      # BM25关键词检索（rank_bm25）
│   │   │   ├── hybrid_retriever.py    # 混合检索（RRF融合/加权融合）
│   │   │   ├── reranker.py            # 重排序（BGE-Reranker-v2-m3）
│   │   │   └── ensemble_retriever.py  # 融合检索器（多路召回+重排序）
│   │   │
│   │   ├── query_rewriting/           # Query改写层
│   │   │   ├── query_rewriter.py      # LLM驱动的Query重写 + 意图分类
│   │   │   ├── query_decomposer.py    # 复杂问题分解（Multi-Query）
│   │   │   ├── hyde_generator.py      # HyDE（假设文档嵌入）
│   │   │   └── stepback_prompt.py     # Step-Back Prompting
│   │   │
│   │   ├── generation/                # 生成层
│   │   │   ├── rag_chain.py           # 核心RAG链（LangGraph StateGraph编排）
│   │   │   ├── context_builder.py     # 上下文构建与压缩
│   │   │   ├── prompt_templates.py    # Prompt模板管理（多风格）
│   │   │   └── response_synthesizer.py# 响应合成（compact/refine/tree_summarize）
│   │   │
│   │   ├── memory/                    # 对话记忆层
│   │   │   └── conversation_memory.py # 对话历史管理 + 问题压缩
│   │   │
│   │   ├── evaluation/                # 评测层
│   │   │   ├── retrieval_metrics.py   # 检索指标（Hit Rate/MRR/NDCG/Precision/Recall）
│   │   │   └── ragas_eval.py          # RAGAS框架评测
│   │   │
│   │   ├── utils/                     # 工具层
│   │   │   └── ocr_utils.py           # RapidOCR工具（支持中英文）
│   │   │
│   │   └── api/                       # API层（FastAPI）
│   │       ├── main.py                # FastAPI入口 + 生命周期管理
│   │       ├── dependencies.py        # 依赖注入（单例模式）
│   │       └── routes/
│   │           ├── chat.py            # 对话路由（支持流式SSE）
│   │           ├── document.py        # 文档管理路由（上传/入库/删除）
│   │           ├── retrieval.py       # 检索路由（dense/sparse/hybrid）
│   │           └── knowledge_base.py  # 知识库管理路由
│   │
│   ├── scripts/                       # 运维脚本
│   │
│   ├── data/                          # 数据目录
│   │   ├── uploads/                   # 上传的文档
│   │   └── metadata.db               # SQLite元数据数据库
│   │
│   ├── models/                        # 本地模型目录
│   │   ├── bge-m3/                    # BGE-M3 Embedding模型
│   │   └── bge-reranker-v2-m3/        # BGE-Reranker重排序模型
│   │
│   └── cache/                         # 缓存目录
│       ├── embeddings/                # Embedding缓存
│       └── bm25/                      # BM25索引缓存
│
└── frontend/                          # 前端（React + Ant Design）
```

## 核心处理流程

```
用户 Query
    │
    ▼
┌──────────────────────────────────┐
│  1. 意图分类（两层策略）          │
│  ├── 规则快速过滤（正则匹配）     │
│  └── LLM准确判断                 │
└──────────────┬───────────────────┘
               │ "retrieve" 或 "chat"
               ▼
┌──────────────────────────────────┐
│  2. Query 重写层（LLM驱动）      │
│  ├── Multi-Query：多角度改写      │
│  ├── Query Decompose：子问题分解  │
│  ├── HyDE：生成假设文档           │
│  └── Step-Back：回溯背景问题      │
└──────────────┬───────────────────┘
               │ 多个改写 Query
               ▼
┌──────────────────────────────────┐
│  3. 多路召回层（并行执行）        │
│  ┌─────────┐   ┌─────────┐      │
│  │Dense检索 │   │Sparse检索│      │
│  │(BGE-M3)  │   │(BM25)    │      │
│  └────┬────┘   └────┬────┘      │
│       └──────┬──────┘            │
│              ▼                   │
│        RRF / 加权融合             │
└──────────────┬───────────────────┘
               │ Top-K 候选文档
               ▼
┌──────────────────────────────────┐
│  4. 重排序层                      │
│  BGE-Reranker-v2-m3 Cross-Encoder│
│  精排 + 阈值过滤                  │
└──────────────┬───────────────────┘
               │ Top-N 精排结果
               ▼
┌──────────────────────────────────┐
│  5. 上下文构建层                  │
│  去重 → 相关性过滤 → 元数据注入   │
│  → 贪心填充 → 长度截断            │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│  6. 响应合成层                    │
│  LLM + RAG Prompt（多风格可选）   │
│  支持 compact / refine /         │
│  tree_summarize 三种模式          │
│  引用标注 + 流式输出              │
└──────────────┬───────────────────┘
               │
               ▼
            用户回答
```

## 数据层支持的文件类型

| 类型 | 扩展名 | 解析方案 |
|------|--------|----------|
| PDF | `.pdf` | PyMuPDF + RapidOCR(扫描件) + 表格/图片提取 |
| Word | `.docx` `.doc` | python-docx + antiword(.doc) |
| Excel | `.xlsx` `.xls` `.csv` | openpyxl + pandas |
| PPT | `.pptx` `.ppt` | python-pptx |
| 图片 | `.png` `.jpg` `.jpeg` `.bmp` `.tiff` `.tif` | RapidOCR |
| Markdown | `.md` | 正则解析（保留层级结构） |
| 纯文本 | `.txt` `.log` `.rst` | 直接读取 |
| HTML | `.html` `.htm` | html2text + BeautifulSoup |
| 代码 | `.py` `.js` `.ts` `.tsx` `.java` `.go` `.rs` `.cpp` `.c` `.h` | 语法感知分割器 |
| JSON/YAML | `.json` `.yaml` `.yml` | 结构化文档加载器 |

## 检索效果评估

### 评估结果

| 指标 | 值 | 说明 |
|------|-----|------|
| Hit Rate | 1.0000 | 所有查询都命中相关文档 |
| MRR | 1.0000 | 相关文档总是排在第1位 |
| Recall@1 | 0.9000 | 90%的问题在第1位找到全部相关文档 |
| Recall@5 | 0.9000 | 前5个结果覆盖全部相关文档 |
| NDCG@5 | 1.0000 | 排序质量完美 |
| 平均检索耗时 | 3.23s | 包含首次模型加载 |

### 运行评估

```bash
# 执行检索效果评估
python scripts/evaluate_retrieval.py --output scripts/output/results.json

# 参数说明
# --dataset: 测试数据集路径（默认 scripts/test_dataset.json）
# --top-k: 检索返回数量（默认20）
# --output: 结果输出文件路径
```

## 快速开始

### 1. 环境准备

```bash
# 安装 uv（如未安装）
pip install uv

# 克隆项目
git clone <repo-url>
cd RAG-KnowledgeSystem/backend

# 创建虚拟环境并安装依赖
uv sync

# 复制环境变量配置
cp .env.example .env
# 编辑 .env 填入你的配置
```

### 2. 下载本地模型

```bash
# 首次运行会自动从 ModelScope 下载模型
# BGE-M3 Embedding 模型（约2GB）
# BGE-Reranker-v2-m3 重排序模型（约1GB）
# 模型保存在 backend/models/ 目录下
```

### 3. 启动 Qdrant

```bash
# 方式1：本地部署（推荐）
# 下载 Qdrant 到 C:\qdrant\ 目录
# 启动服务
C:\qdrant\qdrant.exe

# 方式2：Docker
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest

# 方式3：内存模式（测试用）
# 在 .env 中设置 QDRANT_USE_MEMORY=true
```

### 4. 配置环境变量

编辑 `.env` 文件：

```env
# LLM配置
LLM_API_KEY=your_api_key
LLM_BASE_URL=your_base_url
LLM_MODEL=mimo-v2.5-pro

# Embedding配置（本地模型）
EMBEDDING_MODEL_NAME=./models/bge-m3
EMBEDDING_DEVICE=cuda

# 重排序配置（本地模型）
RERANKER_MODEL=./models/bge-reranker-v2-m3
RERANKER_DEVICE=cuda

# Qdrant配置
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_USE_MEMORY=false

# 检索参数
CHUNK_SIZE=1024
CHUNK_OVERLAP=200
RETRIEVAL_TOP_K=20
RERANK_TOP_N=5
DENSE_WEIGHT=0.7
BM25_WEIGHT=0.3
```

### 5. 初始化知识库

```bash
# 将文档放入 data/uploads/ 目录
# 通过API上传文档
curl -X POST http://localhost:8000/api/v1/documents/ingest/upload \
  -F "file=@document.pdf"
```

### 6. 启动服务

```bash
python -m src.api.main
# 或
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
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

# 删除文档
curl -X DELETE http://localhost:8000/api/v1/documents/ \
  -H "Content-Type: application/json" \
  -d '{"file_path": "data/uploads/document.pdf"}'
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

# 查看文档列表
curl http://localhost:8000/api/v1/knowledge-base/documents
```

## 环境变量说明

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_API_KEY` | - | API密钥 |
| `LLM_BASE_URL` | - | API地址 |
| `LLM_MODEL` | `your_model` | 模型名称 |
| `EMBEDDING_MODEL_NAME` | `./models/bge-m3` | Embedding模型路径 |
| `EMBEDDING_DEVICE` | `cpu` | 运行设备 (cpu/cuda) |
| `EMBEDDING_USE_FP16` | `false` | 半精度加速 |
| `EMBEDDING_BATCH_SIZE` | `32` | 批处理大小 |
| `RERANKER_MODEL` | `./models/bge-reranker-v2-m3` | 重排序模型路径 |
| `RERANKER_DEVICE` | `cpu` | 重排序设备 (cpu/cuda) |
| `QDRANT_HOST` | `localhost` | Qdrant地址 |
| `QDRANT_PORT` | `6333` | Qdrant HTTP端口 |
| `QDRANT_USE_MEMORY` | `false` | 内存模式 |
| `CHUNK_SIZE` | `1024` | 文档分块大小 |
| `CHUNK_OVERLAP` | `200` | 分块重叠字符数 |
| `SEMANTIC_CHUNKING_ENABLED` | `true` | 启用语义分块 |
| `RETRIEVAL_TOP_K` | `20` | 检索返回数量 |
| `RERANK_TOP_N` | `5` | 重排序返回数量 |
| `BM25_WEIGHT` | `0.3` | BM25检索权重 |
| `DENSE_WEIGHT` | `0.7` | 向量检索权重 |

## 开发指南

### 添加新的文件类型加载器

1. 在 `src/data_loader/` 下创建新的 loader 文件
2. 继承 `BaseDocumentLoader`，实现 `lazy_load()` 和 `supports()` 方法
3. 使用 `@loader_registry.register(extensions=[".xxx"])` 装饰器注册

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

### 调整检索策略

在 `.env` 中可配置：
- `DENSE_WEIGHT` / `BM25_WEIGHT`: 加权融合的权重
- `RETRIEVAL_TOP_K`: 检索返回数量
- `RERANK_TOP_N`: 重排序返回数量

## License

MIT
