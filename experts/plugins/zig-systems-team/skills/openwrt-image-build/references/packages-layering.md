# PACKAGES 三层叠加与包治理（packages-layering）

read-when：PACKAGES 列表变多、多设备/多档位共用一套构建、或需要从默认集移除包时。

## 1. 语义速查（IB Makefile 帮助文本与 BUILD_PACKAGES 逻辑，基线 25.12.5）

- `make image PACKAGES="a b c"`：在默认包 + PROFILE 包之上**追加**；
- `make image PACKAGES="-pkgname"`：**移除** pkgname（含其作为默认集成员的身份；若其他包硬依赖它，opkg 会报依赖错误，构建失败）;
- `PACKAGES="-a b"` 可以同条指令内既移除又追加；
- 最终清单用 `make manifest PROFILE=... PACKAGES=...` 预演（不产镜像）；
- 依赖查询：`make package_depends PACKAGE=<pkg>` / `make package_whatdepends PACKAGE=<pkg>`。

## 2. 三层叠加模式（生产模板 build-template.sh:167-176）

```text
packages.common.txt      # 层1 全设备通用：基础服务与运行时
packages.tier-<TIER>.txt # 层2 档位/场景：pro / edge / lite
arch/packages.txt        # 层3 架构专属：如 x86 需要的驱动、armsr 需要的内核包
```

拼接规则：注释行（`#` 开头）剔除后按空格连接，重复包由 opkg 幂等处理；`-pkg` 移除项放最末层（arch 层）以便按设备裁剪。

优点：一处改、多架构生效；diff 友好；审计包来源时按层定位。

## 3. 操作流程

1. 把需求映射为包名，先在 `make package_list` 输出中确认存在（IB 仓库范围内）；
2. 加入对应层文本文件；
3. `make manifest` 预演：检查新增包的间接依赖体积、确认 `-pkg` 没误删被依赖项；
4. `make image` 构建后，从 `bin/targets/.../<profile>.manifest`（或 `make manifest` 输出）核对最终清单；
5. 变更记录进版本库（每层一个文件，提交信息写明动机）。

## 4. 常见错误

| 错误 | 后果与纠正 |
|---|---|
| 把 `-pkg` 写在中间层、arch 层又追加同名包 | 结果取决于顺序，易出"以为删了还在"——移除项统一放最后一层 |
| 包名拼错 | opkg 报 `unknown package`，构建失败——先 `make package_list | grep` 核对 |
| 用 PACKAGES 装"配置" | 包只装文件不配行为；行为配置走 FILES= 的 uci-defaults/init.d |
| 依赖被 `-pkg` 误删 | opkg 依赖错误中止；先 `package_whatdepends` 看引用面 |
| 档位文件缺失仍构建 | 生产模板直接 fail（`未找到档位包列表`），不要静默降级为 common-only |

## 5. Hand-off

- 包内服务怎么自启/配置 → `openwrt-procd-init` / `openwrt-uci-defaults`
- 存储类包（块设备挂载）的运行时配置 → `openwrt-storage-mount`
- 发布时校验清单与体积门禁 → `fw-release-gate`
