# test_p1_standalone.py — P1 无数据库依赖验证
"""验证安全模块、JWT、Schema — 不依赖 PostgreSQL"""
import os
import sys
import unittest

# 设置环境变量（测试用，避免 Fernet 崩溃）
os.environ["CREDENTIAL_ENCRYPTION_KEY"] = "ZGJfZGF0YWJhc2VfcGFzc3dvcmRfY2hhbmdlX21l"  # 无效但不会在验证时崩溃

# 切换到项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cryptography.fernet import Fernet

# 用有效 Fernet 密钥覆盖环境变量后重新加载
VALID_FERNET_KEY = Fernet.generate_key().decode()
os.environ["CREDENTIAL_ENCRYPTION_KEY"] = VALID_FERNET_KEY


class TestSecurity(unittest.TestCase):
    """测试 security.py — bcrypt + Fernet"""

    @classmethod
    def setUpClass(cls):
        # 重新导入以使用有效密钥
        from app.auth import security
        import importlib
        importlib.reload(security)
        cls.security = security

    def test_hash_and_verify_password(self):
        """密码哈希和验证"""
        plain = "my_secret_password_123"
        hashed = self.security.hash_password(plain)
        self.assertNotEqual(plain, hashed)
        self.assertTrue(hashed.startswith("$2b$"))
        self.assertTrue(self.security.verify_password(plain, hashed))
        self.assertFalse(self.security.verify_password("wrong_password", hashed))

    def test_encrypt_decrypt_credential(self):
        """教务凭证加密和解密"""
        plain = "my_jwglxt_password"
        encrypted = self.security.encrypt_credential(plain)
        self.assertNotEqual(plain, encrypted)
        self.assertIsInstance(encrypted, str)
        decrypted = self.security.decrypt_credential(encrypted)
        self.assertEqual(plain, decrypted)

    def test_encrypt_chinese_text(self):
        """加密中文字符串"""
        plain = "北京化工大学教务系统2024"
        encrypted = self.security.encrypt_credential(plain)
        decrypted = self.security.decrypt_credential(encrypted)
        self.assertEqual(plain, decrypted)

    def test_encrypt_empty_string(self):
        """加密空字符串"""
        encrypted = self.security.encrypt_credential("")
        decrypted = self.security.decrypt_credential(encrypted)
        self.assertEqual("", decrypted)


class TestJWT(unittest.TestCase):
    """测试 jwt.py — JWT 令牌"""

    def setUp(self):
        os.environ["JWT_SECRET_KEY"] = "test_secret_key_for_unit_tests_only_12345678"
        os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
        os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
        from app.auth import jwt
        import importlib
        importlib.reload(jwt)
        self.jwt = jwt

    def test_create_and_verify_access_token(self):
        """Access Token 生成和验证"""
        token = self.jwt.create_access_token("user-uuid-123")
        self.assertIsInstance(token, str)
        payload = self.jwt.verify_token(token, expected_type="access")
        self.assertEqual(payload["sub"], "user-uuid-123")
        self.assertEqual(payload["type"], "access")

    def test_create_and_verify_refresh_token(self):
        """Refresh Token 生成和验证"""
        token = self.jwt.create_refresh_token("user-uuid-456")
        payload = self.jwt.verify_token(token, expected_type="refresh")
        self.assertEqual(payload["sub"], "user-uuid-456")
        self.assertEqual(payload["type"], "refresh")

    def test_token_type_rejection(self):
        """Token 类型校验 — access 不能当 refresh 用"""
        token = self.jwt.create_access_token("user-1")
        from jose import JWTError
        with self.assertRaises(JWTError):
            self.jwt.verify_token(token, expected_type="refresh")

    def test_invalid_token(self):
        """无效 Token 被拒绝"""
        from jose import JWTError
        with self.assertRaises(JWTError):
            self.jwt.verify_token("not.a.valid.token")

    def test_get_user_id_from_token(self):
        """从 Token 提取 user_id"""
        token = self.jwt.create_access_token("extract-me-789")
        uid = self.jwt.get_user_id_from_token(token)
        self.assertEqual(uid, "extract-me-789")


