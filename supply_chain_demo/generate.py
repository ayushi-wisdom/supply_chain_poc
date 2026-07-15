#!/usr/bin/env python3
"""
Supply Chain Demo — Canonical Seed Generator
Generates all 12 tables with encoded data moments for Vantage Industrial Supply.

Usage:
    python generate.py                          # anchor = today
    python generate.py --anchor-date 2026-07-15 # explicit anchor
"""

import argparse
import csv
import os
import random
import math
from datetime import date, datetime, timedelta
from pathlib import Path

# ── CONFIG ──────────────────────────────────────────────────────────────────
SEED = 42
HISTORY_MONTHS = 12

# Directories
BASE_DIR = Path(__file__).parent
SNOWFLAKE_DIR = BASE_DIR / "data" / "snowflake"
DATABRICKS_DIR = BASE_DIR / "data" / "databricks"

# ── ENTITY DEFINITIONS (pinned across all regenerations) ────────────────────

CATEGORIES = {
    "Electrical Components": [
        ("EC-1847", "High-Voltage Relay Module", 84.50, 142.00, "A", 8.0, 2.1),
        ("EC-2291", "Industrial Circuit Breaker 30A", 67.20, 112.00, "A", 6.5, 1.8),
        ("EC-3004", "Brushless Motor Controller", 125.00, 209.00, "A", 12.0, 3.2),
        ("EC-3517", "Power Distribution Block 600V", 43.80, 73.00, "A", 4.5, 0.9),
        ("EC-1102", "Terminal Strip 12-Position", 12.40, 21.00, "B", 2.0, 0.3),
        ("EC-1205", "DIN Rail Mounted Timer", 28.60, 48.00, "B", 3.5, 0.5),
        ("EC-1330", "Panel Mount Indicator Light", 8.90, 15.00, "B", 1.5, 0.2),
        ("EC-1455", "Miniature Relay 24VDC", 15.70, 26.00, "B", 2.5, 0.3),
        ("EC-1580", "Wire Duct 2x2 6ft", 22.30, 37.00, "B", 4.0, 1.2),
        ("EC-1610", "Push Button Switch IP67", 11.50, 19.00, "B", 1.8, 0.2),
        ("EC-1720", "Cable Gland PG13.5", 3.20, 5.50, "C", 0.5, 0.1),
        ("EC-1835", "Fuse Holder 30A", 6.80, 11.50, "C", 1.0, 0.15),
        ("EC-1940", "Surge Protector DIN Rail", 18.90, 32.00, "C", 3.0, 0.4),
        ("EC-2050", "Conduit Fitting 3/4in", 2.10, 3.50, "C", 0.3, 0.05),
        ("EC-2160", "Wire Connector Assortment", 7.40, 12.50, "C", 1.2, 0.2),
        ("EC-2275", "EMI Filter 10A", 24.50, 41.00, "C", 3.8, 0.6),
        ("EC-2380", "Contactor 3-Pole 25A", 52.30, 87.00, "C", 7.5, 1.4),
        ("EC-2490", "Transformer 120/24V 100VA", 38.70, 65.00, "C", 5.5, 2.8),
        ("EC-2595", "Ground Bar Kit", 9.60, 16.00, "C", 1.5, 0.3),
        ("EC-2680", "Phase Monitor Relay", 45.20, 75.00, "C", 6.8, 0.7),
        ("EC-2790", "Disconnect Switch 60A", 62.40, 104.00, "C", 9.0, 2.0),
        ("EC-2885", "Control Relay Socket", 5.30, 9.00, "C", 0.8, 0.1),
        ("EC-2970", "LED Strip Light 24V 5m", 16.80, 28.00, "C", 2.5, 0.4),
        ("EC-3100", "Motor Starter DOL 10HP", 89.50, 149.00, "C", 13.0, 3.5),
    ],
    "Precision Bearings": [
        ("PB-4010", "Deep Groove Ball Bearing 6205", 18.50, 31.00, "A", 3.0, 0.4),
        ("PB-4125", "Tapered Roller Bearing 30206", 34.20, 57.00, "A", 5.5, 0.8),
        ("PB-4230", "Spherical Roller Bearing 22210", 72.60, 121.00, "A", 11.0, 2.1),
        ("PB-4340", "Angular Contact Bearing 7206", 28.90, 48.00, "B", 4.5, 0.6),
        ("PB-4455", "Needle Roller Bearing NK20/16", 14.30, 24.00, "B", 2.2, 0.3),
        ("PB-4560", "Thrust Ball Bearing 51105", 11.80, 20.00, "B", 1.8, 0.25),
        ("PB-4675", "Pillow Block Bearing UCP205", 22.40, 37.00, "B", 3.5, 0.9),
        ("PB-4780", "Linear Ball Bearing LM20UU", 9.50, 16.00, "B", 1.5, 0.2),
        ("PB-4890", "Flanged Bearing UCF206", 26.70, 45.00, "B", 4.2, 1.0),
        ("PB-4995", "Self-Aligning Bearing 1205", 19.80, 33.00, "B", 3.1, 0.5),
        ("PB-5100", "Cam Follower KR30", 16.20, 27.00, "C", 2.5, 0.35),
        ("PB-5215", "Rod End Bearing SA10", 8.70, 14.50, "C", 1.3, 0.2),
        ("PB-5320", "Insert Bearing UC205", 13.60, 23.00, "C", 2.1, 0.4),
        ("PB-5430", "Slewing Ring Bearing 110x200", 245.00, 409.00, "C", 38.0, 12.5),
        ("PB-5540", "Miniature Bearing 608ZZ", 3.40, 5.70, "C", 0.5, 0.05),
        ("PB-5650", "Plain Bearing Bush 20x23x20", 4.80, 8.00, "C", 0.7, 0.08),
        ("PB-5760", "Cross Roller Bearing RB3010", 135.00, 225.00, "C", 21.0, 1.8),
        ("PB-5870", "Combined Bearing 4.054", 42.30, 71.00, "C", 6.5, 1.2),
        ("PB-5980", "Track Roller LFR5201", 15.90, 26.50, "C", 2.4, 0.3),
        ("PB-6090", "Bearing Housing SNL510", 58.40, 97.00, "C", 9.0, 4.5),
        ("PB-6195", "Adapter Sleeve H2310", 12.10, 20.00, "C", 1.9, 0.6),
        ("PB-6280", "Withdrawal Sleeve AH2310", 14.50, 24.00, "C", 2.2, 0.7),
        ("PB-6370", "Bearing Lock Nut KM5", 5.20, 8.70, "C", 0.8, 0.15),
        ("PB-6460", "Bearing Seal Kit 6205", 3.90, 6.50, "C", 0.6, 0.04),
    ],
    "Industrial Fasteners": [
        ("IF-7010", "Hex Bolt M12x60 GR8.8 Box/50", 32.50, 54.00, "A", 5.0, 2.8),
        ("IF-7125", "Socket Head Cap Screw M10x40 Box/100", 28.40, 47.00, "A", 4.4, 2.2),
        ("IF-7230", "Structural Bolt A325 3/4x3 Box/25", 45.60, 76.00, "A", 7.0, 3.5),
        ("IF-7340", "Stainless Hex Bolt M8x30 Box/100", 38.20, 64.00, "B", 5.9, 1.8),
        ("IF-7455", "Carriage Bolt 3/8x4 Box/50", 18.70, 31.00, "B", 2.9, 1.5),
        ("IF-7560", "Flange Bolt M10x25 Box/50", 21.30, 36.00, "B", 3.3, 1.2),
        ("IF-7675", "U-Bolt 3/8x3x6", 8.40, 14.00, "B", 1.3, 0.8),
        ("IF-7780", "Eye Bolt M12 Forged", 12.60, 21.00, "B", 1.9, 0.6),
        ("IF-7890", "Anchor Bolt 5/8x12 Box/10", 26.80, 45.00, "B", 4.1, 2.5),
        ("IF-7995", "Thread Rod M16x1000", 14.50, 24.00, "B", 2.2, 1.8),
        ("IF-8100", "Hex Nut M12 GR8 Box/100", 9.80, 16.50, "C", 1.5, 1.0),
        ("IF-8215", "Nylon Lock Nut M10 Box/100", 11.20, 19.00, "C", 1.7, 0.8),
        ("IF-8320", "Flat Washer M12 Box/200", 6.40, 11.00, "C", 1.0, 0.6),
        ("IF-8430", "Split Lock Washer 3/8 Box/200", 4.80, 8.00, "C", 0.7, 0.4),
        ("IF-8540", "Rivet 3/16x1/2 Box/500", 15.30, 26.00, "C", 2.4, 0.5),
        ("IF-8650", "Set Screw M8x12 Box/100", 7.90, 13.00, "C", 1.2, 0.4),
        ("IF-8760", "Dowel Pin 6x30 Box/50", 10.40, 17.50, "C", 1.6, 0.3),
        ("IF-8870", "Cotter Pin 3/32x1 Box/100", 3.50, 6.00, "C", 0.5, 0.2),
        ("IF-8980", "Clevis Pin 8x40", 5.60, 9.50, "C", 0.9, 0.15),
        ("IF-9090", "Hitch Pin 1/2x4", 4.20, 7.00, "C", 0.6, 0.2),
        ("IF-9195", "Spring Pin 5x30 Box/50", 8.10, 13.50, "C", 1.2, 0.25),
        ("IF-9280", "Stud Bolt M16x100", 16.70, 28.00, "C", 2.6, 0.9),
        ("IF-9370", "Wing Nut M8 Box/50", 5.90, 10.00, "C", 0.9, 0.3),
        ("IF-9460", "Coupling Nut M12x36", 7.30, 12.00, "C", 1.1, 0.4),
    ],
    "Hydraulic Fittings": [
        ("HF-1010", "Hydraulic Hose 1/2in x 10ft 3000PSI", 48.60, 81.00, "A", 7.5, 2.8),
        ("HF-1125", "Quick Disconnect Coupling 1/2in", 22.30, 37.00, "A", 3.4, 0.5),
        ("HF-1230", "Hydraulic Cylinder 3in Bore x 8in", 285.00, 475.00, "A", 44.0, 8.5),
        ("HF-1340", "JIC Fitting 90° Elbow 1/2in", 8.70, 14.50, "B", 1.3, 0.2),
        ("HF-1455", "O-Ring Face Seal Fitting 3/4in", 14.20, 24.00, "B", 2.2, 0.3),
        ("HF-1560", "Hydraulic Filter Element 10 Micron", 34.50, 58.00, "B", 5.3, 0.8),
        ("HF-1675", "Pressure Gauge 0-5000PSI", 28.90, 48.00, "B", 4.5, 0.4),
        ("HF-1780", "Ball Valve 3/4in 5000PSI", 42.10, 70.00, "B", 6.5, 1.2),
        ("HF-1890", "Hydraulic Pump Gear Type 11GPM", 195.00, 325.00, "B", 30.0, 6.2),
        ("HF-1995", "Check Valve Inline 1/2in", 18.60, 31.00, "B", 2.9, 0.3),
        ("HF-2100", "Tube Nut 3/8in Box/10", 6.30, 10.50, "C", 1.0, 0.1),
        ("HF-2215", "Suction Strainer 1in 100 Mesh", 24.70, 41.00, "C", 3.8, 0.6),
        ("HF-2320", "Hydraulic Seal Kit 3in Cyl", 19.40, 32.00, "C", 3.0, 0.2),
        ("HF-2430", "Manifold Block 4-Station", 68.50, 114.00, "C", 10.5, 3.4),
        ("HF-2540", "Accumulator 1 Quart 3000PSI", 142.00, 237.00, "C", 22.0, 4.1),
        ("HF-2650", "Flow Control Valve 1/2in", 36.80, 61.00, "C", 5.7, 0.8),
        ("HF-2760", "Directional Valve 4/3 Way", 98.50, 164.00, "C", 15.2, 2.5),
        ("HF-2870", "Reservoir Tank 5 Gallon", 75.30, 126.00, "C", 11.6, 8.0),
        ("HF-2980", "Hydraulic Hose Crimping Ferrule", 2.80, 4.70, "C", 0.4, 0.05),
        ("HF-3090", "Test Port Coupling M14x1.5", 7.50, 12.50, "C", 1.2, 0.1),
        ("HF-3195", "SAE Flange 1in Code 61", 31.20, 52.00, "C", 4.8, 1.5),
        ("HF-3280", "Pipe Plug 1/2 NPT Box/25", 4.60, 7.70, "C", 0.7, 0.08),
        ("HF-3370", "Swivel Joint 1/2in", 26.40, 44.00, "C", 4.1, 0.6),
        ("HF-3460", "Hydraulic Oil ISO 46 5 Gal", 52.00, 87.00, "C", 8.0, 18.5),
    ],
    "Safety Equipment": [
        ("SE-1010", "Hard Hat Type II Full Brim", 32.40, 54.00, "A", 5.0, 0.5),
        ("SE-1125", "Safety Glasses Anti-Fog Z87.1", 8.60, 14.50, "A", 1.3, 0.1),
        ("SE-1230", "Fall Protection Harness", 125.00, 209.00, "A", 19.3, 1.8),
        ("SE-1340", "Nitrile Gloves XL Box/100", 14.20, 24.00, "B", 2.2, 0.8),
        ("SE-1455", "Ear Plugs NRR32 Box/200", 18.50, 31.00, "B", 2.9, 0.6),
        ("SE-1560", "Hi-Vis Safety Vest Class 2", 11.30, 19.00, "B", 1.7, 0.3),
        ("SE-1675", "Respirator Half-Face P100", 28.70, 48.00, "B", 4.4, 0.4),
        ("SE-1780", "Steel Toe Boot Cover", 16.80, 28.00, "B", 2.6, 0.5),
        ("SE-1890", "First Aid Kit 50 Person", 62.40, 104.00, "B", 9.6, 3.2),
        ("SE-1995", "Fire Extinguisher 10lb ABC", 45.60, 76.00, "B", 7.0, 5.5),
        ("SE-2100", "Safety Cone 28in Reflective", 9.40, 16.00, "C", 1.5, 1.8),
        ("SE-2215", "Caution Tape 1000ft Roll", 6.80, 11.50, "C", 1.0, 0.9),
        ("SE-2320", "Lockout Tagout Station", 85.00, 142.00, "C", 13.1, 2.5),
        ("SE-2430", "Spill Kit 20 Gallon", 72.30, 121.00, "C", 11.2, 6.0),
        ("SE-2540", "Emergency Shower/Eyewash", 320.00, 533.00, "C", 49.4, 15.0),
        ("SE-2650", "Gas Detector 4-Gas", 195.00, 325.00, "C", 30.1, 0.5),
        ("SE-2760", "Welding Helmet Auto-Dark", 68.50, 114.00, "C", 10.6, 0.8),
        ("SE-2870", "Safety Harness Lanyard 6ft", 42.10, 70.00, "C", 6.5, 0.4),
        ("SE-2980", "Knee Pads Professional", 24.30, 41.00, "C", 3.8, 0.5),
        ("SE-3090", "Face Shield Bracket + Visor", 15.60, 26.00, "C", 2.4, 0.3),
        ("SE-3195", "Hearing Band NRR25", 7.20, 12.00, "C", 1.1, 0.1),
        ("SE-3280", "Safety Sign Pack Assorted", 34.50, 58.00, "C", 5.3, 1.2),
        ("SE-3370", "Chemical Splash Goggles", 10.80, 18.00, "C", 1.7, 0.15),
        ("SE-3460", "Traffic Delineator Post 42in", 28.90, 48.00, "C", 4.5, 3.5),
    ],
}

