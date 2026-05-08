---
name: apple-platform
description: "Apple platform interop on macOS — Notes (memo CLI), Reminders (remindctl), FindMy/AirTags (FindMy.app + AppleScript), and iMessage/SMS (imsg CLI). All require macOS with appropriate permissions and app access."
category: apple
---

# Apple Platform — Notes, Reminders, FindMy, iMessage

All tools require **macOS** with the respective app signed in and permissions granted.

## Quick Reference

| Tool | Use Case | Command |
|------|----------|---------|
| `memo` | Apple Notes — create, search, edit | `memo notes -a "title"` |
| `remindctl` | Apple Reminders — todo lists with iCloud sync | `remindctl add "task" --due tomorrow` |
| FindMy.app | AirTags and device tracking via screen capture | AppleScript + `screencapture` |
| `imsg` | iMessage/SMS — send, read, watch chats | `imsg send --to "+1..." --text "..."` |

## Shared Prerequisites

- **macOS** with respective app (Notes/Reminders/Messages/FindMy) signed into iCloud
- Homebrew for CLI tool installation
- Screen Recording permission (for FindMy screenshot capture)
- Full Disk Access (for imsg to read Messages history)
- Automation permission for the respective app

---

## Section 1: Apple Notes — `memo` CLI

**Prereq**: `brew install antoniorodr/memo/memo` → grant Notes Automation access.

### When to Use
- User wants notes synced across iPhone/iPad/Mac
- Saving info to Apple Notes from terminal

### When NOT to Use
- Obsidian vault → use `obsidian` skill
- Agent-internal notes → use `memory` tool

### Commands
```bash
memo notes                        # List all notes
memo notes -f "Folder"            # Filter by folder
memo notes -s "query"             # Search notes
memo notes -a "Title"             # Quick add with title
memo notes -e                     # Interactive edit
memo notes -d                     # Interactive delete
memo notes -m                     # Move to folder
memo notes -ex                    # Export to HTML/Markdown
```

### Limitations
- Cannot edit notes with images/attachments
- Interactive prompts need terminal access (`pty=true`)

---

## Section 2: Apple Reminders — `remindctl` CLI

**Prereq**: `brew install steipete/tap/remindctl` → grant Reminders permission.

### When to Use
- Personal to-dos syncing to iPhone/iPad
- Due date reminders with iCloud sync

### When NOT to Use
- Agent cronjob alerts → use `cronjob` tool
- Calendar events → use `google-workspace` or Apple Calendar
- Project tracking → use GitHub Issues, Linear, Notion

### Commands
```bash
remindctl                    # Today's reminders
remindctl today              # Today only
remindctl tomorrow           # Tomorrow
remindctl week               # This week
remindctl overdue            # Past due
remindctl all                # Everything

# Lists
remindctl list               # All lists
remindctl list Work --create # Create list
remindctl list Work --delete # Delete list

# Create
remindctl add "Buy milk"
remindctl add --title "Call mom" --list Personal --due tomorrow
remindctl add --title "Meeting" --due "2026-02-15 09:00"

# Complete/Delete
remindctl complete 1 2 3     # By ID
remindctl delete ID --force

# Formats
remindctl today --json       # JSON output
remindctl today --plain      # TSV
remindctl today --quiet      # Counts only
```

### Date Formats
`today`, `tomorrow`, `yesterday`, `YYYY-MM-DD`, `YYYY-MM-DD HH:mm`, ISO 8601.

---

## Section 3: FindMy (AirTags + Devices) — AppleScript + Screen Capture

**No CLI available** — uses AppleScript app control + screenshot capture + `vision_analyze`.

**Prereq**: Screen Recording permission, optional `peekaboo` (`brew install steipete/tap/peekaboo`).

### When to Use
- "Where is my [device/pet/keys]?"
- Tracking AirTag patrol routes over time
- Checking iPhone/iPad/Mac location

### Method 1: AppleScript + Screenshot (Basic)
```bash
# Open FindMy app
osascript -e 'tell application "FindMy" to activate'
sleep 3

# Take screenshot of window
screencapture -w -o /tmp/findmy.png
```
Then analyze with `vision_analyze(image_url="/tmp/findmy.png", question="What devices and locations are shown?")`

### Method 2: Peekaboo (Recommended)
```bash
peekaboo see --app "FindMy" --annotate --path /tmp/findmy-ui.png
peekaboo click --on B3 --app "FindMy"   # Click element by ID
peekaboo image --app "FindMy" --path /tmp/detail.png
```
Then `vision_analyze` the captured image.

### Switch Tabs
```bash
# Devices tab
osascript -e 'tell application "System Events" to tell process "FindMy" to click button "Devices" of toolbar 1 of window 1'
# Items tab (AirTags)
osascript -e 'tell application "System Events" to tell process "FindMy" to click button "Items" of toolbar 1 of window 1'
```

### AirTag Route Tracking
AirTags only update while the FindMy **page is actively displayed**. Keep FindMy open and foreground. Use a loop with periodic `screencapture` + `vision_analyze`.

### Limitations
- No native CLI/API — UI automation only
- Screen Recording permission required
- AppleScript may break across macOS versions
- AirTags update only when page is open

---

## Section 4: iMessage/SMS — `imsg` CLI

**Prereq**: `brew install steipete/tap/imsg` → grant Full Disk Access + Messages Automation.

### When to Use
- Send iMessage/text from terminal
- Read recent message history
- Monitor incoming messages

### When NOT to Use
- Telegram/Discord/Slack/WhatsApp → use respective gateway
- Group chat management → not supported
- Bulk messaging → always confirm with user first

### Commands
```bash
# List chats
imsg chats --limit 10 --json

# Read history
imsg history --chat-id 1 --limit 20 --json
imsg history --chat-id 1 --attachments --json  # with attachments

# Send
imsg send --to "+141****1212" --text "Hello!"
imsg send --to "+1..." --file /path/img.jpg   # with attachment
imsg send --to "+1..." --service imessage      # force iMessage
imsg send --to "+1..." --service sms           # force SMS

# Watch for new messages
imsg watch --chat-id 1 --attachments
```

### Rules
1. **Always confirm** recipient + message before sending
2. Never send to unknown numbers
3. Verify file paths before attaching
4. Don't bulk-message without explicit user approval

---

## Rule Summary

| Situation | Tool |
|-----------|------|
| Cross-device personal notes | `memo` / Apple Notes |
| Personal todos synced to iPhone | `remindctl` / Apple Reminders |
| AirTag/device location | FindMy.app + vision_analyze |
| Send/receive iMessages | `imsg` |
| Agent internal memory | `memory` tool |
| Markdown knowledge base | `obsidian` skill |
| Agent scheduling/alerts | `cronjob` tool |
