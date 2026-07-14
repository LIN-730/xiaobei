# tests/test_credentials_api.py — 凭证 API 集成测试
"""测试 教务凭证 绑定/解绑/状态 流程"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestCredentialBind:
    """POST /api/v1/credentials/bind"""

    async def test_bind_success(self, client: AsyncClient, auth_headers: dict):
        """正常绑定凭证"""
        resp = await client.post("/api/v1/credentials/bind", json={
            "student_no": "2024050020",
            "login_account": "2024050020",
            "password": "edu_password_123",
        }, headers=auth_headers)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["student_no"] == "2024050020"
        assert data["is_valid"] is True

    async def test_bind_with_doubao_key(self, client: AsyncClient, auth_headers: dict):
        """绑定凭证 + 自定义豆包 Key"""
        resp = await client.post("/api/v1/credentials/bind", json={
            "student_no": "2024050100",
            "login_account": "2024050100",
            "password": "edu_pass",
            "doubao_api_key": "sk-custom-key-123",
            "doubao_model": "doubao-pro-32k",
        }, headers=auth_headers)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["student_no"] == "2024050100"

    async def test_bind_missing_student_no(self, client: AsyncClient, auth_headers: dict):
        """缺少学号 → 422"""
        resp = await client.post("/api/v1/credentials/bind", json={
            "login_account": "2024050020",
            "password": "edu_pass",
        }, headers=auth_headers)
        assert resp.status_code == 422

    async def test_bind_without_auth(self, client: AsyncClient):
        """无认证 → 401"""
        resp = await client.post("/api/v1/credentials/bind", json={
            "student_no": "2024050020",
            "login_account": "2024050020",
            "password": "edu_pass",
        })
        assert resp.status_code == 401


@pytest.mark.integration
class TestCredentialStatus:
    """GET /api/v1/credentials/status"""

    async def test_status_unbound(self, client: AsyncClient, auth_headers: dict):
        """未绑定凭证时返回 is_bound=false"""
        resp = await client.get("/api/v1/credentials/status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_bound"] is False
        assert data["student_no"] is None

    async def test_status_bound(self, client: AsyncClient, auth_headers: dict):
        """绑定后返回绑定信息"""
        # 先绑定
        bind_resp = await client.post("/api/v1/credentials/bind", json={
            "student_no": "2024050300",
            "login_account": "2024050300",
            "password": "edu_pass",
        }, headers=auth_headers)
        assert bind_resp.status_code == 201

        # 再查询
        resp = await client.get("/api/v1/credentials/status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_bound"] is True
        assert data["student_no"] == "2024050300"


@pytest.mark.integration
class TestCredentialUnbind:
    """DELETE /api/v1/credentials/unbind"""

    async def test_unbind_success(self, client: AsyncClient, auth_headers: dict):
        """绑定后解绑"""
        # 先绑定
        bind_resp = await client.post("/api/v1/credentials/bind", json={
            "student_no": "2024050400",
            "login_account": "2024050400",
            "password": "edu_pass",
        }, headers=auth_headers)
        assert bind_resp.status_code == 201

        # 解绑
        resp = await client.delete("/api/v1/credentials/unbind", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["is_bound"] is False

    async def test_unbind_when_not_bound(self, client: AsyncClient, auth_headers: dict):
        """未绑定时解绑 → 仍返回 200"""
        resp = await client.delete("/api/v1/credentials/unbind", headers=auth_headers)
        assert resp.status_code == 200