# The 4 Apex crisis SKUs
APEX_CRISIS_SKUS = ["EC-1847", "EC-2291", "EC-3004", "EC-3517"]

# Industrial Fasteners top SKUs for overstock moment
OVERSTOCK_SKUS = ["IF-7010", "IF-7125", "IF-7230", "IF-7340", "IF-7455",
                  "IF-7560", "IF-7675", "IF-7780", "IF-7890", "IF-7995",
                  "IF-8100", "IF-8215", "IF-8320", "IF-8430", "IF-8540"]

SUPPLIERS = [
    ("SUP-1001", "Apex Components", "China", "APAC", "strategic", "Electrical Components", 1095, 30, 14),
    ("SUP-1002", "GlobalParts Inc", "USA", "North America", "strategic", "Electrical Components", 1460, 45, 10),
    ("SUP-1003", "Ironclad Fasteners", "USA", "North America", "preferred", "Industrial Fasteners", 1825, 30, 7),
    ("SUP-1004", "Pacific Bearing Co", "Japan", "APAC", "strategic", "Precision Bearings", 2190, 45, 18),
    ("SUP-1005", "HydraForce Supply", "Germany", "Europe", "preferred", "Hydraulic Fittings", 1460, 60, 21),
    ("SUP-1006", "SafeGuard Pro", "USA", "North America", "preferred", "Safety Equipment", 1095, 30, 5),
    ("SUP-1007", "Nanjing Electric", "China", "APAC", "approved", "Electrical Components", 730, 30, 16),
    ("SUP-1008", "Midwest Fastener Dist", "USA", "North America", "approved", "Industrial Fasteners", 548, 30, 5),
    ("SUP-1009", "Euro Bearings GmbH", "Germany", "Europe", "approved", "Precision Bearings", 1095, 60, 25),
    ("SUP-1010", "Delta Hydraulics", "USA", "North America", "approved", "Hydraulic Fittings", 730, 30, 10),
    ("SUP-1011", "Shield Safety Corp", "Canada", "North America", "approved", "Safety Equipment", 548, 45, 8),
    ("SUP-1012", "ShenZhen Precision", "China", "APAC", "approved", "Precision Bearings", 365, 30, 20),
    ("SUP-1013", "TechBolt Industries", "Taiwan", "APAC", "approved", "Industrial Fasteners", 912, 30, 12),
    ("SUP-1014", "Nordic Fluid Power", "Sweden", "Europe", "approved", "Hydraulic Fittings", 1095, 60, 28),
    ("SUP-1015", "Atlas Electrical", "USA", "North America", "probationary", "Electrical Components", 180, 30, 8),
    ("SUP-1016", "Titan Fasteners Ltd", "UK", "Europe", "approved", "Industrial Fasteners", 730, 45, 14),
    ("SUP-1017", "QuickConnect Hydro", "USA", "North America", "probationary", "Hydraulic Fittings", 270, 30, 7),
    ("SUP-1018", "Fortress Safety Int", "Australia", "APAC", "approved", "Safety Equipment", 548, 30, 15),
]

