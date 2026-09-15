# 分区表模板（partition-table-template）

read-when：新建工程要自定义分区、或为 OTA 准备双 app 槽。
基线：ESP-IDF v6.1，走读 2026-09-02（官方分区表文档，置信度高）。

## 机制要点

- CSV 默认烧在 **0x8000**；首行注释 `# Name, Type, SubType, Offset, Size, Flags`。
- 最多 95 项，末尾自动附 MD5 校验。
- **Offset 留空 = 自动排布**（推荐）；app 分区须 64KB 对齐，data 分区 4KB 对齐。
- Type：`app` / `data` / `bootloader` / `partition_table`。
- app SubType：`factory`、`ota_0`(0x10)~`ota_15`(0x1F)、`test`。
- data SubType：`nvs`、`phy`、`ota`(otadata)、`coredump`、`fat`、`spiffs` 等。
- OTA 双分区布局 = **factory + ota_0 + ota_1 + otadata**：bootloader 按 otadata 的 ota_seq 选启动槽，otadata 为空则启动 factory。
- 构建时校验：app 镜像必须放得进某个 app 分区，放不下直接报错（好事，别绕过）。

## 模板一：单 factory（无 OTA）

```csv
# Name,   Type, SubType, Offset,  Size,    Flags
nvs,      data, nvs,     ,        0x6000,
phy_init, data, phy,     ,        0x1000,
factory,  app,  factory,  ,        0x300000,
coredump, data, coredump, ,        0x10000,
```

## 模板二：双 OTA 槽（OTA 改造起点）

```csv
# Name,   Type, SubType, Offset,  Size,    Flags
nvs,      data, nvs,     ,        0x6000,
otadata,  data, ota,     ,        0x2000,
phy_init, data, phy,     ,        0x1000,
ota_0,    app,  ota_0,   ,        0x1F0000,
ota_1,    app,  ota_1,   ,        0x1F0000,
coredump, data, coredump, ,        0x10000,
```

说明：以上 Size 为**示意值**，必须按实测 flash 容量与 app 实际大小调整（`idf.py build` 末尾会报告镜像大小）；勿照抄到 1MB flash 的模组上。Offset 全部留空交由工具自动排布，天然满足对齐要求。

## 反幻觉红线

- **禁止编造分区偏移**：不知道就留空自动排布，或以 `idf.py partition-table` 打印结果为准。
- **Flash 总容量以实物为准**：menuconfig 的 flash size 与模组实际容量不一致会导致布局错误，改分区前先核对。
- 两份模板都要配合 menuconfig 的 Partition Table 预设指向自定义 CSV 才生效。

## 验证命令

```bash
idf.py partition-table           # 打印解析后的分区表
idf.py partition-table-flash     # 单独烧分区表（改表后需重新烧写）
idf.py build                     # 构建期校验镜像与 app 分区匹配
```

CSV↔bin 由 gen_esp32part.py 转换；改完 CSV 直接 build 即可再生并校验。
