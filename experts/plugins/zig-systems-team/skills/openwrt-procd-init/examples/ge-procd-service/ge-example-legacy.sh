#!/bin/sh /etc/rc.common
# Golden Example: legacy (non-procd) init script skeleton
# This is a golden example for skill verification, not production code.
# Demonstrates: rc.common shebang, START/STOP, manual start/stop, PID file.
# Use USE_PROCD=1 whenever possible; legacy mode only when procd is not suitable.
# See SKILL.md §Capability Boundaries for when to choose legacy vs procd.

START=70
STOP=30
PROG="/usr/bin/ge-example-batch-worker"

start() {
    service_start $PROG --daemon --pidfile /var/run/ge-batch.pid
    logger -t ge-batch "started"
}

stop() {
    service_stop /var/run/ge-batch.pid
    logger -t ge-batch "stopped"
}

reload() {
    stop && start
}
