/**
 * Golden Example: Wi-Fi Provisioning (Security 1 + SoftAP) config (esp32-wifi-provision 黄金示例)
 * 这是 golden example，供技能验证用，非生产代码。
 * Security 1 = Proof of Possession (PoP) 字符串验证。
 * 凭据 NVS 持久化标注"运行时核验"（基线未直接确认）。
 * See SKILL.md §provisioning-comparison.md §security-scheme.md
 */

#include <string.h>
#include "wifi_provisioning/manager.h"
#include "wifi_provisioning/scheme_softap.h"
#include "nvs_flash.h"

/* PoP 密码（生产环境需随机生成或设备唯一） */
#define PROV_POP_PASSWORD  "tinynas-2026"
#define PROV_SEC_VERSION   WIFI_PROV_SECURITY_1

void ge_wifi_provision_init(void) {
    /* NVS 初始化（凭据持久化存储，运行时核验） */
    nvs_flash_init();

    wifi_prov_scheme_softap_config_t softap_config = {
        .scheme = wifi_prov_scheme_softap,
        .pop_type = WIFI_PROV_POP_TYPE_STRING,
        .pop = PROV_POP_PASSWORD,
    };

    wifi_prov_mgr_config_t mgr_config = {
        .scheme = softap_config,
        .scheme_event_handler = WIFI_PROV_EVENT_HANDLER_NONE,
    };

    wifi_prov_mgr_init(mgr_config);

    /* 启动配网：设备创建名为 "ESP-PROV" 的 SoftAP */
    wifi_prov_mgr_start_provisioning(
        PROV_SEC_VERSION,
        PROV_POP_PASSWORD,  /* PoP */
        "ESP-PROV",          /* SoftAP SSID */
        NULL                 /* SoftAP 密码（开放） */
    );
}
