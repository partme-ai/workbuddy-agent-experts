#!/bin/bash
# Golden Example: key governance script (esp32-secureboot 黄金示例)
# 这是 golden example，供技能验证用，非生产代码。
# 演示：生成签名密钥 → 用公钥验证签名 → 安全擦除私钥 → 输出治理报告。
# ⚠️ 生产环境密钥绝不进仓库/CI 明文。
# See SKILL.md §key-governance.md §sb2-facts.md

set -euo pipefail
WORKDIR=$(mktemp -d)
echo "=== Key Governance Golden Example ==="

echo "[1/5] Generating Ed25519 signing keypair..."
openssl genpkey -algorithm ed25519 -out "$WORKDIR/signing_key.pem" 2>/dev/null
openssl pkey -in "$WORKDIR/signing_key.pem" -pubout -out "$WORKDIR/signing_pub.pem" 2>/dev/null
echo "  private: $WORKDIR/signing_key.pem"
echo "  public:  $WORKDIR/signing_pub.pem"

echo "[2/5] Signing test payload..."
echo "firmware-v1.0.0-payload" > "$WORKDIR/payload.bin"
openssl pkeyutl -sign -inkey "$WORKDIR/signing_key.pem" -rawin -in "$WORKDIR/payload.bin" -out "$WORKDIR/sig.bin"
echo "  signature: $WORKDIR/sig.bin ($(wc -c < "$WORKDIR/sig.bin") bytes)"

echo "[3/5] Verifying signature with public key..."
if openssl pkeyutl -verify -pubin -inkey "$WORKDIR/signing_pub.pem" -rawin -in "$WORKDIR/payload.bin" -sigfile "$WORKDIR/sig.bin" >/dev/null 2>&1; then
    echo "  ✅ signature verified"
else
    echo "  ❌ signature verification FAILED"
    exit 1
fi

echo "[4/5] Securely erasing private key..."
shred -u "$WORKDIR/signing_key.pem" 2>/dev/null || rm -f "$WORKDIR/signing_key.pem"
[ -f "$WORKDIR/signing_key.pem" ] && echo "  ❌ erase failed" || echo "  ✅ private key erased"

echo "[5/5] Governance report:"
echo "  - signing_key.pem: DELETED (shred + rm)"
echo "  - signing_pub.pem: RETAINED (safe for firmware embedding)"
echo "  - ⚠️ Production key must NEVER be in repo/CI plaintext"
echo ""
echo "=== DONE ==="
rm -rf "$WORKDIR"
