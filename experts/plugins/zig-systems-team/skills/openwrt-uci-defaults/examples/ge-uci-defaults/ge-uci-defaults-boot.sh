#!/bin/sh
# Golden Example: idempotent uci-defaults script
# This is a golden example for skill verification, not production code.
# Demonstrates: 幂等写法、exit 0 结尾、不覆盖现有值。
# See SKILL.md §uci-defaults-lifecycle.md §preset-vs-defaults.md

# 检测：如果已配置过则跳过（幂等）
[ -f /etc/config/ge-example ] && exit 0

# 设置主机名（仅首次）
uci -q get system.@system[0].hostname >/dev/null || uci set system.@system[0].hostname='tinynas-demo'
uci -q get system.@system[0].timezone >/dev/null || {
    uci set system.@system[0].timezone='CST-8'
    uci set system.@system[0].zonename='Asia/Shanghai'
}

# uHTTPd 补缺项（不覆盖已有值）
uci -q get uhttpd.main.rfc1918_filter >/dev/null || uci set uhttpd.main.rfc1918_filter='1'
uci -q get uhttpd.main.cgi_prefix >/dev/null || uci set uhttpd.main.cgi_prefix='/cgi-bin'

# 创建 UCI 配置（幂等）
uci -q batch <<'UCI'
set ge-example.settings=ge-example
set ge-example.settings.enabled='1'
set ge-example.settings.debug='0'
UCI

uci commit
exit 0
