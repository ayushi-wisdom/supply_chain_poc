# Vantage Industrial Supply — Domain Context

## Business Overview

Vantage Industrial Supply is a mid-size industrial distributor serving manufacturing, energy, construction, mining, marine, and defense customers across the United States. They source products from 18 suppliers across 5 categories (Electrical Components, Precision Bearings, Industrial Fasteners, Hydraulic Fittings, Safety Equipment) and distribute through 4 regional warehouses to 60 active customer accounts.

## Data Sources

Data spans two structured sources and an unstructured document store:

- **Snowflake** (primary): ERP-derived operational data — products, suppliers, warehouses, customers, purchase orders, inventory snapshots, demand forecasts, supplier scorecards
- **Databricks** (secondary): Logistics and fulfillment data — sales orders, shipments, returns, freight invoices
- **SharePoint** (unstructured): Supplier contracts, quality audit reports, carrier rate cards, internal policies

## Date Anchor

All data uses actual calendar dates. The most recent data point corresponds to the current date. History extends 12 months back.

## Key Business Context

- ABC classification drives inventory management: A-class products (top 20% by revenue) get 14-day safety stock, B-class gets 10-day, C-class gets 7-day
- Supplier tiers (strategic/preferred/approved/probationary) determine contract terms and review cadence
- Customer tiers (platinum/gold/silver/untiered) determine service level priority and escalation paths
- Fill rate and OTIF (on-time in-full) are the two north-star metrics tracked at the executive level
- Warehouses operate as either distribution centers, fulfillment centers, or raw materials hubs with different operational profiles