WAREHOUSES = [
    ("WH-EAST", "Atlantic Distribution Center", "Newark", "NJ", "Northeast", "distribution_center", 185000),
    ("WH-WEST", "Pacific Fulfillment Center", "Fontana", "CA", "West", "fulfillment_center", 142000),
    ("WH-CENTRAL", "Heartland Hub", "Indianapolis", "IN", "Midwest", "distribution_center", 168000),
    ("WH-SOUTH", "Gulf Coast Warehouse", "Houston", "TX", "Southeast", "raw_materials", 95000),
]

CUSTOMER_NAMES = [
    # Platinum (5)
    ("CUST-0012", "Meridian Industries", "enterprise", "Manufacturing", "Northeast", "Hartford", "CT", "platinum"),
    ("CUST-0025", "Cascade Power Systems", "enterprise", "Energy", "West", "Portland", "OR", "platinum"),
    ("CUST-0038", "Pinnacle Manufacturing", "enterprise", "Manufacturing", "Midwest", "Detroit", "MI", "platinum"),
    ("CUST-0041", "Redstone Engineering", "enterprise", "Construction", "Southeast", "Atlanta", "GA", "platinum"),
    ("CUST-0056", "Sterling Aerospace", "enterprise", "Aerospace", "West", "Tucson", "AZ", "platinum"),
    # Gold (12)
    ("CUST-0067", "Horizon Mining Corp", "enterprise", "Mining", "West", "Reno", "NV", "gold"),
    ("CUST-0073", "Bridgeport Automation", "enterprise", "Manufacturing", "Northeast", "Boston", "MA", "gold"),
    ("CUST-0089", "Summit Construction Group", "enterprise", "Construction", "Southeast", "Charlotte", "NC", "gold"),
    ("CUST-0102", "Prairie Wind Energy", "mid_market", "Energy", "Midwest", "Omaha", "NE", "gold"),
    ("CUST-0115", "Ironworks Fabrication", "mid_market", "Manufacturing", "Midwest", "Cleveland", "OH", "gold"),
    ("CUST-0128", "Pacific Shipyard Services", "mid_market", "Marine", "West", "Long Beach", "CA", "gold"),
    ("CUST-0134", "Valley Agricultural Equip", "mid_market", "Agriculture", "Midwest", "Des Moines", "IA", "gold"),
    ("CUST-0147", "Coastal Defense Systems", "mid_market", "Defense", "Southeast", "Savannah", "GA", "gold"),
    ("CUST-0155", "Northern Pipeline Inc", "mid_market", "Oil & Gas", "Midwest", "Bismarck", "ND", "gold"),
    ("CUST-0168", "Lakeshore Utilities", "mid_market", "Utilities", "Midwest", "Milwaukee", "WI", "gold"),
    ("CUST-0171", "Tidewater Marine Repair", "mid_market", "Marine", "Southeast", "Norfolk", "VA", "gold"),
    ("CUST-0183", "Appalachian Resources", "mid_market", "Mining", "Southeast", "Charleston", "WV", "gold"),
    # Silver (18)
    ("CUST-0200", "Elm City Machine Works", "mid_market", "Manufacturing", "Northeast", "New Haven", "CT", "silver"),
    ("CUST-0215", "Sunbelt Contractors", "mid_market", "Construction", "Southeast", "Tampa", "FL", "silver"),
    ("CUST-0230", "Great Lakes Steel Fab", "mid_market", "Manufacturing", "Midwest", "Gary", "IN", "silver"),
    ("CUST-0245", "Ridgeline Environmental", "mid_market", "Environmental", "West", "Denver", "CO", "silver"),
    ("CUST-0260", "Capital City Mechanical", "smb", "HVAC", "Southeast", "Richmond", "VA", "silver"),
    ("CUST-0275", "Desert Sun Electric", "smb", "Electrical", "West", "Phoenix", "AZ", "silver"),
    ("CUST-0290", "Heartland Grain Systems", "smb", "Agriculture", "Midwest", "Wichita", "KS", "silver"),
    ("CUST-0305", "New England Boatworks", "smb", "Marine", "Northeast", "Newport", "RI", "silver"),
    ("CUST-0320", "Ozark Manufacturing", "smb", "Manufacturing", "Midwest", "Springfield", "MO", "silver"),
    ("CUST-0335", "Lone Star Fabricators", "smb", "Manufacturing", "Southeast", "San Antonio", "TX", "silver"),
    ("CUST-0350", "Sierra Equipment Rental", "smb", "Construction", "West", "Sacramento", "CA", "silver"),
    ("CUST-0365", "Harbor Light Marine", "smb", "Marine", "Northeast", "Gloucester", "MA", "silver"),
    ("CUST-0380", "Keystone Industrial", "smb", "Manufacturing", "Northeast", "Allentown", "PA", "silver"),
    ("CUST-0395", "Bluegrass Mechanical", "smb", "HVAC", "Southeast", "Louisville", "KY", "silver"),
    ("CUST-0410", "Columbia River Works", "smb", "Manufacturing", "West", "Vancouver", "WA", "silver"),
    ("CUST-0425", "Magnolia Power Services", "smb", "Energy", "Southeast", "Jackson", "MS", "silver"),
    ("CUST-0440", "Prairie State Machining", "smb", "Manufacturing", "Midwest", "Peoria", "IL", "silver"),
    ("CUST-0455", "Timber Creek Logging", "smb", "Forestry", "West", "Eugene", "OR", "silver"),
    # Untiered (25)
    ("CUST-0500", "Bayou Welding Supply", "smb", "Welding", "Southeast", "Baton Rouge", "LA", None),
    ("CUST-0510", "Crossroads Hardware Dist", "smb", "Retail", "Midwest", "Topeka", "KS", None),
    ("CUST-0520", "Eagle Mountain Mining", "smb", "Mining", "West", "Boise", "ID", None),
    ("CUST-0530", "Flathead Electric Coop", "smb", "Utilities", "West", "Kalispell", "MT", None),
    ("CUST-0540", "Granite State Industrial", "smb", "Manufacturing", "Northeast", "Manchester", "NH", None),
    ("CUST-0550", "High Plains Equipment", "smb", "Agriculture", "Midwest", "Dodge City", "KS", None),
    ("CUST-0560", "Inland Empire Fabricators", "smb", "Manufacturing", "West", "Spokane", "WA", None),
    ("CUST-0570", "Juniata Valley Machine", "smb", "Manufacturing", "Northeast", "Lewistown", "PA", None),
    ("CUST-0580", "Kaskaskia River Works", "smb", "Manufacturing", "Midwest", "Carlyle", "IL", None),
    ("CUST-0590", "Lehigh Valley Hydraulics", "smb", "Hydraulics", "Northeast", "Bethlehem", "PA", None),
    ("CUST-0600", "Mesabi Range Equipment", "smb", "Mining", "Midwest", "Hibbing", "MN", None),
    ("CUST-0610", "North Cascade Logging", "smb", "Forestry", "West", "Bellingham", "WA", None),
    ("CUST-0620", "Ouachita Machine Shop", "smb", "Manufacturing", "Southeast", "Hot Springs", "AR", None),
    ("CUST-0630", "Piedmont Tool & Die", "smb", "Manufacturing", "Southeast", "Greensboro", "NC", None),
    ("CUST-0640", "Quabbin Reservoir Services", "smb", "Utilities", "Northeast", "Ware", "MA", None),
    ("CUST-0650", "Rio Grande Contractors", "smb", "Construction", "West", "Albuquerque", "NM", None),
    ("CUST-0660", "Scioto Valley Mechanical", "smb", "HVAC", "Midwest", "Chillicothe", "OH", None),
    ("CUST-0670", "Thunder Bay Fabrication", "smb", "Manufacturing", "Midwest", "Duluth", "MN", None),
    ("CUST-0680", "Upper Valley Electric", "smb", "Electrical", "Northeast", "White River Jct", "VT", None),
    ("CUST-0690", "Verde Valley Equipment", "smb", "Agriculture", "West", "Cottonwood", "AZ", None),
    ("CUST-0700", "Wabash River Industrial", "smb", "Manufacturing", "Midwest", "Terre Haute", "IN", None),
    ("CUST-0710", "Yadkin Valley Supply", "smb", "Manufacturing", "Southeast", "Elkin", "NC", None),
    ("CUST-0720", "Zuni Mountain Services", "smb", "Mining", "West", "Gallup", "NM", None),
    ("CUST-0730", "Black Hills Maintenance", "smb", "Mining", "Midwest", "Rapid City", "SD", None),
    ("CUST-0740", "Chesapeake Bay Marine", "smb", "Marine", "Northeast", "Annapolis", "MD", None),
]

