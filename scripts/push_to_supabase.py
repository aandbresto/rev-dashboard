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

def safe_insert(table, rows):
    """Insert rows, retrying row by row if batch fails."""
    if not rows:
        return 0
    try:
        db.table(table).insert(rows).execute()
        return len(rows)
    except Exception as e:
        print(f"  ⚠ Batch insert failed for {table}: {str(e)[:200]}")
        # Retry row by row
        success = 0
        for row in rows:
            try:
                db.table(table).insert(row).execute()
                success += 1
            except Exception as row_err:
                print(f"    Skipped row: {str(row_err)[:120]}")
        return success

# Insert snapshot
try:
    db.table("daily_snapshots").insert(payload["snapshot"]).execute()
    print(f"  ✓ Snapshot")
except Exception as e:
    print(f"  ✗ Snapshot failed: {e}")
    sys.exit(1)

# Insert AR
count = safe_insert("ar_items", payload.get("ar_items", []))
print(f"  ✓ {count} AR items")

# Insert AP
count = safe_insert("ap_items", payload.get("ap_items", []))
print(f"  ✓ {count} AP items")

# Insert transactions
count = safe_insert("transactions", payload.get("transactions", []))
print(f"  ✓ {count} transactions")

print(f"\n✅ Dashboard updated for {report_date}")
