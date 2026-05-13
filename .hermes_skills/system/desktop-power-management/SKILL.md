---
name: desktop-power-management
description: Prevent Linux desktop sleep/blanking — KDE, GNOME, XFCE, and generic Freedesktop inhibitors. Covers caffeine, kde-inhibit, systemd-inhibit, xdg-screensaver, and PowerDevil D-Bus introspection.
category: system
---

# desktop-power-management

Prevent a Linux desktop from sleeping, blanking, or suspending on demand.

## Trigger

User wants to temporarily or permanently prevent desktop sleep/blanking — either as a one-off command or as a daemonized inhibitor.

## Core Tools

| Tool | Scope | Notes |
|------|-------|-------|
| `kde-inhibit --power CMD` | KDE Plasma only | Most reliable on KDE; talks directly to PowerDevil |
| `kde-inhibit --screenSaver CMD` | KDE Plasma only | Blocks screensaver/blanking only |
| `systemd-inhibit` | Any systemd desktop | Works on GNOME, XFCE, etc.; shows in `systemd-inhibit --list` |
| `caffeine` | Any X11 desktop | Daemon; auto-inhibits on full-screen windows |
| `xdg-screensaver` | Any X11 desktop | Query/suspend screensaver |
| `dbus-send` | Any desktop | Low-level D-Bus calls when qdbus is absent |

## KDE Plasma — Recommended

```bash
# Inhibit sleep+suspend for N seconds (auto-releases)
kde-inhibit --power sleep 3600

# Keep alive indefinitely (until killed)
kde-inhibit --power xdg-screensaver suspend 0 &
```

`--power` blocks PowerDevil sleep/suspend. `--screenSaver` blocks only blanking. Both use KDE's own D-Bus interface (org.kde.PowerDevil), NOT systemd inhibitors — they will NOT appear in `systemd-inhibit --list`.

**Release:** `kill <pid>` of the kde-inhibit process.

**Verify inhibitors active:**
```bash
ps aux | grep kde-inhibit | grep -v grep
```

**Check PowerDevil D-Bus** (requires org.kde.PowerDevil on DBus):
```bash
dbus-send --session --dest=org.kde.PowerDevil /org/kde/PowerDevil org.kde.PowerDevil.getInhibitors
```

## systemd-inhibit — Cross-Desktop

Works on GNOME, XFCE, and other Freedesktop-compliant desktops.

```bash
# Block sleep+idle for N seconds
systemd-inhibit --what=sleep:idle --who="me" --why="working" --mode=block sleep 3600 &

# List active inhibitors
systemd-inhibit --list
```

Mode options: `block` (strongest), `delay` (allows sleep after delay), `block-weak`.

## caffeine — Auto Full-Screen Detect

```bash
caffeine &
# Runs as daemon; automatically inhibits when a full-screen window is detected.
# No manual activate/status commands in this version.
```

## xdg-screensaver — Query/Suspend

```bash
xdg-screensaver status    # enabled / disabled
xdg-screensaver suspend 0 # suspend indefinitely
xdg-screensaver reset     # resume normal operation
```

## Debugging Power Inhibitors

**KDE inhibitors not in systemd-inhibit --list? Normal.** KDE's PowerDevil uses its own D-Bus API — KDE inhibitors live in the PowerDevil session bus, not the systemd inhibitor list.

**qdbus not found?** Use `dbus-send` instead:
```bash
dbus-send --session --print-reply --dest=org.kde.PowerDevil /org/kde/PowerDevil org.freedesktop.DBus.Properties.GetAll string:org.kde.PowerDevil
```

**systemd not PID 1?** On container/CI environments (e.g., WSL without systemd as init), `systemd-inhibit --list` returns "System has not been booted with systemd as init". Use `kde-inhibit` (on KDE) or `xdg-screensaver` instead.

## keep-awake Wrapper Script

For clean start/stop/status management of an indefinite KDE power inhibit:

```bash
keep-awake start   # inhibits sleep until killed
keep-awake stop    # releases
keep-awake status  # check
```

