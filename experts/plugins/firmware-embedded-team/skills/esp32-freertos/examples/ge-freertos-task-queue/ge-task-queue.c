/**
 * Golden Example: FreeRTOS task + queue (esp32-freertos 黄金示例)
 * 这是 golden example，供技能验证用，非生产代码。
 * 栈大小单位为**字节**（与原生 FreeRTOS 的"字"不同）。
 * SMP 绑核：xTaskCreatePinnedToCore 参数 Core 0=PRO_CPU, 1=APP_CPU。
 * 优先级范围：默认 0-24（以 sdkconfig 为准），数字越大优先级越高。
 */

#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"

#define QUEUE_LEN  10
#define STACK_SIZE 2048  /* 字节，不是字！(sdkconfig 默认值=25，以实际为准) */

static QueueHandle_t xQueue;

/* 生产者：发送消息到队列，绑定 PRO_CPU */
static void producer_task(void *pvParameters) {
    int count = 0;
    for (;;) {
        count++;
        if (xQueueSend(xQueue, &count, pdMS_TO_TICKS(100)) == pdTRUE) {
            printf("[producer] sent %d\n", count);
        }
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

/* 消费者：从队列读取消息，绑定 APP_CPU */
static void consumer_task(void *pvParameters) {
    int received;
    for (;;) {
        if (xQueueReceive(xQueue, &received, pdMS_TO_TICKS(5000)) == pdTRUE) {
            printf("[consumer] got %d\n", received);
        } else {
            printf("[consumer] timeout, no data\n");
        }
    }
}

void app_main(void) {
    xQueue = xQueueCreate(QUEUE_LEN, sizeof(int));

    /* pinnedToCore: 0=PRO_CPU, 1=APP_CPU; stack=字节 */
    xTaskCreatePinnedToCore(producer_task, "producer", STACK_SIZE, NULL, 5, NULL, 0);
    xTaskCreatePinnedToCore(consumer_task, "consumer", STACK_SIZE, NULL, 5, NULL, 1);
}
