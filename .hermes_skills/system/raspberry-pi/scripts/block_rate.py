#!/usr/bin/env python3
"""Block rate calculator for Pi-hole FTL query database (queries table, status=3 = blocked)."""
import sqlite3

try:
    conn = sqlite3.connect('/etc/pihole/pihole-FTL.db')
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM queries")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM queries WHERE status=3")
    blocked = cur.fetchone()[0]
    conn.close()
    if total > 0:
        print(f"{(blocked/total*100):.1f}%")
    else:
        print("0%")
except:
    print("--")
