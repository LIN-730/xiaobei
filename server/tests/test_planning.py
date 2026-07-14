# tests/test_planning.py — 学业规划 API 测试
"""测试 4 个规划端点的基本响应格式"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestPlanningEndpoints:
    """学业规划端点 — 验证响应格式和认证要求"""

    async def test_credit_gap_requires_auth(self, client: AsyncClient):
        """未认证访问 → 401"""
        resp = await client.get("/api/v1/planning/credit-gap")
        assert resp.status_code == 401

    async def test_credit_gap_with_auth(self, client: AsyncClient, auth_headers: dict):
        """认证访问 → 200（数据依赖同步）"""
        resp = await client.get("/api/v1/planning/credit-gap", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        # 即使数据为空，格式也应该正确
        assert "total_credits_required" in data or "modules" in data or "gap" in data

    async def test_required_courses_with_auth(self, client: AsyncClient, auth_headers: dict):
        """必修课检查 → 200"""
        resp = await client.get("/api/v1/planning/required-courses", headers=auth_headers)
        assert resp.status_code == 200, resp.text

    async def test_recommend_with_auth(self, client: AsyncClient, auth_headers: dict):
        """选课推荐 → 200"""
        resp = await client.get("/api/v1/planning/recommend", headers=auth_headers)
        assert resp.status_code == 200, resp.text

    async def test_path_plan_with_auth(self, client: AsyncClient, auth_headers: dict):
        """学业路径规划 → 200"""
        resp = await client.get("/api/v1/planning/path", headers=auth_headers)
        assert resp.status_code == 200, resp.text


@pytest.mark.integration
class TestDashboard:
    """仪表盘端点"""

    async def test_dashboard_with_auth(self, client: AsyncClient, auth_headers: dict):
        """认证访问 → 200"""
        resp = await client.get("/api/v1/dashboard", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        # 基本结构验证
        assert isinstance(data, dict)


@pytest.mark.integration
class TestHealth:
    """健康检查端点（无需认证）"""

    async def test_health_check(self, client: AsyncClient):
        """GET /health → 200"""
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
