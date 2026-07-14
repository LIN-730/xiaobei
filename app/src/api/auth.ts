// ============================================================
// 认证 API — POST/GET /api/v1/auth/*
// ============================================================
import apiClient from './client';
import type {
  LoginRequest,
  RegisterRequest,
  TokenRefreshRequest,
  TokenResponse,
  UserProfile,
} from '../types/auth';

export const authApi = {
  /** 用户注册 */
  register(data: RegisterRequest): Promise<TokenResponse> {
    return apiClient.post('/auth/register', data).then((r) => r.data);
  },

  /** 用户登录 */
  login(data: LoginRequest): Promise<TokenResponse> {
    return apiClient.post('/auth/login', data).then((r) => r.data);
  },

  /** 刷新 Token */
  refresh(data: TokenRefreshRequest): Promise<TokenResponse> {
    return apiClient.post('/auth/refresh', data).then((r) => r.data);
  },

  /** 获取当前用户信息 */
  getProfile(): Promise<UserProfile> {
    return apiClient.get('/auth/me').then((r) => r.data);
  },
};
