// ============================================================
// 空闲教室查询页
// ============================================================
import React, { useCallback, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { classroomsApi, type ClassroomItem } from '../../api/classrooms';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { EmptyState } from '../../components/ui/EmptyState';

const WEEKDAYS = [
  { value: undefined, label: '全部' },
  { value: 1, label: '周一' },
  { value: 2, label: '周二' },
  { value: 3, label: '周三' },
  { value: 4, label: '周四' },
  { value: 5, label: '周五' },
  { value: 6, label: '周六' },
  { value: 7, label: '周日' },
];

const BUILDINGS = ['全部', '主教', '第一教学楼', '第二教学楼', '科教楼', '图书馆', '实验楼'];

function formatNode(n: number): string {
  const h = Math.floor((n - 1) / 2) + 1;
  const m = n % 2 === 1 ? '00' : '30';
  return `${h}:${m}`;
}

export function ClassroomsScreen() {
  const [weekDay, setWeekDay] = useState<number | undefined>();
  const [building, setBuilding] = useState<string>('');
  const [buildingIdx, setBuildingIdx] = useState(0);

  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['classrooms', weekDay, building],
    queryFn: () =>
      classroomsApi.getClassrooms(
        weekDay,
        building || undefined,
      ),
  });

  const classrooms = data?.data || [];

  return (
    <View style={styles.container}>
      {/* 星期筛选 */}
      <FlatList
        horizontal
        style={styles.filterRow}
        contentContainerStyle={styles.filterContent}
        showsHorizontalScrollIndicator={false}
        data={WEEKDAYS}
        keyExtractor={(item) => String(item.value ?? 'all')}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[
              styles.filterChip,
              weekDay === item.value && styles.filterChipActive,
            ]}
            onPress={() => setWeekDay(item.value)}
          >
            <Text
              style={[
                styles.filterText,
                weekDay === item.value && styles.filterTextActive,
              ]}
            >
              {item.label}
            </Text>
          </TouchableOpacity>
        )}
      />

      {/* 教学楼筛选 */}
      <FlatList
        horizontal
        style={styles.buildingRow}
        contentContainerStyle={styles.filterContent}
        showsHorizontalScrollIndicator={false}
        data={BUILDINGS}
        keyExtractor={(item) => item}
        renderItem={({ item, index }) => (
          <TouchableOpacity
            style={[
              styles.filterChip,
              buildingIdx === index && styles.filterChipActive,
            ]}
            onPress={() => {
              setBuildingIdx(index);
              setBuilding(index === 0 ? '' : item);
            }}
          >
            <Text
              style={[
                styles.filterText,
                buildingIdx === index && styles.filterTextActive,
              ]}
            >
              {item}
            </Text>
          </TouchableOpacity>
        )}
      />

      {/* 结果 */}
      {isLoading ? (
        <LoadingSpinner />
      ) : (
        <FlatList
          style={styles.list}
          contentContainerStyle={
            classrooms.length === 0 ? styles.empty : styles.listContent
          }
          data={classrooms}
          keyExtractor={(item, i) =>
            `${item.building}-${item.room_no}-${item.week_day}-${i}`
          }
          onRefresh={refetch}
          refreshing={isRefetching}
          ListEmptyComponent={
            <EmptyState
              icon="🏫"
              title="暂无可选教室"
              description="换个筛选条件试试"
            />
          }
          renderItem={({ item }) => (
            <View style={styles.card}>
              <View style={styles.cardHeader}>
                <Text style={styles.roomName}>
                  {item.building} {item.room_no}
                </Text>
                <View style={styles.capacityBadge}>
                  <Text style={styles.capacityText}>{item.capacity} 座</Text>
                </View>
              </View>
              <View style={styles.cardBody}>
                <Text style={styles.detailText}>
                  📍 {item.campus || '未知校区'}
                </Text>
                <Text style={styles.detailText}>
                  🕐 第{item.start_node}-{item.end_node}节 ({formatNode(item.start_node)}-{formatNode(item.end_node + 1)})
                </Text>
                <Text
                  style={[
                    styles.statusText,
                    {
                      color:
                        item.status === '空闲' || !item.status
                          ? '#059669'
                          : '#DC2626',
                    },
                  ]}
                >
                  {item.status || '空闲'}
                </Text>
              </View>
            </View>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  filterRow: {
    maxHeight: 44,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 0.5,
    borderBottomColor: '#F3F4F6',
  },
  buildingRow: {
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
  card: {
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
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  roomName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    flex: 1,
  },
  capacityBadge: {
    backgroundColor: '#EFF6FF',
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 8,
  },
  capacityText: { fontSize: 12, color: '#0880D7', fontWeight: '500' },
  cardBody: { gap: 4 },
  detailText: { fontSize: 13, color: '#6B7280' },
  statusText: { fontSize: 13, fontWeight: '600', marginTop: 4 },
});
