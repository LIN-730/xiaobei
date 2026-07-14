// ============================================================
// 对话状态管理 (Zustand)
// ============================================================
import { create } from 'zustand';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'tool';
  content: string;
  toolName?: string;
  timestamp: number;
  isStreaming?: boolean; // 是否还在流式接收中
}

interface ChatState {
  /** 当前会话 key */
  currentSessionKey: string | null;
  /** 当前会话消息 (仅内存，不持久化) */
  messages: ChatMessage[];
  /** 是否正在接收 SSE 流 */
  isStreaming: boolean;
  /** 当前使用的工具名 */
  activeTool: string | null;

  // Actions
  setSessionKey: (key: string | null) => void;
  addMessage: (msg: ChatMessage) => void;
  updateLastAssistant: (content: string) => void;
  setStreaming: (val: boolean) => void;
  setActiveTool: (tool: string | null) => void;
  clearMessages: () => void;
  /** 将流式消息标记为完成 */
  finishStreaming: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  currentSessionKey: null,
  messages: [],
  isStreaming: false,
  activeTool: null,

  setSessionKey: (key) => set({ currentSessionKey: key }),

  addMessage: (msg) =>
    set((s) => ({ messages: [...s.messages, msg] })),

  updateLastAssistant: (content) =>
    set((s) => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === 'assistant' && last.isStreaming) {
        msgs[msgs.length - 1] = { ...last, content: last.content + content };
      }
      return { messages: msgs };
    }),

  setStreaming: (val) => set({ isStreaming: val }),

  setActiveTool: (tool) => set({ activeTool: tool }),

  clearMessages: () => set({ messages: [] }),

  finishStreaming: () =>
    set((s) => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = { ...last, isStreaming: false };
      }
      return { messages: msgs, isStreaming: false, activeTool: null };
    }),
}));
