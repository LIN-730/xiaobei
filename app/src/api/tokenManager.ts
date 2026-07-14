// ============================================================
// Token 生命周期管理 + 刷新队列
// ============================================================
import axios from 'axios';
import { secureStorage } from '../utils/storage';
import { TOKEN_CONFIG, API_BASE_URL } from '../utils/constants';
import { isTokenExpired } from '../utils/jwt';
import type { TokenResponse } from '../types/auth';

// ============================================================
// 刷新队列 — 并发 401 不重复刷新
// ============================================================
interface QueueSubscriber {
  resolve: (token: string) => void;
  reject: (error: Error) => void;
}

let isRefreshing = false;
let refreshSubscribers: QueueSubscriber[] = [];

function onRefreshed(newToken: string): void {
  refreshSubscribers.forEach((sub) => {
    sub.resolve(newToken);
  });
  refreshSubscribers = [];
}

function onRefreshFailed(error: Error): void {
  refreshSubscribers.forEach((sub) => {
    sub.reject(error);
  });
  refreshSubscribers = [];
}

function subscribeToRefresh(resolve: (token: string) => void, reject: (error: Error) => void): void {
  refreshSubscribers.push({ resolve, reject });
}

// ============================================================
// Token 存储操作
// ============================================================
export const tokenManager = {
  async getAccessToken(): Promise<string | null> {
    return secureStorage.get(TOKEN_CONFIG.ACCESS_TOKEN_KEY);
  },

  async getRefreshToken(): Promise<string | null> {
    return secureStorage.get(TOKEN_CONFIG.REFRESH_TOKEN_KEY);
  },

  async setTokens(tokens: TokenResponse): Promise<void> {
    await secureStorage.set(TOKEN_CONFIG.ACCESS_TOKEN_KEY, tokens.access_token);
    await secureStorage.set(TOKEN_CONFIG.REFRESH_TOKEN_KEY, tokens.refresh_token);
  },

  async clearTokens(): Promise<void> {
    await secureStorage.clear();
  },

  /** 检查 access_token 是否有效 (未过期) */
  async isAccessTokenValid(): Promise<boolean> {
    const token = await this.getAccessToken();
    if (!token) return false;
    return !isTokenExpired(token, TOKEN_CONFIG.REFRESH_THRESHOLD_SEC);
  },

  /** 使用 refresh_token 获取新 Token 对 (带超时) */
  async refreshToken(): Promise<TokenResponse> {
    const refreshToken = await this.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    // 直接使用 axios (不走拦截器，避免循环)，设置独立超时
    const response = await axios.post<TokenResponse>(
      `${API_BASE_URL}/api/v1/auth/refresh`,
      { refresh_token: refreshToken },
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 10000, // 刷新请求单独 10s 超时
      },
    );

    const tokens = response.data;
    await this.setTokens(tokens);
    return tokens;
  },
};

// ============================================================
// 对外暴露的刷新队列接口 (供 axios 拦截器使用)
// ============================================================
export const refreshQueue = {
  get isRefreshing() {
    return isRefreshing;
  },
  set isRefreshing(val: boolean) {
    isRefreshing = val;
  },
  subscribe: subscribeToRefresh,
  onRefreshed,
  onRefreshFailed,
};
