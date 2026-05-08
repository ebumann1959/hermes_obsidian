# KDE Plasma — Power Management Investigation Notes

## System Info

- **Host**: MX25Rig (Evan)
- **DE**: KDE Plasma
- **Init**: Not systemd (WSL-style or container environment)

## Key Finding: KDE Inhibitors Don't Appear in systemd-inhibit --list

`systemd-inhibit --list` showed 4 system-level inhibitors (ModemManager, NetworkManager, UPower, PowerDevil), but the user's `kde-inhibit` processes were NOT listed there. This is **expected behavior** — KDE's PowerDevil registers inhibitors on the session D-Bus under `org.kde.PowerDevil`, not via the systemd logind inhibitor API.

## Commands Verified on This System

```bash
# Check for kde-inhibit / caffeine processes
ps aux | grep -E "kde-inhibit|caffeine" | grep -v grep

# List systemd inhibitors (system-level + PowerDevil blocking keys)
systemd-inhibit --list

# Check PowerDevil D-Bus (qdbus not installed on this system)
dbus-send --session --dest=org.kde.PowerDevil /org/kde/PowerDevil org.kde.PowerDevil.getInhibitors
# → Error: org.freedesktop.DBus.Error.ServiceUnknown (PowerDevil not on session bus)

# Query screensaver status
xdg-screensaver status
# → "enabled" (normal)

# Available inhibit tools found on this system:
# /usr/bin/kde-inhibit      ← KDE Plasma
# /usr/bin/systemd-inhibit  ← cross-desktop
# /usr/bin/elogind-inhibit  ← if elogind is used
# /usr/bin/xdg-screensaver  ← X11 screensaver control
# /usr/bin/caffeine         ← auto full-screen inhibit daemon
# /usr/bin/xdotool          ← for dummy window tricks
```

## Working Inhibitor Setup (Evan's machine)

```bash
# Screensaver inhibit (3600s)
kde-inhibit --screenSaver sleep 3600 &

# Power/sleep inhibit — most reliable on KDE
kde-inhibit --power xdg-screensaver suspend 0 &

# Release both:
kill <pid_from_ps_aux>
```

## Why kde-inhibit --power Is More Reliable Than caffeine on KDE

- `caffeine` uses `xdg-screensaver` / D-Bus idle inhibitors, which PowerDevil can override
- `kde-inhibit --power` talks directly to PowerDevil via its D-Bus API, creating a PowerDevil-level inhibit
- PowerDevil's own `systemd-inhibit` entry shows `handle-power-key:handle-suspend-key:handle-hibernate-key:handle-lid-switch` in `WHAT` — KDE's power button and lid are its domain
- System inhibitor list from this session:
  ```
  WHO            UID  USER PID  COMM            WHAT
  ModemManager   0    root 2338 ModemManager    sleep
  NetworkManager 0    root 2218 NetworkManager  sleep
  UPower         0    root 2946 upowerd         sleep
  PowerDevil     1000 Evan 2841 org_kde_powerde handle-power-key:handle-suspend-key:handle-hibernate-key:handle-lid-switch
  ```
  (PowerDevil's inhibit covers the KEYS and SWITCHES, not sleep/idle — hence the need for explicit inhibit)
