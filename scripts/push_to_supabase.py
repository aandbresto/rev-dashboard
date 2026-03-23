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

report_date = payload["date"]           # was payload["report_date"]
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
        success = 0
        for row in rows:
            try:
                db.table(table).insert(row).execute()
                success += 1
            except Exception as row_err:
                print(f"    Skipped row: {str(row_err)[:120]}")
        return success

# ── Build snapshot from cash_position ────────────────────────────────────────
cash = payload["cash_position"]
impr = cash["improvement"]
rest = cash["restoration"]
comb = cash["combined"]

snapshot = {
    "report_date": report_date,
    # Improvement
    "impr_qb_balance":       impr.get("qb_bank_balance"),
    "impr_bank_2657":        impr.get("bank_balance_2657"),
    "impr_mm_2690":          impr.get("money_market_2690"),
    "impr_total_cash":       impr.get("total_cash_in_bank"),
    "impr_ar":               impr.get("accounts_receivable"),
    "impr_cap_one_cc":       impr.get("cap_one_cc"),
    "impr_loc_3705":         impr.get("loc_3705"),
    "impr_ap":               impr.get("accounts_payable"),
    "impr_net_total":        impr.get("net_total"),
    # Restoration
    "rest_qb_balance":       rest.get("qb_bank_balance"),
    "rest_bank_7363":        rest.get("bank_balance_7363"),
    "rest_mm_2798":          rest.get("money_market_2798"),
    "rest_total_cash":       rest.get("total_cash_in_bank"),
    "rest_ar":               rest.get("accounts_receivable"),
    "rest_loc_5064":         rest.get("loc_5064"),
    "rest_cap_one_cc":       rest.get("cap_one_cc"),
    "rest_ap":               rest.get("accounts_payable"),
    "rest_net_total":        rest.get("net_total"),
    # Combined
    "total_cash_in_bank":    comb.get("total_cash_in_bank"),
    "total_ar":              comb.get("total_ar"),
    "total_ap":              comb.get("total_ap"),
    "credit_debt":           comb.get("credit_debt"),
    "net_cash_availability": comb.get("net_cash_availability"),
}

try:
    db.table("daily_snapshots").insert(snapshot).execute()
    print(f"  ✓ Snapshot")
except Exception as e:
    print(f"  ✗ Snapshot failed: {e}")
    sys.exit(1)

# ── AR items (improvement + restoration) ─────────────────────────────────────
ar_rows = []
for row in payload["ar"]["improvement"] + payload["ar"]["restoration"]:
    ar_rows.append({
        "report_date":      report_date,
        "invoice_num":      row.get("invoice_num"),
        "client_job":       row.get("client_job"),
        "balance":          row.get("balance"),
        "invoice_date":     row.get("invoice_date"),
        "due_date":         row.get("due_date"),
        "days_out":         row.get("days_out"),
        "expected_payment": row.get("expected_payment"),
        "last_update":      row.get("last_update"),
        "division":         row.get("division"),
    })

count = safe_insert("ar_items", ar_rows)
print(f"  ✓ {count} AR items")

# ── AP items (improvement + restoration) ─────────────────────────────────────
ap_rows = []
for row in payload["ap"]["improvement"] + payload["ap"]["restoration"]:
    ap_rows.append({
        "report_date":       report_date,
        "inv_date":          row.get("inv_date"),
        "vendor":            row.get("vendor"),
        "invoice_num":       row.get("invoice_num"),
        "amount":            row.get("amount"),
        "billed":            row.get("billed"),
        "profit_pct":        row.get("profit_pct"),
        "approval_status":   row.get("approval_status"),
        "job_total":         row.get("job_total"),
        "due_date":          row.get("due_date"),
        "pay_friday":        row.get("pay_friday"),
        "division":          row.get("division"),
    })

count = safe_insert("ap_items", ap_rows)
print(f"  ✓ {count} AP items")

# ── Transactions ──────────────────────────────────────────────────────────────
txn_rows = []
for row in payload.get("transactions", []):
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
        "account":     row.get("account"),
        "division":    row.get("division"),
    })

count = safe_insert("transactions", txn_rows)
print(f"  ✓ {count} transactions")

# ── Optional brief ────────────────────────────────────────────────────────────
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
