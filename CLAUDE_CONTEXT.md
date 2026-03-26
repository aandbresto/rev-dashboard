# REV / A&B Dashboard — Claude Context File
> Paste the raw URL of this file at the start of every new chat to restore full project context instantly.
> URL: https://raw.githubusercontent.com/aandbresto/ab-dashboard/refs/heads/main/CLAUDE_CONTEXT.md

---

## Project Overview
Daily financial dashboard for **REV Construction & Restoration** (A&B), two divisions: Improvement and Restoration.
Every morning a CFO master workbook is uploaded, parsed into `daily_data.json`, pushed to Supabase, and displayed on a GitHub Pages dashboard.
Monthly P&L PDFs are uploaded to generate the Monthly Financial Report tab.

---

## URLs
- **Dashboard**: https://aandbresto.github.io/ab-dashboard/
- **GitHub Repo**: https://github.com/aandbresto/ab-dashboard
- **Supabase Project**: https://svbmgueornewnasixpnh.supabase.co
- **Supabase Publishable Key**: `sb_publishable_kdp8f09n4MJKzoQS6amd0A_rVJPnXxf`

---

## Repo Structure
```
ab-dashboard/
├── index.html                  # Full dashboard frontend (single file — DO NOT MODIFY)
├── data/
│   └── daily_data.json         # Generated daily from workbook, triggers Action
├── scripts/
│   └── push_to_supabase.py     # Parses daily_data.json → inserts into Supabase
└── .github/workflows/
    └── upload.yml              # Triggers on data/daily_data.json push + workflow_dispatch
```

---

## Daily Workflow
1. User uploads `CFO_Master_Workbook.xlsx` to Claude
2. Claude runs the parser (Python) → generates `daily_data.json` dated **today's actual date** (always use today regardless of transaction dates)
3. User commits `daily_data.json` to GitHub repo under `data/`
4. GitHub Action triggers automatically → runs `scripts/push_to_supabase.py`
5. Dashboard at GitHub Pages reads from Supabase and displays data

**Manual trigger**: Go to Actions tab → Upload to Supabase → Run workflow

---

## Monthly Workflow
1. User uploads monthly P&L PDFs (Construction ABPI + Restoration ABPR) to Claude
2. Claude parses the PDFs and generates monthly report data
3. Data is pushed to Supabase `monthly_snapshots` table
4. Monthly Financial Report tab on dashboard updates automatically

**P&L data is YTD (cumulative from January through the report month)**
- January report = January only
- February report = January + February cumulative
- Label as "YTD through [Month]"

---

## CRITICAL RULES — DO NOT CHANGE
- **index.html is stable and complete — never modify it**
- **Always use today's actual date as report_date** regardless of transaction dates in workbook
- **Transaction dates (trans_date, posted_date) stay as-is from workbook**
- **Never ask user to edit code manually** — always provide the complete file to upload
- **File upload method for GitHub**: delete old file first, then upload new one

---

## Workbook Parser — Column Mappings

### Sheet: `💳 Daily Transactions`
| Section Row | Account Name | Division |
|-------------|-------------|----------|
| 8  | Capital One – Construction (2897) | improvement |
| 32 | Construction Checking – 2657 | improvement |
| 56 | Construction MM – 2690 | improvement |
| 81 | Capital One – Restoration | restoration |
| 105 | Restoration Checking – 7363 | restoration |
| 129 | Restoration MM – 2798 | restoration |

Header rows (skipped): 9, 33, 57, 82, 106, 130
Columns (0-indexed): `col[1]=trans_date, col[2]=posted_date, col[3]=card_desc, col[4]=vendor, col[5]=amount, col[6]=explanation, col[7]=approved_by, col[8]=txn_type`
txn_type values: `Credit`, `Debit`, `Transfer` (capitalized)

### Sheet: `📥 AR Tracker`
- Improvement: offset col 1 → `invoice_num, client_job, balance, invoice_date, due_date, days_out, expected_payment, last_update`
- Restoration: offset col 10 → same fields
- Data rows: 8 to end. Skip null / 'Invoice #' / 'TOTAL'