CARRIERS = [
    "FastTrack Logistics",
    "Continental Freight",
    "Pacific Coast Carriers",
    "Midwest Express Shipping",
    "Southern Route Transport",
    "Atlas Global Freight",
]


# ── HELPERS ─────────────────────────────────────────────────────────────────

def write_csv(filepath, headers, rows):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)
    print(f"  wrote {filepath.name}: {len(rows):,} rows")


def rand_date(start, end):
    """Random date between start and end (inclusive)."""
    delta = (end - start).days
    if delta <= 0:
        return start
    return start + timedelta(days=random.randint(0, delta))


def rand_weekday(start, end):
    """Random weekday between start and end."""
    for _ in range(100):
        d = rand_date(start, end)
        if d.weekday() < 5:
            return d
    return start


def jitter(value, pct=0.05):
    """Add small random noise to a value."""
    return round(value * (1 + random.uniform(-pct, pct)), 2)


# ── PRODUCT ID LOOKUP ───────────────────────────────────────────────────────

ALL_PRODUCTS = {}
for cat_name, items in CATEGORIES.items():
    for (sku, name, cost, price, abc, rp, wt) in items:
        ALL_PRODUCTS[sku] = {
            "sku": sku, "name": name, "category": cat_name,
            "unit_cost": cost, "unit_price": price, "abc_class": abc,
            "reorder_point": rp, "weight_kg": wt,
        }

# Map supplier to SKUs they supply
SUPPLIER_SKUS = {
    "SUP-1001": [s for s in list(CATEGORIES["Electrical Components"])[:4] + list(CATEGORIES["Precision Bearings"])[:3]],  # Apex - crisis + some bearings
    "SUP-1002": [s for s in list(CATEGORIES["Electrical Components"])[4:10]],   # GlobalParts
    "SUP-1003": [s for s in list(CATEGORIES["Industrial Fasteners"])[:15]],       # Ironclad
    "SUP-1004": [s for s in list(CATEGORIES["Precision Bearings"])[3:10]],        # Pacific Bearing
    "SUP-1005": [s for s in list(CATEGORIES["Hydraulic Fittings"])[:6]],           # HydraForce
    "SUP-1006": [s for s in list(CATEGORIES["Safety Equipment"])[:6]],             # SafeGuard
    "SUP-1007": [s for s in list(CATEGORIES["Electrical Components"])[10:16]],    # Nanjing
    "SUP-1008": [s for s in list(CATEGORIES["Industrial Fasteners"])[9:15]],      # Midwest
    "SUP-1009": [s for s in list(CATEGORIES["Precision Bearings"])[10:17]],       # Euro Bearings
    "SUP-1010": [s for s in list(CATEGORIES["Hydraulic Fittings"])[6:12]],        # Delta
    "SUP-1011": [s for s in list(CATEGORIES["Safety Equipment"])[6:12]],          # Shield
    "SUP-1012": [s for s in list(CATEGORIES["Precision Bearings"])[17:]],         # ShenZhen
    "SUP-1013": [s for s in list(CATEGORIES["Industrial Fasteners"])[15:]],       # TechBolt
    "SUP-1014": [s for s in list(CATEGORIES["Hydraulic Fittings"])[12:18]],       # Nordic
    "SUP-1015": [s for s in list(CATEGORIES["Electrical Components"])[16:20]],    # Atlas
    "SUP-1016": [s for s in list(CATEGORIES["Industrial Fasteners"])[15:20]],     # Titan
    "SUP-1017": [s for s in list(CATEGORIES["Hydraulic Fittings"])[18:]],         # QuickConnect
    "SUP-1018": [s for s in list(CATEGORIES["Safety Equipment"])[12:]],           # Fortress
}


# ── GENERATION FUNCTIONS ────────────────────────────────────────────────────

def gen_products(anchor):
    """Generate products table."""
    rows = []
    for cat_name, items in CATEGORIES.items():
        for (sku, name, cost, price, abc, rp, wt) in items:
            # Safety stock days varies by ABC class
            ssd = {"A": 14, "B": 10, "C": 7}[abc]
            ltd = random.randint(5, 25)
            rows.append([
                sku, sku, name, cat_name,
                cat_name,  # subcategory = category for simplicity
                cost, price, abc, rp, ssd, ltd, wt, True
            ])
    headers = ["product_id", "sku", "name", "category", "subcategory",
               "unit_cost", "unit_price", "abc_class", "reorder_point",
               "safety_stock_days", "lead_time_days", "weight_kg", "is_active"]
    write_csv(SNOWFLAKE_DIR / "products.csv", headers, rows)
    return rows


def gen_suppliers(anchor):
    """Generate suppliers table."""
    rows = []
    for (sid, name, country, region, tier, cat, age_days, pt, ltd) in SUPPLIERS:
        onboard = anchor - timedelta(days=age_days)
        expiry = anchor + timedelta(days=random.randint(90, 730))
        rows.append([sid, name, country, region, tier, cat,
                     onboard.isoformat(), expiry.isoformat(), pt, ltd])
    headers = ["supplier_id", "name", "country", "region", "tier",
               "primary_category", "onboarding_date", "contract_expiry_date",
               "payment_terms_days", "lead_time_days_contracted"]
    write_csv(SNOWFLAKE_DIR / "suppliers.csv", headers, rows)
    return rows


def gen_warehouses(anchor):
    """Generate warehouses table."""
    rows = []
    for (wid, name, city, state, region, wtype, cap) in WAREHOUSES:
        rows.append([wid, name, city, state, region, wtype, cap, True])
    headers = ["warehouse_id", "name", "city", "state", "region", "type",
               "capacity_sqft", "is_active"]
    write_csv(SNOWFLAKE_DIR / "warehouses.csv", headers, rows)
    return rows


def gen_customers(anchor):
    """Generate customers table."""
    rows = []
    for (cid, name, seg, ind, region, city, state, tier) in CUSTOMER_NAMES:
        onboard = anchor - timedelta(days=random.randint(180, 2555))
        rows.append([cid, name, seg, ind, region, city, state,
                     tier if tier else "", onboard.isoformat()])
    headers = ["customer_id", "name", "segment", "industry", "region",
               "city", "state", "account_tier", "onboarding_date"]
    write_csv(SNOWFLAKE_DIR / "customers.csv", headers, rows)
    return rows


