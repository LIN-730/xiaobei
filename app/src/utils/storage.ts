// ============================================================
// 安全存储封装 — 跨平台
// iOS: Keychain | Android: Keystore | Web: localStorage (仅开发用)
// ============================================================

/**
 * Web fallback: 开发调试时用 localStorage 替代 SecureStore。
 * ⚠️ Token 明文存储，仅用于 `npx expo start --web` 本地预览。
 */
const webStorage = {
  async get(key: string): Promise<string | null> {
    return localStorage.getItem(key);
  },
  async set(key: string, value: string): Promise<void> {
    localStorage.setItem(key, value);
  },
  async remove(key: string): Promise<void> {
    localStorage.removeItem(key);
  },
};

function createNativeStorage() {
  try {
    const SecureStore = require('expo-secure-store');
    return {
      async get(key: string): Promise<string | null> {
        try {
          return await SecureStore.getItemAsync(key);
        } catch {
          return null;
        }
      },
      async set(key: string, value: string): Promise<void> {
        try {
          await SecureStore.setItemAsync(key, value);
        } catch {
          console.warn(`[secureStorage] Failed to write key: ${key}`);
          throw new Error(`Failed to store ${key}`);
        }
      },
      async remove(key: string): Promise<void> {
        try {
          await SecureStore.deleteItemAsync(key);
        } catch {
          console.warn(`[secureStorage] Failed to remove key: ${key}`);
        }
      },
    };
  } catch {
    return null;
  }
}

// 检测平台: 优先检测 window 对象 (web), 再试 require expo-secure-store
const isWeb = typeof window !== 'undefined' && typeof window.document !== 'undefined';
const nativeStorage = isWeb ? null : createNativeStorage();
const impl = nativeStorage ?? webStorage;

export const secureStorage = {
  get: (key: string) => impl.get(key),
  set: (key: string, value: string) => impl.set(key, value),
  remove: (key: string) => impl.remove(key),
  async clear(): Promise<void> {
    await impl.remove('access_token');
    await impl.remove('refresh_token');
  },
};
