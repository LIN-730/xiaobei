# crawlers/base.py — 爬虫基类（统一封装POST请求、JSON解析、错误处理）
import json
import time
from typing import Optional, Dict, Any
class BaseCrawler:
    """所有教务数据爬虫的基类，封装通用POST + GNMKDM码请求逻辑"""

    def __init__(self, session, student_no: str, base_url: Optional[str] = None):
        """
        Args:
            session: requests.Session（已登录教务系统）
            student_no: 学生学号
            base_url: 教务系统根URL（如 https://jwglxt.buct.edu.cn）
        """
        self.session = session
        self.student_no = student_no
        self.base_url = base_url or "https://jwglxt.buct.edu.cn"

    # ── 通用 POST 请求 ─────────────────────────────────────────────
    def _post_api(
        self,
        path: str,
        data: Dict[str, Any],
        gnmkdm: Optional[str] = None,
        referer_path: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        extra_params: Optional[str] = None,
    ):
        """
        向教务数据API发起POST请求。

        Args:
            path: API路径（如 /jwglxt/kbcx/xskbcx_cxXsKb.html）
            data: POST表单数据
            gnmkdm: GNMKDM模块码（自动附加到URL）
            referer_path: Referer页面路径（不传则用path）
            extra_headers: 额外请求头
            extra_params: 额外的URL参数字符串（如 "doType=query"）

        Returns:
            requests.Response 对象
        """
        url = f"{self.base_url}{path}"
        params = []
        if extra_params:
            params.append(extra_params)
        if gnmkdm:
            params.append(f"gnmkdm={gnmkdm}")
        if params:
            url += "?" + "&".join(params)

        # 设置标准请求头
        headers = {
            "Referer": f"{self.base_url}{referer_path or path}",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": self.base_url,
        }
        if extra_headers:
            headers.update(extra_headers)

        # 临时更新session headers（保留原有）
        old_headers = {}
        for k in headers:
            old_headers[k] = self.session.headers.get(k)
            self.session.headers[k] = headers[k]

        try:
            resp = self.session.post(url, data=data, timeout=15)
            return resp
        finally:
            # 恢复原有headers
            for k, v in old_headers.items():
                if v is None:
                    self.session.headers.pop(k, None)
                else:
                    self.session.headers[k] = v

    # ── 安全 JSON 解析 ─────────────────────────────────────────────
    def _safe_json(self, resp, module_name: str = "") -> Optional[Dict]:
        """
        安全解析JSON响应，打印调试日志。

        Returns:
            dict / list，解析失败返回 None
        """
        try:
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" in content_type or "登录" in resp.text[:200]:
                print(f"❌ [{module_name}] 接口被拦截（可能需要重新登录）")
                return None

            data = resp.json()
            return data
        except json.JSONDecodeError:
            print(f"❌ [{module_name}] JSON解析失败，状态码: {resp.status_code}")
            print(f"   响应前500字符: {resp.text[:500]}")
            return None
        except Exception as e:
            print(f"❌ [{module_name}] 请求异常: {e}")
            return None

    # ── 通用探针（探测未知API） ─────────────────────────────────────
    def _probe_api(
        self,
        path: str,
        data: Dict[str, Any],
        gnmkdm: str,
        module_name: str = "",
    ) -> Optional[Dict]:
        """
        探针模式：POST请求 + 打印完整响应 → 供开发者分析API结构。
        用于首次探索未知数据API时的响应格式分析。

        Returns:
            dict / list，成功则返回JSON数据
        """
        print(f"🔍 [{module_name}] 探测API: {path}")
        print(f"   GNMKDM: {gnmkdm}")
        print(f"   POST Data: {json.dumps(data, ensure_ascii=False)}")

        resp = self._post_api(path, data, gnmkdm=gnmkdm)
        if resp is None:
            return None

        print(f"   状态码: {resp.status_code}")
        result = self._safe_json(resp, module_name)

        if result is not None:
            # 打印结构摘要
            if isinstance(result, dict):
                keys = list(result.keys())
                print(f"   响应顶层keys ({len(keys)}个): {keys[:15]}")
                # 检查嵌套列表
                for k in keys:
                    v = result[k]
                    if isinstance(v, list) and len(v) > 0:
                        if isinstance(v[0], dict):
                            print(f"   result['{k}']: 列表({len(v)}条), 每条keys: {list(v[0].keys())[:10]}")
                        else:
                            print(f"   result['{k}']: 列表({len(v)}条), 值类型: {type(v[0]).__name__}")
                    elif isinstance(v, dict):
                        print(f"   result['{k}']: dict, keys: {list(v.keys())[:10]}")
                    elif isinstance(v, str) and len(v) < 200:
                        print(f"   result['{k}']: '{v}'")
            elif isinstance(result, list):
                print(f"   响应: 顶层列表({len(result)}条)")
                if len(result) > 0 and isinstance(result[0], dict):
                    print(f"   每条keys: {list(result[0].keys())[:10]}")

        return result

    # ── 子类必须实现的方法 ──────────────────────────────────────────
    def crawl(self):
        """爬取数据（子类必须实现）"""
        raise NotImplementedError(f"{self.__class__.__name__}.crawl() 未实现")

    def save_to_db(self, data):
        """保存数据到数据库（子类必须实现）"""
        raise NotImplementedError(f"{self.__class__.__name__}.save_to_db() 未实现")

    # ── 日志工具 ───────────────────────────────────────────────────
    def _log_start(self, module: str):
        print(f"🚀 [{module}] 开始爬取...")

    def _log_done(self, module: str, count: int):
        print(f"✅ [{module}] 爬取完成，共 {count} 条")

    def _log_save(self, module: str, count: int):
        print(f"💾 [{module}] 保存成功，共 {count} 条")

    def _log_skip(self, module: str, reason: str = ""):
        msg = f"⏭️  [{module}] 跳过"
        if reason:
            msg += f": {reason}"
        print(msg)
