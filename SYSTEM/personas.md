# Discord Personas — Active Configuration

**Migrated:** 2026-04-20 from `~/.hermes/context/personas.json`
**Last updated:** 2026-04-13 (original)

---

## Active Bots

| Name | Runner | Channel | Status |
|------|--------|---------|--------|
| Gigi | runner.py --persona gigi --continuous --interval 30 | #nonsense (1491728632740315176) | Active |
| Veronica | runner.py --persona veronica --continuous --interval 30 | #nonsense (1491728632740315176) | Active |
| Morgan Freeman | morgan_freeman_runner.py --continuous --interval 30 | #nonsense (1491728632740315176) | Active (narrator) |
| Richard | runner.py --persona richard --continuous --interval 30 | #nonsense (1491728632740315176) | Idle |
| Susan | runner.py --persona susan --continuous --interval 30 | #nonsense (1491728632740315176) | Idle |

## Bot IDs
| Bot | ID |
|-----|-----|
| Gigi | 1491738070679027793 |
| Veronica | 1491737050028966030 |
| Richard | 1491920549121753229 |
| Susan | 1491922915703390298 |
| Auntie | 1492016717537345626 |
| Morgan Freeman | 1492089048368414760 |

## Discord Guild
**Captain Colonel Angus's Entertainment Emporium**
Channel: #nonsense | ID: 1491728632740315176

## Key Threads
- 1491747709432889406
- 1491747960424501403
- 1491748145657544794
- 1491750543679557773

## Gateway Status
- `hermes_gateway` state: `startup_failed` — Discord failed to connect
- May need re-auth or token refresh

## Character Notes
- **"Becky" is deprecated** — was renamed to Gigi. Do not use "Becky" anywhere.
- **Veronica** is the active bot name (not a nickname for Becky)
- Discord masks bot content — assume provocative

## Reload Command
```bash
touch /tmp/{name}.reload
```
Where `{name}` = the persona name (gigi, veronica, etc.)

## Restart Command
```bash
cd ~/.hermes/persona-runners && nohup python runner.py --continuous --interval 30 --persona {name} >> /tmp/{name}.log 2>&1 &
```
