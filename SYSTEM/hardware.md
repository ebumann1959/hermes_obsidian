# Hardware — Pi (Shadys-Gamblin-Corner)

**Updated:** 2026-04-20

## CPU
| Field | Value |
|-------|-------|
| model | Cortex-A76 |
| cores | 4 |
| architecture | aarch64 (RPi 5) |

## Memory
| Field | Value |
|-------|-------|
| total | 16 GB (was 8GB in old records) |

## Disks
| Device | Size | Type | Mount | Used |
|--------|------|------|-------|------|
| /dev/mmcblk0 | 59.5 GB | mmc | / | 28% |
| /dev/sda1 | 931.5 GB | SSD | /mnt/ssd | 1% |

## GPU
| Driver | Render Device |
|--------|--------------|
| v3d | renderD128 |

## Notes
- /mnt/ssd is the old SSD mount point. Obsidian vault is now at /mnt/nvme/ (NVMe)
- hardware.json in context/ still references old 8GB — migrate complete, context/ files are deprecated
