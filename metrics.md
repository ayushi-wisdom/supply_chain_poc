# Metrics

## Executive Metrics

### Overall Fill Rate
- **Definition:** Percentage of sales order lines shipped complete (qty_shipped = qty_ordered)
- **SQL:** `COUNT(CASE WHEN qty_shipped = qty_ordered AND status != 'cancelled' THEN 1 END) * 100.0 / NULLIF(COUNT(CASE WHEN status != 'cancelled' THEN 1 END), 0)` from sales_orders
- **Target:** 97%
- **Grain:** Can be calculated at product, category, warehouse, customer, or time period level

### Customer OTIF
- **Definition:** Percentage of delivered sales orders where actual_delivery_date <= promised_delivery_date
- **SQL:** `COUNT(CASE WHEN actual_delivery_date <= promised_delivery_date THEN 1 END) * 100.0 / COUNT(*)` from sales_orders WHERE status = 'delivered'
- **Target:** 95% platinum, 93% gold, 90% overall

### Revenue at Risk
- **Definition:** Total revenue of orders currently backordered
- **SQL:** `SUM(revenue)` from sales_orders WHERE status = 'backordered'
- **Segment by:** customer_id, account_tier, product category

### Total Backorder Count
- **Definition:** Count of sales order lines currently in backordered status
- **SQL:** `COUNT(*)` from sales_orders WHERE status = 'backordered'

## Supplier Metrics

### Supplier OTIF
- **Definition:** Percentage of PO lines delivered on or before promised_delivery_date
- **SQL:** `COUNT(CASE WHEN actual_delivery_date <= promised_delivery_date THEN 1 END) * 100.0 / COUNT(*)` from purchase_orders WHERE status = 'received'
- **Target:** 92% per standard SLA
- **Also available:** Pre-calculated monthly in supplier_scorecards.otif_pct (may be stale)

### Supplier Reject Rate
- **Definition:** Percentage of received quantity rejected for quality issues
- **SQL:** `SUM(qty_rejected) * 100.0 / NULLIF(SUM(qty_received + qty_rejected), 0)` from purchase_orders WHERE status = 'received'
- **Target:** Below 3%

### Average Supplier Lead Time
- **Definition:** Average days between order_date and actual_delivery_date
- **SQL:** `AVG(DATEDIFF('day', order_date, actual_delivery_date))` from purchase_orders WHERE actual_delivery_date IS NOT NULL
- **Compare to:** suppliers.lead_time_days_contracted

### Open PO Count
- **Definition:** Number of PO lines not yet received
- **SQL:** `COUNT(*)` from purchase_orders WHERE status = 'open'

### Overdue PO Count
- **Definition:** Open POs past their promised delivery date
- **SQL:** `COUNT(*)` from purchase_orders WHERE status = 'open' AND promised_delivery_date < CURRENT_DATE

## Inventory Metrics

### Days of Supply (DOS)
- **Definition:** Pre-calculated in inventory_daily.days_of_supply
- **Thresholds:** A-class < 14 days = critical, B-class < 10, C-class < 7

### Excess Inventory Value
- **Definition:** Value of inventory where DOS > 60 days
- **SQL:** `SUM(i.qty_on_hand * p.unit_cost)` from inventory_daily i JOIN products p WHERE i.days_of_supply > 60 AND i.snapshot_date = (most recent date)

### Stockout SKU Count
- **Definition:** Products with DOS = 0 or qty_available = 0
- **SQL:** `COUNT(DISTINCT product_id)` from inventory_daily WHERE days_of_supply <= 1 AND snapshot_date = (most recent date)

### Reorder Alert Count
- **Definition:** Product-warehouse combinations flagged for reorder
- **SQL:** `COUNT(*)` from inventory_daily WHERE reorder_flag = true AND snapshot_date = (most recent date)

### Monthly Carrying Cost
- **Definition:** Estimated monthly cost of holding current inventory
- **Formula:** SUM(qty_on_hand * unit_cost) * 0.25 / 12
- **Source:** inventory_daily JOIN products, filtered to most recent snapshot_date

## Forecast Metrics

### Forecast Error (MAE)
- **Definition:** Mean absolute error between forecast and actual demand
- **SQL:** `AVG(ABS(forecast_qty - actual_qty))` joining demand_forecast to aggregated sales_orders
- **Segment by:** forecast_method to compare statistical vs manual_override accuracy

### Forecast Bias
- **Definition:** Whether forecasts systematically over- or under-predict
- **SQL:** `AVG(forecast_qty - actual_qty)` — positive means over-forecasting, negative means under-forecasting

## Logistics Metrics

### Monthly Freight Spend
- **Definition:** Total freight invoiced amount per month
- **SQL:** `SUM(total_invoiced)` from freight_invoices grouped by month

### Expedited Shipment Rate
- **Definition:** Percentage of shipments using expedited/rush delivery
- **SQL:** `COUNT(CASE WHEN is_expedited THEN 1 END) * 100.0 / COUNT(*)` from shipments
- **Target:** Below 5% (expedited shipments cost ~2.4x standard)

### Freight Invoice Dispute Rate
- **Definition:** Percentage of invoices flagged for pricing disputes
- **SQL:** `COUNT(CASE WHEN dispute_flag THEN 1 END) * 100.0 / COUNT(*)` from freight_invoices

### Carrier Fuel Surcharge Trend
- **Definition:** Average fuel surcharge as percentage of base rate, tracked over time
- **SQL:** `AVG(fuel_surcharge / NULLIF(base_rate, 0))` from freight_invoices grouped by carrier and month

## Returns Metrics

### Return Rate
- **Definition:** Returns as a percentage of delivered orders
- **Target:** Below 3%

### Supplier-Attributable Return Rate
- **Definition:** Percentage of returns where root cause traces to a supplier
- **SQL:** `COUNT(CASE WHEN supplier_attributable THEN 1 END) * 100.0 / COUNT(*)` from returns
- **Segment by:** reason_code, supplier (via product tracing)

### Total Refund Amount
- **Definition:** Sum of refund_amount from returns over a given period
