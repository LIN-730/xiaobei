// ============================================================
// AI 对话类型 — 对应 app/agent/schemas.py
// ============================================================

/** POST /agent/chat 请求 */
export interface ChatRequest {
  message: string;
  session_key?: string;
}

/** 会话列表项 */
export interface AgentSession {
  session_key: string;
  title: string;
  last_message_preview: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface AgentSessionListResponse {
  sessions: AgentSession[];
  total: number;
}

/** 消息历史项 */
export interface AgentMessage {
  role: 'user' | 'assistant' | 'tool';
  content: string;
  tool_name: string | null;
  event_id: number;
  created_at: string;
}

export interface AgentMessageListResponse {
  messages: AgentMessage[];
  has_more: boolean;
}

/** 删除会话响应 */
export interface AgentDeleteResponse {
  ok: boolean;
  session_key: string;
}

// ============================================================
// SSE 事件类型
// ============================================================

export type SSEEventType = 'meta' | 'token' | 'tool_start' | 'tool_end' | 'done' | 'error' | 'heartbeat';

export interface SSEMetaEvent {
  type: 'meta';
  session_key: string;
}

export interface SSETokenEvent {
  type: 'token';
  content: string;
}

export interface SSEToolStartEvent {
  type: 'tool_start';
  tool: string;
}

export interface SSEToolEndEvent {
  type: 'tool_end';
  tool: string;
}

export interface SSEDoneEvent {
  type: 'done';
  session_key: string;
  message_id: number;
}

export interface SSEErrorEvent {
  type: 'error';
  message: string;
}

export type SSEEventData =
  | SSEMetaEvent
  | SSETokenEvent
  | SSEToolStartEvent
  | SSEToolEndEvent
  | SSEDoneEvent
  | SSEErrorEvent;
