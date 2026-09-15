---
name: zig-crypto
license: Apache-2.0
description: Zig 加密与安全技能。涉及 std.crypto 的哈希、AEAD 加密、数字签名、密钥交换、密码哈希、KDF 和安全随机数。在需要加解密数据、验证签名或安全存储密码时调用。
---

# Zig 加密与安全

> 基于 std.crypto 的密码学原语（Zig 0.16.0）。

## Capability Boundaries

### ✅ 强项
1. 哈希计算（SHA-2、SHA-3、Blake3、BLAKE2）
2. AEAD 加密/解密（AES-GCM、ChaCha20-Poly1305）
3. 数字签名（Ed25519、ECDSA）
4. 密钥交换（X25519、ML-KEM 后量子）
5. 密码哈希（Argon2、scrypt、bcrypt、PBKDF2）
6. 消息认证码（HMAC、SipHash）
7. KDF（HKDF）
8. 安全随机数生成

### ⚠️ 前置要求
1. 确认 Zig 版本（`zig version`）
2. 理解基本密码学概念（密钥、IV、nonce）

### ❌ 不适用范围
1. 非安全场景的随机数 → 使用 `zig-0.16` 的 std.Random
2. HTTP 加密传输 → 使用 `zig-http` 技能（std.http 已内置 TLS）

## 何时使用

- "帮我加密这段数据"
- "如何计算 SHA256 哈希？"
- "生成一个 Ed25519 密钥对并签名"
- "安全地存储用户密码"

## Data Privacy

本技能不收集、存储或传输任何用户数据。所有加密操作在本地完成。

## Workflow

步骤 1. **明确需求** — 哈希/加密/签名/密码？
步骤 2. **选择算法** — 参考下方算法选择指南
步骤 3. **实现** — 使用 std.crypto.* 模块
步骤 4. **安全验证** — 确认密钥管理、nonce 唯一性

## 算法选择指南

```
需要加密？
├── 带认证 → AEAD（Aes256Gcm, ChaCha20Poly1305）
└── 流加密 → stream.chacha.*（通常应使用 AEAD）

需要哈希？
├── 通用 → Sha256, Sha512, Blake3
├── 密码存储 → argon2, scrypt, bcrypt
└── 遗留兼容 → Md5, Sha1（不推荐新设计）

需要签名？
├── 标准 → Ed25519
└── ECDSA 兼容 → ecdsa.EcdsaP256Sha256

需要密钥交换？
├── 标准 → X25519
└── 后量子 → ml_kem.*（Kyber）

需要 MAC？
├── 带密钥 → HmacSha256
└── 哈希表键控 → siphash
```

## 哈希

### SHA-256（一次性）
```zig
var digest: [std.crypto.hash.sha2.Sha256.digest_length]u8 = undefined;
std.crypto.hash.sha2.Sha256.hash("hello world", &digest, .{});
```

### SHA-256（流式）
```zig
var hasher = std.crypto.hash.sha2.Sha256.init(.{});
hasher.update("hello ");
hasher.update("world");
var digest: [32]u8 = undefined;
hasher.final(&digest);
```

### Blake3
```zig
var out: [32]u8 = undefined;
std.crypto.hash.Blake3.hash("hello world", &out, .{});
```

## AEAD 加密/解密

### ChaCha20-Poly1305
```zig
const key: [32]u8 = .{ ... };  // 32 字节密钥
const nonce: [12]u8 = .{ ... }; // 12 字节 nonce（每次加密必须唯一）
var plaintext = "hello";
var ciphertext: [64]u8 = undefined;
var tag: [16]u8 = undefined;

// 加密
try std.crypto.aead.chacha_poly.ChaCha20Poly1305.encrypt(
    ciphertext[0..plaintext.len], &tag, plaintext, nonce, key, "", .{},
);

// 解密
try std.crypto.aead.chacha_poly.ChaCha20Poly1305.decrypt(
    plaintext, ciphertext[0..plaintext.len], tag, nonce, key, "", .{},
);
```

