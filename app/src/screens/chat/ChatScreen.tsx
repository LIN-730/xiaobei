// ============================================================
// AI 聊天界面 — SSE 流式对话 + 消息历史
// ============================================================
import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Alert,
} from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { agentApi } from '../../api/agent';
import { connectSSE } from '../../api/sse';
import type { SSEConnection } from '../../api/sse';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import type {
  AgentMessage,
  ChatStackParamList,
  SSEMetaEvent,
  SSETokenEvent,
  SSEToolStartEvent,
  SSEToolEndEvent,
  SSEDoneEvent,
  SSEErrorEvent,
} from '../../types';

type Props = NativeStackScreenProps<ChatStackParamList, 'Chat'>;

// ============================================================
// 本地消息类型（扩展 AgentMessage，增加客户端状态）
// ============================================================

interface ChatMessage {
  /** 本地唯一 ID */
  localId: string;
  role: 'user' | 'assistant' | 'tool';
  content: string;
  toolName?: string;
  eventId?: number;
  isStreaming?: boolean;
  timestamp: number;
}

let localIdCounter = 0;
function nextLocalId(): string {
  localIdCounter += 1;
  return `msg_${Date.now()}_${localIdCounter}`;
}

// ============================================================
// 消息气泡组件
// ============================================================

interface BubbleProps {
  message: ChatMessage;
}

function MessageBubble({ message }: BubbleProps) {
  // ── 工具调用消息 ──
  if (message.role === 'tool') {
    return (
      <View style={bubbleStyles.toolContainer}>
        <View style={bubbleStyles.toolBubble}>
          <Text style={bubbleStyles.toolIcon}>🔧</Text>
          <Text style={bubbleStyles.toolText}>
            查询: {message.toolName || '未知工具'}
          </Text>
        </View>
      </View>
    );
  }

  // ── 用户 / AI 消息 ──
  const isUser = message.role === 'user';

  return (
    <View
      style={[
        bubbleStyles.row,
        isUser ? bubbleStyles.rowRight : bubbleStyles.rowLeft,
      ]}
    >
      {!isUser && (
        <View style={bubbleStyles.avatar}>
          <Text style={bubbleStyles.avatarText}>🤖</Text>
        </View>
      )}
      <View
        style={[
          bubbleStyles.bubble,
          isUser ? bubbleStyles.userBubble : bubbleStyles.assistantBubble,
        ]}
      >
        <Text
          style={[
            bubbleStyles.bubbleText,
            isUser ? bubbleStyles.userText : bubbleStyles.assistantText,
          ]}
        >
          {message.content}
          {message.isStreaming && <Text style={bubbleStyles.cursor}>▍</Text>}
        </Text>
      </View>
      {isUser && (
        <View style={bubbleStyles.avatar}>
          <Text style={bubbleStyles.avatarText}>👤</Text>
        </View>
      )}
    </View>
  );
}

const bubbleStyles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    marginVertical: 4,
    paddingHorizontal: 12,
    alignItems: 'flex-end',
  },
  rowRight: {
    justifyContent: 'flex-end',
  },
  rowLeft: {
    justifyContent: 'flex-start',
  },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: 18,
  },
  bubble: {
    maxWidth: '75%',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 18,
  },
  userBubble: {
    backgroundColor: '#0880D7',
    marginRight: 8,
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    backgroundColor: '#F3F4F6',
    marginLeft: 8,
    borderBottomLeftRadius: 4,
  },
  bubbleText: {
    fontSize: 15,
    lineHeight: 22,
  },
  userText: {
    color: '#FFFFFF',
  },
  assistantText: {
    color: '#1F2937',
  },
  cursor: {
    color: '#0880D7',
    fontWeight: '700',
  },
  // ── 工具消息 ──
  toolContainer: {
    alignItems: 'center',
    marginVertical: 6,
  },
  toolBubble: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#FDE68A',
  },
  toolIcon: {
    fontSize: 14,
    marginRight: 6,
  },
  toolText: {
    fontSize: 13,
    color: '#92400E',
    fontWeight: '500',
  },
});

// ============================================================
// ChatScreen 主组件
// ============================================================

