// ============================================================
// SSE 传输层 — XHR 流式解析 text/event-stream
// ============================================================
// React Native 不支持浏览器原生 EventSource，且后端 POST /chat
// 需要 POST body，因此用 XHR + onprogress 解析 SSE 流。
// ============================================================
import { API_BASE_URL } from '../utils/constants';
import { tokenManager } from './tokenManager';
import type {
  SSEMetaEvent,
  SSETokenEvent,
  SSEToolStartEvent,
  SSEToolEndEvent,
  SSEDoneEvent,
  SSEErrorEvent,
  ChatRequest,
} from '../types/chat';

// ============================================================
// Handler 接口
// ============================================================

export interface SSEHandlers {
  onMeta: (event: SSEMetaEvent) => void;
  onToken: (event: SSETokenEvent) => void;
  onToolStart: (event: SSEToolStartEvent) => void;
  onToolEnd: (event: SSEToolEndEvent) => void;
  onDone: (event: SSEDoneEvent) => void;
  onError: (event: SSEErrorEvent) => void;
  onHeartbeat?: () => void;
  /** SSE 连接已断开（用于 UI 更新） */
  onDisconnect?: () => void;
}

// ============================================================
// SSE 事件解析器
// ============================================================

interface RawEvent {
  event?: string;
  data: string;
  id?: string;
}

/**
 * 解析增量 SSE 文本，返回完整事件列表。
 * 未完成的事件保留在 buffer 中供下次拼接。
 */
function parseSSEChunk(
  chunk: string,
  buffer: string,
): { events: RawEvent[]; remaining: string } {
  const combined = buffer + chunk;
  const parts = combined.split('\n\n');
  // 最后一段可能不完整，保留
  const remaining = parts.pop() || '';

  const events: RawEvent[] = [];
  for (const part of parts) {
    if (!part.trim()) continue;
    const event: RawEvent = { data: '' };
    const lines = part.split('\n');
    for (const line of lines) {
      if (line.startsWith(':')) {
        // 注释行（心跳等），忽略
        continue;
      }
      const colonIdx = line.indexOf(':');
      if (colonIdx === -1) continue;
      const field = line.substring(0, colonIdx).trim();
      const value = line.substring(colonIdx + 1);
      // value 可能以空格开头，SSE 规范要求去掉一个前导空格
      const trimmedValue = value.startsWith(' ') ? value.substring(1) : value;

      switch (field) {
        case 'event':
          event.event = trimmedValue;
          break;
        case 'data':
          event.data += trimmedValue;
          break;
        case 'id':
          event.id = trimmedValue;
          break;
        // retry 等其他字段忽略
      }
    }
    if (event.data) {
      events.push(event);
    }
  }

  return { events, remaining };
}

/**
 * 将 RawEvent 分发到对应的 handler。
 * 支持 type 字段在 data JSON 内部（后端约定）或 event 字段。
 */
function dispatchEvent(raw: RawEvent, handlers: SSEHandlers, lastEventId: { current: number | null }): void {
  // 更新 Last-Event-ID
  if (raw.id !== undefined) {
    const parsed = parseInt(raw.id, 10);
    if (!isNaN(parsed)) {
      lastEventId.current = parsed;
    }
  }

  // 解析 data JSON
  let parsed: Record<string, unknown>;
  try {
    parsed = JSON.parse(raw.data);
  } catch {
    // data 不是有效 JSON（如纯文本 token），按 token 处理
    handlers.onToken({ type: 'token', content: raw.data });
    return;
  }

  // 事件类型优先从 raw.event，其次从 parsed.type
  const eventType = raw.event || (parsed.type as string | undefined);

  switch (eventType) {
    case 'meta':
      handlers.onMeta(parsed as unknown as SSEMetaEvent);
      break;
    case 'token':
      handlers.onToken(parsed as unknown as SSETokenEvent);
      break;
    case 'tool_start':
      handlers.onToolStart(parsed as unknown as SSEToolStartEvent);
      break;
    case 'tool_end':
      handlers.onToolEnd(parsed as unknown as SSEToolEndEvent);
      break;
    case 'done':
      handlers.onDone(parsed as unknown as SSEDoneEvent);
      break;
    case 'error':
      handlers.onError(parsed as unknown as SSEErrorEvent);
      break;
    default:
      // 未知类型，忽略
      break;
  }
}

