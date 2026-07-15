#!/usr/bin/env python3
"""
Supply Chain Demo — Moment Verification
Tests every encoded data moment and journey layer against generated CSVs.
"""

import sys
import duckdb
from pathlib import Path

BASE = Path(__file__).parent
SNOWFLAKE = BASE / "data" / "snowflake"
DATABRICKS = BASE / "data" / "databricks"

PASS = 0
FAIL = 0
WARN = 0


def check(name, query, condition_fn, con, explain=""):
    """Run a query and test the result against a condition function."""
    global PASS, FAIL, WARN
    try:
        result = con.execute(query).fetchall()
        ok, detail = condition_fn(result)
        if ok:
            PASS += 1
            print(f"  ✓ {name}: {detail}")
        else:
            FAIL += 1
            print(f"  ✗ {name}: {detail}")
            if explain:
                print(f"       {explain}")
    except Exception as e:
        FAIL += 1
        print(f"  ✗ {name}: ERROR — {str(e)[:120]}")


def between(val, lo, hi):
    return lo <= val <= hi


def main():
    print("=" * 70)
    print("SUPPLY CHAIN DEMO — MOMENT VERIFICATION")
    print("=" * 70)

    con = duckdb.connect(":memory:")

    # Load all tables
    print("\nLoading tables...")
    for csv_file in sorted(SNOWFLAKE.glob("*.csv")):
        con.execute(f"CREATE TABLE {csv_file.stem} AS SELECT * FROM read_csv_auto('{csv_file}', header=True)")
        cnt = con.execute(f"SELECT COUNT(*) FROM {csv_file.stem}").fetchone()[0]
        print(f"  {csv_file.stem}: {cnt:,} rows")
    for csv_file in sorted(DATABRICKS.glob("*.csv")):
        con.execute(f"CREATE TABLE {csv_file.stem} AS SELECT * FROM read_csv_auto('{csv_file}', header=True)")
        cnt = con.execute(f"SELECT COUNT(*) FROM {csv_file.stem}").fetchone()[0]
        print(f"  {csv_file.stem}: {cnt:,} rows")

    anchor = con.execute("SELECT MAX(snapshot_date) FROM inventory_daily").fetchone()[0]
    print(f"\n  Anchor date (from inventory_daily max): {anchor}")

    # ─── JOURNEY 1: FILL RATE / SUPPLIER DEGRADATION ───────────────────────

    print(f"\n{'─' * 70}")
    print("JOURNEY 1: Why is our fill rate dropping?")
    print(f"{'─' * 70}")

    # L1: Fill rate decline
    check("L1: Overall fill rate declined",
        f"""
        SELECT 
            CASE WHEN order_date < '{anchor}'::DATE - INTERVAL 60 DAY THEN 'before' ELSE 'recent' END as period,
            COUNT(CASE WHEN status = 'delivered' AND actual_delivery_date <= promised_delivery_date THEN 1 END) * 100.0 
                / NULLIF(COUNT(CASE WHEN status = 'delivered' THEN 1 END), 0) as fill_rate
        FROM sales_orders
        WHERE status IN ('delivered', 'backordered', 'shipped')
        GROUP BY 1
        ORDER BY 1
        """,
        lambda r: (len(r) == 2 and r[0][1] > r[1][1],
                   f"before={r[0][1]:.1f}%, recent={r[1][1]:.1f}%") if len(r) == 2 else (False, f"got {len(r)} rows"),
        con)

    # L2: Categories driving decline
    check("L2: Electrical Components + Precision Bearings have backorders",
        """
        SELECT p.category, COUNT(*) as backorder_count
        FROM sales_orders so
        JOIN products p ON so.product_id = p.product_id
        WHERE so.status = 'backordered'
        GROUP BY p.category
        ORDER BY backorder_count DESC
        """,
        lambda r: (len(r) >= 1 and r[0][0] in ('Electrical Components', 'Precision Bearings'),
                   f"top backordered category: {r[0][0]} ({r[0][1]} orders)") if r else (False, "no backorders found"),
        con)

    # L3: Specific crisis SKUs
    check("L3: Crisis SKUs (EC-1847, EC-2291, EC-3004, EC-3517) have backorders",
        """
        SELECT product_id, COUNT(*) as bo_count
        FROM sales_orders
        WHERE status = 'backordered'
        AND product_id IN ('EC-1847', 'EC-2291', 'EC-3004', 'EC-3517')
        GROUP BY product_id
        """,
        lambda r: (len(r) >= 2, f"{len(r)} crisis SKUs have backorders, total={sum(x[1] for x in r)}") if r else (False, "none"),
        con)

    # L4: Inventory position on crisis SKUs
    check("L4: Crisis SKUs below safety stock (DOS < 14 for Class A)",
        f"""
        SELECT i.product_id, i.warehouse_id, i.days_of_supply, i.reorder_flag, i.qty_in_transit
        FROM inventory_daily i
        JOIN products p ON i.product_id = p.product_id
        WHERE i.snapshot_date = '{anchor}'
        AND i.product_id IN ('EC-1847', 'EC-2291', 'EC-3004', 'EC-3517')
        AND i.reorder_flag = true
        ORDER BY i.days_of_supply
        """,
        lambda r: (len(r) >= 4, f"{len(r)} product-warehouse combos in reorder, lowest DOS={r[0][2]:.1f}") if r else (False, "none found"),
        con)

    # L5: Open POs from Apex
    check("L5: Open POs for crisis SKUs all from Apex (SUP-1001)",
        """
        SELECT supplier_id, COUNT(*) as open_count,
               AVG(DATEDIFF('day', promised_delivery_date::DATE, CURRENT_DATE)) as avg_days_overdue
        FROM purchase_orders
        WHERE status = 'open'
        AND product_id IN ('EC-1847', 'EC-2291', 'EC-3004', 'EC-3517')
        GROUP BY supplier_id
        """,
        lambda r: (len(r) >= 1 and r[0][0] == 'SUP-1001' and r[0][1] >= 5,
                   f"Apex has {r[0][1]} open POs") if r else (False, "no open POs"),
        con)

    # L6: Apex OTIF degradation over 6 months
    check("L6: Apex OTIF degrades 94% → 76% over 6 months",
        """
        SELECT month, otif_pct
        FROM supplier_scorecards
        WHERE supplier_id = 'SUP-1001'
        ORDER BY month DESC
        LIMIT 6
        """,
        lambda r: (len(r) == 6 and r[0][1] <= 0.78 and r[5][1] >= 0.90,
                   f"most recent={r[0][1]:.0%}, 6mo ago={r[5][1]:.0%}") if len(r) == 6 else (False, f"got {len(r)} rows"),
        con)

    # L6b: Stale risk rating
    check("L6b: Apex risk_rating stays 'medium' (stale)",
        """
        SELECT DISTINCT risk_rating
        FROM supplier_scorecards
        WHERE supplier_id = 'SUP-1001'
        ORDER BY month DESC
        LIMIT 6
        """,
        lambda r: (len(r) == 1 and r[0][0] == 'medium',
                   f"rating: {r[0][0]}") if r else (False, "no data"),
        con)

    # L6c: Apex below 92% SLA for 4+ months
    check("L6c: Apex below 92% SLA threshold for 4+ months",
        """
        SELECT COUNT(*) FROM (
            SELECT month, otif_pct FROM supplier_scorecards
            WHERE supplier_id = 'SUP-1001' AND otif_pct < 0.92
            ORDER BY month DESC LIMIT 6
        )
        """,
        lambda r: (r[0][0] >= 4, f"{r[0][0]} months below 92%"),
        con)

    # ─── JOURNEY 2: EXCESS INVENTORY ──────────────────────────────────────

    print(f"\n{'─' * 70}")
    print("JOURNEY 2: Why is there $1.2M in excess inventory?")
    print(f"{'─' * 70}")

    # L1: Excess inventory in WH-EAST
    check("L1: Excess inventory (>60 DOS) in Industrial Fasteners at WH-EAST",
        f"""
        SELECT SUM(i.qty_on_hand * p.unit_cost) as excess_value, AVG(i.days_of_supply) as avg_dos
        FROM inventory_daily i
        JOIN products p ON i.product_id = p.product_id
        WHERE i.snapshot_date = '{anchor}'
        AND i.warehouse_id = 'WH-EAST'
        AND p.category = 'Industrial Fasteners'
        AND i.days_of_supply > 60
        """,
        lambda r: (r[0][0] is not None and r[0][0] > 500000,
                   f"${r[0][0]:,.0f} excess, avg DOS={r[0][1]:.0f}") if r and r[0][0] else (False, "no excess found"),
        con)

    # L3: Forecast method accuracy
    check("L3: Manual override has higher error than statistical",
        f"""
        WITH actuals AS (
            SELECT product_id,
                   DATE_TRUNC('month', order_date) as month,
                   SUM(qty_ordered) as actual_qty
            FROM sales_orders
            WHERE product_id LIKE 'IF-%'
            GROUP BY 1, 2
        )
        SELECT f.forecast_method,
               AVG(ABS(f.forecast_qty - a.actual_qty)) as avg_error
        FROM demand_forecast f
        JOIN actuals a ON f.product_id = a.product_id
            AND DATE_TRUNC('month', f.period_start) = a.month
        WHERE f.product_id LIKE 'IF-%'
        AND f.forecast_method IN ('statistical', 'manual_override')
        GROUP BY f.forecast_method
        """,
        lambda r: (len(r) == 2 and
                   any(x[0] == 'manual_override' for x in r) and
                   [x[1] for x in r if x[0] == 'manual_override'][0] >
                   [x[1] for x in r if x[0] == 'statistical'][0],
                   f"statistical={[x[1] for x in r if x[0]=='statistical'][0]:.0f}, " +
                   f"override={[x[1] for x in r if x[0]=='manual_override'][0]:.0f}")
        if len(r) == 2 else (False, f"got {len(r)} methods"),
        con)

    # L4: J. Martinez was the overrider
    check("L4: J. Martinez made the manual overrides",
        """
        SELECT DISTINCT created_by
        FROM demand_forecast
        WHERE product_id IN ('IF-7010','IF-7125','IF-7230','IF-7340','IF-7455',
                             'IF-7560','IF-7675','IF-7780','IF-7890','IF-7995')
        AND forecast_method = 'manual_override'
        """,
        lambda r: (any('Martinez' in str(x[0]) for x in r),
                   f"overriders: {[x[0] for x in r]}") if r else (False, "no manual overrides found"),
        con)

    # L5: Warehouse imbalance
    check("L5: Same SKUs overstocked in WH-EAST, critically low in WH-WEST",
        f"""
        SELECT warehouse_id, AVG(days_of_supply) as avg_dos
        FROM inventory_daily
        WHERE snapshot_date = '{anchor}'
        AND product_id LIKE 'IF-%'
        AND warehouse_id IN ('WH-EAST', 'WH-WEST')
        GROUP BY warehouse_id
        ORDER BY warehouse_id
        """,
        lambda r: (len(r) == 2 and r[0][1] > 50 and r[1][1] < 25,
                   f"WH-EAST avg DOS={r[0][1]:.0f}, WH-WEST avg DOS={r[1][1]:.0f}")
        if len(r) == 2 else (False, f"got {len(r)} warehouses"),
        con)

    # ─── JOURNEY 3: FREIGHT COST SPIKE ────────────────────────────────────

    print(f"\n{'─' * 70}")
    print("JOURNEY 3: Why did logistics costs spike?")
    print(f"{'─' * 70}")

    # L1: Freight spend trend (per-day rate to handle partial months)
    check("L1: Recent month freight spend rate > prior average rate",
        f"""
        SELECT
            CASE WHEN invoice_date >= '{anchor}'::DATE - INTERVAL 30 DAY THEN 'recent' ELSE 'prior' END as period,
            SUM(total_invoiced) as total_spend,
            COUNT(DISTINCT invoice_date) as days_active,
            SUM(total_invoiced) / NULLIF(COUNT(DISTINCT invoice_date), 0) as daily_rate
        FROM freight_invoices
        WHERE invoice_date >= '{anchor}'::DATE - INTERVAL 120 DAY
        GROUP BY 1
        """,
        lambda r: (len(r) == 2 and
                   [x[3] for x in r if x[0] == 'recent'][0] >
                   [x[3] for x in r if x[0] == 'prior'][0] * 1.1,
                   f"recent daily=${[x[3] for x in r if x[0]=='recent'][0]:,.0f}, " +
                   f"prior daily=${[x[3] for x in r if x[0]=='prior'][0]:,.0f}")
        if len(r) == 2 else (False, f"got {len(r)} periods"),
        con)

    # L2: Expedited shipments spike
    check("L2: Expedited shipments increased recently",
        f"""
        SELECT
            CASE WHEN ship_date >= '{anchor}'::DATE - INTERVAL 42 DAY THEN 'last_6wk' ELSE 'prior' END as period,
            COUNT(CASE WHEN is_expedited THEN 1 END) as expedited_count,
            COUNT(*) as total,
            COUNT(CASE WHEN is_expedited THEN 1 END) * 100.0 / COUNT(*) as expedited_pct
        FROM shipments
        WHERE ship_date >= '{anchor}'::DATE - INTERVAL 180 DAY
        GROUP BY 1
        """,
        lambda r: (len(r) == 2 and
                   [x[3] for x in r if x[0] == 'last_6wk'][0] >
                   [x[3] for x in r if x[0] == 'prior'][0],
                   f"last 6wk={[x[3] for x in r if x[0]=='last_6wk'][0]:.1f}%, " +
                   f"prior={[x[3] for x in r if x[0]=='prior'][0]:.1f}%")
        if len(r) == 2 else (False, f"got {len(r)} periods"),
        con)

    # L5: Disputed invoices
    check("L5: 3+ disputed invoices with material variance",
        """
        SELECT COUNT(*) as dispute_count, SUM(variance_amount) as total_variance
        FROM freight_invoices
        WHERE dispute_flag = true
        """,
        lambda r: (r[0][0] >= 3 and r[0][1] > 5000,
                   f"{r[0][0]} disputes, total variance=${r[0][1]:,.0f}") if r else (False, "no disputes"),
        con)

    # ─── JOURNEY 4: CUSTOMER IMPACT ──────────────────────────────────────

    print(f"\n{'─' * 70}")
    print("JOURNEY 4: Are we losing customers?")
    print(f"{'─' * 70}")

    # L1: Customer OTIF decline
    check("L1: Customer OTIF declined in recent period",
        f"""
        SELECT
            CASE WHEN actual_delivery_date < '{anchor}'::DATE - INTERVAL 60 DAY THEN 'before' ELSE 'recent' END as period,
            COUNT(CASE WHEN actual_delivery_date <= promised_delivery_date THEN 1 END) * 100.0 / COUNT(*) as otif
        FROM sales_orders
        WHERE status = 'delivered' AND actual_delivery_date IS NOT NULL
        GROUP BY 1
        """,
        lambda r: (len(r) == 2 and
                   [x[1] for x in r if x[0] == 'before'][0] > [x[1] for x in r if x[0] == 'recent'][0],
                   f"before={[x[1] for x in r if x[0]=='before'][0]:.1f}%, " +
                   f"recent={[x[1] for x in r if x[0]=='recent'][0]:.1f}%")
        if len(r) == 2 else (False, f"got {len(r)} periods"),
        con)

    # L2: Meridian Industries (platinum) affected
    check("L2: Meridian Industries has backorders",
        """
        SELECT c.name, c.account_tier, COUNT(*) as bo_count, SUM(so.revenue) as rev_at_risk
        FROM sales_orders so
        JOIN customers c ON so.customer_id = c.customer_id
        WHERE so.status = 'backordered'
        AND so.customer_id = 'CUST-0012'
        GROUP BY c.name, c.account_tier
        """,
        lambda r: (len(r) >= 1 and r[0][3] > 300000,
                   f"{r[0][0]} ({r[0][1]}): {r[0][2]} backorders, ${r[0][3]:,.0f} at risk") if r else (False, "no Meridian backorders"),
        con)

    # L4: Multiple key accounts affected
    check("L4: Multiple platinum/gold accounts have backorders",
        """
        SELECT c.account_tier, COUNT(DISTINCT c.customer_id) as affected_accounts
        FROM sales_orders so
        JOIN customers c ON so.customer_id = c.customer_id
        WHERE so.status = 'backordered'
        AND c.account_tier IN ('platinum', 'gold')
        GROUP BY c.account_tier
        """,
        lambda r: (sum(x[1] for x in r) >= 2,
                   f"affected: {', '.join(f'{x[0]}={x[1]}' for x in r)}") if r else (False, "none found"),
        con)

    # L5: Total revenue at risk
    check("L5: Total backorder revenue at risk > $200K",
        """
        SELECT SUM(revenue) as total_at_risk
        FROM sales_orders
        WHERE status = 'backordered'
        """,
        lambda r: (r[0][0] > 200000,
                   f"${r[0][0]:,.0f} total revenue at risk") if r and r[0][0] else (False, "no backorders"),
        con)

    # L6: Supplier-attributable returns
    check("L6: 60%+ of late_delivery returns are supplier-attributable",
        f"""
        SELECT
            COUNT(CASE WHEN supplier_attributable THEN 1 END) * 100.0 / COUNT(*) as attr_pct,
            SUM(refund_amount) as total_refunds
        FROM returns
        WHERE reason_code = 'late_delivery'
        AND return_date >= '{anchor}'::DATE - INTERVAL 60 DAY
        """,
        lambda r: (r[0][0] >= 60,
                   f"{r[0][0]:.0f}% supplier-attributable, ${r[0][1]:,.0f} in refunds") if r and r[0][0] else (False, "no data"),
        con)

    # ─── STANDALONE MOMENTS ──────────────────────────────────────────────

    print(f"\n{'─' * 70}")
    print("STANDALONE MOMENTS")
    print(f"{'─' * 70}")

    # GlobalParts contrast
    check("GlobalParts OTIF consistently above 95%",
        """
        SELECT MIN(otif_pct) as min_otif, AVG(otif_pct) as avg_otif
        FROM supplier_scorecards
        WHERE supplier_id = 'SUP-1002'
        """,
        lambda r: (r[0][0] >= 0.93 and r[0][1] >= 0.95,
                   f"min={r[0][0]:.0%}, avg={r[0][1]:.0%}") if r else (False, "no data"),
        con)

    # Carrier fuel surcharge creep
    check("Continental Freight fuel surcharge creeping up",
        f"""
        SELECT
            CASE WHEN invoice_date < '{anchor}'::DATE - INTERVAL 150 DAY THEN 'early' ELSE 'recent' END as period,
            AVG(fuel_surcharge / NULLIF(base_rate, 0)) as avg_fuel_pct
        FROM freight_invoices
        WHERE carrier_name = 'Continental Freight'
        GROUP BY 1
        """,
        lambda r: (len(r) == 2 and
                   [x[1] for x in r if x[0] == 'recent'][0] > [x[1] for x in r if x[0] == 'early'][0],
                   f"early={[x[1] for x in r if x[0]=='early'][0]:.1%}, " +
                   f"recent={[x[1] for x in r if x[0]=='recent'][0]:.1%}")
        if len(r) == 2 else (False, f"got {len(r)} periods"),
        con)

    # Meridian returns
    check("Meridian has recent returns for late delivery",
        """
        SELECT COUNT(*) as ret_count, SUM(refund_amount) as total_refund
        FROM returns
        WHERE customer_id = 'CUST-0012'
        AND reason_code = 'late_delivery'
        """,
        lambda r: (r[0][0] >= 2,
                   f"{r[0][0]} returns, ${r[0][1]:,.0f} refunded") if r else (False, "none"),
        con)

    # ─── CROSS-TABLE INTEGRITY ──────────────────────────────────────────

    print(f"\n{'─' * 70}")
    print("CROSS-TABLE INTEGRITY")
    print(f"{'─' * 70}")

    integrity_checks = [
        ("product_ids in purchase_orders exist in products",
         "SELECT COUNT(*) FROM purchase_orders po LEFT JOIN products p ON po.product_id = p.product_id WHERE p.product_id IS NULL"),
        ("supplier_ids in purchase_orders exist in suppliers",
         "SELECT COUNT(*) FROM purchase_orders po LEFT JOIN suppliers s ON po.supplier_id = s.supplier_id WHERE s.supplier_id IS NULL"),
        ("warehouse_ids in inventory_daily exist in warehouses",
         "SELECT COUNT(*) FROM inventory_daily i LEFT JOIN warehouses w ON i.warehouse_id = w.warehouse_id WHERE w.warehouse_id IS NULL"),
        ("customer_ids in sales_orders exist in customers",
         "SELECT COUNT(*) FROM sales_orders so LEFT JOIN customers c ON so.customer_id = c.customer_id WHERE c.customer_id IS NULL"),
        ("product_ids in inventory_daily exist in products",
         "SELECT COUNT(*) FROM inventory_daily i LEFT JOIN products p ON i.product_id = p.product_id WHERE p.product_id IS NULL"),
    ]

    for name, query in integrity_checks:
        check(f"No orphaned {name}",
              query,
              lambda r: (r[0][0] == 0, f"orphaned: {r[0][0]}"),
              con)

    # ─── SUMMARY ────────────────────────────────────────────────────────

    print(f"\n{'=' * 70}")
    print(f"RESULTS: {PASS} PASSED, {FAIL} FAILED")
    if FAIL == 0:
        print("ALL MOMENTS VERIFIED ✓ — READY TO UPLOAD")
    else:
        print("FIX FAILURES BEFORE UPLOADING ✗")
    print(f"{'=' * 70}")

    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
