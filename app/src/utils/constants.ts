// ============================================================
// 常量配置
// ============================================================
import Constants from 'expo-constants';
import { Platform } from 'react-native';

/** API 基础 URL — 开发环境自动检测本机 IP，生产环境用正式域名 */
export const API_BASE_URL = __DEV__
  ? (() => {
      // Android 模拟器用 adb reverse 端口转发 → localhost 即宿主机
      if (Platform.OS === 'android') {
        return 'http://10.0.2.2:8000';
      }
      // iOS 模拟器直接用 localhost
      if (Platform.OS === 'ios') {
        return 'http://localhost:8000';
      }
      // Web 版：Expo dev server 的 hostUri 即电脑 IP
      const hostUri = Constants.expoConfig?.hostUri;
      if (hostUri) {
        const host = hostUri.split(':')[0];
        return `http://${host}:8000`;
      }
      return 'http://localhost:8000';
    })()
  : 'https://api.xiaobei.buct.edu.cn';

/** Token 配置 */
export const TOKEN_CONFIG = {
  /** Access Token 提前刷新阈值 (秒) */
  REFRESH_THRESHOLD_SEC: 60,
  /** Token 存储 Key */
  ACCESS_TOKEN_KEY: 'access_token',
  REFRESH_TOKEN_KEY: 'refresh_token',
} as const;

/** 应用信息 */
export const APP_INFO = {
  name: '小北',
  fullName: '教务智能助手',
  version: '1.0.0',
} as const;
