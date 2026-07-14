// ============================================================
// 知识库相关类型定义 (P4.6)
// ============================================================

/** 知识库文件信息 */
export interface KnowledgeFile {
  filename: string;
  category: string;
  file_type?: string;
  pages?: number;
  size_kb?: number;
  chunks?: number;
  count?: number;
  ingested_at?: string;
}

/** 知识库统计 */
export interface KnowledgeStats {
  total_chunks: number;
  total_sources: number;
  sources: KnowledgeFile[];
  categories: Record<string, number>;
}

/** 文件列表响应 */
export interface KnowledgeFileListResponse {
  data: KnowledgeFile[];
}

/** 知识库搜索结果 */
export interface KnowledgeSearchResult {
  text: string;
  source: string;
  category: string;
  distance: number;
}

/** 搜索响应 */
export interface KnowledgeSearchResponse {
  query: string;
  total: number;
  results: KnowledgeSearchResult[];
}

/** 上传响应 */
export interface KnowledgeUploadResponse {
  status: 'ok' | 'error';
  filename: string;
  type: string;
  pages: number;
  chunks: number;
  category: string;
  courses: string[];
  size_kb: number;
  error?: string;
}

/** 搜索请求体 */
export interface KnowledgeSearchRequest {
  query: string;
  top_k?: number;
  category?: string;
}
