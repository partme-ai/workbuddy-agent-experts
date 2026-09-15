/**
 * Golden Example: GPIO output + UART transmit init (esp32-peripherals 黄金示例)
 * 这是 golden example，供技能验证用，非生产代码。
 * 引脚号须核验芯片 datasheet 或板原理图，禁止编造 Strapping 引脚值。
 * See SKILL.md §Workflow 1: "引脚落点：核验后的引脚号必须显式写入驱动初始化配置"
 */

#include <stdio.h>
#include "driver/gpio.h"
#include "driver/uart.h"

/* ⚠️ 引脚号须核验目标板原理图或 datasheet，此处为 ESP32-C3 常见默认 */
#define BLINK_GPIO      GPIO_NUM_8   /* C3 板载 LED（非 Strapping 引脚） */
#define UART_TX_PIN     GPIO_NUM_21  /* 以板实测为准 */
#define UART_RX_PIN     GPIO_NUM_20  /* 以板实测为准 */
#define UART_PORT_NUM   UART_NUM_1

void ge_gpio_init(void) {
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << BLINK_GPIO),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    gpio_config(&io_conf);
    gpio_set_level(BLINK_GPIO, 0);
}

void ge_uart_init(void) {
    uart_config_t uart_config = {
        .baud_rate = 115200,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };
    uart_param_config(UART_PORT_NUM, &uart_config);
    uart_set_pin(UART_PORT_NUM, UART_TX_PIN, UART_RX_PIN,
                 UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
    uart_driver_install(UART_PORT_NUM, 1024, 1024, 0, NULL, 0);
}

void app_main(void) {
    ge_gpio_init();
    ge_uart_init();
    gpio_set_level(BLINK_GPIO, 1);
    uart_write_bytes(UART_PORT_NUM, "hello tinynas\n", 14);
}
