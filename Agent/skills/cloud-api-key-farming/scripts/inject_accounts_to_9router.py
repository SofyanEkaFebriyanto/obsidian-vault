#!/usr/bin/env python3
"""Batch-inject existing accounts.txt lines into a 9router SQLite DB.

Use when accounts already exist (e.g. from a proxy-mode run before Warp was
enabled, or synced from another host) and were never injected into 9router.
Reads config.json (9router.providerId / nodeName / prefix / baseUrl / sqliteDb)
plus accounts.txt, inserts each `xy-*` key, skipping duplicates.

Run from the project dir:
    source venv/bin/activate && python inject_accounts_to_9router.py
"""
import sqlite3, json, uuid, os
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(HERE, "config.json")
ACCOUNTS_FILE = os.path.join(HERE, "accounts.txt")


def load_cfg():
    with open(CFG_PATH) as f:
        return json.load(f)


def inject(conn, api_key, account_name, nr):
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM providerConnections WHERE provider=? AND json_extract(data,'$.apiKey')=?",
        (nr["providerId"], api_key),
    )
    if cur.fetchone():
        print(f"     [skip] {account_name} already in 9router")
        return
    now = datetime.now(timezone.utc).isoformat()
    cid = str(uuid.uuid4())
    data = {
        "apiKey": api_key,
        "testStatus": "active",
        "backoffLevel": 0,
        "providerSpecificData": {
            "prefix": nr["prefix"],
            "apiType": "chat",
            "baseUrl": nr["baseUrl"],
            "nodeName": nr["nodeName"],
            "connectionProxyEnabled": False,
            "connectionProxyUrl": "",
            "connectionNoProxy": "",
        },
    }
    cur.execute(
        "INSERT INTO providerConnections (id, provider, authType, name, priority, isActive, createdAt, updatedAt, data, email) "
        "VALUES (?,?,?,?,?,?,?,?,?,NULL)",
        (cid, nr["providerId"], "apikey", account_name, 1, 1, now, now, json.dumps(data)),
    )
    conn.commit()
    print(f"     [ok] injected as {account_name}")


def main():
    cfg = load_cfg()
    nr = cfg["9router"]
    db = os.path.expanduser(nr["sqliteDb"])
    conn = sqlite3.connect(db)
    count = 0
    with open(ACCOUNTS_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(":")
            if len(parts) < 3 or not parts[2].startswith("xy-"):
                continue
            email, api_key = parts[0], parts[2]
            count += 1
            print(f"[{count}] {email}")
            inject(conn, api_key, f"Xyris #{count}", nr)
    conn.close()
    print(f"\nDone! Processed {count} accounts from {ACCOUNTS_FILE}.")


if __name__ == "__main__":
    main()
