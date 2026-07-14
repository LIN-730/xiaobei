# tests/test_auth_api.py — 认证 API 集成测试
"""测试 注册 → 登录 → Token 刷新 完整 JWT 链路"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestRegister:
    """POST /api/v1/auth/register"""

    async def test_register_success(self, client: AsyncClient):
        """正常注册"""
        resp = await client.post("/api/v1/auth/register", json={
            "username": "newuser001",
            "password": "secure1234",
        })
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["username"] == "newuser001"
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_duplicate_username(self, client: AsyncClient):
        """重复用户名 → 409"""
        payload = {"username": "dupuser", "password": "pass1234"}
        # 第一次
        resp1 = await client.post("/api/v1/auth/register", json=payload)
        assert resp1.status_code == 201
        # 第二次
        resp2 = await client.post("/api/v1/auth/register", json=payload)
        assert resp2.status_code == 409

    async def test_register_short_username(self, client: AsyncClient):
        """用户名过短 → 422"""
        resp = await client.post("/api/v1/auth/register", json={
            "username": "ab",
            "password": "pass1234",
        })
        assert resp.status_code == 422

    async def test_register_short_password(self, client: AsyncClient):
        """密码过短 → 422"""
        resp = await client.post("/api/v1/auth/register", json={
            "username": "validuser",
            "password": "12345",
        })
        assert resp.status_code == 422

    async def test_register_invalid_username_chars(self, client: AsyncClient):
        """用户名含特殊字符 → 422"""
        resp = await client.post("/api/v1/auth/register", json={
            "username": "user name!",
            "password": "pass1234",
        })
        assert resp.status_code == 422


@pytest.mark.integration
class TestLogin:
    """POST /api/v1/auth/login"""

    @pytest.fixture
    async def registered_user(self, client: AsyncClient):
        """辅助 fixture: 注册用户并返回凭据"""
        payload = {"username": "logintest", "password": "mypassword1"}
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 201
        return payload

    async def test_login_success(self, client: AsyncClient, registered_user: dict):
        """正常登录"""
        resp = await client.post("/api/v1/auth/login", json=registered_user)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["username"] == registered_user["username"]
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_wrong_password(self, client: AsyncClient, registered_user: dict):
        """密码错误 → 401"""
        resp = await client.post("/api/v1/auth/login", json={
            "username": registered_user["username"],
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """不存在的用户 → 401"""
        resp = await client.post("/api/v1/auth/login", json={
            "username": "noone_here_999",
            "password": "somepass123",
        })
        assert resp.status_code == 401


@pytest.mark.integration
class TestTokenRefresh:
    """POST /api/v1/auth/refresh"""

    @pytest.fixture
    async def tokens(self, client: AsyncClient):
        """辅助 fixture: 注册并登录，返回 tokens"""
        payload = {"username": "refreshtest", "password": "mypassword1"}
        register_resp = await client.post("/api/v1/auth/register", json=payload)
        if register_resp.status_code != 201:
            # 可能是重复，直接登录
            login_resp = await client.post("/api/v1/auth/login", json=payload)
            assert login_resp.status_code == 200
            return login_resp.json()
        return register_resp.json()

    async def test_refresh_success(self, client: AsyncClient, tokens: dict):
        """使用有效 refresh_token 刷新"""
        resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": tokens["refresh_token"],
        })
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_with_access_token(self, client: AsyncClient, tokens: dict):
        """使用 access_token 当 refresh_token → 401"""
        resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": tokens["access_token"],
        })
        assert resp.status_code == 401

    async def test_refresh_with_invalid_token(self, client: AsyncClient):
        """无效 token → 401"""
        resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": "not.a.valid.jwt.token",
        })
        assert resp.status_code == 401


@pytest.mark.integration
class TestProtectedEndpoint:
    """测试认证依赖注入 — 访问需要登录的端点"""

    async def test_access_without_token(self, client: AsyncClient):
        """无 Token 访问受保护端点 → 401"""
        resp = await client.get("/api/v1/credentials/status")
        assert resp.status_code == 401

    async def test_access_with_invalid_token(self, client: AsyncClient):
        """无效 Token → 401"""
        resp = await client.get("/api/v1/credentials/status", headers={
            "Authorization": "Bearer invalid.token.here",
        })
        assert resp.status_code == 401

    async def test_access_with_valid_token(self, client: AsyncClient, auth_headers: dict):
        """有效 Token → 200 (凭证未绑定)"""
        resp = await client.get("/api/v1/credentials/status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_bound"] is False