### Sheet: `📤 AP Tracker`
- Improvement: offset col 1 → `inv_date, vendor, invoice_num, amount, billed, profit_pct, approval_status, job_total, due_date, pay_friday`
- Restoration: offset col 12 → same fields
- Data rows: 8 to end

### Sheet: `💰 Cash Position`
Column index 2, 0-indexed rows:
- 6=impr_qb_bank, 7=impr_bank_2657, 8=impr_mm_2690, 9=impr_total_cash, 10=impr_ar, 11=impr_cap_one_cc, 12=impr_loc_3705, 13=impr_ap, 15=impr_net
- 18=rest_qb_bank, 19=rest_bank_7363, 20=rest_mm_2798, 21=rest_total_cash, 22=rest_ar, 23=rest_loc_5064, 24=rest_cap_one_cc, 25=rest_ap, 27=rest_net
- 30=combined_total_cash, 31=combined_total_ar, 32=combined_total_ap, 33=combined_credit_debt, 34=combined_net_availability

---

## daily_data.json Schema
```json
{
  "date": "2026-03-26",
  "generated_at": "2026-03-26T00:00:00Z",
  "cash_position": { "improvement": {}, "restoration": {}, "combined": {} },
  "ar": { "totals": {}, "improvement": [], "restoration": [] },
  "ap": { "totals": {}, "improvement": [], "restoration": [] },
  "transactions": [
    {"trans_date": "2026-03-24", "posted_date": "2026-03-24",
     "card_desc": "2671", "vendor": "Vendor", "amount": 0.0,
     "explanation": "", "approved_by": null, "txn_type": "Debit",
     "account": "Capital One – Construction (2897)", "division": "improvement"}
  ],
  "brief": [
    {"icon": "✅", "category": "Healthy Position", "message": "Net availability of $X is solid."}
  ]
}
```

---

## CFO Daily Brief — Auto-Generated Logic
Generated automatically by the parser. Smart insights, not just raw numbers:
- Net cash: 🌟 Strong (>$50K) / ✅ Healthy ($20-50K) / ⚠️ Alert (<$20K)
- Collections: 🎉 Great (>$30K credits) / 📥 Normal
- AR: 🚨 60+ days overdue (escalate named clients) / ⏰ 30+ days (send reminders)
- AP: 📤 Payments due this week with vendor names
- Division: 🔧 Improvement watch if net < $5K / 🏠 Restoration praise if strong
- Gap: 💡 When AP exceeds AR

---

## Supabase Tables & Exact Column Names

### `daily_snapshots`
```
id, report_date, impr_qb_bank, impr_bank_2657, impr_mm_2690, impr_cash,
impr_ar, impr_ap, impr_net, rest_qb_bank, rest_bank_7363, rest_mm_2798,
rest_cash, rest_ar, rest_ap, rest_net, cap_one_construction, loc_3705,
loc_5064, cap_one_restoration, total_cash, total_ar, total_ap,
credit_debt, net_availability, created_at
```

### `ar_items`
```
id, report_date, client, balance, invoice_date, due_date,
days_outstanding (INTEGER — cast float to int),
expected_payment_date, notes, invoice_number, division, created_at
```

### `ap_items`
```
report_date, invoice_date, vendor, invoice_number, amount,
billed_to_client, profit_pct, notes, job_total, due_date,
pay_friday, division, created_at
```

### `transactions`
```
id, report_date, trans_date, posted_date, account, account_type,
division, card_no, vendor, amount, explanation, approved_by, txn_type, created_at
```
- `account`: filter key — `cap_one_construction`, `checking_2657`, `mm_2690`, `cap_one_restoration`, `checking_7363`, `mm_2798`
- `account_type`: `"credit_card"` or `"bank"`
- `card_no` maps from JSON field `card_desc`

### `daily_briefs`
```
report_date, brief (JSON array of {icon, category, message})
```

### `payment_approvals`
```
report_date, vendor, invoice_number, division, status, comment, updated_at
```

