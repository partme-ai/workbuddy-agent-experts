# Golden Example: signing pipeline stages (esp32-secureboot)
# 这是 golden example，供技能验证用，非生产代码。
# 演示：开发 rehearsal → 小批量试产 → 放量三阶段签名流水线。
# See SKILL.md §key-governance.md §sb2-facts.md

## Stage 1: Development Rehearsal

```bash
# 生成开发用密钥对（仅用于本地测试，不保护）
openssl genpkey -algorithm ed25519 -out dev-signing-key.pem
openssl pkey -in dev-signing-key.pem -pubout -out dev-signing-pub.pem

# 用开发密钥签名固件
openssl pkeyutl -sign -inkey dev-signing-key.pem -rawin -in firmware.bin -out firmware.sig

# Secure Boot 仿真模式（不烧 eFuse，可逆）
idf.py -DSECURE_BOOT_FLASH_ENCRYPTION_SCHEME="Development" menuconfig
idf.py build && idf.py flash
```

## Stage 2: Pilot Production (小批量试产)

```bash
# 生成生产密钥对（HSM 或离线机器，绝不联网）
openssl genpkey -algorithm ed25519 -out prod-signing-key.pem
# → 立即导出公钥，删除私钥本机副本，私钥仅存 HSM

# 烧录 Secure Boot eFuse（不可逆！先 rehearsal 验证！）
espefuse.py --port /dev/ttyUSB0 burn_key secure_boot_signing_key prod-signing-pub.pem SECURE_BOOT_DIGEST0

# 签名固件（私钥从 HSM 取出签名，不落盘）
esptool.py sign_data --key prod-signing-key.pem --output firmware-signed.bin firmware.bin
```

## Stage 3: Mass Production (放量)

```bash
# CI 环境只持有签名后的固件（firmware-signed.bin），不持有私钥
# 烧录命令不含签名操作（已在 Stage 2 完成）
esptool.py --chip esp32c3 write_flash 0x10000 firmware-signed.bin
```

## eFuse 烧录顺序（以官方 security 文档为准，运行时核验）

1. **先 Secure Boot v2**：烧录签名公钥摘要到 eFuse（不可逆）
2. **后 Flash Encryption**：启用加密（Release 模式不可回退，明文烧录限制 3 次）

> ⚠️ "先 SB 后 FE" 为基线建议，以官方 security 文档为准。
