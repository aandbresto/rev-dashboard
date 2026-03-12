"""
REV Dashboard — Supabase Push Script
Runs automatically via GitHub Actions when daily_data.json is updated.
"""
import json, os, sys
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

db = create_client(SUPABASE_URL, SUPABASE_KEY)

with open("data/daily_data.json", "r") as f:
    payload = json.load(f)

report_date = payload["report_date"]
print(f"Pushing data for {report_date}...")

# Clear existing data for this date
for table in ["daily_snapshots", "ar_items", "ap_items", "transactions"]:
    db.table(table).delete().eq("report_date", report_date).execute()
    print(f"  Cleared {table}")

# Insert snapshot
db.table("daily_snapshots").insert(payload["snapshot"]).execute()
print(f"  ✓ Snapshot")

# Insert AR
if payload.get("ar_items"):
    db.table("ar_items").insert(payload["ar_items"]).execute()
    print(f"  ✓ {len(payload['ar_items'])} AR items")

# Insert AP
if payload.get("ap_items"):
    db.table("ap_items").insert(payload["ap_items"]).execute()
    print(f"  ✓ {len(payload['ap_items'])} AP items")

# Insert transactions
if payload.get("transactions"):
    db.table("transactions").insert(payload["transactions"]).execute()
    print(f"  ✓ {len(payload['transactions'])} transactions")

print(f"\n✅ Dashboard updated for {report_date}")