export function ChatScreen({ route, navigation }: Props) {
  const { sessionKey: initialSessionKey, title: initialTitle } = route.params || {};

  // ── 状态 ──
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(!!initialSessionKey);
  const [historyHasMore, setHistoryHasMore] = useState(false);
  const [sessionKey, setSessionKey] = useState<string | null>(initialSessionKey || null);
  const [sessionTitle, setSessionTitle] = useState(initialTitle || '新对话');

  const sseRef = useRef<SSEConnection | null>(null);
  const flatListRef = useRef<FlatList<ChatMessage>>(null);
  const lastEventIdRef = useRef<number | null>(null);

  // ── 加载历史消息 ──
  useEffect(() => {
    if (!initialSessionKey) {
      setLoadingHistory(false);
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const res = await agentApi.getMessages(initialSessionKey, undefined, 50);
        if (cancelled) return;

        const loaded: ChatMessage[] = res.messages.map((m: AgentMessage) => ({
          localId: nextLocalId(),
          role: m.role,
          content: m.content || '',
          toolName: m.tool_name || undefined,
          eventId: m.event_id || undefined,
          isStreaming: false,
          timestamp: new Date(m.created_at).getTime(),
        }));

        setMessages(loaded);
        setHistoryHasMore(res.has_more);
        if (loaded.length > 0) {
          const lastMsg = loaded[loaded.length - 1];
          if (lastMsg.eventId) {
            lastEventIdRef.current = lastMsg.eventId;
          }
        }
      } catch {
        if (!cancelled) {
          Alert.alert('加载失败', '无法加载消息历史');
        }
      } finally {
        if (!cancelled) setLoadingHistory(false);
      }
    })();

    return () => { cancelled = true; };
  }, [initialSessionKey]);

  // ── 设置导航标题 ──
  useEffect(() => {
    navigation.setOptions({
      title: sessionTitle,
      headerBackTitle: '返回',
    });
  }, [navigation, sessionTitle]);

  // ── 清理 SSE 连接 ──
  useEffect(() => {
    return () => {
      sseRef.current?.abort();
    };
  }, []);

  // ── 自动滚动到底部 ──
  const scrollToBottom = useCallback((animated = true) => {
    if (flatListRef.current && messages.length > 0) {
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated });
      }, 100);
    }
  }, [messages.length]);

  // ── 发送消息 ──
  const handleSend = useCallback(async () => {
    const text = inputText.trim();
    if (!text || isStreaming) return;

    // 取消上一次 SSE（如果还在连接）
    sseRef.current?.abort();

    setInputText('');
    setIsStreaming(true);

    // 添加用户消息
    const userMsg: ChatMessage = {
      localId: nextLocalId(),
      role: 'user',
      content: text,
      timestamp: Date.now(),
    };

    // 添加空的 AI 消息（流式填充）
    const assistantMsg: ChatMessage = {
      localId: nextLocalId(),
      role: 'assistant',
      content: '',
      isStreaming: true,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);

    // ── 建立 SSE 连接 ──
    try {
      const conn = await connectSSE(
        { message: text, session_key: sessionKey || undefined },
        {
          onMeta: (evt: SSEMetaEvent) => {
            if (!sessionKey) {
              setSessionKey(evt.session_key);
              setSessionTitle((prev) => prev === '新对话' ? text.slice(0, 12) : prev);
            }
          },

          onToken: (evt: SSETokenEvent) => {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last && last.role === 'assistant') {
                updated[updated.length - 1] = {
                  ...last,
                  content: last.content + evt.content,
                };
              }
              return updated;
            });
          },

          onToolStart: (evt: SSEToolStartEvent) => {
            // 添加工具调用消息
            const toolMsg: ChatMessage = {
              localId: nextLocalId(),
              role: 'tool',
              content: '',
              toolName: evt.tool,
              isStreaming: true,
              timestamp: Date.now(),
            };
            setMessages((prev) => [...prev, toolMsg]);
          },

          onToolEnd: (evt: SSEToolEndEvent) => {
            setMessages((prev) => {
              const updated = [...prev];
              // 找到最后一个匹配的 tool 消息并标记完成
              for (let i = updated.length - 1; i >= 0; i--) {
                if (updated[i].role === 'tool' && updated[i].toolName === evt.tool && updated[i].isStreaming) {
                  updated[i] = { ...updated[i], isStreaming: false };
                  break;
                }
              }
              return updated;
            });
          },

          onDone: (evt: SSEDoneEvent) => {
            if (evt.session_key && !sessionKey) {
              setSessionKey(evt.session_key);
            }
            if (evt.message_id) {
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last && last.role === 'assistant') {
                  updated[updated.length - 1] = {
                    ...last,
                    isStreaming: false,
                    eventId: evt.message_id,
                  };
                }
                return updated;
              });
            } else {
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last && last.role === 'assistant') {
                  updated[updated.length - 1] = { ...last, isStreaming: false };
                }
                return updated;
              });
            }
            setIsStreaming(false);
          },

          onError: (evt: SSEErrorEvent) => {
            Alert.alert('出错', evt.message || 'AI 服务暂时不可用，请稍后重试');
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last && last.role === 'assistant') {
                updated[updated.length - 1] = {
                  ...last,
                  isStreaming: false,
                  content: last.content || '（回复失败）',
                };
              }
              return updated;
            });
            setIsStreaming(false);
          },

          onDisconnect: () => {
            setIsStreaming(false);
          },
        },
      );

      sseRef.current = conn;
    } catch (err) {
      const msg = err instanceof Error ? err.message : '连接失败';
      Alert.alert('连接失败', msg);
      // 清理空的 AI 消息（避免错误状态残留）
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last && last.role === 'assistant' && last.isStreaming) {
          updated[updated.length - 1] = {
            ...last,
            isStreaming: false,
            content: '（连接失败，请重试）',
          };
        }
        return updated;
      });
      setIsStreaming(false);
    }
  }, [inputText, isStreaming, sessionKey]);

  // ── 加载更多历史 ──
  const handleLoadMore = useCallback(async () => {
    if (!sessionKey || !historyHasMore || loadingHistory) return;

    const oldestMsg = messages[0];
    if (!oldestMsg?.eventId) return;

    setLoadingHistory(true);
    try {
      const res = await agentApi.getMessages(sessionKey, oldestMsg.eventId, 50);
      const loaded: ChatMessage[] = res.messages.map((m: AgentMessage) => ({
        localId: nextLocalId(),
        role: m.role,
        content: m.content || '',
        toolName: m.tool_name || undefined,
        eventId: m.event_id || undefined,
        isStreaming: false,
        timestamp: new Date(m.created_at).getTime(),
      }));

      setMessages((prev) => [...loaded, ...prev]);
      setHistoryHasMore(res.has_more);
    } catch {
      setHistoryHasMore(false); // 加载失败，停止尝试
    } finally {
      setLoadingHistory(false);
    }
  }, [sessionKey, historyHasMore, loadingHistory, messages]);

  // ── 内容尺寸变化时自动滚动 ──
  useEffect(() => {
    scrollToBottom();
  }, [messages.length, scrollToBottom]);

  // ── 渲染 ──

  if (loadingHistory) {
    return (
      <View style={styles.container}>
        <LoadingSpinner message="加载消息..." fullScreen />
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
    >
      {/* ── 消息列表 ── */}
      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(item) => item.localId}
        renderItem={({ item }) => <MessageBubble message={item} />}
        contentContainerStyle={styles.messageList}
        onContentSizeChange={() => scrollToBottom(false)}
        // 滚动到顶部加载更早的历史消息
        onStartReached={handleLoadMore}
        onStartReachedThreshold={0.3}
        // 空状态
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyIcon}>🤖</Text>
            <Text style={styles.emptyTitle}>小北 AI 助手</Text>
            <Text style={styles.emptyDesc}>
              我可以帮你查询课表、成绩、考试安排{'\n'}
              还能为你的学业规划提供建议
            </Text>
          </View>
        }
      />

      {/* ── 输入栏 ── */}
      <View style={styles.inputBar}>
        <TextInput
          style={styles.input}
          value={inputText}
          onChangeText={setInputText}
          placeholder="输入消息..."
          placeholderTextColor="#9CA3AF"
          multiline
          maxLength={4000}
          editable={!isStreaming}
          returnKeyType="send"
          onSubmitEditing={handleSend}
          blurOnSubmit={false}
        />
        <TouchableOpacity
          style={[
            styles.sendBtn,
            (!inputText.trim() || isStreaming) && styles.sendBtnDisabled,
          ]}
          onPress={handleSend}
          disabled={!inputText.trim() || isStreaming}
          activeOpacity={0.7}
        >
          <Text style={styles.sendBtnText}>发送</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

// ============================================================
// Styles
// ============================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  messageList: {
    flexGrow: 1,
    paddingVertical: 12,
    paddingBottom: 8,
  },
  // ── 空状态 ──
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
    paddingTop: 120,
  },
  emptyIcon: {
    fontSize: 56,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 10,
  },
  emptyDesc: {
    fontSize: 14,
    color: '#9CA3AF',
    textAlign: 'center',
    lineHeight: 22,
  },
  // ── 输入栏 ──
  inputBar: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderTopWidth: 0.5,
    borderTopColor: '#E5E7EB',
    backgroundColor: '#FFFFFF',
  },
  input: {
    flex: 1,
    minHeight: 40,
    maxHeight: 120,
    backgroundColor: '#F3F4F6',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 15,
    color: '#1F2937',
    lineHeight: 20,
    marginRight: 8,
  },
  sendBtn: {
    backgroundColor: '#0880D7',
    paddingHorizontal: 18,
    paddingVertical: 10,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendBtnDisabled: {
    backgroundColor: '#93C5FD',
  },
  sendBtnText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
});
