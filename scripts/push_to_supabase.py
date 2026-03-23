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

report_date = payload["date"]
print(f"Pushing data for {report_date}...")

# Clear existing data for this date
for table in ["daily_snapshots", "ar_items", "ap_items", "transactions"]:
    result = db.table(table).delete().eq("report_date", report_date).execute()
    print(f"  Cleared {table}: {result}")

def safe_insert(table, rows):
    if not rows:
        print(f"  No rows to insert into {table}")
        return 0
    print(f"  Attempting to insert {len(rows)} rows into {table}...")
    try:
        result = db.table(table).insert(rows).execute()
        print(f"  ✓ Inserted {len(rows)} rows into {table}: {result}")
        return len(rows)
    except Exception as e:
        print(f"  ✗ Batch insert FAILED for {table}: {e}")
        success = 0
        for row in rows:
            try:
                db.table(table).insert(row).execute()
                success += 1
            except Exception as row_err:
                print(f"    Skipped row: {row_err}")
        print(f"  Row-by-row: {success}/{len(rows)} succeeded")
        return success

# ── Snapshot ──────────────────────────────────────────────────────────────────
cash = payload["cash_position"]
impr = cash["improvement"]
rest = cash["restoration"]
comb = cash["combined"]

snapshot = {
    "report_date":          report_date,
    "impr_qb_bank":         impr.get("qb_bank_balance"),
    "impr_bank_2657":       impr.get("bank_balance_2657"),
    "impr_mm_2690":         impr.get("money_market_2690"),
    "impr_cash":            impr.get("total_cash_in_bank"),
    "impr_ar":              impr.get("accounts_receivable"),
    "cap_one_construction": impr.get("cap_one_cc"),
    "loc_3705":             impr.get("loc_3705"),
    "impr_ap":              impr.get("accounts_payable"),
    "impr_net":             impr.get("net_total"),
    "rest_qb_bank":         rest.get("qb_bank_balance"),
    "rest_bank_7363":       rest.get("bank_balance_7363"),
    "rest_mm_2798":         rest.get("money_market_2798"),
    "rest_cash":            rest.get("total_cash_in_bank"),
    "rest_ar":              rest.get("accounts_receivable"),
    "loc_5064":             rest.get("loc_5064"),
    "cap_one_restoration":  rest.get("cap_one_cc"),
    "rest_ap":              rest.get("accounts_payable"),
    "rest_net":             rest.get("net_total"),
    "total_cash":           comb.get("total_cash_in_bank"),
    "total_ar":             comb.get("total_ar"),
    "total_ap":             comb.get("total_ap"),
    "credit_debt":          comb.get("credit_debt"),
    "net_availability":     comb.get("net_cash_availability"),
}

try:
    result = db.table("daily_snapshots").insert(snapshot).execute()
    print(f"  ✓ Snapshot: {result}")
except Exception as e:
    print(f"  ✗ Snapshot failed: {e}")
    sys.exit(1)

# ── AR ────────────────────────────────────────────────────────────────────────
ar_rows = []
for row in payload["ar"]["improvement"] + payload["ar"]["restoration"]:
    ar_rows.append({
        "report_date":           report_date,
        "invoice_number":        row.get("invoice_num"),
        "client":                row.get("client_job"),
        "balance":               row.get("balance"),
        "invoice_date":          row.get("invoice_date"),
        "due_date":              row.get("due_date"),
        "days_outstanding":      row.get("days_out"),
        "expected_payment_date": row.get("expected_payment"),
        "notes":                 row.get("last_update"),
        "division":              row.get("division"),
    })

count = safe_insert("ar_items", ar_rows)
print(f"  ✓ {count} AR items")

# ── AP ────────────────────────────────────────────────────────────────────────
ap_rows = []
for row in payload["ap"]["improvement"] + payload["ap"]["restoration"]:
    ap_rows.append({
        "report_date":      report_date,
        "invoice_date":     row.get("inv_date"),
        "vendor":           row.get("vendor"),
        "invoice_number":   row.get("invoice_num"),
        "amount":           row.get("amount"),
        "billed_to_client": row.get("billed"),
        "profit_pct":       row.get("profit_pct"),
        "notes":            row.get("approval_status"),
        "job_total":        row.get("job_total"),
        "due_date":         row.get("due_date"),
        "pay_friday":       row.get("pay_friday"),
        "division":         row.get("division"),
    })

count = safe_insert("ap_items", ap_rows)
print(f"  ✓ {count} AP items")

# ── Transactions ──────────────────────────────────────────────────────────────
txn_rows = []
for row in payload.get("transactions", []):
    account = row.get("account")
    txn_rows.append({
        "report_date": report_date,
        "trans_date":  row.get("trans_date"),
        "posted_date": row.get("posted_date"),
        "card_desc":   row.get("card_desc"),
        "vendor":      row.get("vendor"),
        "amount":      row.get("amount"),
        "explanation": row.get("explanation"),
        "approved_by": row.get("approved_by"),
        "txn_type":    row.get("txn_type"),
        "account":     account,
        "division":    row.get("division"),
    })

count = safe_insert("transactions", txn_rows)
print(f"  ✓ {count} transactions")

# ── Brief ─────────────────────────────────────────────────────────────────────
if payload.get("brief"):
    try:
        db.table("daily_briefs").delete().eq("report_date", report_date).execute()
        db.table("daily_briefs").insert({
            "report_date": report_date,
            "brief": payload["brief"]
        }).execute()
        print(f"  ✓ CFO brief")
    except Exception as e:
        print(f"  ✗ Brief failed: {e}")

print(f"\n✅ Dashboard updated for {report_date}")
