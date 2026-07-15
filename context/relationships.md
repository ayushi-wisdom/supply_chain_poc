# Relationships and Join Paths

## Primary Join Paths

### products (hub table)
Products is the central dimension that connects most fact tables.

- `products.product_id` = `purchase_orders.product_id` (1:many)
- `products.product_id` = `inventory_daily.product_id` (1:many)
- `products.product_id` = `demand_forecast.product_id` (1:many)
- `products.product_id` = `sales_orders.product_id` (1:many)
- `products.product_id` = `returns.product_id` (1:many)

### suppliers → purchase_orders → shipments (inbound chain)
- `suppliers.supplier_id` = `purchase_orders.supplier_id` (1:many)
- `suppliers.supplier_id` = `supplier_scorecards.supplier_id` (1:many)
- `purchase_orders.po_id` = `shipments.reference_id` WHERE `shipments.reference_type = 'PO'` (1:many)

**Important:** To join shipments to suppliers, you must go through purchase_orders. There is no direct supplier_id on the shipments table.

```sql
-- Correct: supplier → PO → shipment (inbound)
SELECT s.name, sh.shipment_id, sh.actual_arrival
FROM suppliers s
JOIN purchase_orders po ON s.supplier_id = po.supplier_id
JOIN shipments sh ON po.po_id = sh.reference_id AND sh.reference_type = 'PO'
```

### customers → sales_orders → shipments (outbound chain)
- `customers.customer_id` = `sales_orders.customer_id` (1:many)
- `sales_orders.so_id` = `shipments.reference_id` WHERE `shipments.reference_type = 'SO'` (1:many)
- `sales_orders.so_id` = `returns.so_id` (1:many)
- `customers.customer_id` = `returns.customer_id` (1:many, direct shortcut)

### shipments → freight_invoices
- `shipments.shipment_id` = `freight_invoices.shipment_id` (1:many, typically 1:1)

### warehouses
- `warehouses.warehouse_id` = `inventory_daily.warehouse_id` (1:many)
- `warehouses.warehouse_id` = `purchase_orders.warehouse_id` (1:many)
- `warehouses.warehouse_id` = `sales_orders.warehouse_id` (1:many)
- `warehouses.warehouse_id` = `shipments.origin_warehouse_id` (1:many)

## Cross-Source Joins

The following joins bridge Snowflake and Databricks tables. These are the key cross-source connections that enable end-to-end visibility:

1. **Product-level join** (most common): `products.product_id` (Snowflake) = `sales_orders.product_id` (Databricks)
2. **Warehouse-level join**: `warehouses.warehouse_id` (Snowflake) = `sales_orders.warehouse_id` (Databricks)
3. **Full supply chain trace**: `suppliers` → `purchase_orders` → `products` → `sales_orders` → `customers` spans both sources

## Polymorphic Join: Shipments

The shipments table uses `reference_type` + `reference_id` to link to either purchase_orders or sales_orders:

```sql
-- Inbound shipments (from suppliers)
SELECT * FROM shipments WHERE reference_type = 'PO'
-- Join: shipments.reference_id = purchase_orders.po_id

-- Outbound shipments (to customers)  
SELECT * FROM shipments WHERE reference_type = 'SO'
-- Join: shipments.reference_id = sales_orders.so_id
```

**Never join shipments.reference_id directly without filtering on reference_type first.** The same reference_id value could exist in both purchase_orders and sales_orders.

## Forecast-to-Actuals Join

To compare demand forecast to actual sales:

```sql
SELECT 
    f.product_id,
    f.period_start,
    f.forecast_qty,
    f.forecast_method,
    COALESCE(a.actual_qty, 0) as actual_qty,
    ABS(f.forecast_qty - COALESCE(a.actual_qty, 0)) as forecast_error
FROM demand_forecast f
LEFT JOIN (
    SELECT product_id,
           DATE_TRUNC('month', order_date) as month,
           SUM(qty_ordered) as actual_qty
    FROM sales_orders
    GROUP BY 1, 2
) a ON f.product_id = a.product_id
    AND DATE_TRUNC('month', f.period_start) = a.month
```

## Scorecard vs. Raw PO Data

Supplier scorecards are manually maintained and may be stale. To get real-time supplier OTIF, calculate directly from purchase_orders:

```sql
SELECT 
    po.supplier_id,
    COUNT(CASE WHEN po.actual_delivery_date <= po.promised_delivery_date THEN 1 END) * 1.0 
        / COUNT(*) as calculated_otif
FROM purchase_orders po
WHERE po.status = 'received'
AND po.actual_delivery_date IS NOT NULL
GROUP BY po.supplier_id
```

Compare this to `supplier_scorecards.otif_pct` to identify rating discrepancies.
