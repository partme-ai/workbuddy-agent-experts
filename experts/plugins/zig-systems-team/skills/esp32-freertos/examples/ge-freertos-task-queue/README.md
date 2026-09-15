# GE · freertos-task-queue（esp32-freertos 黄金示例）

**徽章**：`B0 Build Verification Only`（代码片段，需 IDF 环境编译验证）

## 与 SKILL.md 映射

- §Pitfalls: "栈单位是字节不是字" → `STACK_SIZE 2048` + 注释
- §Pitfalls: "vTaskSuspendAll 仅当前核" → 未使用（注释说明）
- §Workflow 1: `xTaskCreatePinnedToCore` → producer=PRO_CPU(0), consumer=APP_CPU(1)
- §References: task-checklist.md → 栈/优先级/队列使用清单
- §References: smp-pinning.md → PRO_CPU/APP_CPU 芯片表

## 验证

```bash
# 需 IDF v6.1 + esp32 target（参考 esp32-idf/ge-idf-hello-build）
idf.py set-target esp32
idf.py build  # 编译通过即为 B0 证据
```
