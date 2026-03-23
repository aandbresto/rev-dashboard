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

def get_account_type(account):
    """Classify account as credit_card or bank based on name."""
    if not account:
        return None
    a = account.lower()
    if "capital one" in a or "cap one" in a:
        return "credit_card"
    return "bank"

# ── Build snapshot from cash_position ────────────────────────────────────────
# Column names match exactly what index.html reads (snap.impr_cash, snap.rest_cash, etc.)
cash = payload["cash_position"]
impr = cash["improvement"]
rest = cash["restoration"]
comb = cash["combined"]

snapshot = {
    "report_date":          report_date,
    # Improvement
    "impr_qb_bank":         impr.get("qb_bank_balance"),
    "impr_bank_2657":       impr.get("bank_balance_2657"),
    "impr_mm_2690":         impr.get("money_market_2690"),
    "impr_cash":            impr.get("total_cash_in_bank"),
    "impr_ar":              impr.get("accounts_receivable"),
    "cap_one_construction": impr.get("cap_one_cc"),
    "loc_3705":             impr.get("loc_3705"),
    "impr_ap":              impr.get("accounts_payable"),
    "impr_net":             impr.get("net_total"),
    # Restoration
    "rest_qb_bank":         rest.get("qb_bank_balance"),
    "rest_bank_7363":       rest.get("bank_balance_7363"),
    "rest_mm_2798":         rest.get("money_market_2798"),
    "rest_cash":            rest.get("total_cash_in_bank"),
    "rest_ar":              rest.get("accounts_receivable"),
    "loc_5064":             rest.get("loc_5064"),
    "cap_one_restoration":  rest.get("cap_one_cc"),
    "rest_ap":              rest.get("accounts_payable"),
    "rest_net":             rest.get("net_total"),
    # Combined
    "total_cash":           comb.get("total_cash_in_bank"),
    "total_ar":             comb.get("total_ar"),
    "total_ap":             comb.get("total_ap"),
    "credit_debt":          comb.get("credit_debt"),
    "net_availability":     comb.get("net_cash_availability"),
}

try:
    db.table("daily_snapshots").insert(snapshot).execute()
    print(f"  ✓ Snapshot")
except Exception as e:
    print(f"  ✗ Snapshot failed: {e}")
    sys.exit(1)

# ── AR items ─────────────────────────────────────────────────────────────────
# Column names match what loadAR() reads: r.client, r.balance, r.days_outstanding,
# r.expected_payment_date, r.notes, r.invoice_number, r.invoice_date, r.due_date
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

# ── AP items ──────────────────────────────────────────────────────────────────
# Column names match what loadAP() reads: r.vendor, r.invoice_number, r.amount,
# r.billed_to_client, r.profit_pct, r.notes, r.job_total, r.due_date, r.pay_friday
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
# account stored as the filter key (e.g. "checking_7363") so dashboard chips work
# account_type set to "credit_card" or "bank" so CC vs bank split works
ACCOUNT_FILTER_KEYS = {
    "Capital One – Construction (2897)": "cap_one_construction",
    "Construction Checking – 2657":      "checking_2657",
    "Construction MM – 2690":            "mm_2690",
    "Capital One – Restoration":         "cap_one_restoration",
    "Restoration Checking – 7363":       "checking_7363",
    "Restoration MM – 2798":             "mm_2798",
}

txn_rows = []
for row in payload.get("transactions", []):
    account = row.get("account")
    txn_rows.append({
        "report_date":  report_date,
        "trans_date":   row.get("trans_date"),
        "posted_date":  row.get("posted_date"),
        "card_desc":    row.get("card_desc"),
        "vendor":       row.get("vendor"),
        "amount":       row.get("amount"),
        "explanation":  row.get("explanation"),
        "approved_by":  row.get("approved_by"),
        "txn_type":     row.get("txn_type"),
        "account":      ACCOUNT_FILTER_KEYS.get(account, account),
        "account_type": get_account_type(account),
        "division":     row.get("division"),
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
