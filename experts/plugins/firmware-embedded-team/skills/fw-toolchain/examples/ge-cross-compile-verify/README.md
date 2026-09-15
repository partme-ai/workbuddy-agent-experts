# GE · cross-compile-verify（fw-toolchain 黄金示例）

**徽章**：`S1 Executable Evidence`（可在 macOS/Linux 上运行）

## 被测物

| 文件 | 验证点 |
|---|---|
| `ge-cross-compile-verify.sh` | 4 个工具链检测（aarch64-musl/gnu、riscv、xtensa）、2 个编译冒烟测试、未安装标记 SKIPPED |

## 与 SKILL.md 映射

- §Workflow: "优先让平台构建系统托管工具链" → riscv/xtensa 由 IDF 托管，本脚本只检测不安装
- §Pitfalls: "禁 apt 装 xtensa gcc" → 只检测，不执行安装
- §References: hosting-matrix.md → 三平台谁托管
- §References: version-pinning.md → 工具链版本锚定

## 验证

```bash
bash -n ge-cross-compile-verify.sh && echo "syntax OK"
chmod +x ge-cross-compile-verify.sh
./ge-cross-compile-verify.sh  # 应输出 pass/skip 计数，无 fail
```
