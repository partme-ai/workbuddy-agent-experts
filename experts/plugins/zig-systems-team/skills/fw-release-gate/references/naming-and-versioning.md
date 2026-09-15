# 命名与版本策略（naming-and-versioning）

read-when：给镜像定名/定版本、设计渠道与水印字段，或命名 lint 报错需要判则时。

## 1. 五段式模板

模式提炼自 TinyNAS 实践（走读 2026-09-02）：

```text
openwrt_<brand>-<tier>-<device>_v<SemVer>-<channel>_<date>.img.gz
```

| 段 | 含义 | 例 |
|---|---|---|
| 1 产品线 | 固件家族 | `openwrt`（MCU 侧可为 `fw`） |
| 2 品牌-档位-设备 | 谁的、哪档、哪台设备 | `acme-pro-n1`、`acme-lite-mt7981` |
| 3 版本-渠道 | SemVer + 渠道标签 | `v1.2.0-stable`、`v0.9.0-beta` |
| 4 日期 | 构建日期 | `20260902` |
| 5 扩展名 | 产物形态 | `.img.gz` / `.bin` |

设计理由：**文件名即元数据**——拿到一个文件，不看说明也能回答"给什么设备、什么版本、什么渠道、哪天构建"。模式可裁剪：MCU 固件可去 brand/tier 段（如 `fw_esp32s3_v1.2.0-beta_20260902.bin`），但**设备、版本、渠道、日期四要素必须在**。

## 2. SemVer 在固件上的判则

- **MAJOR**：分区布局变化、配置不迁移、升级后不可降级（降级要重刷/丢数据）；
- **MINOR**：新增能力、新增设备/渠道支持；
- **PATCH**：缺陷修复，布局与接口不变；
- 版本号必须同时写入镜像内可查询字段（版本文件或版本 API），与文件名一致——"名字与内容一致"是发布门禁检查项；
- 判断拿不准时：倾向升 MAJOR 并在发布说明写清迁移/不可回退影响，宁可保守。

## 3. 渠道与水印字段

- channel ∈ {`stable`, `beta`, `dev`}（可按需扩展，但必须枚举固定、lint 可查）：同名不同质是事故源，渠道必须在文件名里；
- 水印：把 brand/tier/version/channel/build-date 写入镜像内固定路径，售后取证时读镜像即知身份；**值由构建脚本外部传入**（发布时固定），不在构建瞬间生成——否则破坏可复现性；
- 禁止 `latest.img`、`v_final`、`final_v2` 这类不可判定名；`latest` 只允许作为渠道索引层的符号指向，产物文件名永不叫 latest。

## 4. 命名 lint 判则（可直接脚本化）

对每个产物文件名依次检查，任一失败即 lint 失败：

1. 全小写（含扩展名）；
2. 段数正确（五段式 = 4 个 `_` 分隔段 + 扩展名）；
3. 版本段匹配 `^v[0-9]+\.[0-9]+\.[0-9]+$`；
4. 渠道段 ∈ 枚举 {stable, beta, dev}；
5. 日期段为 8 位数字 `^20[0-9]{6}$` 且不晚于当天；
6. 扩展名 ∈ {`.img.gz`, `.bin`, `.img`}（按项目枚举）；
7. 文件名中的 device/version/channel/date 与构建记录一致。

sh 参考实现（骨架，按项目替换枚举）：

```sh
# name-lint.sh <file> —— 命中规则输出 FAIL，全过输出 PASS
name=$(basename "$1")
case "$name" in
  *[A-Z]*) echo "FAIL 大写: $name"; exit 1 ;;
esac
echo "$name" | grep -qE '^[a-z]+_[a-z0-9-]+_v[0-9]+\.[0-9]+\.[0-9]+-(stable|beta|dev)_20[0-9]{6}\.(img\.gz|bin|img)$' \
  && echo "PASS $name" || { echo "FAIL 段格式: $name"; exit 1; }
```

## 5. 与门禁的衔接

- lint 是 `fw-release-gate` 发布检查单第 2 项；改名/改版后**重跑全单**；
- 文件名与镜像内水印不一致 = 按失败处理（元数据分裂比缺元数据更危险）；
- SemVer 升级与"是否可降级"的结论要同步给 `fw-hil-testing` 的升级路径验收行。
