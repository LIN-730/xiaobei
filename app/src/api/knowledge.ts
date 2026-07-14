// ============================================================
// 知识库 API — /api/v1/knowledge/*
// ============================================================
import apiClient from './client';
import type {
  KnowledgeFileListResponse,
  KnowledgeStats,
  KnowledgeSearchRequest,
  KnowledgeSearchResponse,
  KnowledgeUploadResponse,
} from '../types/knowledge';

export const knowledgeApi = {
  /** 上传文件到知识库 */
  upload(
    fileUri: string,
    fileName: string,
    mimeType: string,
    onProgress?: (pct: number) => void,
  ): Promise<KnowledgeUploadResponse> {
    const formData = new FormData();
    formData.append('file', {
      uri: fileUri,
      name: fileName,
      type: mimeType,
    } as any);

    return apiClient
      .post('/knowledge/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (event) => {
          if (onProgress && event.total) {
            onProgress(Math.round((event.loaded * 100) / event.total));
          }
        },
      })
      .then((r) => r.data);
  },

  /** 列出已索引文件 */
  getFiles(): Promise<KnowledgeFileListResponse> {
    return apiClient.get('/knowledge/files').then((r) => r.data);
  },

  /** 删除文件 */
  deleteFile(filename: string): Promise<void> {
    return apiClient
      .delete(`/knowledge/files/${encodeURIComponent(filename)}`)
      .then((r) => r.data);
  },

  /** 获取知识库统计 */
  getStats(): Promise<KnowledgeStats> {
    return apiClient.get('/knowledge/stats').then((r) => r.data);
  },

  /** 语义搜索 */
  search(body: KnowledgeSearchRequest): Promise<KnowledgeSearchResponse> {
    return apiClient.post('/knowledge/search', body).then((r) => r.data);
  },
};
