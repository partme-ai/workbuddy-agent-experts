#!/bin/sh
# Golden Example: release-gate pre-publish checklist script
# This is a golden example for skill verification, not production code.
# pass/fail counter, 全绿 exit 0; 任一 fail → exit 1.
# See SKILL.md §release-checklist.md §naming-and-versioning.md

set -u
FAIL=0
pass() { echo "  ✅ $1"; }
fail() { echo "  ❌ $1"; FAIL=1; }

IMG="${1:?usage: $0 <firmware.img.gz>}"

echo "── 1. 产物存在 ──"
[ -f "$IMG" ] && pass "$IMG exists" || fail "$IMG not found"
[ -f "${IMG}.sha256" ] && pass "sha256 present" || fail "sha256 missing"

echo "── 2. 校验和 ──"
if [ -f "${IMG}.sha256" ]; then
    sha256sum -c "${IMG}.sha256" >/dev/null 2>&1 && pass "sha256 OK" || fail "sha256 mismatch"
fi

echo "── 3. 命名规范（五段式）──"
BASE=$(basename "$IMG")
case "$BASE" in
    openwrt_tinynas-*) pass "naming OK: $BASE" ;;
    *) fail "naming: expected openwrt_tinynas-* prefix, got $BASE" ;;
esac

echo "── 4. 外链扫描（零外链）──"
# 如果产物目录下有 www/，扫描外链
if [ -d "${IMG%/*}/www" ]; then
    HITS=$(grep -rlE '(src|href)="https?://' "${IMG%/*}/www" 2>/dev/null | wc -l)
    [ "$HITS" -eq 0 ] && pass "zero external links" || fail "found $HITS files with external links"
fi

echo "── 5. 密钥泄露扫描 ──"
HITS=$(grep -rlE '(PRIVATE KEY|SECRET=)' "$IMG" 2>/dev/null | wc -l)
[ "$HITS" -eq 0 ] && pass "no private keys in artifact" || fail "potential key leak in artifact"

echo "══════════════"
[ "$FAIL" -eq 0 ] && echo "✅ Release gate passed" || echo "❌ Release gate failed"
exit $FAIL
