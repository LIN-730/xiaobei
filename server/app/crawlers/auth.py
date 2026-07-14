# crawlers/auth.py — 教务系统登录认证（RSA PKCS1_v1_5加密）
import requests
from bs4 import BeautifulSoup
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import base64
import time
# 注意: 多用户模式下，凭据由调用方传入


def rsa_encrypt_zf(password: str, public_key: str) -> str:
    """
    使用正方教务系统RSA公钥加密密码。

    Args:
        password: 明文密码
        public_key: PEM格式的RSA公钥字符串

    Returns:
        Base64编码的加密密码
    """
    key = RSA.importKey(public_key)
    cipher = PKCS1_v1_5.new(key)
    encrypted = cipher.encrypt(password.encode())
    return base64.b64encode(encrypted).decode()


def login_edu(yhm: str, mm_plain: str, base_url: str):
    """
    登录正方教务系统，返回带JSESSIONID Cookie的requests.Session。

    登录流程:
    1. GET 登录页 → 获取 CSRF Token
    2. GET /login_getPublicKey.html → 获取 RSA 公钥 (modulus + exponent)
    3. RSA PKCS1_v1_5 加密密码 → Base64 编码
    4. POST 登录表单 → 获取 JSESSIONID Cookie
    5. GET /index_initMenu.html → 验证登录态

    Args:
        yhm: 教务系统登录账号
        mm_plain: 明文密码
        base_url: 教务系统根URL (e.g. https://jwglxt.buct.edu.cn)

    Returns:
        已登录的 requests.Session，失败返回 None
    """
    if not all([yhm, mm_plain, base_url]):
        print("❌ 缺少教务系统登录信息（yhm/mm_plain/base_url）！")
        return None

    session = requests.Session()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "max-age=0",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
    }
    session.headers.update(headers)

    # ── Step 1: 访问登录页获取 CSRF Token ──
    login_page_url = f"{base_url}/jwglxt/xtgl/login_slogin.html"
    try:
        resp = session.get(login_page_url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ 登录页访问失败: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    csrftoken_tag = soup.find("input", id="csrftoken")
    if not csrftoken_tag:
        csrftoken_tag = soup.find("input", {"name": "__RequestVerificationToken"})
        if not csrftoken_tag:
            print("❌ 未找到登录页 CSRF Token")
            return None
    csrftoken = csrftoken_tag.get("value", "")

    # ── Step 2: 获取RSA公钥 ──
    pubkey_url = f"{base_url}/jwglxt/xtgl/login_getPublicKey.html?time={int(time.time() * 1000)}"
    try:
        pubkey_resp = session.get(pubkey_url, timeout=10)
        pubkey_resp.raise_for_status()
        pubkey_data = pubkey_resp.json()
        modulus = int.from_bytes(base64.b64decode(pubkey_data["modulus"]), byteorder="big")
        exponent = int.from_bytes(base64.b64decode(pubkey_data["exponent"]), byteorder="big")
        rsa_key = RSA.construct((modulus, exponent))
        public_key_pem = rsa_key.export_key().decode()
    except Exception as e:
        print(f"❌ RSA公钥获取失败: {e}")
        return None

    # ── Step 3: 加密密码 ──
    mm_encrypted = rsa_encrypt_zf(mm_plain, public_key_pem)

    # ── Step 4: 提交登录 ──
    login_url = f"{base_url}/jwglxt/xtgl/login_slogin.html?time={int(time.time() * 1000)}"
    login_data = {
        "csrftoken": csrftoken,
        "yhm": yhm,
        "mm": mm_encrypted,
        "yzm": "",
        "language": "zh_CN",
    }
    session.headers.update({
        "Referer": login_page_url,
        "Origin": base_url,
        "Content-Type": "application/x-www-form-urlencoded",
    })

    try:
        resp = session.post(login_url, data=login_data, timeout=15, allow_redirects=True)
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return None

    # ── Step 5: 验证登录态 ──
    index_url = f"{base_url}/jwglxt/xtgl/index_initMenu.html"
    try:
        index_resp = session.get(index_url, timeout=10, allow_redirects=False)
        if index_resp.status_code == 200 and "login_slogin.html" not in index_resp.text:
            print("🎉 登录教务系统成功！")
            session.headers.update({"X-Requested-With": "XMLHttpRequest"})
            return session
        else:
            print("❌ 登录失败，账号/密码错误")
            return None
    except Exception as e:
        print(f"❌ 登录态验证失败: {e}")
        return None


if __name__ == "__main__":
    print("测试教务系统登录...")
    session = login_edu()
    if session:
        print("✅ 登录测试通过")
    else:
        print("❌ 登录测试失败")
