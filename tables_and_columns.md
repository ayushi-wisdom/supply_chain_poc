# Tables and Columns

## Snowflake Tables

### products
Product master data for all SKUs in the catalog.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| product_id | VARCHAR | Primary key, matches SKU code | EC-1847 |
| sku | VARCHAR | Stock keeping unit code | EC-1847 |
| name | VARCHAR | Full product name | High-Voltage Relay Module |
| category | VARCHAR | Product category | Electrical Components |
| subcategory | VARCHAR | Product subcategory | Electrical Components |
| unit_cost | DECIMAL | Cost per unit in USD | 84.50 |
| unit_price | DECIMAL | Selling price per unit in USD | 142.00 |
| abc_class | CHAR(1) | ABC inventory classification (A=high revenue, B=medium, C=low) | A |
| reorder_point | DECIMAL | Minimum quantity threshold triggering reorder | 8.0 |
| safety_stock_days | INTEGER | Target days of safety stock (A=14, B=10, C=7) | 14 |
| lead_time_days | INTEGER | Standard procurement lead time in days | 12 |
| weight_kg | DECIMAL | Product weight in kilograms | 2.1 |
| is_active | BOOLEAN | Whether the product is currently active in the catalog | true |

### suppliers
Supplier master data for all vendors.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| supplier_id | VARCHAR | Primary key | SUP-1001 |
| name | VARCHAR | Supplier company name | Apex Components |
| country | VARCHAR | Country of origin | China |
| region | VARCHAR | Geographic region | APAC |
| tier | VARCHAR | Supplier tier: strategic, preferred, approved, or probationary | strategic |
| primary_category | VARCHAR | Main product category supplied | Electrical Components |
| onboarding_date | DATE | Date supplier was onboarded | 2023-07-15 |
| contract_expiry_date | DATE | Current contract expiration date | 2027-03-22 |
| payment_terms_days | INTEGER | Payment terms in net days | 30 |
| lead_time_days_contracted | INTEGER | Contractually agreed lead time in days | 14 |

### warehouses
Warehouse/distribution center locations.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| warehouse_id | VARCHAR | Primary key | WH-EAST |
| name | VARCHAR | Facility name | Atlantic Distribution Center |
| city | VARCHAR | City | Newark |
| state | VARCHAR(2) | State abbreviation | NJ |
| region | VARCHAR | Geographic region | Northeast |
| type | VARCHAR | Facility type: distribution_center, fulfillment_center, or raw_materials | distribution_center |
| capacity_sqft | INTEGER | Total warehouse capacity in square feet | 185000 |
| is_active | BOOLEAN | Whether the facility is currently operational | true |

### customers
Customer account master data.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| customer_id | VARCHAR | Primary key | CUST-0012 |
| name | VARCHAR | Customer company name | Meridian Industries |
| segment | VARCHAR | Customer segment: enterprise, mid_market, or smb | enterprise |
| industry | VARCHAR | Customer's industry vertical | Manufacturing |
| region | VARCHAR | Geographic region | Northeast |
| city | VARCHAR | City | Hartford |
| state | VARCHAR(2) | State abbreviation | CT |
| account_tier | VARCHAR | Service tier: platinum, gold, silver, or empty (untiered) | platinum |
| onboarding_date | DATE | Date customer account was created | 2022-01-10 |

### purchase_orders
Inbound procurement order lines from suppliers.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| po_id | VARCHAR | Purchase order identifier | PO-1042 |
| po_line_id | INTEGER | Line number within the PO | 1 |
| supplier_id | VARCHAR | FK to suppliers table | SUP-1001 |
| product_id | VARCHAR | FK to products table | EC-1847 |
| warehouse_id | VARCHAR | FK to warehouses table — receiving warehouse | WH-EAST |
| order_date | DATE | Date the PO was placed | 2026-06-01 |
| promised_delivery_date | DATE | Supplier's committed delivery date | 2026-06-15 |
| actual_delivery_date | DATE | Actual receipt date (empty if not yet received) | 2026-06-22 |
| qty_ordered | INTEGER | Quantity ordered | 200 |
| qty_received | INTEGER | Quantity actually received (0 if still open) | 190 |
| qty_rejected | INTEGER | Quantity rejected on receipt due to quality issues | 10 |
| unit_cost | DECIMAL | Cost per unit on this PO line | 84.50 |
| total_cost | DECIMAL | Total line cost (qty_ordered * unit_cost) | 16900.00 |
| status | VARCHAR | PO status: open, partial, received, closed, or cancelled | received |

**Key notes:**
- A PO with status "open" and actual_delivery_date empty means the supplier hasn't delivered yet
- The gap between promised_delivery_date and actual_delivery_date is the delivery delay
- qty_rejected / qty_ordered gives the quality rejection rate for that delivery

