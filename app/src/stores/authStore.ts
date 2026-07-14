// ============================================================
// 认证状态管理 (Zustand)
// ============================================================
import { create } from 'zustand';
import type { UserProfile } from '../types/auth';
import { tokenManager } from '../api/tokenManager';
import { authApi } from '../api/auth';

interface AuthState {
  /** 当前登录用户信息 */
  user: UserProfile | null;
  /** 是否已认证 (有有效 Token) */
  isAuthenticated: boolean;
  /** 应用启动初始化是否完成 */
  isInitialized: boolean;
  /** 登录/注册加载中 */
  isLoading: boolean;
  /** 错误信息 */
  error: string | null;

  // Actions
  setUser: (user: UserProfile) => void;
  setInitialized: (val: boolean) => void;
  setLoading: (val: boolean) => void;
  setError: (msg: string | null) => void;
  clearError: () => void;

  /** 注册 */
  register: (username: string, password: string, email?: string, phone?: string) => Promise<void>;
  /** 登录 */
  login: (username: string, password: string) => Promise<void>;
  /** 登出 */
  logout: () => Promise<void>;
  /** 应用启动初始化 — 检测已存储 Token 并恢复会话 */
  initialize: () => Promise<void>;
  /** 刷新用户信息 */
  refreshProfile: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  isInitialized: false,
  isLoading: false,
  error: null,

  setUser: (user) => set({ user, isAuthenticated: true }),
  setInitialized: (val) => set({ isInitialized: val }),
  setLoading: (val) => set({ isLoading: val }),
  setError: (msg) => set({ error: msg }),
  clearError: () => set({ error: null }),

  register: async (username, password, email, phone) => {
    set({ isLoading: true, error: null });
    try {
      const tokens = await authApi.register({ username, password, email, phone });
      await tokenManager.setTokens(tokens);
      const user = await authApi.getProfile();
      set({ user, isAuthenticated: true });
    } catch (err: unknown) {
      const msg = extractErrorMessage(err, '注册失败，请稍后重试');
      set({ error: msg });
      throw err;
    } finally {
      set({ isLoading: false });
    }
  },

  login: async (username, password) => {
    set({ isLoading: true, error: null });
    try {
      const tokens = await authApi.login({ username, password });
      await tokenManager.setTokens(tokens);
      const user = await authApi.getProfile();
      set({ user, isAuthenticated: true });
    } catch (err: unknown) {
      const msg = extractErrorMessage(err, '用户名或密码错误');
      set({ error: msg });
      throw err;
    } finally {
      set({ isLoading: false });
    }
  },

  logout: async () => {
    await tokenManager.clearTokens();
    set({ user: null, isAuthenticated: false, error: null });
  },

  initialize: async () => {
    try {
      const accessToken = await tokenManager.getAccessToken();
      if (!accessToken) {
        set({ isInitialized: true });
        return;
      }

      // Token 存在 → 验证有效性
      try {
        const user = await authApi.getProfile();
        set({ user, isAuthenticated: true });
      } catch (err: unknown) {
        // 仅 401 才尝试刷新，网络错误不刷新 (避免网络不通时误刷新导致无限循环)
        if (isHttpError(err, 401)) {
          try {
            await tokenManager.refreshToken();
            const user = await authApi.getProfile();
            set({ user, isAuthenticated: true });
          } catch (refreshErr: unknown) {
            // 刷新 401 → Token 真正过期 → 清除
            if (isHttpError(refreshErr, 401)) {
              await tokenManager.clearTokens();
            }
            // 网络错误 → 保留 Token，允许离线使用
            set({ user: null, isAuthenticated: false });
          }
        } else {
          // 网络错误 → 保留 Token，允许进入 App (离线降级)
          set({ user: null, isAuthenticated: false });
        }
      }
    } finally {
      set({ isInitialized: true });
    }
  },

  refreshProfile: async () => {
    try {
      const user = await authApi.getProfile();
      set({ user });
    } catch {
      // 刷新失败 — 保留当前用户信息但不标记为错误
    }
  },
}));

/** 从 Axios 错误中提取用户可读消息 */
function extractErrorMessage(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const response = (err as { response?: { data?: { detail?: string } } }).response;
    if (response?.data?.detail) {
      return response.data.detail;
    }
  }
  if (err instanceof Error) {
    return err.message;
  }
  return fallback;
}

/** 判断错误是否是特定 HTTP 状态码 */
function isHttpError(err: unknown, status: number): boolean {
  return (
    typeof err === 'object' &&
    err !== null &&
    'response' in err &&
    typeof (err as { response?: { status?: number } }).response?.status === 'number' &&
    (err as { response: { status: number } }).response.status === status
  );
}

// 非 Hook 场景使用 (拦截器等)
export const authStore = {
  getState: () => useAuthStore.getState(),
};