def gen_purchase_orders(anchor):
    """Generate purchase_orders with Apex degradation encoded."""
    rows = []
    start = anchor - timedelta(days=365)
    po_counter = 1000

    # For each month in the 12-month window
    for month_offset in range(12):
        month_start = start + timedelta(days=month_offset * 30)
        month_end = month_start + timedelta(days=29)
        if month_end > anchor:
            month_end = anchor

        months_ago = 11 - month_offset  # 11 = oldest, 0 = most recent

        for sup_id, sup_items in SUPPLIER_SKUS.items():
            # How many PO lines this supplier generates per month
            if sup_id == "SUP-1001":
                lines_per_month = random.randint(35, 45)  # Apex is a major supplier
            elif sup_id in ("SUP-1002", "SUP-1003", "SUP-1004", "SUP-1005"):
                lines_per_month = random.randint(18, 28)
            else:
                lines_per_month = random.randint(8, 15)

            for _ in range(lines_per_month):
                po_counter += 1
                po_id = f"PO-{po_counter}"
                po_line = 1  # simplified to 1 line per PO

                item = random.choice(sup_items)
                sku = item[0]
                unit_cost = item[2]

                # Warehouse distribution
                wh = random.choice(["WH-EAST", "WH-WEST", "WH-CENTRAL", "WH-SOUTH"])
                order_date = rand_weekday(month_start, month_end)
                qty = random.choice([25, 50, 100, 150, 200, 250, 500])

                # Lead time and delivery logic
                sup_data = [s for s in SUPPLIERS if s[0] == sup_id][0]
                contracted_lt = sup_data[8]  # lead_time_days_contracted

                promised = order_date + timedelta(days=contracted_lt)

                # ── APEX DEGRADATION PATTERN ──
                if sup_id == "SUP-1001":
                    if months_ago >= 7:
                        # Before degradation: on-time or early
                        delay = random.choice([-2, -1, 0, 0, 0, 1])
                        reject_rate = 0.02
                    elif months_ago >= 6:
                        delay = random.choice([-1, 0, 0, 1, 2, 3])
                        reject_rate = 0.028
                    elif months_ago >= 5:
                        delay = random.choice([0, 1, 2, 3, 4, 5])
                        reject_rate = 0.041
                    elif months_ago >= 4:
                        delay = random.choice([1, 2, 3, 4, 5, 6, 7])
                        reject_rate = 0.053
                    elif months_ago >= 3:
                        delay = random.choice([2, 3, 5, 6, 7, 8, 9])
                        reject_rate = 0.062
                    elif months_ago >= 2:
                        delay = random.choice([3, 5, 7, 8, 9, 10, 12])
                        reject_rate = 0.07
                    elif months_ago >= 1:
                        delay = random.choice([5, 7, 9, 10, 12, 14])
                        reject_rate = 0.07
                    else:
                        # Most recent month: some POs still open (crisis)
                        delay = None  # will be open/past due
                        reject_rate = 0.07

                    # For the 4 crisis SKUs in the most recent ~14 days, make them OPEN
                    if sku in APEX_CRISIS_SKUS and months_ago == 0 and (anchor - order_date).days < 20:
                        actual_delivery = None
                        status = "open"
                        qty_received = 0
                        qty_rejected = 0
                    elif delay is None:
                        # Other recent Apex POs: very late but delivered
                        delay = random.choice([8, 10, 12, 14])
                        actual_delivery = promised + timedelta(days=delay)
                        if actual_delivery > anchor:
                            actual_delivery = None
                            status = "open"
                            qty_received = 0
                            qty_rejected = 0
                        else:
                            status = "received"
                            qty_rejected = max(0, round(qty * reject_rate))
                            qty_received = qty - qty_rejected
                    else:
                        actual_delivery = promised + timedelta(days=delay)
                        if actual_delivery > anchor:
                            actual_delivery = None
                            status = "open"
                            qty_received = 0
                            qty_rejected = 0
                        else:
                            status = "received"
                            qty_rejected = max(0, round(qty * reject_rate))
                            qty_received = qty - qty_rejected
                else:
                    # ── NORMAL SUPPLIERS ──
                    # GlobalParts: consistently good
                    if sup_id == "SUP-1002":
                        delay = random.choice([-2, -1, -1, 0, 0, 0, 0, 1])
                        reject_rate = random.uniform(0.005, 0.015)
                    else:
                        # Everyone else: mostly on time with occasional minor delays
                        delay = random.choices(
                            [-2, -1, 0, 1, 2, 3, 5],
                            weights=[5, 10, 40, 20, 15, 8, 2],
                            k=1
                        )[0]
                        reject_rate = random.uniform(0.005, 0.03)

                    actual_delivery = promised + timedelta(days=delay)
                    if actual_delivery > anchor:
                        actual_delivery = None
                        status = "open"
                        qty_received = 0
                        qty_rejected = 0
                    else:
                        status = "received"
                        qty_rejected = max(0, round(qty * reject_rate))
                        qty_received = qty - qty_rejected

                total_cost = round(qty * unit_cost, 2)
                act_del_str = actual_delivery.isoformat() if actual_delivery else ""

                rows.append([
                    po_id, po_line, sup_id, sku, wh,
                    order_date.isoformat(), promised.isoformat(), act_del_str,
                    qty, qty_received, qty_rejected,
                    unit_cost, total_cost, status
                ])

    headers = ["po_id", "po_line_id", "supplier_id", "product_id", "warehouse_id",
               "order_date", "promised_delivery_date", "actual_delivery_date",
               "qty_ordered", "qty_received", "qty_rejected",
               "unit_cost", "total_cost", "status"]
    write_csv(SNOWFLAKE_DIR / "purchase_orders.csv", headers, rows)
    return rows


def gen_inventory_daily(anchor):
    """Generate inventory_daily with stockout + overstock patterns."""
    rows = []
    start = anchor - timedelta(days=365)

    # Product-warehouse assignments (not every product in every warehouse)
    pw_combos = []
    all_skus = list(ALL_PRODUCTS.keys())
    for sku in all_skus:
        # Each product in 1-3 warehouses
        n_wh = random.choices([1, 2, 3], weights=[20, 50, 30], k=1)[0]
        whs = random.sample(["WH-EAST", "WH-WEST", "WH-CENTRAL", "WH-SOUTH"], n_wh)
        # Ensure crisis SKUs are in EAST and WEST at minimum
        if sku in APEX_CRISIS_SKUS:
            whs = ["WH-EAST", "WH-WEST", "WH-CENTRAL"]
        # Ensure overstock SKUs are in EAST and WEST
        if sku in OVERSTOCK_SKUS:
            if "WH-EAST" not in whs:
                whs.append("WH-EAST")
            if "WH-WEST" not in whs:
                whs.append("WH-WEST")
        for wh in whs:
            pw_combos.append((sku, wh))

    # Generate daily snapshots
    for day_offset in range(366):
        current_date = start + timedelta(days=day_offset)
        days_to_anchor = (anchor - current_date).days

        for (sku, wh) in pw_combos:
            prod = ALL_PRODUCTS[sku]
            base_qty = {"A": 800, "B": 400, "C": 200}[prod["abc_class"]]

            # ── APEX CRISIS SKUs: declining DOS over last 21 days ──
            if sku in APEX_CRISIS_SKUS:
                if days_to_anchor > 30:
                    # Normal inventory levels
                    qty_oh = base_qty + random.randint(-100, 150)
                elif days_to_anchor > 21:
                    # Starting to feel tight
                    qty_oh = int(base_qty * 0.6) + random.randint(-50, 50)
                else:
                    # Declining rapidly
                    decline_pct = max(0.02, (days_to_anchor / 21.0) * 0.4)
                    qty_oh = max(0, int(base_qty * decline_pct) + random.randint(-10, 10))
                    if days_to_anchor <= 9 and wh in ("WH-EAST", "WH-WEST"):
                        # Below safety stock for 9+ days
                        qty_oh = max(0, random.randint(5, 35))

                qty_in_transit = 0 if days_to_anchor <= 14 else random.randint(0, 100)
                qty_on_order = 0 if days_to_anchor <= 14 else random.randint(0, 200)

            # ── OVERSTOCK SKUs in WH-EAST: growing excess ──
            elif sku in OVERSTOCK_SKUS and wh == "WH-EAST":
                if days_to_anchor > 60:
                    qty_oh = base_qty + random.randint(-80, 80)
                else:
                    # Inventory growing because demand dropped but replenishment continued
                    growth = int(base_qty * 4.0 * (1 - days_to_anchor / 60.0))
                    qty_oh = base_qty + growth + random.randint(-30, 30)
                qty_in_transit = random.randint(50, 200)
                qty_on_order = random.randint(100, 400)

            # ── OVERSTOCK SKUs in WH-WEST: critically low ──
            elif sku in OVERSTOCK_SKUS and wh == "WH-WEST":
                if days_to_anchor > 45:
                    qty_oh = base_qty + random.randint(-80, 80)
                else:
                    # Declining because this WH gets less replenishment
                    decline_pct = max(0.15, days_to_anchor / 45.0 * 0.7)
                    qty_oh = max(10, int(base_qty * decline_pct) + random.randint(-20, 20))
                qty_in_transit = random.randint(0, 30)
                qty_on_order = random.randint(0, 100)

            else:
                # Normal products: steady with noise
                seasonal = 1.0 + 0.1 * math.sin(2 * math.pi * day_offset / 365)
                qty_oh = max(10, int(base_qty * seasonal) + random.randint(-80, 80))
                qty_in_transit = random.randint(0, int(base_qty * 0.3))
                qty_on_order = random.randint(0, int(base_qty * 0.5))

            qty_allocated = random.randint(0, max(1, int(qty_oh * 0.3)))
            qty_available = max(0, qty_oh - qty_allocated)

            # Days of supply calculation
            daily_demand = max(1, int(base_qty / 30))
            dos = round(qty_oh / daily_demand, 1) if daily_demand > 0 else 999

            # Reorder flag
            safety_days = {"A": 14, "B": 10, "C": 7}[prod["abc_class"]]
            reorder = dos < safety_days

            rows.append([
                current_date.isoformat(), sku, wh,
                qty_oh, qty_allocated, qty_available, qty_in_transit, qty_on_order,
                dos, reorder
            ])

    headers = ["snapshot_date", "product_id", "warehouse_id",
               "qty_on_hand", "qty_allocated", "qty_available",
               "qty_in_transit", "qty_on_order", "days_of_supply", "reorder_flag"]
    write_csv(SNOWFLAKE_DIR / "inventory_daily.csv", headers, rows)
    return rows