// ============================================================
// SSE 连接
// ============================================================

export interface SSEConnection {
  /** 取消连接 */
  abort: () => void;
  /** 当前 session_key（meta 事件后设置） */
  sessionKey: string | null;
}

/**
 * 建立 SSE 连接，返回控制对象。
 *
 * @param request   聊天请求
 * @param handlers  事件处理器
 * @param signal    可选 AbortSignal 用于外部取消
 * @param lastEventId 断线重连时传入上次最后接收到的事件 ID
 */
export async function connectSSE(
  request: ChatRequest,
  handlers: SSEHandlers,
  signal?: AbortSignal,
  lastEventId?: number | null,
): Promise<SSEConnection> {
  const token = await tokenManager.getAccessToken();
  const xhr = new XMLHttpRequest();

  // XHR 文本模式让 onprogress 可用（显式设 text 确保 RN 兼容）

  const connection: SSEConnection = {
    abort: () => {
      xhr.abort();
    },
    sessionKey: request.session_key || null,
  };

  let processedLength = 0;
  let parserBuffer = '';
  const lastId = { current: lastEventId ?? null };

  // ── 进度回调：增量解析 SSE ──
  xhr.onprogress = () => {
    const responseText = xhr.responseText;
    if (!responseText) return;

    // 取上次处理后新增部分（加长度保护防竞态）
    if (processedLength >= responseText.length) return;
    const newText = responseText.substring(processedLength);
    processedLength = responseText.length;
    if (!newText) return;

    const { events, remaining } = parseSSEChunk(newText, parserBuffer);
    parserBuffer = remaining;

    for (const raw of events) {
      // 检测心跳注释
      if (raw.event === 'heartbeat' || (raw.data === '' && !raw.event)) {
        handlers.onHeartbeat?.();
        continue;
      }
      dispatchEvent(raw, handlers, lastId);
    }
  };

  // ── 加载完成 ──
  xhr.onload = () => {
    // 处理可能残留的数据
    const responseText = xhr.responseText;
    if (responseText && processedLength < responseText.length) {
      const remaining = responseText.substring(processedLength);
      if (remaining.trim()) {
        const { events } = parseSSEChunk(remaining, parserBuffer);
        for (const raw of events) {
          dispatchEvent(raw, handlers, lastId);
        }
      }
    }
    handlers.onDisconnect?.();
  };

  // ── 中止处理 ──
  xhr.onabort = () => {
    handlers.onDisconnect?.();
  };

  // ── 错误处理 ──
  xhr.onerror = () => {
    handlers.onError({
      type: 'error',
      message: '网络连接失败，请检查网络后重试',
    });
    handlers.onDisconnect?.();
  };

  xhr.ontimeout = () => {
    handlers.onError({
      type: 'error',
      message: '请求超时，AI 服务响应过慢，请稍后重试',
    });
    handlers.onDisconnect?.();
  };

  // ── AbortSignal 监听 ──
  if (signal) {
    if (signal.aborted) {
      // 已经在发送前被取消
      return connection;
    }
    signal.addEventListener('abort', () => xhr.abort(), { once: true });
  }

  // ── 发送请求 ──
  const url = `${API_BASE_URL}/api/v1/agent/chat`;
  xhr.open('POST', url);
  xhr.setRequestHeader('Content-Type', 'application/json');
  if (token) {
    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
  }
  if (lastEventId !== null && lastEventId !== undefined) {
    xhr.setRequestHeader('Last-Event-ID', String(lastEventId));
  }
  xhr.timeout = 120000; // 2 分钟超时（AI 回复可能较长）

  xhr.send(JSON.stringify({
    message: request.message,
    session_key: request.session_key,
  }));

  return connection;
}
