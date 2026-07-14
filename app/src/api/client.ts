// ============================================================
// Axios 实例 + 拦截器
// ============================================================
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { API_BASE_URL } from '../utils/constants';
import { tokenManager, refreshQueue } from './tokenManager';
import { isTokenExpired, isTokenFullyExpired } from '../utils/jwt';
import { authStore } from '../stores/authStore';

// ============================================================
// 创建 Axios 实例
// ============================================================
export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// ============================================================
// Request 拦截器 — 注入 Token + 提前刷新
// ============================================================
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    // 跳过无需认证的 auth 端点 (login/register/refresh)
    if (config.url?.startsWith('/auth/login') || config.url?.startsWith('/auth/register') || config.url?.startsWith('/auth/refresh')) {
      return config;
    }

    const accessToken = await tokenManager.getAccessToken();
    if (accessToken) {
      // 提前刷新：Token 即将过期时静默刷新
      if (isTokenExpired(accessToken, 60) && !isTokenFullyExpired(accessToken)) {
        try {
          const refreshToken = await tokenManager.getRefreshToken();
          if (refreshToken && !isTokenFullyExpired(refreshToken)) {
            const tokens = await tokenManager.refreshToken();
            config.headers.Authorization = `Bearer ${tokens.access_token}`;
            return config;
          }
        } catch {
          // 刷新失败不阻塞请求，让后端返回 401 → 触发正式刷新流程
        }
      }
      config.headers.Authorization = `Bearer ${accessToken}`;
    }

    return config;
  },
  (error) => Promise.reject(error),
);

// ============================================================
// Response 拦截器 — 401 刷新队列
// ============================================================
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // 只处理 401 + 排除 login/register/refresh (不需要刷新的端点) + 未重试过
    const skipRetry = originalRequest.url?.startsWith('/auth/login') ||
      originalRequest.url?.startsWith('/auth/register') ||
      originalRequest.url?.startsWith('/auth/refresh');
    if (
      error.response?.status !== 401 ||
      skipRetry ||
      originalRequest._retry
    ) {
      return Promise.reject(error);
    }

    // 正在刷新 → 加入队列等待
    if (refreshQueue.isRefreshing) {
      return new Promise((resolve, reject) => {
        refreshQueue.subscribe(
          (token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            resolve(apiClient(originalRequest));
          },
          (err: Error) => {
            reject(err);
          },
        );
      });
    }

    // 开始刷新
    originalRequest._retry = true;
    refreshQueue.isRefreshing = true;

    try {
      const tokens = await tokenManager.refreshToken();
      refreshQueue.onRefreshed(tokens.access_token);
      originalRequest.headers.Authorization = `Bearer ${tokens.access_token}`;
      return apiClient(originalRequest);
    } catch (refreshError) {
      const err = refreshError instanceof Error ? refreshError : new Error('Token refresh failed');
      refreshQueue.onRefreshFailed(err);
      // 刷新失败 → 登出
      authStore.getState().logout();
      return Promise.reject(refreshError);
    } finally {
      refreshQueue.isRefreshing = false;
    }
  },
);

export default apiClient;