### inventory_daily
Daily inventory position snapshots by product and warehouse.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| snapshot_date | DATE | Date of the inventory snapshot | 2026-07-15 |
| product_id | VARCHAR | FK to products table | EC-1847 |
| warehouse_id | VARCHAR | FK to warehouses table | WH-EAST |
| qty_on_hand | INTEGER | Physical quantity in the warehouse | 450 |
| qty_allocated | INTEGER | Quantity allocated to open sales orders | 120 |
| qty_available | INTEGER | qty_on_hand minus qty_allocated | 330 |
| qty_in_transit | INTEGER | Quantity on inbound shipments not yet received | 200 |
| qty_on_order | INTEGER | Quantity on open POs not yet shipped | 500 |
| days_of_supply | DECIMAL | Estimated days of remaining stock based on average daily demand | 28.5 |
| reorder_flag | BOOLEAN | True if days_of_supply is below the product's safety_stock_days threshold | false |

**Key notes:**
- Not every product is stocked in every warehouse
- Daily grain enables trend analysis (declining DOS over time)
- reorder_flag = true means the product needs immediate replenishment attention

### demand_forecast
Periodic demand forecasts by product and warehouse.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| forecast_id | VARCHAR | Primary key | FC-00042 |
| product_id | VARCHAR | FK to products table | IF-7010 |
| warehouse_id | VARCHAR | FK to warehouses table | WH-EAST |
| forecast_date | DATE | Date the forecast was generated or overridden | 2026-05-01 |
| period_start | DATE | Start of the forecast period | 2026-05-15 |
| period_end | DATE | End of the forecast period | 2026-06-14 |
| forecast_qty | INTEGER | Forecasted demand quantity for the period | 450 |
| forecast_method | VARCHAR | Method used: statistical, consensus, or manual_override | statistical |
| confidence_level | DECIMAL | Model confidence (0 to 1, 0 for manual overrides) | 0.82 |
| created_by | VARCHAR | Who created or overrode the forecast | System |

**Key notes:**
- Multiple forecast records can exist for the same product/period with different methods
- manual_override entries were created by a named planner who adjusted the system forecast
- To compare forecast accuracy, join forecast_qty to actual sales order volume for the same product and period

### supplier_scorecards
Monthly supplier performance scorecards maintained by the procurement team.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| scorecard_id | VARCHAR | Primary key | SC-00001 |
| supplier_id | VARCHAR | FK to suppliers table | SUP-1001 |
| month | DATE | First day of the scored month | 2026-06-01 |
| otif_pct | DECIMAL | On-time in-full delivery percentage (0 to 1) | 0.76 |
| avg_lead_time_days | DECIMAL | Average actual lead time in days for the month | 19 |
| reject_rate_pct | DECIMAL | Percentage of received quantity rejected (0 to 1) | 0.07 |
| order_count | INTEGER | Number of PO lines delivered that month | 38 |
| total_spend | DECIMAL | Total procurement spend with this supplier for the month | 152000.00 |
| quality_score | DECIMAL | Composite quality score (derived from OTIF and reject rate) | 62.0 |
| risk_rating | VARCHAR | Procurement team's risk assessment: low, medium, high, or critical | medium |

**Key notes:**
- risk_rating is manually maintained and may not reflect current performance data
- otif_pct is calculated from PO delivery data: deliveries on or before promised_delivery_date / total deliveries
- Compare risk_rating to actual otif_pct to find stale or inaccurate ratings

## Databricks Tables

### sales_orders
Outbound customer order lines.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| so_id | VARCHAR | Sales order identifier | SO-2042 |
| so_line_id | INTEGER | Line number within the SO | 1 |
| customer_id | VARCHAR | FK to customers table | CUST-0012 |
| product_id | VARCHAR | FK to products table | EC-1847 |
| warehouse_id | VARCHAR | FK to warehouses table — fulfilling warehouse | WH-EAST |
| order_date | DATE | Date the customer placed the order | 2026-07-01 |
| requested_delivery_date | DATE | Date the customer requested delivery | 2026-07-08 |
| promised_delivery_date | DATE | Date Vantage committed to deliver | 2026-07-09 |
| actual_ship_date | DATE | Actual shipment date (empty if not yet shipped) | 2026-07-07 |
| actual_delivery_date | DATE | Actual delivery date (empty if not yet delivered) | 2026-07-09 |
| qty_ordered | INTEGER | Quantity ordered by the customer | 100 |
| qty_shipped | INTEGER | Quantity actually shipped (0 if backordered) | 100 |
| qty_backordered | INTEGER | Quantity on backorder due to stockout | 0 |
| unit_price | DECIMAL | Selling price per unit | 142.00 |
| revenue | DECIMAL | Line revenue (qty_ordered * unit_price) | 14200.00 |
| status | VARCHAR | Order status: pending, processing, shipped, delivered, backordered, or cancelled | delivered |

