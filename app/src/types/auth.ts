// ============================================================
// 认证相关类型 — 对应 app/auth/schemas.py
// ============================================================

/** POST /auth/register 请求 */
export interface RegisterRequest {
  username: string;
  password: string;
  email?: string;
  phone?: string;
}

/** POST /auth/login 请求 */
export interface LoginRequest {
  username: string;
  password: string;
}

/** POST /auth/refresh 请求 */
export interface TokenRefreshRequest {
  refresh_token: string;
}

/** Token 响应 (login/register/refresh 共用) */
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
}

/** GET /auth/me 响应 — UserResponse */
export interface UserProfile {
  id: string; // UUID
  username: string;
  email: string | null;
  phone: string | null;
  is_active: boolean;
  has_credential: boolean;
}

/** JWT Payload (解码后) */
export interface JwtPayload {
  sub: string; // user_id
  type: 'access' | 'refresh';
  exp: number; // unix timestamp
  iat: number;
}
