# security.py — 密码哈希 (bcrypt) + 教务凭证加密 (AES-256-GCM / Fernet)
import base64
import bcrypt
from cryptography.fernet import Fernet, InvalidToken
from app.config import settings

# Fernet (AES-256-GCM) 凭证加密 — 延迟初始化 + 密钥验证
_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    """惰性初始化 Fernet，验证密钥是否为有效的 32 字节 Base64"""
    global _fernet
    if _fernet is None:
        key = settings.CREDENTIAL_ENCRYPTION_KEY
        try:
            # 验证密钥是有效的 32 字节 URL-safe Base64
            decoded = base64.urlsafe_b64decode(key.encode())
            if len(decoded) != 32:
                raise ValueError(
                    f"CREDENTIAL_ENCRYPTION_KEY 解密后应为 32 字节，实际 {len(decoded)} 字节。"
                    f" 请用 'python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"' 生成"
                )
        except Exception as e:
            raise ValueError(
                f"CREDENTIAL_ENCRYPTION_KEY 无效: {e}。"
                f" 请用 'python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"' 生成"
            )
        _fernet = Fernet(key.encode())
    return _fernet


def hash_password(password: str) -> str:
    """对用户密码进行 bcrypt 哈希"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码是否匹配 bcrypt 哈希"""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def encrypt_credential(plain_text: str) -> str:
    """使用 Fernet (AES-256-GCM) 加密教务凭证"""
    return _get_fernet().encrypt(plain_text.encode()).decode()


def decrypt_credential(encrypted_text: str) -> str:
    """解密 Fernet 加密的教务凭证"""
    return _get_fernet().decrypt(encrypted_text.encode()).decode()