The script is already installed at `~/bin/keep-awake` and executable. Run directly:
```bash
keep-awake start   # inhibits sleep until killed
keep-awake stop    # releases
keep-awake status  # check
```
The pidfile at `/tmp/keep-awake-$USER.pid` prevents duplicate instances.

The underlying inhibit command is `kde-inhibit --power -- bash -c 'while true; do sleep 30; done'` — more reliable than `sleep N` (no auto-expiry) and persists across terminal tab closes.

## Why the Machine Won't Sleep — Even Without keep-awake

The PowerDevil row visible in `systemd-inhibit --list` is **NOT** a sleep block:

```
PowerDevil  Evan  PID  org_kde_powerde handle-power-key:handle-suspend-key:handle-hibernate-key:handle-lid-switch  block  KDE handles power events
```

The `what=` field is `handle-power-key:handle-suspend-key:handle-hibernate-key:handle-lid-switch` — these are *event handlers* (so KDE, not logind, decides what happens when the user presses the power button or closes the lid). It does **not** inhibit idle sleep. Idle sleep is governed entirely by `AutoSuspendAction` / `AutoSuspendIdleTimeoutSec` in `~/.config/powerdevilrc`.

**Real reasons idle sleep silently fails:**

1. **AutoSuspendAction=2 (Hibernate) with no swap** — most common. Hibernate writes RAM to swap; if `/proc/swaps` is empty (or swap < RAM), the kernel refuses and PowerDevil gives up with no fallback. Check: `cat /proc/swaps; free -h`.
2. **A real block-mode inhibitor from an app** — e.g. media player, VM, screen-sharing tool. In `systemd-inhibit --list`, look for `mode=block` rows whose `what=` includes `sleep` or `idle` (not just the handle-* entries).
3. **`keep-awake` or stray `kde-inhibit --power` still running** — `ps -ef | grep kde-inhibit`.

**Action codes (`AutoSuspendAction`):**
- `0` = None (do nothing)
- `1` = Sleep / Suspend-to-RAM ← the normal "sleep" value
- `2` = Hibernate / Suspend-to-Disk (requires swap ≥ RAM)
- `4` = Suspend-Hybrid
- `8` = Shutdown

## Pitfalls

- **Do not edit AutoSuspendAction to inhibit sleep**: Use `keep-awake` / `kde-inhibit --power` for temporary inhibition — never repurpose `powerdevilrc` for that. Action codes: `0`=None, `1`=Sleep (suspend-to-RAM, the normal value), `2`=Hibernate, `4`=Hybrid, `8`=Shutdown. Setting `=2` on a machine with no/insufficient swap silently disables idle sleep entirely (hibernate fails, no fallback). To restore normal sleep: `kwriteconfig6 --file powerdevilrc --group AC --group SuspendAndShutdown --key AutoSuspendAction 1`, then reload with `qdbus6 org.kde.Solid.PowerManagement /org/kde/Solid/PowerManagement refreshStatus` (or `dbus-send --session --type=method_call --dest=org.kde.Solid.PowerManagement /org/kde/Solid/PowerManagement org.kde.Solid.PowerManagement.refreshStatus`).
- **keep-awake stop is sufficient**: It kills the `kde-inhibit --power` process — the only inhibitor it ever created. The PowerDevil `handle-power-key:...` row in `systemd-inhibit --list` is unrelated and not a sleep block. Do *not* log out or `pkill startplasma-x11` to "release" sleep.
- **Two caffeine instances**: can accumulate if launched multiple times. `ps aux | grep caffeine` to check; `kill <extra_pid>` to remove.
- **PowerDevil override**: KDE's PowerDevil can still suspend even if `caffeine` is running if the terminal is closed or the DBus inhibitor is released. Use `kde-inhibit --power` for KDE reliability.
- **systemd inhibitors are session-scoped**: they disappear when the login session ends. Long-running processes should use `nohup` or `disown`.
- **xdg-screensaver suspend is fragile**: some desktops ignore it. `kde-inhibit --power` is more robust on KDE.

## References

- `references/kde-plasma.md` — KDE Plasma session transcript, PowerDevil D-Bus details, verification commands
- `scripts/keep-awake` — start/stop/status wrapper for indefinite KDE power inhibit