### `monthly_snapshots`
Stores monthly P&L data for the Monthly Financial Report tab.
Populated when monthly P&L PDFs are uploaded to Claude.

---

## push_to_supabase.py — Key Logic
- `payload["date"]` → `report_date`
- `get_account_key(account)`: substring number matching (avoids em dash issues):
  - "capital one" + "restoration" → `cap_one_restoration`
  - "capital one" → `cap_one_construction`
  - "2657" → `checking_2657`, "2690" → `mm_2690`, "7363" → `checking_7363`, "2798" → `mm_2798`
- `to_int(v)`: casts float to int for days_outstanding
- `get_account_type(account)`: "credit_card" if "capital one" in name else "bank"
- Supabase JS v2: NO `.execute()` calls needed

---

## Dashboard Tabs (index.html — DO NOT MODIFY)
1. **Overview** — KPI cards, division breakdown, 30-day trend, credit utilization, CFO Daily Brief
2. **Cash Position** — improvement/restoration/combined tables
3. **Transactions** — grouped by division → by account, sorted posted_date oldest→newest. Filter chips by account. Columns: Trans Date, Posted Date, Account, Vendor, Amount, Explanation, Approved By
4. **Receivables** — AR by division, days outstanding badges
5. **Payables** — Friday payments with approval buttons (✅❌↺) + comment textarea. Full AP tables by division.
6. **Cash Flow** — 7/15/30/45d windows, payroll schedule, business expenses, historical chart
7. **Monthly Financial Report** — Construction/Restoration toggle, 5 charts, KPI cards, metrics table, executive summary

---

## Payables — Approval System
- Friday payments: AP items with `pay_friday = "Yes"`
- Approval buttons: ✅ Approved, ❌ Hold, ↺ Reset
- Comment field: textarea, saves on blur even without status (`if (status || comment)`)
- Saved to `payment_approvals` table, reloads AP after save

---

## Monthly Financial Report Tab
- Division toggle: Construction / Restoration
- Data: YTD cumulative P&L
- 5 Charts matching PDF format:
  1. Gross Profit vs Net Profit (grouped bar)
  2. Payroll Expenses vs Revenue (grouped bar)
  3. Total Expenses vs Revenue (grouped bar)
  4. Revenue Breakdown by Service (grouped bar)
  5. Monthly Target vs Actual (grouped bar + line combo)
- KPI cards, metrics comparison table, AI executive summary

### Jan 2026 data — Construction (ABPI)
Employees: 3 current / 4 prior. Target: $75K/month
Revenue: $8,457 vs $17,923. Gross: 55.96% vs 27.97%. Net: -64.23% vs -204.12%

### Jan 2026 data — Restoration (ABPR)
Employees: 6 current / 8 prior. Target: $125K/month
Revenue: $91,587 vs $150,725. Gross: 90.79% vs 77.21%. Net: 40.04% vs 20.50%

---

## Hardcoded Values in index.html
**Payroll Schedule** (update when amounts change):
- Improvement: lastPaid 2026-03-06, est. $1,658.70
- Admin: lastPaid 2026-03-06, est. $3,119.00
- Restoration: lastPaid 2026-03-13, est. $15,500.00

---

## Known Bugs Fixed (do not reintroduce)
1. `payload["report_date"]` → must be `payload["date"]`
2. `card_desc` → maps to `card_no` in Supabase
3. `days_outstanding` float → cast to int
4. Em dash in account names → use substring number matching
5. `.execute()` calls → not needed in Supabase JS v2
6. `window._saveAppr` → alias for `window.saveFridayApproval`
7. Comment `if (status)` → must be `if (status || comment)`
8. GitHub upload → delete old file first, then upload

---

## How to Start a New Chat
1. Open a new Claude chat
2. Paste: "Here is my project context: https://raw.githubusercontent.com/aandbresto/ab-dashboard/refs/heads/main/CLAUDE_CONTEXT.md"
3. Upload workbook for daily JSON, or P&L PDFs for monthly report
4. Do NOT ask Claude to modify index.html — it is stable and complete
5. Claude always uses today's actual date as report_date