def gen_demand_forecast(anchor):
    """Generate demand_forecast with manual override engineered."""
    rows = []
    fc_counter = 0
    start = anchor - timedelta(days=365)

    all_skus = list(ALL_PRODUCTS.keys())
    warehouses = ["WH-EAST", "WH-WEST", "WH-CENTRAL", "WH-SOUTH"]

    for month_offset in range(12):
        period_start = start + timedelta(days=month_offset * 30)
        period_end = period_start + timedelta(days=29)
        forecast_date = period_start - timedelta(days=random.randint(5, 15))
        months_ago = 11 - month_offset

        for sku in all_skus:
            prod = ALL_PRODUCTS[sku]
            # Base demand by ABC
            base_demand = {"A": 450, "B": 200, "C": 80}[prod["abc_class"]]
            # Seasonal factor
            seasonal = 1.0 + 0.15 * math.sin(2 * math.pi * (month_offset - 3) / 12)
            stat_forecast = int(base_demand * seasonal + random.randint(-20, 20))

            # ── INDUSTRIAL FASTENERS: override disaster ──
            if sku in OVERSTOCK_SKUS:
                if months_ago <= 2:
                    # Statistical model caught the decline
                    stat_forecast = int(base_demand * 0.7 + random.randint(-15, 15))

                if months_ago == 2:
                    # J. Martinez overrode upward right before the drop
                    fc_counter += 1
                    # Statistical version
                    rows.append([
                        f"FC-{fc_counter:05d}", sku, "WH-EAST",
                        forecast_date.isoformat(), period_start.isoformat(),
                        period_end.isoformat(),
                        stat_forecast, "statistical", 0.72, "System"
                    ])
                    fc_counter += 1
                    # Manual override version (the one that was used)
                    override_qty = int(base_demand * 1.3 + random.randint(-10, 10))
                    rows.append([
                        f"FC-{fc_counter:05d}", sku, "WH-EAST",
                        (forecast_date + timedelta(days=3)).isoformat(),
                        period_start.isoformat(), period_end.isoformat(),
                        override_qty, "manual_override", 0.0, "J. Martinez"
                    ])
                    continue
                elif months_ago <= 1:
                    # After the drop: statistical adjusted, override stayed high
                    fc_counter += 1
                    rows.append([
                        f"FC-{fc_counter:05d}", sku, "WH-EAST",
                        forecast_date.isoformat(), period_start.isoformat(),
                        period_end.isoformat(),
                        stat_forecast, "statistical", 0.65, "System"
                    ])
                    fc_counter += 1
                    rows.append([
                        f"FC-{fc_counter:05d}", sku, "WH-EAST",
                        (forecast_date + timedelta(days=2)).isoformat(),
                        period_start.isoformat(), period_end.isoformat(),
                        int(base_demand * 1.2), "manual_override", 0.0, "J. Martinez"
                    ])
                    continue

            # ── SAFETY EQUIPMENT: seasonal pattern ──
            if prod["category"] == "Safety Equipment":
                # Last year had a seasonal ramp in months 8-11 (summer/fall)
                if 3 <= month_offset <= 6:
                    stat_forecast = int(base_demand * 1.35 + random.randint(-10, 10))
                    confidence = 0.6  # low confidence, only 1 year data
                else:
                    confidence = 0.8
                fc_counter += 1
                rows.append([
                    f"FC-{fc_counter:05d}", sku, random.choice(warehouses),
                    forecast_date.isoformat(), period_start.isoformat(),
                    period_end.isoformat(),
                    stat_forecast, "consensus", confidence, "System"
                ])
                continue

            # Normal forecast
            method = random.choices(
                ["statistical", "consensus", "manual_override"],
                weights=[60, 30, 10], k=1
            )[0]
            confidence = round(random.uniform(0.7, 0.95), 2)
            created_by = "System" if method != "manual_override" else random.choice(["A. Chen", "R. Patel", "System"])

            fc_counter += 1
            rows.append([
                f"FC-{fc_counter:05d}", sku, random.choice(warehouses),
                forecast_date.isoformat(), period_start.isoformat(),
                period_end.isoformat(),
                stat_forecast, method, confidence, created_by
            ])

    headers = ["forecast_id", "product_id", "warehouse_id", "forecast_date",
               "period_start", "period_end", "forecast_qty", "forecast_method",
               "confidence_level", "created_by"]
    write_csv(SNOWFLAKE_DIR / "demand_forecast.csv", headers, rows)
    return rows


def gen_supplier_scorecards(anchor):
    """Generate supplier_scorecards with stale Apex risk rating."""
    rows = []
    sc_counter = 0

    apex_otif =    [0.94, 0.91, 0.87, 0.83, 0.79, 0.76]
    apex_lt =      [12,   13,   15,   16,   18,   19]
    apex_reject =  [0.02, 0.028,0.041,0.053,0.062,0.07]

    for month_offset in range(12):
        month_date = anchor - timedelta(days=(11 - month_offset) * 30)
        month_str = month_date.strftime("%Y-%m-01")
        months_ago = 11 - month_offset

        for (sid, name, country, region, tier, cat, _, pt, ltd) in SUPPLIERS:
            sc_counter += 1

            if sid == "SUP-1001":  # Apex
                if months_ago <= 5:
                    idx = 5 - months_ago
                    otif = apex_otif[idx]
                    avg_lt = apex_lt[idx]
                    rr = apex_reject[idx]
                else:
                    otif = round(0.93 + random.uniform(0, 0.03), 3)
                    avg_lt = random.randint(11, 14)
                    rr = round(random.uniform(0.015, 0.025), 3)
                # STALE risk rating - stays medium even as performance degrades
                risk = "medium"
                spend = round(random.uniform(120000, 180000), 2)
                qs = round(otif * 100 - rr * 200, 1)

            elif sid == "SUP-1002":  # GlobalParts - always good
                otif = round(0.96 + random.uniform(0, 0.02), 3)
                avg_lt = random.randint(8, 11)
                rr = round(random.uniform(0.005, 0.015), 3)
                risk = "low"
                spend = round(random.uniform(80000, 120000), 2)
                qs = round(otif * 100 - rr * 100, 1)

            else:
                # Normal suppliers
                otif = round(random.uniform(0.91, 0.98), 3)
                avg_lt = random.randint(int(ltd * 0.8), int(ltd * 1.2))
                rr = round(random.uniform(0.005, 0.03), 3)
                if otif >= 0.95:
                    risk = "low"
                elif otif >= 0.90:
                    risk = "medium"
                else:
                    risk = "high"
                spend = round(random.uniform(30000, 100000), 2)
                qs = round(otif * 100 - rr * 150, 1)

            order_count = random.randint(15, 45) if sid in ("SUP-1001", "SUP-1002", "SUP-1003") else random.randint(5, 20)

            rows.append([
                f"SC-{sc_counter:05d}", sid, month_str,
                otif, avg_lt, rr, order_count, spend, qs, risk
            ])

    headers = ["scorecard_id", "supplier_id", "month", "otif_pct",
               "avg_lead_time_days", "reject_rate_pct", "order_count",
               "total_spend", "quality_score", "risk_rating"]
    write_csv(SNOWFLAKE_DIR / "supplier_scorecards.csv", headers, rows)
    return rows


