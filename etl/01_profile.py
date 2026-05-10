import pandas as pd
from pathlib import Path
from datetime import datetime

CLEAN_DIR = Path.home() / "Desktop" / "Restaurant-Data-Stack" / "data" / "clean"
DOCS_DIR  = Path.home() / "Desktop" / "Restaurant-Data-Stack" / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

print("Loading data...")
orders = pd.read_csv(CLEAN_DIR / "orders.csv")
order_items = pd.read_csv(CLEAN_DIR / "order_items.csv")
payments = pd.read_csv(CLEAN_DIR / "payments.csv")
tags = pd.read_csv(CLEAN_DIR / "tags.csv")

print(f"  orders: {len(orders):,}")
print(f"  order_items: {len(order_items):,}")
print(f"  payments: {len(payments):,}")
print(f"  tags: {len(tags):,}")

print("\nPreparing data...")
orders["order_reference"] = orders["reference"].astype(str)
payments["order_reference"] = payments["order_reference"].astype(str)

print("\nRunning quality checks...")
dup_orders = orders["order_reference"].duplicated().sum()
print(f"  Duplicate orders: {dup_orders}")

payment_sums = payments.groupby("order_reference")["amount"].sum().reset_index()
payment_sums.columns = ["order_reference", "payment_total"]

merged = orders[["order_reference", "total_price"]].merge(payment_sums, on="order_reference", how="left")
merged["total_price"] = pd.to_numeric(merged["total_price"], errors="coerce")
merged["payment_total"] = pd.to_numeric(merged["payment_total"], errors="coerce")

reconciled = (merged["total_price"] == merged["payment_total"]).sum()
recon_rate = round(reconciled / len(merged) * 100, 2)
unreconciled = len(merged) - reconciled

print(f"  Payment reconciliation: {recon_rate}%")
print(f"  Unreconciled orders: {unreconciled}")

branches = sorted(orders["branch_name"].dropna().unique())
print(f"  Branches: {len(branches)}")

print("\nGenerating HTML...")

html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Data Quality Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f7fa; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        h1 {{ color: #667eea; border-bottom: 3px solid #667eea; padding-bottom: 10px; }}
        h2 {{ color: #2c3e50; margin-top: 30px; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
        .metric {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-left: 4px solid #667eea; border-radius: 4px; }}
        .metric-label {{ font-size: 0.85em; color: #666; text-transform: uppercase; letter-spacing: 0.5px; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #2c3e50; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #f0f0f0; padding: 12px; text-align: left; border-bottom: 2px solid #ddd; font-weight: 600; }}
        td {{ padding: 12px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f9f9f9; }}
        .pass {{ color: #27ae60; font-weight: bold; }}
        .warn {{ color: #e67e22; font-weight: bold; }}
        .checklist {{ margin: 20px 0; }}
        .check-item {{ padding: 12px; margin: 8px 0; border-radius: 4px; border-left: 4px solid #27ae60; background: #d4edda; color: #155724; }}
        .check-warn {{ padding: 12px; margin: 8px 0; border-radius: 4px; border-left: 4px solid #e67e22; background: #fff3cd; color: #856404; }}
        footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 0.85em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Project Marcus — Data Quality Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>📊 Summary</h2>
        <div class="metric">
            <div class="metric-label">Total Orders</div>
            <div class="metric-value">{len(orders):,}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Total Order Items</div>
            <div class="metric-value">{len(order_items):,}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Total Payments</div>
            <div class="metric-value">{len(payments):,}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Active Branches</div>
            <div class="metric-value">{len(branches)}</div>
        </div>
        
        <h2>✅ Quality Checks</h2>
        <div class="checklist">
            <div class="{'check-item' if dup_orders == 0 else 'check-warn'}">
                <strong>Duplicate Order IDs:</strong> {dup_orders} duplicates — {'✅ PASS' if dup_orders == 0 else '⚠️ INVESTIGATE'}
            </div>
            <div class="{'check-item' if recon_rate >= 98 else 'check-warn'}">
                <strong>Payment Reconciliation:</strong> {recon_rate}% reconciled ({unreconciled:,} unreconciled) — {'✅ PASS' if recon_rate >= 98 else '⚠️ INVESTIGATE'}
            </div>
            <div class="check-item">
                <strong>Branch Coverage:</strong> {len(branches)} branches present — ✅ PASS
            </div>
        </div>
        
        <h2>🏪 Branch Details</h2>
        <table>
            <tr>
                <th>Branch Name</th>
                <th>Orders</th>
                <th>Items</th>
                <th>Avg Ticket (SAR)</th>
            </tr>
"""

for branch in branches:
    b_orders = len(orders[orders["branch_name"] == branch])
    b_items = len(order_items[order_items["branch_name"] == branch])
    b_avg = orders[orders["branch_name"] == branch]["total_price"].astype(float).mean()
    html += f"""            <tr>
                <td>{branch}</td>
                <td>{b_orders:,}</td>
                <td>{b_items:,}</td>
                <td>{b_avg:,.1f}</td>
            </tr>
"""

html += """
        </table>
        
        <h2>📋 Null Rates — Orders Table</h2>
        <table>
            <tr><th>Column</th><th>Null %</th><th>Non-Null Count</th></tr>
"""

for col in orders.columns:
    if col == "order_reference":
        continue
    null_pct = round(orders[col].isna().sum() / len(orders) * 100, 2)
    non_null = orders[col].notna().sum()
    color = "color: #e74c3c;" if null_pct > 2 else ""
    html += f'<tr><td>{col}</td><td style="{color}">{null_pct}%</td><td>{non_null:,}</td></tr>'

html += """
        </table>
        
        <h2>📋 Null Rates — Order Items Table</h2>
        <table>
            <tr><th>Column</th><th>Null %</th><th>Non-Null Count</th></tr>
"""

for col in order_items.columns:
    null_pct = round(order_items[col].isna().sum() / len(order_items) * 100, 2)
    non_null = order_items[col].notna().sum()
    color = "color: #e74c3c;" if null_pct > 2 else ""
    html += f'<tr><td>{col}</td><td style="{color}">{null_pct}%</td><td>{non_null:,}</td></tr>'

html += """
        </table>

        <h2>📋 Null Rates — Payments Table</h2>
        <table>
            <tr><th>Column</th><th>Null %</th><th>Non-Null Count</th></tr>
"""

for col in payments.columns:
    null_pct = round(payments[col].isna().sum() / len(payments) * 100, 2)
    non_null = payments[col].notna().sum()
    color = "color: #e74c3c;" if null_pct > 2 else ""
    html += f'<tr><td>{col}</td><td style="{color}">{null_pct}%</td><td>{non_null:,}</td></tr>'

html += """
        </table>
        
        <footer>
            <p><strong>Phase 1 — Data Foundation | Project Marcus</strong></p>
            <p>This report validates data quality before warehouse construction. Filtered to بروستد الريف branches only.</p>
        </footer>
    </div>
</body>
</html>
"""

report_path = DOCS_DIR / "data_quality_report.html"
with open(report_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\n✅ Report saved to: {report_path}")
print("Open docs/data_quality_report.html in your browser.")
print("\nDone!")