**Key notes:**
- Customer OTIF is calculated by comparing actual_delivery_date to promised_delivery_date
- Fill rate is the percentage of orders that shipped complete (qty_shipped = qty_ordered)
- Backordered orders indicate stockout conditions for the product at the fulfilling warehouse

### shipments
Shipment tracking records for both inbound (from suppliers) and outbound (to customers) shipments.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| shipment_id | VARCHAR | Primary key | SHP-5042 |
| reference_type | VARCHAR | Whether this shipment is for a PO (inbound) or SO (outbound) | SO |
| reference_id | VARCHAR | The PO or SO ID this shipment is associated with | SO-2042 |
| carrier_name | VARCHAR | Carrier/logistics provider name | FastTrack Logistics |
| mode | VARCHAR | Shipping mode: ground, air, ocean, LTL, or FTL | ground |
| origin_warehouse_id | VARCHAR | Originating warehouse ID | WH-EAST |
| destination | VARCHAR | Destination city/address | Hartford, CT |
| ship_date | DATE | Date the shipment was dispatched | 2026-07-07 |
| estimated_arrival | DATE | Estimated delivery date | 2026-07-10 |
| actual_arrival | DATE | Actual arrival date (empty if in transit) | 2026-07-09 |
| freight_cost | DECIMAL | Freight cost for this shipment | 245.80 |
| is_expedited | BOOLEAN | Whether this was an expedited/rush shipment | false |
| weight_kg | DECIMAL | Shipment weight in kilograms | 125.3 |
| status | VARCHAR | Shipment status: in_transit, delivered, delayed, or exception | delivered |

**Key notes:**
- reference_type + reference_id creates a polymorphic join: filter by reference_type = 'PO' to get inbound supplier shipments, or 'SO' for outbound customer shipments
- is_expedited = true means premium shipping was used (typically 2.4x standard cost)
- Compare estimated_arrival to actual_arrival to measure carrier performance

### returns
Customer return records.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| return_id | VARCHAR | Primary key | RET-00042 |
| so_id | VARCHAR | FK to sales_orders — the original sales order | SO-2042 |
| so_line_id | INTEGER | Line on the original SO being returned | 1 |
| customer_id | VARCHAR | FK to customers table | CUST-0012 |
| product_id | VARCHAR | FK to products table | EC-1847 |
| return_date | DATE | Date the return was processed | 2026-07-10 |
| qty_returned | INTEGER | Quantity returned | 15 |
| reason_code | VARCHAR | Return reason: defective, damaged_in_transit, wrong_item, late_delivery, or customer_change | late_delivery |
| disposition | VARCHAR | What happened to the returned goods: restock, scrap, or return_to_supplier | return_to_supplier |
| refund_amount | DECIMAL | Refund issued to the customer | 2130.00 |
| supplier_attributable | BOOLEAN | Whether the return root cause traces back to a supplier issue | true |

**Key notes:**
- supplier_attributable = true means the return was caused by a supplier problem (late delivery, quality defect originating from supplier)
- Join to sales_orders via so_id to trace the original order details
- reason_code = 'late_delivery' with supplier_attributable = true indicates the customer return was caused by upstream supplier delay

### freight_invoices
Carrier invoices for freight charges.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| invoice_id | VARCHAR | Primary key | INV-8042 |
| shipment_id | VARCHAR | FK to shipments table | SHP-5042 |
| carrier_name | VARCHAR | Carrier name (should match shipments.carrier_name) | FastTrack Logistics |
| invoice_date | DATE | Date the invoice was issued | 2026-07-12 |
| base_rate | DECIMAL | Base freight rate in USD | 245.80 |
| fuel_surcharge | DECIMAL | Fuel surcharge amount | 19.66 |
| accessorial_charges | DECIMAL | Additional charges (detention, liftgate, etc.) | 0.00 |
| total_invoiced | DECIMAL | Total invoice amount (base + fuel + accessorial) | 265.46 |
| contracted_rate | DECIMAL | The rate that should have been charged per the carrier agreement | 258.09 |
| variance_amount | DECIMAL | Difference between total_invoiced and contracted_rate (positive = overcharge) | 7.37 |
| dispute_flag | BOOLEAN | Whether this invoice has been flagged for dispute due to overcharge | false |

**Key notes:**
- variance_amount > 0 means the carrier charged more than the contracted rate
- dispute_flag = true means the overcharge was identified and flagged for resolution
- To analyze freight cost trends, aggregate total_invoiced by month and compare to prior periods
- Fuel surcharge as a percentage of base_rate should be monitored for creep over time
