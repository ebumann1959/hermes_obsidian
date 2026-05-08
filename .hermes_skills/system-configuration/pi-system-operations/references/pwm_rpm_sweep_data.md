# PWM/RPM Sweep Data (RPi5 — Shadys-Gamblin-Corner)

## Hardware Paths (RPi5)
Fan RPM and PWM are on `hwmon3`, NOT hwmon1:
```
/sys/class/hwmon/hwmon3/fan1_input   # RPM (~1970 RPM at full speed)
/sys/class/hwmon/hwmon3/pwm1         # PWM duty cycle (0–255)
```

On this Pi: hwmon1 = temp sensors, hwmon3 = fan.

## PWM to Percentage
```
PERCENT = (pwm / 255) * 100
```

## PWM to RPM (approximate linear mapping)
```
RPM ≈ pwm * 8  (empirical, ~2040 at PWM=255)
```

## Conky execgraph config for fan speed
Raw RPM cannot be used directly in execgraph (scale must be 0–100). Log percentage to a file instead:
```bash
PWM=$(cat /sys/class/hwmon/hwmon3/pwm1)
PERCENT=$(( PWM * 100 / 255 ))
echo "$PERCENT" >> /tmp/fan_pwm_log
```
Then in conky: `${execgraph "cat /tmp/fan_pwm_log" 80,180 100 -t}`
