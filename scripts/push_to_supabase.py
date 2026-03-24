"""
REV Dashboard — Supabase Push Script
"""
import json, os, sys
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
db = create_client(SUPABASE_URL, SUPABASE_KEY)

with open("data/daily_data.json", "r") as f:
    payload = json.load(f)

report_date = payload["date"]
print(f"Pushing data for {report_date}...")

for table in ["daily_snapshots", "ar_items", "ap_items", "transactions"]:
    db.table(table).delete().eq("report_date", report_date).execute()
    print(f"  Cleared {table}")

def safe_insert(table, rows):
    if not rows:
        return 0
    try:
        db.table(table).insert(rows).execute()
        return len(rows)
    except Exception as e:
        print(f"  Batch failed for {table}: {e}")
        success = 0
        for row in rows:
            try:
                db.table(table).insert(row).execute()
                success += 1
            except Exception as err:
                print(f"    Skipped: {err}")
        return success

def to_int(v):
    if v is None: return None
    try: return int(float(v))
    except: return None

def get_account_type(account):
    if not account: return None
    return "credit_card" if "capital one" in account.lower() else "bank"

def get_account_key(account):
    keys = {
        "Capital One": "cap_one_construction",
        "Construction Checking": "checking_2657",
        "Construction MM": "mm_2690",
        "Restoration": "cap_one_restoration",
        "Restoration Checking": "checking_7363",
        "Restoration MM": "mm_2798",
    }
    if not account: return account
    for k, v in keys.items():
        if k in account:
            if "Capital One" in account and "Restoration" in account:
                return "cap_one_restoration"
            if "Checking" in account and "2657" in account:
                return "checking_2657"
            if "MM" in account and "2690" in account:
                return "mm_2690"
            if "Checking" in account and "7363" in account:
                return "checking_7363"
            if "MM" in account and "2798" in account:
                return "mm_2798"
            if "Capital One" in account:
                return "cap_one_construction"
    return account

cash = payload["cash_position"]
impr = cash["improvement"]
rest = cash["restoration"]
comb = cash["combined"]

snapshot = {
    "report_date": report_date,
    "impr_qb_bank": impr.get("qb_bank_balance"),
    "impr_bank_2657": impr.g
