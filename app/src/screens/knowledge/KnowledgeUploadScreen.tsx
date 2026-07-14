// ============================================================
// 知识库文件上传页
// ============================================================
import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Alert,
} from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import { knowledgeApi } from '../../api/knowledge';
import { Button } from '../../components/ui/Button';
import type { KnowledgeUploadResponse } from '../../types/knowledge';

const ALLOWED_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  'application/vnd.ms-powerpoint',
  'text/plain',
  'text/csv',
];

const TYPE_LABELS: Record<string, string> = {
  pdf: '📄 PDF',
  docx: '📝 Word',
  xlsx: '📊 Excel',
  pptx: '📽️ PPT',
  txt: '📃 文本',
  csv: '📋 CSV',
};

export function KnowledgeUploadScreen() {
  const [selectedFile, setSelectedFile] =
    useState<DocumentPicker.DocumentPickerResult | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<KnowledgeUploadResponse | null>(null);

  const handlePick = async () => {
    try {
      const res = await DocumentPicker.getDocumentAsync({
        type: ALLOWED_TYPES,
        copyToCacheDirectory: true,
      });
      if (!res.canceled && res.assets?.length > 0) {
        setSelectedFile(res);
        setResult(null);
      }
    } catch {
      Alert.alert('选择失败', '无法访问文件选择器');
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || selectedFile.canceled || !selectedFile.assets?.[0])
      return;

    const asset = selectedFile.assets[0];
    setUploading(true);
    setProgress(0);

    try {
      const res = await knowledgeApi.upload(
        asset.uri,
        asset.name,
        asset.mimeType || 'application/octet-stream',
        (pct) => setProgress(pct),
      );
      setResult(res);
      setSelectedFile(null);
    } catch (e: any) {
      const msg =
        e?.response?.data?.detail || e?.message || '上传失败，请稍后重试';
      Alert.alert('上传失败', msg);
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  const asset = selectedFile?.assets?.[0];

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
    >
      {/* 选择文件区域 */}
      <TouchableOpacity
        style={[styles.pickZone, styles.cardShadow]}
        onPress={handlePick}
        activeOpacity={0.7}
        disabled={uploading}
      >
        {asset ? (
          <View style={styles.fileInfo}>
            <Text style={styles.fileIcon}>
              {TYPE_LABELS[asset.name?.split('.').pop()?.toLowerCase() || ''] || '📎'}
            </Text>
            <Text style={styles.fileName} numberOfLines={2}>
              {asset.name}
            </Text>
            <Text style={styles.fileSize}>
              {asset.size != null
                ? asset.size > 1024 * 1024
                  ? `${(asset.size / 1024 / 1024).toFixed(1)} MB`
                  : `${Math.round(asset.size / 1024)} KB`
                : '大小未知'}
            </Text>
            <Text style={styles.changeHint}>点击更换文件</Text>
          </View>
        ) : (
          <View style={styles.pickPlaceholder}>
            <Text style={styles.pickIcon}>📤</Text>
            <Text style={styles.pickText}>点击选择文件</Text>
            <Text style={styles.pickHint}>
              支持 PDF / Word / Excel / PPT / TXT / CSV
            </Text>
          </View>
        )}
      </TouchableOpacity>

      {/* 上传进度 */}
      {uploading && (
        <View style={styles.progressCard}>
          <Text style={styles.progressText}>上传中... {progress}%</Text>
          <View style={styles.progressBar}>
            <View
              style={[styles.progressFill, { width: `${progress}%` }]}
            />
          </View>
        </View>
      )}

      {/* 上传按钮 */}
      <Button
        title={uploading ? '上传中...' : '上传到知识库'}
        variant="primary"
        size="lg"
        disabled={!asset || uploading}
        loading={uploading}
        style={styles.uploadBtn}
        onPress={handleUpload}
      />

      {/* 结果卡片 */}
      {result && (
        <View style={[styles.resultCard, styles.cardShadow]}>
          <Text style={styles.resultTitle}>✅ 上传成功</Text>
          <ResultRow label="文件名" value={result.filename} />
          <ResultRow label="分类" value={result.category} />
          <ResultRow label="类型" value={result.type?.toUpperCase()} />
          <ResultRow label="文本块" value={`${result.chunks} 块`} />
          <ResultRow label="大小" value={`${result.size_kb} KB`} />
          {result.courses?.length > 0 && (
            <ResultRow label="关联课程" value={result.courses.join(', ')} />
          )}
        </View>
      )}

      <Text style={styles.note}>
        💡 上传的文档将自动分类并向量化，之后可通过 AI 对话或搜索功能查询
      </Text>
    </ScrollView>
  );
}

function ResultRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.resultRow}>
      <Text style={styles.resultLabel}>{label}</Text>
      <Text style={styles.resultValue} numberOfLines={2}>
        {value}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  content: { padding: 16, paddingTop: 12 },
  pickZone: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 32,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 180,
    marginBottom: 16,
  },
  cardShadow: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  pickPlaceholder: { alignItems: 'center' },
  pickIcon: { fontSize: 48, marginBottom: 12 },
  pickText: { fontSize: 17, fontWeight: '600', color: '#111827' },
  pickHint: {
    fontSize: 13,
    color: '#9CA3AF',
    marginTop: 6,
    textAlign: 'center',
  },
  fileInfo: { alignItems: 'center' },
  fileIcon: { fontSize: 40, marginBottom: 10 },
  fileName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    textAlign: 'center',
  },
  fileSize: { fontSize: 13, color: '#9CA3AF', marginTop: 4 },
  changeHint: {
    fontSize: 12,
    color: '#0880D7',
    marginTop: 10,
    textDecorationLine: 'underline',
  },
  progressCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  progressText: { fontSize: 14, color: '#111827', marginBottom: 8 },
  progressBar: {
    height: 6,
    backgroundColor: '#F3F4F6',
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#0880D7',
    borderRadius: 3,
  },
  uploadBtn: { width: '100%', marginBottom: 16 },
  resultCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  resultTitle: { fontSize: 17, fontWeight: '600', color: '#111827', marginBottom: 14 },
  resultRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 0.5,
    borderBottomColor: '#F3F4F6',
  },
  resultLabel: { fontSize: 13, color: '#6B7280' },
  resultValue: { fontSize: 13, color: '#111827', fontWeight: '500', flex: 1, textAlign: 'right', marginLeft: 12 },
  note: {
    fontSize: 13,
    color: '#9CA3AF',
    lineHeight: 19,
    textAlign: 'center',
    marginTop: 8,
    paddingHorizontal: 16,
  },
});
