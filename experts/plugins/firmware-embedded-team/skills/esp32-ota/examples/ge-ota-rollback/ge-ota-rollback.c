/**
 * Golden Example: OTA rollback logic (esp32-ota 黄金示例)
 * 这是 golden example，供技能验证用，非生产代码。
 * 核心反陷阱：CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE 启用后，新映像
 *   必须显式调用 esp_ota_mark_app_valid_cancel_rollback() 否则重启回滚。
 * See SKILL.md §ota-state-machine.md §rollback-checklist.md
 */

#include <string.h>
#include "esp_ota_ops.h"
#include "esp_log.h"

static const char *TAG = "ge-ota";

esp_err_t ge_ota_begin_and_write(const void *firmware_data, size_t firmware_size) {
    esp_ota_handle_t update_handle = 0;
    const esp_partition_t *update_partition = NULL;

    update_partition = esp_ota_get_next_update_partition(NULL);
    if (update_partition == NULL) {
        ESP_LOGE(TAG, "no OTA partition available");
        return ESP_FAIL;
    }

    esp_err_t err = esp_ota_begin(update_partition, OTA_SIZE_UNKNOWN, &update_handle);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "esp_ota_begin failed: %s", esp_err_to_name(err));
        return err;
    }

    err = esp_ota_write(update_handle, firmware_data, firmware_size);
    if (err != ESP_OK) {
        esp_ota_abort(update_handle);
        ESP_LOGE(TAG, "esp_ota_write failed: %s", esp_err_to_name(err));
        return err;
    }

    err = esp_ota_end(update_handle);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "esp_ota_end failed: %s", esp_err_to_name(err));
        return err;
    }

    err = esp_ota_set_boot_partition(update_partition);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "set_boot_partition failed: %s", esp_err_to_name(err));
        return err;
    }

    ESP_LOGI(TAG, "OTA complete, will boot from new partition on restart");
    return ESP_OK;
}

/**
 * 新映像启动后必须调用：确认运行正常 → 取消回滚标记。
 * 若不调用，下次重启 bootloader 将回滚到旧映像。
 */
void ge_ota_mark_valid(void) {
    esp_err_t err = esp_ota_mark_app_valid_cancel_rollback();
    if (err == ESP_OK) {
        ESP_LOGI(TAG, "app marked valid, rollback cancelled");
    } else {
        ESP_LOGE(TAG, "mark_app_valid failed: %s", esp_err_to_name(err));
    }
}
