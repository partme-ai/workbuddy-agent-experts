# 内核线与版本解析（ophub/kernel）

来源：`remake` 脚本与 model_database.conf 头注释（HEAD `c593d56`，走读 2026-09-02）。行号指 remake 脚本。

## KERNEL_TAGS 语法（conf L19-28）

格式 `<tags>/<list>`，tags 即 ophub/kernel releases 的 tag 名（`kernel_` 前缀）：

| 写法 | 含义 |
|---|---|
| `stable/all` | kernel_stable 全部线（common kernel） |
| `stable/6.x.y` | kernel_stable 的 6.x 宏展开 |
| `flippy/all` / `beta/all` | 另两条 common 线，可与 stable 互换 |
| `rk3588/6.1.y` | 专用线（rk3588 系列） |
| `rk35xx/6.1.y` | 专用线（rk3328/3399/3528/3566/3568） |
| `h6/6.6.y` | 专用线（Allwinner H6） |

- 专用线默认仍从 kernel_stable tag 下载，可被 common 线替换（conf L24）。
- 展开宏：`5.x.y` → 5.10.y 5.15.y；`6.x.y` → 6.1.y 6.6.y 6.12.y 6.18.y（remake L99-100）。**宏不是版本号**。
- 通用线当前默认：`stable_kernel=("6.12.y" "6.18.y")`、`rk3588_kernel=("6.1.y")`、`rk35xx_kernel=("6.1.y")`、`h6_kernel=("6.6.y")`（L93-98）。

## remake 解析规则（逐行）

1. 拆分：`conf_kernel_tags=${KERNEL_TAGS%%/*}`、`conf_kernel_list=${KERNEL_TAGS##*/}`（L724-725）。
2. `all` → 取脚本同名数组 `${tags}_kernel`（L734-736）；数值列表按 `_` 拆成数组（L738-740），`5.x.y`/`6.x.y` 宏在 check_data 同样展开（L391-399）。
3. `auto_kernel=true`（默认）时 query_kernel 逐 tag 访问 `releases/expanded_assets/kernel_<tag>`，抓该线最新 `<major.minor>.<patch>`（L569-611）。
4. 板型期望列表与最新版本正则取交集，空交集报错退出（L746-754）。

## 参数 → 内核选择的影响

| 参数 | 作用 | 源码 |
|---|---|---|
| `-u <usage>` | 把默认 stable tag 换成 flippy/beta 等（自动剥 `kernel_` 前缀，只替换 stable 起头的条目） | L219、L374-380、L727 |
| `-k <v1_v2>` | 下划线分隔，覆盖 stable/flippy/beta/specific 全部版本数组 | L225-238 |
| `-a false` | 关闭自动取最新；此时**必须** `-k`，否则报错（L403-409） | L239-246 |
| `-r <repo>` | 换内核仓库；https 形式自动转 owner/repo（L432-433） | L209-216 |

## 下载与完整性

- 包地址：`https://github.com/<repo>/releases/download/kernel_<tag>/<ver>.tar.gz`（L641）；下载重试 10 次、间隔 60s（L644-654）。
- 每版本解包后是**三件套**：`boot-<ver>.tar.gz`、`dtb-<platform>-<ver>.tar.gz`、`modules-<ver>.tar.gz`（replace_kernel L952-957）。
- 含 `sha256sums` 则逐文件校验，缺文件或哈希不符即退出（check_kernel L613-627，调用点 L664）。

## 三包安装位置（Amlogic）

- `/boot`：`uInitrd-<ver>`、`vmlinuz-<ver>`，并复制出无版本别名 `uInitrd`、`zImage`（L960-962）。
- `/boot/dtb/amlogic/`：解包 dtb 包（L968-969）；板型 FDTFILE 必须在此目录中能找到（uEnv.txt/extlinux.conf 用 sed 写入该文件名，L1004-1026）。
- `/lib/modules/<ver>/`：解包 modules 包；删除 `build`、`source`、顶层 `*.ko` 后重建符号链接（L974-975）。
- Amlogic 专属 TEXT_OFFSET 检查：zImage 前 15 字节第 7 列 `0108`=带补丁（无需重载），否则 `need_overload=yes` 走 bootfs 的 `u-boot.ext` 重载路径（get_textoffset L182-188，调用 L965）。

## 与 eMMC 在线更新的耦合

refactor_rootfs 把 `amlogic_firmware_tag`（含源码别名与分支）、`amlogic_kernel_tags=kernel_<tags>`、`amlogic_kernel_branch=<major.minor>` 写进镜像 `etc/config/amlogic`（L1061-1069）——晶晨宝盒在线更新用同一 tag/branch 拉包（见 emmc-install.md）。换线构建时这里会跟着变。

## 反幻觉红线

- 不要报未验证的"最新内核版本号"——运行时以 query_kernel 同源接口（kernel tag releases 页）为准。
- 不要把 `6.x.y` 宏当实际版本；实际只有 6.1/6.6/6.12/6.18 四条 6.x 线（conf L26-27）。
- 不要假设某 DTB 在某内核线存在——以对应版本 dtb 包实际内容为准。
