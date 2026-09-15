# 发布前检查单（release-checklist，可脚本化骨架）

read-when：执行 `fw-release-gate` 发布门禁时。风格对标生产门禁脚本（run-lint.sh 模式）：pass/fail 计数、全绿退出 0、任一失败退出 1。

## 1. 脚本骨架（通用模式，按项目替换顶部变量）

```sh
#!/bin/sh
# release-gate.sh — 发布门禁骨架。用法: BIN_DIR=out RELEASE_NOTES=notes.md sh release-gate.sh
set -u
BIN_DIR="${BIN_DIR:-out}"
NOTES="${RELEASE_NOTES:-RELEASE_NOTES.md}"
ROLLBACK_DOC="${ROLLBACK_DOC:-ROLLBACK.md}"
EXTS="${EXTS:-img\.gz|bin|img}"            # 产物扩展名枚举（正则片段）
NAME_RE='^[a-z]+_[a-z0-9-]+_v[0-9]+\.[0-9]+\.[0-9]+-(stable|beta|dev)_20[0-9]{6}\.(img\.gz|bin|img)$'
TEST_KEY_EXEMPT="${TEST_KEY_EXEMPT:-tests/fixtures/keys/}"   # 有意入库的公开测试密钥目录

FAIL=0
pass() { echo "  PASS $1"; }
fail() { echo "  FAIL $1"; FAIL=1; }

echo "== 1. 产物存在 + sha256 成对且重算一致 =="
FOUND=0
for f in "$BIN_DIR"/*; do
  case "$f" in *.sha256) continue ;; esac
  echo "$f" | grep -qE "\.($EXTS)$" || continue
  FOUND=1
  [ -f "$f.sha256" ] || fail "缺 $f.sha256"
done
[ "$FOUND" -eq 1 ] || fail "BIN_DIR 无产物"
if ls "$BIN_DIR"/*.sha256 >/dev/null 2>&1; then
  (cd "$BIN_DIR" && sha256sum -c *.sha256 >/dev/null 2>&1) \
    && pass "校验和重算一致" || fail "校验和重算失败（或平台缺 sha256sum，换 shasum -c）"
fi

echo "== 2. 命名 lint =="
for f in "$BIN_DIR"/*; do
  case "$f" in *.sha256) continue ;; esac
  echo "$f" | grep -qE "\.($EXTS)$" || continue
  basename "$f" | grep -qE "$NAME_RE" && pass "$(basename "$f")" || fail "命名不合规: $(basename "$f")"
done

echo "== 3. 零外链扫描（随包前端/资源） =="
if grep -rqE '(src|href)="https?://' "$BIN_DIR" 2>/dev/null; then
  fail "外链: $(grep -rlE '(src|href)="https?://' "$BIN_DIR" 2>/dev/null | tr '\n' ' ')"
else
  pass "零公网外链"
fi

echo "== 4. 密钥/凭据扫描 =="
LEAK=$(find "$BIN_DIR" . -maxdepth 3 \( -name '*priv*' -o -name '*secret*' -o -name '*salt*' -o -name '*.pem' \) -type f 2>/dev/null | grep -v "^$TEST_KEY_EXEMPT" | head -5)
[ -n "$LEAK" ] && fail "疑似私钥/凭据: $LEAK" || pass "无密钥入库（测试密钥目录已豁免）"

echo "== 5. 回滚预案 =="
[ -f "$ROLLBACK_DOC" ] && grep -q . "$ROLLBACK_DOC" && pass "回滚预案存在" || fail "缺回滚预案 $ROLLBACK_DOC"

echo "== 6. HIL 徽章达标 =="
grep -q 'HIL Verified' "$NOTES" 2>/dev/null && pass "发布说明载明 HIL Verified" \
  || fail "发布说明未载明 HIL Verified（B0/B1 只能进内部/测试渠道）"

echo "== 7. 发布说明含已知问题 =="
grep -q '已知问题' "$NOTES" 2>/dev/null && pass "已知问题小节存在" || fail "发布说明缺'已知问题'（无也要写'已知问题：无'）"

echo "== 8. LICENSE 清单 =="
[ -f "$NOTES" ] && grep -qi 'license\|许可证' "$NOTES" && pass "许可证清单在发布说明" || fail "缺 LICENSE 清单"

echo "============================"
if [ "$FAIL" -eq 0 ]; then echo "ALL PASS"; else echo "GATE FAILED"; fi
exit $FAIL
```

## 2. 使用说明

- 所有变量在脚本顶部集中声明，接项目时只改顶部，不改检查逻辑；
- 校验和工具按平台选择：Linux 用 `sha256sum -c`，macOS 用 `shasum -a 256 -c`（骨架已留替换点）；
- 密钥扫描只报**路径**不打印内容；豁免目录必须是有意公开的测试密钥，并在 README 标注不具生产权限；
- 新增项目专属检查项时追加编号小节，保持 pass/fail 计数风格，不要引入"警告级"——门禁里警告等于忽略。

## 3. 负向验证（门禁自检，接好后必做一次）

1. 改掉一个产物文件名 → 第 2 项必须 FAIL；
2. 篡改镜像一个字节（不改 .sha256）→ 第 1 项必须 FAIL；
3. 删掉一个 `.sha256` → 第 1 项必须 FAIL；
4. 发布说明删掉"已知问题"→ 第 7 项必须 FAIL。
四条全拦住才算门禁可用；拦不住任何一条的检查项是摆设，删掉重写。

## 私钥泄露响应 runbook

1. **立即停用**：泄露私钥签发的所有产物视为不可信，下架受影响渠道固件；
2. **评估与轮换**：确定泄露时间窗 → 换根/子密钥重签 → 下一版固件内嵌新验证公钥（密钥环过渡期同时接受新旧）；
3. **子密钥作废**：按渠道撤销并重发；对账核对泄露窗口内异常激活；
4. **复盘成文**：泄露路径/时间线/防再发归档（“作废流程成文”为发布前置）。