### AES-256-GCM
```zig
const key: [32]u8 = .{ ... };
const nonce: [12]u8 = .{ ... };
var pt = "secret data";
var ct: [64]u8 = undefined;
var tag: [16]u8 = undefined;

try std.crypto.aead.aes_gcm.Aes256Gcm.encrypt(ct[0..pt.len], &tag, pt, nonce, key, "", .{});
try std.crypto.aead.aes_gcm.Aes256Gcm.decrypt(pt, ct[0..pt.len], tag, nonce, key, "", .{});
```

## 数字签名

### Ed25519 密钥生成 + 签名 + 验证
```zig
// 密钥生成
var keypair = try std.crypto.sign.Ed25519.KeyPair.generate(null);

// 签名
const msg = "hello";
var sig: [std.crypto.sign.Ed25519.Signature.encoded_length]u8 = undefined;
try keypair.sign(&sig, msg, .{});

// 验证
try keypair.public_key.verify(&sig, msg, .{});
```

## 密钥交换

### X25519
```zig
// Alice 生成密钥对
const alice_kp = try std.crypto.dh.X25519.KeyPair.generate(null);
// Bob 生成密钥对
const bob_kp = try std.crypto.dh.X25519.KeyPair.generate(null);

// 共享密钥
var alice_shared: [32]u8 = undefined;
try alice_kp.sharedSecret(&alice_shared, bob_kp.public_key, .{});

var bob_shared: [32]u8 = undefined;
try bob_kp.sharedSecret(&bob_shared, alice_kp.public_key, .{});
// alice_shared == bob_shared
```

## 密码哈希

### Argon2（推荐）
```zig
const password = "user_password";
var hash: [64]u8 = undefined;
try std.crypto.pwhash.argon2.strHash(password, &hash, .{});

// 验证
try std.crypto.pwhash.argon2.strVerify(&hash, password, .{});
```

### scrypt
```zig
var dk: [32]u8 = undefined;
try std.crypto.pwhash.scrypt.kdf(&dk, password, salt, .{});
```

## KDF

### HKDF
```zig
var dk: [32]u8 = undefined;
try std.crypto.kdf.hkdf.HkdfSha256.derive(&dk, ikm, salt, info, .{});
```

## 安全随机数

```zig
// 生成随机字节
var buf: [32]u8 = undefined;
std.crypto.random.bytes(&buf);

// 生成随机整数
const val = std.crypto.random.int(u64);

// 生成随机浮点数
const f = std.crypto.random.float(f64);
```

## 工具函数

```zig
// 安全清零（防止编译器优化）
std.crypto.utils.secureZero(&secret_buffer);

// 常量时间比较（防止时序攻击）
const eq = std.crypto.utils.timingSafeEql([8]u8, a, b);
```

## Gotchas

1. **Nonce 必须唯一** — AEAD 加密每次使用**不同的 nonce**，重复 nonce 会导致加密被破解
2. **密钥管理是最大风险** — std.crypto 不处理密钥存储，密钥需自行安全保管
3. **Md5 和 Sha1 不安全** — 仅用于遗留兼容，新设计使用 Sha256/Blake3
4. **`secureZero` 防止优化** — 普通置零可能被编译器优化掉，必须用 `secureZero`
5. **`timingSafeEql` 防时序攻击** — 比较密钥/MAC 时必须用常量时间比较

## FAQ

**Q：ChaCha20-Poly1305 和 AES-GCM 选哪个？**
A：硬件支持 AES-NI 时 AES-GCM 更快；无硬件加速时 ChaCha20-Poly1305 性能更好且更简单。

**Q：密码哈希为什么不用 SHA256？**
A：SHA256 太快，容易被 GPU 暴力破解。Argon2/scrypt/bcrypt 设计为计算密集型，天然抗暴力破解。

**Q：如何生成安全的随机密钥？**
A：使用 `std.crypto.random.bytes(&key)`。不要用 `std.Random.DefaultPrng`，那是伪随机不适合加密。