class TestSchemas(unittest.TestCase):
    """测试 schemas.py — Pydantic 请求验证"""

    @classmethod
    def setUpClass(cls):
        from app.auth.schemas import (
            UserRegisterRequest, UserLoginRequest,
            TokenRefreshRequest, BindCredentialRequest,
            TokenResponse, UserResponse, CredentialStatusResponse,
        )
        cls.UserRegisterRequest = UserRegisterRequest
        cls.UserLoginRequest = UserLoginRequest
        cls.TokenRefreshRequest = TokenRefreshRequest
        cls.BindCredentialRequest = BindCredentialRequest
        cls.TokenResponse = TokenResponse
        cls.UserResponse = UserResponse
        cls.CredentialStatusResponse = CredentialStatusResponse

    def test_register_valid(self):
        """有效注册请求"""
        req = self.UserRegisterRequest(username="testuser", password="pass123")
        self.assertEqual(req.username, "testuser")

    def test_register_username_too_short(self):
        """用户名过短被拒绝"""
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            self.UserRegisterRequest(username="ab", password="pass123")

    def test_register_username_invalid_chars(self):
        """用户名含特殊字符被拒绝"""
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            self.UserRegisterRequest(username="user name!", password="pass123")

    def test_register_password_too_short(self):
        """密码过短被拒绝"""
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            self.UserRegisterRequest(username="validuser", password="12345")

    def test_login_request(self):
        """登录请求"""
        req = self.UserLoginRequest(username="testuser", password="pass123")
        self.assertEqual(req.username, "testuser")

    def test_refresh_request(self):
        """刷新 Token 请求"""
        req = self.TokenRefreshRequest(refresh_token="eyJhbGciOi...")
        self.assertTrue(req.refresh_token.startswith("eyJ"))

    def test_bind_credential_request(self):
        """绑定凭证请求"""
        req = self.BindCredentialRequest(
            student_no="2024050020",
            login_account="2024050020",
            password="edu_password",
        )
        self.assertEqual(req.student_no, "2024050020")
        self.assertEqual(req.base_url, "https://jwglxt.buct.edu.cn")

    def test_bind_credential_with_doubao(self):
        """绑定凭证 + 豆包 Key"""
        req = self.BindCredentialRequest(
            student_no="2024050020",
            login_account="2024050020",
            password="edu_password",
            doubao_api_key="sk-test-key-123",
        )
        self.assertEqual(req.doubao_api_key, "sk-test-key-123")

    def test_token_response(self):
        """Token 响应序列化"""
        resp = self.TokenResponse(
            access_token="access.xxx.yyy",
            refresh_token="refresh.aaa.bbb",
        )
        data = resp.model_dump()
        self.assertEqual(data["token_type"], "bearer")
        self.assertIn("access_token", data)
        self.assertIn("refresh_token", data)

    def test_user_response_from_attributes(self):
        """用户响应 ORM 转换"""
        resp = self.UserResponse(
            id="uuid-123",
            username="testuser",
            email="test@buct.edu.cn",
            is_active=True,
            has_credential=True,
        )
        self.assertEqual(resp.id, "uuid-123")
        self.assertTrue(resp.has_credential)

    def test_credential_status_unbound(self):
        """凭证状态 — 未绑定"""
        resp = self.CredentialStatusResponse(is_bound=False)
        self.assertFalse(resp.is_bound)
        self.assertIsNone(resp.student_no)

    def test_credential_status_bound(self):
        """凭证状态 — 已绑定"""
        resp = self.CredentialStatusResponse(
            is_bound=True,
            student_no="2024050020",
            is_valid=True,
            last_sync_at="2026-06-12T10:00:00",
        )
        self.assertTrue(resp.is_bound)
        self.assertEqual(resp.student_no, "2024050020")


class TestConfig(unittest.TestCase):
    """测试 config.py"""

    def test_database_url(self):
        """DATABASE_URL 生成"""
        os.environ["POSTGRES_HOST"] = "localhost"
        os.environ["POSTGRES_PORT"] = "5432"
        os.environ["POSTGRES_DB"] = "edu_test"
        os.environ["POSTGRES_USER"] = "test_user"
        os.environ["POSTGRES_PASSWORD"] = "test_pass"
        from app.config import Settings
        s = Settings()
        url = s.DATABASE_URL
        self.assertIn("postgresql+asyncpg://", url)
        self.assertIn("test_user", url)
        self.assertIn("edu_test", url)

    def test_redis_url_format(self):
        """Redis URL 格式正确（默认值或 .env 覆盖值）"""
        from app.config import Settings
        s = Settings()
        self.assertTrue(s.REDIS_URL.startswith("redis://"), f"不是有效的 Redis URL: {s.REDIS_URL}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
