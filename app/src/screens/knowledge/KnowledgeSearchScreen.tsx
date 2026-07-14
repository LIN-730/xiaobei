// ============================================================
// 知识库搜索页
// ============================================================
import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Keyboard,
} from 'react-native';
import { knowledgeApi } from '../../api/knowledge';
import { Button } from '../../components/ui/Button';
import { EmptyState } from '../../components/ui/EmptyState';
import type { KnowledgeSearchResult } from '../../types/knowledge';

const CATEGORIES = [
  { key: '', label: '全部' },
  { key: '培养方案', label: '培养方案' },
  { key: '课程资料', label: '课程资料' },
  { key: '考试资料', label: '考试资料' },
  { key: '课件PPT', label: '课件PPT' },
  { key: '其他', label: '其他' },
];

export function KnowledgeSearchScreen() {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<KnowledgeSearchResult[]>([]);
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    Keyboard.dismiss();
    setSearching(true);
    setSearched(true);
    try {
      const res = await knowledgeApi.search({
        query: query.trim(),
        top_k: 10,
        category: category || undefined,
      });
      setResults(res.results || []);
    } catch {
      setResults([]);
    } finally {
      setSearching(false);
    }
  };

  return (
    <View style={styles.container}>
      {/* 搜索栏 */}
      <View style={styles.searchBar}>
        <TextInput
          style={styles.input}
          placeholder="输入关键词搜索知识库..."
          placeholderTextColor="#9CA3AF"
          value={query}
          onChangeText={setQuery}
          onSubmitEditing={handleSearch}
          returnKeyType="search"
        />
        <Button
          title="搜索"
          variant="primary"
          size="sm"
          loading={searching}
          disabled={!query.trim() || searching}
          onPress={handleSearch}
          style={styles.searchBtn}
        />
      </View>

      {/* 分类筛选 */}
      <FlatList
        horizontal
        style={styles.filterRow}
        contentContainerStyle={styles.filterContent}
        showsHorizontalScrollIndicator={false}
        data={CATEGORIES}
        keyExtractor={(item) => item.key}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[
              styles.filterChip,
              category === item.key && styles.filterChipActive,
            ]}
            onPress={() => setCategory(item.key)}
          >
            <Text
              style={[
                styles.filterText,
                category === item.key && styles.filterTextActive,
              ]}
            >
              {item.label}
            </Text>
          </TouchableOpacity>
        )}
      />

      {/* 结果列表 */}
      <FlatList
        style={styles.list}
        contentContainerStyle={
          results.length === 0 ? styles.empty : styles.listContent
        }
        data={results}
        keyExtractor={(_, i) => i.toString()}
        ListEmptyComponent={
          searched ? (
            <EmptyState icon="🔍" title="未找到相关结果" description="换个关键词试试" />
          ) : null
        }
        renderItem={({ item }) => (
          <View style={styles.resultCard}>
            <Text style={styles.snippet} numberOfLines={5}>
              {item.text}
            </Text>
            <View style={styles.resultMeta}>
              <Text style={styles.source} numberOfLines={1}>
                📄 {item.source}
              </Text>
              <Text style={styles.distance}>
                相似度: {(1 - item.distance).toFixed(2)}
              </Text>
            </View>
            {item.category && (
              <View style={styles.categoryBadge}>
                <Text style={styles.categoryText}>{item.category}</Text>
              </View>
            )}
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  searchBar: {
    flexDirection: 'row',
    padding: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 0.5,
    borderBottomColor: '#E5E7EB',
  },
  input: {
    flex: 1,
    backgroundColor: '#F3F4F6',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 15,
    color: '#111827',
    marginRight: 10,
  },
  searchBtn: { minWidth: 70 },
  filterRow: {
    maxHeight: 44,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 0.5,
    borderBottomColor: '#E5E7EB',
  },
  filterContent: { paddingHorizontal: 12, alignItems: 'center' },
  filterChip: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#F3F4F6',
    marginRight: 8,
  },
  filterChipActive: { backgroundColor: '#0880D7' },
  filterText: { fontSize: 13, color: '#6B7280' },
  filterTextActive: { color: '#FFFFFF', fontWeight: '500' },
  list: { flex: 1 },
  empty: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  listContent: { padding: 16 },
  resultCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 3,
    elevation: 1,
  },
  snippet: {
    fontSize: 14,
    color: '#374151',
    lineHeight: 21,
    marginBottom: 10,
  },
  resultMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  source: {
    fontSize: 12,
    color: '#0880D7',
    flex: 1,
    marginRight: 8,
  },
  distance: { fontSize: 12, color: '#9CA3AF' },
  categoryBadge: {
    alignSelf: 'flex-start',
    marginTop: 8,
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 8,
    backgroundColor: '#F3F4F6',
  },
  categoryText: { fontSize: 11, color: '#6B7280' },
});
