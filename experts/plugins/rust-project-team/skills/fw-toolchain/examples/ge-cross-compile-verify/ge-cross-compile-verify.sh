#!/bin/sh
# Golden Example: cross-compile toolchain verification script
# This is a golden example for skill verification, not production code.
# 检测 aarch64-musl / riscv / xtensa 工具链是否存在、版本、能否编译最小 hello world.
# 未安装的工具链标记 SKIPPED（不报 fail）。
# See SKILL.md §hosting-matrix.md §version-pinning.md

set -u
TOTAL=0; PASS=0; SKIP=0; FAIL=0

check() {
    # TARGET (3rd arg) is accepted for signature symmetry but unused by this check.
    NAME="$1"; CC="$2"
    TOTAL=$((TOTAL+1))
    if command -v "$CC" >/dev/null 2>&1; then
        VER=$($CC --version 2>/dev/null | head -1)
        echo "  ✅ $NAME: $CC found — $VER"
        PASS=$((PASS+1))
    else
        echo "  ⏭️  $NAME: $CC not found — SKIPPED"
        SKIP=$((SKIP+1))
    fi
}

compile_test() {
    NAME="$1"; CC="$2"
    command -v "$CC" >/dev/null 2>&1 || return
    TMP=$(mktemp -d)
    echo 'int main(){return 0;}' > "$TMP/hello.c"
    if $CC -o "$TMP/hello" "$TMP/hello.c" 2>/dev/null; then
        echo "  ✅ $NAME: compile OK"
    else
        echo "  ❌ $NAME: compile FAILED"
        FAIL=$((FAIL+1))
    fi
    rm -rf "$TMP"
}

echo "=== Toolchain Detection ==="
check "aarch64-linux-musl" "aarch64-linux-musl-gcc" "aarch64-unknown-linux-musl"
check "aarch64-linux-gnu" "aarch64-linux-gnu-gcc" "aarch64-unknown-linux-gnu"
check "riscv32-esp-elf" "riscv32-esp-elf-gcc" "riscv32-esp-elf"
check "xtensa-esp32-elf" "xtensa-esp32-elf-gcc" "xtensa-esp32-elf"

echo ""
echo "=== Compile Smoke Test ==="
compile_test "aarch64-linux-musl" "aarch64-linux-musl-gcc"
compile_test "aarch64-linux-gnu" "aarch64-linux-gnu-gcc"

echo ""
echo "=== Summary ==="
echo "total=$TOTAL pass=$PASS skip=$SKIP fail=$FAIL"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
