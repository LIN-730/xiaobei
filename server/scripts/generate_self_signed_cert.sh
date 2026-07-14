#!/bin/bash
# 生成自签名 SSL 证书（开发/测试用）
# 生产环境请使用 Let's Encrypt 或购买正式证书

set -e

SSL_DIR="$(cd "$(dirname "$0")/../ssl" && pwd)"
DAYS=365
COUNTRY="CN"
STATE="Beijing"
CITY="Beijing"
ORG="BUCT"
COMMON_NAME="localhost"

echo "[*] 生成自签名 SSL 证书到: $SSL_DIR"

openssl req -x509 -nodes -days "$DAYS" \
    -newkey rsa:2048 \
    -keyout "$SSL_DIR/server.key" \
    -out "$SSL_DIR/server.crt" \
    -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/CN=$COMMON_NAME"

echo "[+] 证书已生成:"
echo "    证书: $SSL_DIR/server.crt"
echo "    私钥: $SSL_DIR/server.key"
echo ""
echo "[*] 启用 HTTPS:"
echo "    1. 取消 nginx/nginx.conf 中 HTTPS server 块的注释"
echo "    2. 重启 nginx: docker compose restart nginx"