def gen_sales_orders(anchor):
    """Generate sales_orders with backorder and OTIF degradation patterns."""
    rows = []
    so_counter = 2000
    start = anchor - timedelta(days=365)
    all_skus = list(ALL_PRODUCTS.keys())
    customers = [c[0] for c in CUSTOMER_NAMES]
    warehouses = ["WH-EAST", "WH-WEST", "WH-CENTRAL", "WH-SOUTH"]

    # Customer tier weights (platinum orders more)
    tier_order_weights = {}
    for c in CUSTOMER_NAMES:
        cid, _, _, _, _, _, _, tier = c
        if tier == "platinum":
            tier_order_weights[cid] = 8
        elif tier == "gold":
            tier_order_weights[cid] = 5
        elif tier == "silver":
            tier_order_weights[cid] = 3
        else:
            tier_order_weights[cid] = 1

    for month_offset in range(12):
        month_start = start + timedelta(days=month_offset * 30)
        month_end = month_start + timedelta(days=29)
        if month_end > anchor:
            month_end = anchor
        months_ago = 11 - month_offset

        # ~450 lines per month
        lines_this_month = random.randint(420, 480)

        # ── INDUSTRIAL FASTENERS DEMAND DROP ──
        if months_ago <= 2:
            fastener_reduction = 0.35
        else:
            fastener_reduction = 0.0

        # ── SAFETY EQUIPMENT SEASONAL RAMP (historical) ──
        safety_seasonal = 1.0
        if 5 <= month_offset <= 8:
            safety_seasonal = 1.35  # summer/fall ramp last year

        for _ in range(lines_this_month):
            so_counter += 1
            so_id = f"SO-{so_counter}"
            so_line = 1

            # Pick customer weighted by tier
            cid = random.choices(
                list(tier_order_weights.keys()),
                weights=list(tier_order_weights.values()),
                k=1
            )[0]

            # Pick SKU
            sku = random.choice(all_skus)
            prod = ALL_PRODUCTS[sku]

            # Skip some fastener orders if in demand drop window
            if sku in OVERSTOCK_SKUS and months_ago <= 2:
                if random.random() < fastener_reduction:
                    continue

            # Safety equipment seasonal boost
            if prod["category"] == "Safety Equipment" and safety_seasonal > 1.0:
                # Add extra orders by not skipping
                pass

            wh = random.choice(warehouses)
            order_date = rand_weekday(month_start, month_end)
            qty = random.choices([5, 10, 25, 50, 100], weights=[15, 30, 30, 20, 5], k=1)[0]

            req_del = order_date + timedelta(days=random.randint(3, 14))
            promised_del = req_del + timedelta(days=random.choice([0, 0, 0, 1, 2]))

            # ── BACKORDER & LATE DELIVERY PATTERNS ──
            if sku in APEX_CRISIS_SKUS and months_ago == 0:
                # Recent orders for Apex SKUs: some backordered
                if random.random() < 0.35:
                    status = "backordered"
                    actual_ship = None
                    actual_del = None
                    qty_shipped = 0
                    qty_bo = qty
                else:
                    # Shipped but late
                    delay = random.randint(3, 8)
                    actual_ship = promised_del + timedelta(days=delay - 2)
                    actual_del = promised_del + timedelta(days=delay)
                    if actual_del > anchor:
                        status = "shipped"
                        actual_del = None
                        qty_shipped = qty
                        qty_bo = 0
                    else:
                        status = "delivered"
                        qty_shipped = qty
                        qty_bo = 0
            elif sku in APEX_CRISIS_SKUS and months_ago == 1:
                # Month before: late deliveries ramping up
                if random.random() < 0.2:
                    delay = random.randint(2, 6)
                    actual_ship = promised_del + timedelta(days=delay - 2)
                    actual_del = promised_del + timedelta(days=delay)
                    status = "delivered"
                    qty_shipped = qty
                    qty_bo = 0
                else:
                    actual_ship = promised_del - timedelta(days=random.randint(0, 2))
                    actual_del = promised_del + timedelta(days=random.choice([-1, 0, 0, 0, 1]))
                    status = "delivered"
                    qty_shipped = qty
                    qty_bo = 0
            else:
                # Normal: mostly on time
                if months_ago <= 1 and random.random() < 0.06:
                    # Small baseline of late deliveries (non-Apex)
                    delay = random.randint(1, 3)
                    actual_ship = promised_del + timedelta(days=delay - 1)
                    actual_del = promised_del + timedelta(days=delay)
                else:
                    actual_ship = promised_del - timedelta(days=random.randint(0, 3))
                    actual_del = promised_del + timedelta(days=random.choice([-1, 0, 0, 0, 0, 1]))

                if actual_del and actual_del > anchor:
                    status = "shipped" if actual_ship and actual_ship <= anchor else "processing"
                    actual_del = None
                    if status == "processing":
                        actual_ship = None
                    qty_shipped = qty if status == "shipped" else 0
                    qty_bo = 0
                else:
                    status = "delivered"
                    qty_shipped = qty
                    qty_bo = 0

            # ── MERIDIAN BACKORDERS ──
            if cid == "CUST-0012" and sku in APEX_CRISIS_SKUS and months_ago == 0 and status != "backordered":
                # Force some Meridian orders to be backordered
                if random.random() < 0.7:
                    status = "backordered"
                    actual_ship = None
                    actual_del = None
                    qty_shipped = 0
                    qty_bo = qty
                    # Make these higher-value orders
                    qty = random.choice([50, 100, 150])
                    qty_bo = qty

            revenue = round(qty * prod["unit_price"], 2)

            rows.append([
                so_id, so_line, cid, sku, wh,
                order_date.isoformat(),
                req_del.isoformat(),
                promised_del.isoformat(),
                actual_ship.isoformat() if actual_ship else "",
                actual_del.isoformat() if actual_del else "",
                qty, qty_shipped, qty_bo,
                prod["unit_price"], revenue, status
            ])

    # ── ENGINEER SPECIFIC MERIDIAN BACKORDERS ──
    # Ensure we have the ~$380K target
    # EC-1847=$142, EC-2291=$112, EC-3004=$209 → need high qty
    for i, sku in enumerate(APEX_CRISIS_SKUS[:3]):
        so_counter += 1
        prod = ALL_PRODUCTS[sku]
        qty = [900, 1000, 700][i]  # ~$127K + ~$112K + ~$146K = ~$385K
        order_date = anchor - timedelta(days=random.randint(3, 10))
        rev = round(qty * prod["unit_price"], 2)
        rows.append([
            f"SO-{so_counter}", 1, "CUST-0012", sku, "WH-EAST",
            order_date.isoformat(),
            (order_date + timedelta(days=7)).isoformat(),
            (order_date + timedelta(days=8)).isoformat(),
            "", "", qty, 0, qty,
            prod["unit_price"], rev, "backordered"
        ])

    # Add a couple for other gold/platinum customers
    for cid in ["CUST-0025", "CUST-0067"]:
        so_counter += 1
        sku = random.choice(APEX_CRISIS_SKUS)
        prod = ALL_PRODUCTS[sku]
        qty = random.choice([200, 300, 400])
        order_date = anchor - timedelta(days=random.randint(3, 12))
        rev = round(qty * prod["unit_price"], 2)
        rows.append([
            f"SO-{so_counter}", 1, cid, sku, random.choice(warehouses),
            order_date.isoformat(),
            (order_date + timedelta(days=7)).isoformat(),
            (order_date + timedelta(days=8)).isoformat(),
            "", "", qty, 0, qty,
            prod["unit_price"], rev, "backordered"
        ])

    headers = ["so_id", "so_line_id", "customer_id", "product_id", "warehouse_id",
               "order_date", "requested_delivery_date", "promised_delivery_date",
               "actual_ship_date", "actual_delivery_date",
               "qty_ordered", "qty_shipped", "qty_backordered",
               "unit_price", "revenue", "status"]
    write_csv(DATABRICKS_DIR / "sales_orders.csv", headers, rows)
    return rows


def gen_shipments(anchor):
    """Generate shipments with expedited spike pattern."""
    rows = []
    shp_counter = 5000
    start = anchor - timedelta(days=365)

    all_skus = list(ALL_PRODUCTS.keys())
    warehouses = ["WH-EAST", "WH-WEST", "WH-CENTRAL", "WH-SOUTH"]

    for month_offset in range(12):
        month_start = start + timedelta(days=month_offset * 30)
        month_end = month_start + timedelta(days=29)
        if month_end > anchor:
            month_end = anchor
        months_ago = 11 - month_offset

        # ~400 shipments per month
        n_shipments = random.randint(370, 430)

        for _ in range(n_shipments):
            shp_counter += 1
            shp_id = f"SHP-{shp_counter}"

            # 60% outbound (SO), 40% inbound (PO)
            if random.random() < 0.6:
                ref_type = "SO"
                ref_id = f"SO-{random.randint(2001, 2001 + 5400)}"
            else:
                ref_type = "PO"
                ref_id = f"PO-{random.randint(1001, 1001 + 3200)}"

            origin_wh = random.choice(warehouses)
            dest = random.choice([
                "Hartford, CT", "Portland, OR", "Detroit, MI", "Atlanta, GA",
                "Reno, NV", "Boston, MA", "Charlotte, NC", "Omaha, NE",
                "Cleveland, OH", "Long Beach, CA", "Houston, TX", "Indianapolis, IN"
            ])

            ship_date = rand_weekday(month_start, month_end)

            # ── EXPEDITED SPIKE in last 6 weeks for Apex SKUs ──
            is_expedited = False
            if months_ago == 0 or (months_ago == 1 and (month_end - month_start).days > 12):
                if random.random() < 0.28:  # 18% expedited rate (was ~5% before)
                    is_expedited = True
            else:
                if random.random() < 0.05:  # Normal 5% expedited rate
                    is_expedited = True

            carrier = random.choice(CARRIERS)
            if is_expedited:
                carrier = "FastTrack Logistics"  # FastTrack handles most expedited
                mode = "air"
                transit_days = random.randint(1, 3)
                base_freight = round(random.uniform(180, 450) * 2.4, 2)  # 2.4x premium
            else:
                mode = random.choices(
                    ["ground", "LTL", "FTL"],
                    weights=[50, 30, 20], k=1
                )[0]
                transit_days = random.randint(3, 10)
                base_freight = round(random.uniform(120, 380), 2)

            est_arrival = ship_date + timedelta(days=transit_days)

            # Actual arrival
            if est_arrival > anchor:
                actual_arrival = None
                status = "in_transit"
            else:
                arrival_var = random.choices(
                    [-1, 0, 0, 0, 1, 2, 3],
                    weights=[5, 30, 30, 15, 10, 7, 3], k=1
                )[0]
                actual_arrival = est_arrival + timedelta(days=arrival_var)
                if actual_arrival > anchor:
                    actual_arrival = None
                    status = "in_transit"
                elif arrival_var > 1:
                    status = "delayed"
                else:
                    status = "delivered"

            weight = round(random.uniform(10, 500), 1)

            rows.append([
                shp_id, ref_type, ref_id, carrier, mode,
                origin_wh, dest,
                ship_date.isoformat(),
                est_arrival.isoformat(),
                actual_arrival.isoformat() if actual_arrival else "",
                base_freight, is_expedited, weight, status
            ])

    headers = ["shipment_id", "reference_type", "reference_id", "carrier_name",
               "mode", "origin_warehouse_id", "destination",
               "ship_date", "estimated_arrival", "actual_arrival",
               "freight_cost", "is_expedited", "weight_kg", "status"]
    write_csv(DATABRICKS_DIR / "shipments.csv", headers, rows)
    return rows


