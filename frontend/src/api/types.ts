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
}

export interface IngestResponse {
  status: string
  doc_id?: string
  documents_loaded: number
  chunks_created: number
  point_ids?: string[]
  message?: string
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

export interface KnowledgeBaseStats {
  collection: {
    exists: boolean
    points_count: number | null
    vectors_count: number | null
    status: string | null
  }
  total_documents: number
}
