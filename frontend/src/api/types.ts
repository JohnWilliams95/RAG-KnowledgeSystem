export interface ChatRequest {
  question: string
  conversation_id?: string
  enable_query_rewriting?: boolean
  enable_reranking?: boolean
  enable_hyde?: boolean
  enable_stepback?: boolean
  enable_decomposition?: boolean
  prompt_style?: 'concise' | 'detailed' | 'academic'
  top_k?: number
  rerank_top_n?: number
}

export interface ChatResponse {
  question: string
  answer: string
  conversation_id: string
  rewritten_queries: string[]
  num_documents: number
  context_length: number
  metadata: Record<string, unknown>
}

export interface ChatStreamEvent {
  event_type: string
  data: string
  metadata?: Record<string, unknown>
}

export interface IngestResponse {
  status: string
  doc_id?: string
  documents_loaded: number
  chunks_created: number
  point_ids?: string[]
  message?: string
}

export interface IngestDirectoryResponse {
  status: string
  total_files: number
  total_chunks: number
  errors: number
  results?: Record<string, unknown>[]
}

export interface DocumentInfo {
  doc_id: string
  file_name: string
  file_type: string
  file_size: number
  chunk_count: number
  status: string
  created_at: string
}

export interface KnowledgeBaseInfo {
  collection_name: string
  exists: boolean
  points_count: number | null
  vectors_count: number | null
  status: string | null
}

export interface KnowledgeBaseStats {
  collection: {
    exists: boolean
    points_count: number | null
    vectors_count: number | null
    status: string | null
  }
  total_documents: number
}

export interface RetrievedDocument {
  page_content: string
  metadata: Record<string, unknown>
  score?: number
  rerank_score?: number
}

export interface RetrievalResponse {
  query: string
  documents: RetrievedDocument[]
  total: number
}

export interface HealthResponse {
  status: string
  version: string
  qdrant_connected: boolean
}
