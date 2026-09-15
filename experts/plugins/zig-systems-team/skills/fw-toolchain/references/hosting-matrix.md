# Hosting Matrix — 三大工具链族：谁托管、怎么取、禁止什么

> 口径：OpenWrt=25.12.5、ESP-IDF=v6.1（走读 2026-09-02，不自动更新）。
> 原则：**工具链必须有一个明确托管者；没有托管者的拼装方案一律不采用。**

## 1. 托管矩阵

| 链路 | 工具链/target | 托管者 | 正确获取方式 | 禁止事项 |
|---|---|---|---|---|
| OpenWrt 用户态（如 N1 aarch64） | `aarch64-unknown-linux-musl` + 宿主交叉 gcc（`gcc-aarch64-linux-gnu` 一族） | 语言层工具（rustup）+ 发行版交叉包 | Linux 宿主/容器内：`rustup target add aarch64-unknown-linux-musl` + 发行版装交叉 gcc | 手工拼 sysroot；macOS 宿主硬凑 |
| ESP32（Xtensa / RISC-V） | `xtensa-esp-elf` / `riscv32-esp-elf` | **ESP-IDF 自带工具链管理**（安装工具 + 激活脚本，版本与 IDF 严格配套） | 走 IDF 官方安装/激活流程；工程细节路由 `esp32-idf` | apt/brew 手动装；跨 IDF 版本混用工具链 |
| OpenWrt 内核 / 镜像 | 内核交叉工具链 + 打包工具 | **buildroot / Image Builder**（固定版本 tarball 自带配套） | 用 pin 过版本的 IB tarball 构建，路由 `openwrt-image-build` | 用宿主 gcc 编内核/镜像；换用未 pin 的 IB 目录 |

## 2. 为什么"托管优先"

- **版本配套关系是隐含契约**：IDF 工具链与 IDF 源码版本、IB 与目标版本 ipk 仓库、rust target 与 rustc 版本，互相绑定；拆开单配就是漂移。
- **sysroot 手拼三宗罪**：头文件与目标 libc 版本错配、链接器默认路径污染、同事机器不复现——症状往往是"能编过、上板行为怪"。
- **托管者还负责更新**：升级走托管者的升级路径（IDF 版本切换、IB 换版本 tarball、rustup toolchain 文件），不走"再拷一份新的进来"。

## 3. 宿主形态约束

- 官方交叉/构建产物形态以 **Linux x86_64** 为基准（IB 官方发布即 Linux-x86_64；Windows/macOS 走 Docker 内 Linux——与 `openwrt-image-build` 的 Preflight 口径一致）。
- 容器内执行 Workflow A 的基准模式（rustup target + 发行版交叉 gcc）；不要在 macOS 宿主上找等价物硬凑。
- CI：优先复用与本地相同的容器镜像 + 相同 pin 文件，保证"本机=CI"。

## 4. 模式引用（非项目产物）

"rustup target add + 宿主交叉 gcc 出 aarch64 静态二进制"的模式已在实测项目验证（TinyNAS 实例，仅作模式引用；五段式命名等 TinyNAS 专属产物不在本通用包）。链接细节（self-contained musl vs 外部交叉 libc）按引入的 C 依赖实测确定——运行时核验。

## 5. 越界后果速查

| 越界动作 | 典型症状 |
|---|---|
| apt 手装 xtensa gcc | IDF 配置/构建阶段报工具链不识别；镜像行为无法对齐官方 issue |
| 手拼 sysroot | 编过但上板 segfault/符号缺失；两台机器产物不一致 |
| 未 pin 的 IB 目录 | 同一命令不同时间产物不同；ipk 拉到不同版本 |
| 宿主架构硬凑 | 产物 `file` 架构不对或根本链不出来 |
