#!/bin/sh /etc/rc.common
# Golden Example: procd-managed service skeleton (USE_PROCD=1)
# This is a golden example for skill verification, not production code.
# Demonstrates: rc.common shebang, START/STOP, procd_open_instance,
#   procd_set_param (command array, respawn, env, file), service_triggers.
# See SKILL.md §rc-common-api.md + §procd-instance.md for the contract.

START=80
STOP=20
USE_PROCD=1

SERVICE_NAME="ge-example-procd"
SERVICE_BIN="/usr/bin/ge-example-daemon"

start_service() {
    procd_open_instance "$SERVICE_NAME"
    procd_set_param command "$SERVICE_BIN" --config /etc/ge-example/config.yaml
    procd_set_param respawn 3600 5 5       # limit: 3600s window, 5s timeout, 5 retries
    procd_set_param env GIN_MODE=release
    procd_set_param file /etc/ge-example/config.yaml
    procd_set_param limits nofile="4096 8192"
    procd_set_param stderr 1               # redirect stderr to syslog
    procd_set_param stdout 1
    procd_close_instance
}

service_triggers() {
    procd_add_reload_trigger "ge-example"  # reload on UCI config change
}

stop_service() {
    # procd handles stop via procd_kill; custom cleanup only if needed
    :
}
