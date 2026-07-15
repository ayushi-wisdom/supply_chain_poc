# Business Logic and Definitions

## Key Performance Indicators (KPIs)

### Supplier OTIF (On-Time In-Full)
Percentage of purchase order lines delivered on or before the promised delivery date with the full quantity ordered.
- **Source:** purchase_orders
- **Formula:** COUNT(lines where actual_delivery_date <= promised_delivery_date AND qty_received >= qty_ordered) / COUNT(all received lines)
- **Target:** 92% minimum per the standard supplier SLA
- **Frequency:** Calculated monthly, tracked in supplier_scorecards

### Customer OTIF
Percentage of sales order lines delivered to the customer on or before the promised delivery date.
- **Source:** sales_orders
- **Formula:** COUNT(lines where actual_delivery_date <= promised_delivery_date) / COUNT(all delivered lines)
- **Target:** 95% for platinum accounts, 93% for gold, 90% overall
- **Frequency:** Calculated monthly

### Fill Rate
Percentage of customer order lines that were shipped complete (no backorders or short-ships).
- **Source:** sales_orders
- **Formula:** COUNT(lines where qty_shipped = qty_ordered) / COUNT(all lines excluding cancelled)
- **Target:** 97% overall

### Days of Supply (DOS)
Estimated number of days the current inventory will last based on average daily demand.
- **Source:** inventory_daily
- **Pre-calculated:** Available as days_of_supply column
- **Thresholds:** Below safety_stock_days (A=14, B=10, C=7) triggers reorder_flag = true

### Forecast Accuracy
How closely demand forecasts predicted actual order volumes.
- **Source:** demand_forecast joined to sales_orders actuals
- **Formula:** 1 - (ABS(forecast_qty - actual_qty) / actual_qty)
- **Segmentable by:** forecast_method (statistical vs manual_override vs consensus), product, warehouse, time period

### Inventory Carrying Cost
Annual cost of holding inventory, expressed as a percentage of inventory value.
- **Industry standard:** 25% of inventory value per year (includes warehousing, insurance, obsolescence, capital cost)
- **Monthly carrying cost** = (qty_on_hand * unit_cost) * 0.25 / 12
- **Source:** inventory_daily joined to products for unit_cost

### Revenue at Risk
Total revenue value of sales orders currently in backordered status.
- **Source:** sales_orders
- **Formula:** SUM(revenue) WHERE status = 'backordered'
- **Segment by:** customer tier, product category, warehouse

### Freight Cost Per Shipment
Average freight cost across all shipments.
- **Source:** freight_invoices
- **Segmentable by:** carrier, mode (ground/air/LTL/FTL), is_expedited, time period
- **Expedited premium:** Expedited shipments typically cost 2.4x standard ground rate

## Business Rules

### ABC Classification
- **A-class:** Top ~17% of products by revenue contribution (20 SKUs). These get the highest safety stock (14 days), most frequent review, and priority replenishment.
- **B-class:** Middle ~33% (40 SKUs). Moderate safety stock (10 days).
- **C-class:** Bottom ~50% (60 SKUs). Minimal safety stock (7 days).

### Supplier Tier Definitions
- **Strategic:** Top-tier partners with long-term contracts, high spend, critical product supply. Quarterly business reviews.
- **Preferred:** Strong performers with competitive terms. Semi-annual reviews.
- **Approved:** Meet minimum quality and delivery standards. Annual reviews.
- **Probationary:** New or underperforming suppliers under enhanced monitoring. Monthly reviews.

### Customer Tier Definitions
- **Platinum:** Top 5 accounts by revenue and strategic importance. Dedicated account management, highest service priority.
- **Gold:** Next 12 accounts. Priority fulfillment, quarterly business reviews.
- **Silver:** Next 18 accounts. Standard service with proactive communication.
- **Untiered:** Remaining 25 accounts. Standard terms and service.

### Supplier SLA Penalty Structure
Per standard supplier contracts:
- OTIF below contracted threshold (typically 92%) for 2 consecutive months triggers a 5% rebate penalty on the affected period's spend
- Quality response SLA: 48 hours to acknowledge quality issues
- Lead time adherence: actual lead time should not exceed contracted lead time by more than 20%

### Inventory Reorder Logic
- When days_of_supply drops below safety_stock_days, reorder_flag is set to true
- Reorder quantity is typically calculated as: (safety_stock_days * avg_daily_demand) - qty_on_hand - qty_in_transit - qty_on_order
- Critical stockout: days_of_supply = 0 with no qty_in_transit

### Return Classification
- **Supplier-attributable:** Returns where the root cause traces to a supplier issue (late delivery from supplier causing late delivery to customer, quality defect originating from supplier)
- **Non-supplier-attributable:** Damage in transit (carrier issue), wrong item picked (warehouse issue), customer change of mind

## Derived Calculations (not pre-computed in data)

These values should be calculated from raw data, not stored:

- **Supplier risk level** — derive from OTIF trend, reject rate, lead time variance rather than relying on the manually maintained risk_rating
- **Inventory value** — qty_on_hand * unit_cost (join inventory_daily to products)
- **Excess inventory** — inventory where days_of_supply > 60 (significantly above safety stock)
- **Slow-moving inventory** — products with declining demand but stable or growing inventory
- **Expedited freight premium** — difference between expedited shipment cost and equivalent standard ground cost
- **SLA penalty amount** — calculate from spend during breach periods and apply the 5% rebate rate
