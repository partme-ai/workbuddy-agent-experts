#!/bin/bash
# Golden Example: coredump parse wrapper (esp32-debug 黄金示例)
# 这是 golden example，供技能验证用，非生产代码。
# 封装 idf.py coredump-info / coredump-debug 调用 + ELF 输入检查。
# 未安装 IDF 时标记 SKIPPED（不报 fail）。
# See SKILL.md §crash-triage.md §jtag-openocd.md

set -euo pipefail

COREDUMP_FILE="${1:?usage: $0 <coredump-file> [elf-file]}"
ELF_FILE="${2:-build/hello_world.elf}"

echo "=== Coredump Parse Golden Example ==="

# 检测 IDF 环境
if ! command -v idf.py >/dev/null 2>&1; then
    if [ -z "${IDF_PATH:-}" ]; then
        echo "⏭️  IDF not found (IDF_PATH not set, idf.py not in PATH) — SKIPPED"
        echo "   To run: . /path/to/esp-idf/export.sh && $0 $COREDUMP_FILE $ELF_FILE"
        exit 0
    fi
fi

# 检查输入文件
[ -f "$COREDUMP_FILE" ] || { echo "❌ coredump file not found: $COREDUMP_FILE"; exit 1; }
if [ -n "$ELF_FILE" ] && [ ! -f "$ELF_FILE" ]; then
    echo "⚠️  ELF file not found: $ELF_FILE (symbolication unavailable)"
    ELF_FILE=""
fi

echo "[1/3] Coredump file: $COREDUMP_FILE ($(wc -c < "$COREDUMP_FILE") bytes)"

echo "[2/3] Parsing with idf.py coredump-info..."
if [ -n "$ELF_FILE" ]; then
    idf.py coredump-info -c "$COREDUMP_FILE" -e "$ELF_FILE" 2>&1 | head -50
else
    idf.py coredump-info -c "$COREDUMP_FILE" 2>&1 | head -50
fi

echo ""
echo "[3/3] Done. For interactive debug, use: idf.py coredump-debug -c $COREDUMP_FILE -e $ELF_FILE"
echo ""
echo "=== crash-triage checklist ==="
echo "1. 复位原因（panic / watchdog / brownout / power loss）"
echo "2. 崩溃 PC / backtrace"
echo "3. 寄存器快照"
echo "4. 栈顶变量（需 ELF 符号）"
echo "5. 假设性缓解观察项须标注：'因果未经 HIL 实证，验证路由 fw-hil-testing'"
