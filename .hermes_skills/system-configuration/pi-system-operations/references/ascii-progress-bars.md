# ASCII Progress Bars for Conky

## Simple percentage bar (execbar)
```
${execbar cat /tmp/some_value}
```
Value must be 0–100 integer on a single line with no extra whitespace.

## Multi-segment ASCII bar via script
```bash
#!/bin/bash
val=$(cat /tmp/some_value)   # 0–100
width=20
filled=$(( val * width / 100 ))
empty=$(( width - filled ))
printf "%s[%s%s]%3d%%\n" "" "$(printf '█%.0s' $(seq 1 $filled))" "$(printf '░%.0s' $(seq 1 $empty))" "$val"
```
Output: `[████████████░░░░░░] 60%`

## Per-process RAM bar
```bash
printf "RAM  [%s%s] %dM\n" \
  "$(printf '▓%.0s' $(seq 1 $((rss_mb*width/total_mb))))" \
  "$(printf '░%.0s' $(seq 1 $((width - rss_mb*width/total_mb))))" \
  "$rss_mb"
```

## Unicode block characters
Use full-block (█ U+2588) for filled, light-shade (░ U+2591) for empty.
Do NOT use emoji — conky's default font may not render them.

## Alignment with printf
```bash
printf "  %-14s %4s%%  up %s\n" "$name" "$rss_pct" "$uptime"
# %-14s = left-aligned 14-char, %4s = right-aligned 4-char
```
