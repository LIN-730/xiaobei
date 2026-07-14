// ============================================================
// JWT 解码 + 过期判断
// ============================================================
import type { JwtPayload } from '../types/auth';

/**
 * Base64 解码 — 兼容 React Native Hermes 引擎
 * Hermes 不提供全局 atob/btoa，使用自定义实现
 */
function base64Decode(str: string): string {
  // 补齐 Base64 padding
  const padded = str + '='.repeat((4 - (str.length % 4)) % 4);
  const base64Chars =
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';

  let result = '';
  for (let i = 0; i < padded.length; i += 4) {
    const b0 = base64Chars.indexOf(padded[i]!);
    const b1 = base64Chars.indexOf(padded[i + 1]!);
    const b2 = base64Chars.indexOf(padded[i + 2]!);
    const b3 = base64Chars.indexOf(padded[i + 3]!);

    const combined = (b0 << 18) | (b1 << 12) | (b2 << 6) | b3;
    result += String.fromCharCode((combined >> 16) & 0xff);
    if (padded[i + 2] !== '=') {
      result += String.fromCharCode((combined >> 8) & 0xff);
    }
    if (padded[i + 3] !== '=') {
      result += String.fromCharCode(combined & 0xff);
    }
  }

  // UTF-8 解码 (处理中文等非 ASCII 字符)
  try {
    return decodeURIComponent(
      result
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join(''),
    );
  } catch {
    return result; // 纯 ASCII fallback
  }
}

/**
 * 解码 JWT payload (不验证签名)
 * 用于客户端判断 Token 过期时间
 */
export function decodeJwtPayload(token: string): JwtPayload | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;

    const payload = parts[1];
    // URL-safe Base64 → 标准 Base64
    const standard = payload.replace(/-/g, '+').replace(/_/g, '/');
    const json = base64Decode(standard);
    return JSON.parse(json) as JwtPayload;
  } catch {
    return null;
  }
}

/** 检查 JWT 是否已过期或即将过期 */
export function isTokenExpired(token: string, thresholdSec: number = 60): boolean {
  const payload = decodeJwtPayload(token);
  if (!payload) return true; // 解析失败视为过期

  const now = Math.floor(Date.now() / 1000);
  return payload.exp <= now + thresholdSec;
}

/** 检查 JWT 是否已过期 (不含阈值) */
export function isTokenFullyExpired(token: string): boolean {
  const payload = decodeJwtPayload(token);
  if (!payload) return true;

  const now = Math.floor(Date.now() / 1000);
  return payload.exp <= now;
}