def gen_returns(anchor):
    """Generate returns with late_delivery spike."""
    rows = []
    ret_counter = 0
    start = anchor - timedelta(days=365)

    all_skus = list(ALL_PRODUCTS.keys())
    customers = [c[0] for c in CUSTOMER_NAMES]

    for month_offset in range(12):
        month_start = start + timedelta(days=month_offset * 30)
        month_end = month_start + timedelta(days=29)
        if month_end > anchor:
            month_end = anchor
        months_ago = 11 - month_offset

        # ~25-35 returns per month normally
        if months_ago <= 1:
            n_returns = random.randint(40, 55)  # spike
        else:
            n_returns = random.randint(22, 32)

        for _ in range(n_returns):
            ret_counter += 1
            return_id = f"RET-{ret_counter:05d}"
            so_id = f"SO-{random.randint(2001, 2001 + 5400)}"
            so_line = 1
            cid = random.choice(customers)
            sku = random.choice(all_skus)
            prod = ALL_PRODUCTS[sku]
            return_date = rand_weekday(month_start, month_end)
            qty = random.randint(1, 25)

            if months_ago <= 1:
                # Recent: heavy skew to late_delivery + supplier_attributable
                reason = random.choices(
                    ["defective", "damaged_in_transit", "wrong_item", "late_delivery", "customer_change"],
                    weights=[15, 12, 8, 40, 10],
                    k=1
                )[0]
                if reason == "late_delivery":
                    supplier_attr = random.random() < 0.72
                else:
                    supplier_attr = random.random() < 0.15
            else:
                # Normal distribution
                reason = random.choices(
                    ["defective", "damaged_in_transit", "wrong_item", "late_delivery", "customer_change"],
                    weights=[30, 25, 15, 15, 15],
                    k=1
                )[0]
                supplier_attr = random.random() < 0.25

            disposition = random.choices(
                ["restock", "scrap", "return_to_supplier"],
                weights=[50, 20, 30], k=1
            )[0]

            refund = round(qty * prod["unit_price"] * random.uniform(0.85, 1.0), 2)

            rows.append([
                return_id, so_id, so_line, cid, sku,
                return_date.isoformat(), qty, reason, disposition,
                refund, supplier_attr
            ])

    # ── MERIDIAN RETURNS ──
    for i in range(2):
        ret_counter += 1
        sku = APEX_CRISIS_SKUS[i]
        prod = ALL_PRODUCTS[sku]
        return_date = anchor - timedelta(days=random.randint(5, 20))
        qty = random.randint(10, 30)
        rows.append([
            f"RET-{ret_counter:05d}",
            f"SO-{random.randint(2001, 7400)}", 1,
            "CUST-0012", sku,
            return_date.isoformat(), qty, "late_delivery", "return_to_supplier",
            round(qty * prod["unit_price"], 2), True
        ])

    headers = ["return_id", "so_id", "so_line_id", "customer_id", "product_id",
               "return_date", "qty_returned", "reason_code", "disposition",
               "refund_amount", "supplier_attributable"]
    write_csv(DATABRICKS_DIR / "returns.csv", headers, rows)
    return rows


def gen_freight_invoices(anchor):
    """Generate freight_invoices with cost spike and dispute patterns."""
    rows = []
    inv_counter = 8000
    start = anchor - timedelta(days=365)

    for month_offset in range(12):
        month_start = start + timedelta(days=month_offset * 30)
        month_end = month_start + timedelta(days=29)
        if month_end > anchor:
            month_end = anchor
        months_ago = 11 - month_offset

        # Match shipment volume roughly
        n_invoices = random.randint(370, 430)

        monthly_spend = 0
        for j in range(n_invoices):
            inv_counter += 1
            inv_id = f"INV-{inv_counter}"
            shp_id = f"SHP-{5001 + month_offset * 400 + j}"
            invoice_date = rand_weekday(month_start, month_end)

            carrier = random.choice(CARRIERS)

            # Base rate depends on mode/carrier
            is_expedited = False
            if months_ago <= 1:
                if random.random() < 0.28:
                    is_expedited = True
            else:
                if random.random() < 0.05:
                    is_expedited = True

            if is_expedited:
                carrier = "FastTrack Logistics"
                base_rate = round(random.uniform(280, 520), 2)
                contracted_rate = round(base_rate * 2.4, 2)
            else:
                base_rate = round(random.uniform(120, 350), 2)
                contracted_rate = round(base_rate * random.uniform(1.0, 1.08), 2)

            # ── FUEL SURCHARGE CREEP for one carrier ──
            if carrier == "Continental Freight":
                # Base fuel surcharge + monthly creep
                fuel_base = 0.08
                creep_months = min(months_ago, 5)
                if months_ago <= 5:
                    fuel_pct = fuel_base + (5 - months_ago) * 0.025
                else:
                    fuel_pct = fuel_base
                fuel_surcharge = round(base_rate * fuel_pct, 2)
            else:
                fuel_surcharge = round(base_rate * random.uniform(0.06, 0.10), 2)

            accessorial = round(random.uniform(0, 45), 2) if random.random() < 0.3 else 0
            total = round(base_rate + fuel_surcharge + accessorial, 2)
            variance = round(total - contracted_rate, 2)

            # Dispute flag: for overcharges
            dispute = False
            if abs(variance) > contracted_rate * 0.15 and variance > 0:
                dispute = random.random() < 0.03  # Very rare in natural data

            monthly_spend += total

            rows.append([
                inv_id, shp_id, carrier,
                invoice_date.isoformat(),
                base_rate, fuel_surcharge, accessorial,
                total, contracted_rate, variance, dispute
            ])

    # ── ENSURE 3 SPECIFIC DISPUTED INVOICES ──
    for i in range(3):
        inv_counter += 1
        inv_date = anchor - timedelta(days=random.randint(5, 35))
        base = round(random.uniform(350, 500), 2)
        contracted = round(base * 2.4, 2)
        overcharge = round(random.uniform(3500, 5500), 2)
        total = round(contracted + overcharge, 2)
        rows.append([
            f"INV-{inv_counter}",
            f"SHP-{5001 + 11 * 400 + 430 + i}",
            "FastTrack Logistics",
            inv_date.isoformat(),
            base, round(base * 0.08, 2), round(random.uniform(20, 60), 2),
            total, contracted, overcharge, True
        ])

    headers = ["invoice_id", "shipment_id", "carrier_name", "invoice_date",
               "base_rate", "fuel_surcharge", "accessorial_charges",
               "total_invoiced", "contracted_rate", "variance_amount", "dispute_flag"]
    write_csv(DATABRICKS_DIR / "freight_invoices.csv", headers, rows)
    return rows


# ── MAIN ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate supply chain demo data")
    parser.add_argument("--anchor-date", type=str, default=None,
                        help="Anchor date YYYY-MM-DD (default: today)")
    parser.add_argument("--seed", type=int, default=SEED,
                        help="Random seed (default: 42)")
    args = parser.parse_args()

    if args.anchor_date:
        anchor = date.fromisoformat(args.anchor_date)
    else:
        anchor = date.today()

    random.seed(args.seed)

    print(f"=" * 60)
    print(f"SUPPLY CHAIN DEMO — DATA GENERATOR")
    print(f"Anchor date: {anchor}")
    print(f"Seed: {args.seed}")
    print(f"History: {HISTORY_MONTHS} months")
    print(f"=" * 60)

    print(f"\n── Snowflake tables ──")
    gen_products(anchor)
    gen_suppliers(anchor)
    gen_warehouses(anchor)
    gen_customers(anchor)
    gen_purchase_orders(anchor)
    gen_inventory_daily(anchor)
    gen_demand_forecast(anchor)
    gen_supplier_scorecards(anchor)

    print(f"\n── Databricks tables ──")
    gen_sales_orders(anchor)
    gen_shipments(anchor)
    gen_returns(anchor)
    gen_freight_invoices(anchor)

    print(f"\n{'=' * 60}")
    print(f"GENERATION COMPLETE")
    print(f"Snowflake CSVs: {SNOWFLAKE_DIR}")
    print(f"Databricks CSVs: {DATABRICKS_DIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
