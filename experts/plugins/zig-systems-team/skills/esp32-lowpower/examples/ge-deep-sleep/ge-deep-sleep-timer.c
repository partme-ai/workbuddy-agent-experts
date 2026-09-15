/**
 * Golden Example: deep sleep with timer wakeup (esp32-lowpower 黄金示例)
 * 这是 golden example，供技能验证用，非生产代码。
 * µA 数值为 UNVERIFIED——技能正文和 references 中已拒绝背书具体数字，
 *   审批时须以功率计实测为准。
 * See SKILL.md §sleep-modes.md §wakeup-sources.md
 */

#include <stdio.h>
#include "esp_sleep.h"
#include "esp_log.h"

static const char *TAG = "ge-deep-sleep";

/**
 * 定时唤醒深睡（最小可运行示例）
 * ⚠️ 深睡电流（如 10µA 典型）为社区转述，基线 UNVERIFIED，禁止写入文档。
 *    验收用功率计实测（路由 fw-hil-testing）。
 */
void ge_deep_sleep_timer(uint64_t sleep_sec) {
    ESP_LOGI(TAG, "entering deep sleep for %llu seconds", (unsigned long long)sleep_sec);
    esp_sleep_enable_timer_wakeup(sleep_sec * 1000000ULL);
    esp_deep_sleep_start();
    /* 不会执行到这里 */
}

/**
 * GPIO 唤醒深睡（EXT0 = 单 GPIO 高电平）
 * ⚠️ 唤醒源支持范围因芯片而异（ESP32 支持 EXT0/EXT1，ESP32-C3 仅有限支持）。
 *    以 datasheet 和 sdkconfig 为准。
 */
void ge_deep_sleep_gpio(gpio_num_t gpio_num) {
    ESP_LOGI(TAG, "entering deep sleep, wakeup on GPIO %d high", gpio_num);
    esp_sleep_enable_ext0_wakeup(gpio_num, 1);
    esp_deep_sleep_start();
}
