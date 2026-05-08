#!/bin/bash
# Persistent background logger daemon for conky execgraph fan RPM plot
# Run BEFORE conky starts — never via ${execi} inside conky
LOG=/tmp/fan_pwm_log
MAX=180
while true; do
    PWM=$(cat /sys/class/hwmon/hwmon3/pwm1 2>/dev/null || echo 0)
    PERCENT=$(( PWM * 100 / 255 ))
    echo "$PERCENT" >> "$LOG"
    [ "$(wc -l < "$LOG")" -gt "$MAX" ] && tail -n $MAX "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
    sleep 5
done
