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
if [ -f "$IMG" ]; then
  pass "$IMG exists"
else
  fail "$IMG not found"
fi
if [ -f "${IMG}.sha256" ]; then
  pass "sha256 present"
else
  fail "sha256 missing"
fi

echo "── 2. 校验和 ──"
if [ -f "${IMG}.sha256" ]; then
    if sha256sum -c "${IMG}.sha256" >/dev/null 2>&1; then
      pass "sha256 OK"
    else
      fail "sha256 mismatch"
    fi
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
    if [ "$HITS" -eq 0 ]; then
      pass "zero external links"
else
      fail "found $HITS files with external links"
fi
fi

echo "── 5. 密钥泄露扫描 ──"
HITS=$(grep -rlE '(PRIVATE KEY|SECRET=)' "$IMG" 2>/dev/null | wc -l)
if [ "$HITS" -eq 0 ]; then
  pass "no private keys in artifact"
else
  fail "potential key leak in artifact"
fi

echo "══════════════"
[ "$FAIL" -eq 0 ] && echo "✅ Release gate passed" || echo "❌ Release gate failed"
exit $FAIL
